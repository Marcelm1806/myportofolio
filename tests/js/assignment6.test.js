import test from "node:test";
import assert from "node:assert/strict";
import { bindEducationEditor } from "../../static/js/education-edit.js";
import { requestJson } from "../../static/js/rest.js";

const entry = {
    id: "95fe8643-2c05-45ac-9d2f-0eeaacb205ee",
    institution: "Example University", degree: "Example degree", description: "",
    start_year: 2020, end_year: 2023, is_current: false, website: "", display_order: 0,
};
const json = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });
const preventDefault = () => {};

function control(properties = {}) {
    const listeners = new Map();
    return {
        ...properties,
        addEventListener(name, handler) { listeners.set(name, handler); },
        emit(name, event = {}) { return listeners.get(name)?.(event); },
        focus() { document.activeElement = this; },
    };
}

function harness(t, handle) {
    const fields = Object.fromEntries(Object.entries(entry).filter(([name]) => name !== "id").map(([name, value]) => {
        const attributes = new Map();
        const group = { classList: { add() {}, remove() {} }, append(list) { this.error = list; } };
        return [name, control({
            id: "edit_" + name, name, type: typeof value === "boolean" ? "checkbox" : "text",
            labels: [{ textContent: name === "degree" ? "Degree / programme *" : name }],
            closest: () => group, group,
            setAttribute: (key, value) => attributes.set(key, value),
            getAttribute: key => attributes.get(key),
            removeAttribute: key => attributes.delete(key),
        })];
    }));
    const fieldset = { elements: Object.values(fields) };
    const submit = control();
    const restore = control();
    const close = control();
    const summary = control();
    const loading = control();
    const status = control();
    const link = control({ dataset: { educationEdit: entry.id, url: "/api/v1/education/" + entry.id + "/" } });
    const form = control({
        querySelector: key => ({
            fieldset, '[type="submit"]': submit, "[data-edit-restore]": restore,
            "[data-edit-status]": status, "[data-edit-error]": summary,
        })[key],
        querySelectorAll: () => [],
        elements: { namedItem: name => fields[name] },
        setAttribute() {}, removeAttribute() {},
    });
    const dialog = control({
        querySelector: key => ({ form, "[data-edit-load]": loading })[key],
        querySelectorAll: () => [close],
        showModal() { this.open = true; },
        close() { this.open = false; document.activeElement = document.body; },
    });
    const grid = control({ contains: () => true, querySelectorAll: () => [link] });
    const fakeDocument = {
        body: {}, createElement: () => ({ dataset: {}, append(child) { this.child = child; } }),
    };
    const previousDocument = globalThis.document;
    globalThis.document = fakeDocument;
    t.after(() => { globalThis.document = previousDocument; });
    const NativeFormData = globalThis.FormData;
    t.mock.method(globalThis, "FormData", function () {
        const data = new NativeFormData();
        if (!fieldset.disabled) {
            for (const field of fieldset.elements) {
                if (field.type !== "checkbox" || field.checked) data.set(field.name, field.value ?? "on");
            }
        }
        return data;
    });
    const calls = [];
    const notices = [];
    let refreshes = 0;
    bindEducationEditor({
        grid, dialog, csrfToken: "test-csrf", refresh: async () => { refreshes += 1; },
        notify: (...args) => notices.push(args),
        send: (url, options) => requestJson(url, {
            ...options, fetchImpl: (path, init) => {
                calls.push({ path, ...init });
                return handle(path, init);
            },
        }),
    });
    return {
        dialog, form, submit, restore, close, fields, loading, summary, status, calls, notices, link,
        open: (target = link) => grid.emit("click", { target: { closest: () => target }, button: 0, preventDefault }),
        save: () => form.emit("submit", { preventDefault }),
        get refreshes() { return refreshes; },
    };
}

test("edit loads the detail, sends only changed values with PATCH and refreshes the list once", async t => {
    let finishSave;
    const h = harness(t, async (path, { method }) => method === "GET"
        ? json(entry) : new Promise(resolve => { finishSave = () => resolve(json(entry)); }));
    await h.open();
    assert.equal(h.calls[0].method, "GET");
    assert.equal(h.calls[0].path, h.link.dataset.url);
    assert.equal(h.calls[0].cache, "no-store");
    assert.equal(h.calls[0].headers["X-CSRFToken"], undefined);
    assert.equal(h.fields.degree.value, entry.degree);
    assert.equal(h.submit.disabled, true);
    await h.save();
    assert.equal(h.calls.length, 1);
    h.fields.degree.value = "Updated degree";
    h.fields.is_current.checked = true;
    h.fields.end_year.value = "";
    h.form.emit("input");
    assert.match(h.status.textContent, /Degree \/ programme/);
    const saved = h.save();
    await h.save();
    assert.equal(h.calls.length, 2);
    assert.equal(h.calls[1].method, "PATCH");
    assert.equal(h.calls[1].headers["X-CSRFToken"], "test-csrf");
    assert.deepEqual(JSON.parse(h.calls[1].body), {
        degree: "Updated degree", end_year: null, is_current: true,
    });
    assert.equal(h.submit.disabled, true);
    finishSave();
    await saved;
    assert.equal(h.refreshes, 1);
    assert.equal(h.dialog.open, false);
    assert.equal(h.notices.at(-1)[2], "success");
    assert.equal(document.activeElement, h.link);
});

test("validation and permission errors keep the draft and explain the failed save", async t => {
    let response = json({ degree: ["<b>Enter a degree</b>"] }, 400);
    const h = harness(t, async (path, { method }) => method === "GET" ? json(entry) : response);
    await h.open();
    h.fields.degree.value = "<b> </b>";
    h.form.emit("input");
    await h.save();
    assert.equal(h.fields.degree.group.error.child.textContent, "<b>Enter a degree</b>");
    assert.equal(h.fields.degree.getAttribute("aria-invalid"), "true");
    assert.match(h.notices.at(-1)[1], /Enter a degree/);
    response = json({ detail: "You do not have permission to perform this action." }, 403);
    await h.save();
    assert.match(h.notices.at(-1)[1], /do not have permission/);
    assert.equal(h.notices.at(-1)[2], "error");
    assert.equal(h.fields.degree.value, "<b> </b>");
    assert.equal(h.dialog.open, true);
    assert.equal(h.submit.disabled, false);
    assert.equal(h.refreshes, 0);
});

test("restore discards unsaved values locally and prevents an empty update", async t => {
    const h = harness(t, async () => json(entry));
    await h.open();
    h.fields.degree.value = "Unwanted change";
    h.form.emit("input");
    assert.equal(h.restore.disabled, false);
    h.restore.emit("click");
    assert.equal(h.fields.degree.value, entry.degree);
    assert.equal(h.submit.disabled, true);
    await h.save();
    assert.equal(h.calls.length, 1);
});

test("a cancelled detail request cannot overwrite the next entry", async t => {
    let finishFirst;
    const another = { ...entry, id: "b8d8384c-36f8-4c83-b4fc-04c63058cf21", institution: "Other university" };
    const anotherLink = { dataset: { educationEdit: another.id, url: "/api/v1/education/" + another.id + "/" } };
    const h = harness(t, async path => path === anotherLink.dataset.url ? json(another)
        : new Promise(resolve => { finishFirst = () => resolve(json(entry)); }));
    const first = h.open();
    h.close.emit("click");
    assert.equal(h.calls[0].signal.aborted, true);
    await h.open(anotherLink);
    finishFirst();
    await first;
    assert.equal(h.fields.institution.value, another.institution);
    assert.equal(h.dialog.open, true);
    assert.equal(h.notices.length, 0);
});
