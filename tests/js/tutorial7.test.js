import test from "node:test";
import assert from "node:assert/strict";
import { formPayload, requestJson, submitRestForm, bindRestCardActions } from "../../static/js/rest.js";
import { renderProjectCard } from "../../static/js/project-utils.js";

const id = "65f44391-a5c3-4eaa-a97a-b19dcc4c6937";
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

test("JSON payloads use real booleans, numbers and null and exclude privileged fields", () => {
    const data = new FormData();
    for (const [key, value] of Object.entries({ institution: "University", degree: "Course", start_year: "2024",
        end_year: "", display_order: "2", csrfmiddlewaretoken: "secret", id, starred_by: "other" })) data.set(key, value);
    assert.deepEqual(formPayload(data, "education"), {
        institution: "University", degree: "Course", description: "", website: "",
        start_year: 2024, end_year: null, is_current: false, display_order: 2,
    });
    data.set("is_current", "on");
    assert.equal(formPayload(data, "education").is_current, true);
    data.set("title", "Project");
    assert.equal(formPayload(data, "project").is_featured, false);
    data.set("is_featured", "on");
    assert.equal(formPayload(data, "project").is_featured, true);
});

test("POST PUT and PATCH use JSON with session credentials and CSRF", async () => {
    for (const method of ["POST", "PUT", "PATCH"]) {
        const result = await requestJson(`/api/v1/projects/${id}/`, {
            method, csrfToken: "token", data: { title: "New", is_featured: false },
            fetchImpl: async (url, options) => {
                assert.equal(options.method, method);
                assert.equal(options.credentials, "same-origin");
                assert.equal(options.headers["X-CSRFToken"], "token");
                assert.equal(options.headers.Accept, "application/json");
                assert.equal(options.headers["Content-Type"], "application/json");
                assert.deepEqual(JSON.parse(options.body), { title: "New", is_featured: false });
                return response({ id, title: "New" });
            },
        });
        assert.equal(result.id, id);
    }
});

test("DELETE 204 never attempts to parse the empty response body", async () => {
    const result = await requestJson(`/api/v1/projects/${id}/`, {
        method: "DELETE", csrfToken: "token", successStatus: 204,
        fetchImpl: async (url, options) => {
            assert.equal(options.method, "DELETE");
            assert.equal(options.headers["X-CSRFToken"], "token");
            assert.equal(options.body, undefined);
            return { ok: true, status: 204, json() { assert.fail("204 has no JSON body"); } };
        },
    });
    assert.equal(result, null);
});

test("DRF field and non-field errors become safe form messages; detail is retained", async () => {
    await assert.rejects(requestJson("/api/v1/projects/", {
        fetchImpl: async () => response({ title: ["<img src=x>"], non_field_errors: ["Invalid combination"] }, 400),
    }), error => {
        assert.deepEqual(error.errors, { title: [{ message: "<img src=x>" }], non_field_errors: [{ message: "Invalid combination" }] });
        assert.match(error.message, /highlighted fields/);
        return true;
    });
    await assert.rejects(requestJson("/api/v1/projects/", {
        fetchImpl: async () => response({ detail: "Permission denied." }, 403),
    }), /Permission denied/);
});

test("HTML, legacy JSON and uncertain network results are not reported as success", async () => {
    const html = status => ({ ok: status === 200, status, json: async () => { throw new SyntaxError(); } });
    await assert.rejects(requestJson("/api/v1/projects/", { fetchImpl: async () => html(403) }), /session or permission/);
    await assert.rejects(requestJson("/api/v1/projects/", { fetchImpl: async () => html(200) }), /Unexpected response/);
    await assert.rejects(requestJson("/api/v1/projects/", { fetchImpl: async () => response({ pk: id }) }), /Unexpected response/);
    let attempts = 0;
    await assert.rejects(requestJson("/api/v1/projects/", {
        fetchImpl: async () => { attempts += 1; throw new TypeError("Offline"); },
    }), /may have reached the server/);
    assert.equal(attempts, 1);
});

test("the creation adapter accepts flat 201 and supplies the existing toast message", async () => {
    const data = new FormData();
    data.set("title", "Test project");
    const result = await submitRestForm("/api/v1/projects/", data, "csrf", {
        label: "project", fetchImpl: async (url, options) => {
            assert.equal(JSON.parse(options.body).is_featured, false);
            assert.equal(JSON.parse(options.body).title, "Test project");
            return response({ id, title: "Test project" }, 201);
        },
    });
    assert.equal(result.id, id);
    assert.equal(result.message, "Project added successfully.");
});

test("guest, member and owner cards use flat data and the correct REST controls", () => {
    const record = { id, title: "Project", summary: "Summary", contribution: "Work", organization: "UI",
        star_count: 0, is_starred: false, urls: { detail: `/projects/${id}/`, api_detail: `/api/v1/projects/${id}/`, star: `/api/v1/projects/${id}/star/` } };
    const guest = renderProjectCard(record, { loginUrl: "/login/" });
    assert.match(guest, /href="\/login\/"/);
    assert.doesNotMatch(guest, /data-rest-action/);
    const member = renderProjectCard(record, { isAuthenticated: true });
    assert.match(member, /data-rest-action="star"/);
    assert.doesNotMatch(member, /data-rest-action="delete"/);
    const owner = renderProjectCard(record, { isAuthenticated: true, isSuperuser: true });
    assert.match(owner, /data-rest-action="delete"/);
    assert.match(owner, new RegExp(`data-url="/api/v1/projects/${id}/"`));
    assert.match(owner, /popover="auto"/);
});

function actionHarness(t, action, send) {
    const previousDocument = globalThis.document;
    const popover = { hidePopover() { this.hidden = true; } };
    const button = { dataset: { restAction: action, restId: id, url: `/api/v1/projects/${id}/${action === "star" ? "star/" : ""}` },
        closest: () => popover, focus() { this.focused = true; } };
    const handlers = {};
    const grid = { contains: element => element === button, querySelectorAll: () => [button],
        querySelector: () => button, addEventListener: (name, handler) => { handlers[name] = handler; } };
    const notices = [];
    const fallback = { focus() { this.focused = true; } };
    let refreshes = 0;
    globalThis.document = { activeElement: button, body: {} };
    t.after(() => { if (previousDocument === undefined) delete globalThis.document; else globalThis.document = previousDocument; });
    const binding = bindRestCardActions({ grid, csrfToken: "csrf", notify: (...args) => notices.push(args),
        fallbackFocus: fallback, refresh: async () => { refreshes += 1; }, send });
    return { button, grid, notices, popover, fallback, binding, handlers,
        click: () => handlers.click({ target: { closest: () => button } }), get refreshes() { return refreshes; } };
}

test("pending delete submits once, keeps confirmation until success, then refreshes", async t => {
    const pending = deferred();
    let calls = 0;
    const h = actionHarness(t, "delete", async (url, options) => {
        calls += 1;
        assert.equal(options.method, "DELETE");
        assert.equal(options.successStatus, 204);
        return pending.promise;
    });
    const saving = h.click();
    assert.equal(h.button.disabled, true);
    assert.equal(h.popover.hidden, undefined);
    await h.click();
    assert.equal(calls, 1);
    pending.resolve(null);
    await saving;
    assert.equal(h.popover.hidden, true);
    assert.equal(h.refreshes, 1);
    assert.equal(h.notices[0][2], "success");
    assert.equal(h.button.disabled, false);
});

test("failed mutations keep the dialog, unlock the action and do not refresh", async t => {
    const h = actionHarness(t, "delete", async () => { throw new Error("Permission denied."); });
    await h.click();
    assert.equal(h.popover.hidden, undefined);
    assert.equal(h.refreshes, 0);
    assert.equal(h.button.disabled, false);
    assert.equal(h.notices[0][1], "Permission denied.");
    assert.equal(h.notices[0][2], "error");
});

test("star POST refreshes once and restores keyboard focus to the matching action", async t => {
    const h = actionHarness(t, "star", async (url, options) => {
        assert.equal(options.method, "POST");
        assert.equal(options.successStatus, 200);
        return { id, is_starred: true, star_count: 1 };
    });
    await h.click();
    assert.equal(h.refreshes, 1);
    assert.equal(h.button.focused, true);
    assert.equal(h.notices[0][1], "Star added.");
});
