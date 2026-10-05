import test from "node:test";
import assert from "node:assert/strict";
import { normalizeEducationFilters, educationEmptyMessage, renderEducationCard } from "../../static/js/education-utils.js";
import { createListLoader, postForm, AjaxError } from "../../static/js/ajax.js";
import { bindAjaxForm } from "../../static/js/ajax-form.js";

const pk = "65f44391-a5c3-4eaa-a97a-b19dcc4c6937";
const entry = () => ({ pk, fields: {
    institution: "Example University", degree: "M.Sc. Data Science", description: "First\nSecond",
    period_label: "2024–Present", is_current: true, website: "https://example.edu/?a=1&b=2",
    star_count: 3, is_starred: true,
}, urls: { detail: `/education/${pk}/`, edit: `/education/${pk}/edit/`, delete: `/education/${pk}/delete/`, star: `/education/${pk}/star-ajax/` } });
const config = { loginUrl: "/login/", csrfToken: "csrf", isAuthenticated: true, canEdit: true, canManage: true };
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

test("Education retains card styling, period, multiline descriptions and protected actions", () => {
    const html = renderEducationCard(entry(), config);
    for (const fragment of ['class="education-card"', "2024–Present", "First<br>Second", 'aria-pressed="true"', 'class="star-count">3</span>', 'popover="auto"', 'method="post"', 'name="csrfmiddlewaretoken"']) {
        assert.ok(html.includes(fragment), fragment);
    }
    assert.match(html, /rel="noopener noreferrer"/);
    assert.match(html, /https:\/\/example.edu\/\?a=1&amp;b=2/);
});

test("every role gets the right client controls; guests need no missing form element", () => {
    for (const [auth, edit, manage] of [[false, false, false], [true, false, false], [true, true, false], [true, true, true]]) {
        const html = renderEducationCard(entry(), { ...config, isAuthenticated: auth, canEdit: edit, canManage: manage });
        assert.equal(html.includes("data-education-star="), auth);
        assert.equal(html.includes("Edit education:"), edit);
        assert.equal(html.includes("Delete education:"), manage);
        if (!auth) assert.match(html, /href="\/login\/"/);
    }
    assert.doesNotThrow(() => bindAjaxForm({ form: null }));
});

test("all card text and attribute values escape stored XSS payloads", () => {
    const data = entry();
    const payload = `"><img src=x onerror='alert(1)'><script>alert(2)</script>&`;
    for (const name of ["institution", "degree", "description", "period_label"]) data.fields[name] = payload;
    const html = renderEducationCard(data, config);
    assert.doesNotMatch(html, /<img|<script|onerror='alert/);
    assert.match(html, /&lt;img/);
    assert.match(html, /&quot;/);
    assert.match(html, /&#39;/);
});

test("unsafe stored website schemes are omitted, including entity and whitespace tricks", () => {
    for (const website of ["javascript:alert(1)", "java\tscript:alert(1)", "data:text/html,<script>alert(1)</script>", "&#106;avascript:alert(1)", "//evil.example", "ftp://example.edu/"]) {
        const data = entry();
        data.fields.website = website;
        assert.doesNotMatch(renderEducationCard(data, config), /Institution website/);
    }
    for (const website of ["http://example.edu/", "https://example.edu/"]) {
        const data = entry(); data.fields.website = website;
        assert.match(renderEducationCard(data, config), /Institution website/);
    }
    const data = entry(); data.urls.detail = "javascript:alert(1)";
    assert.throws(() => renderEducationCard(data, config), /Invalid local link/);
});

test("search normalizes only supported parameters and preserves the four empty states", () => {
    assert.deepEqual(normalizeEducationFilters({ q: "  Data & AI  ", status: "current", starred: "1", user_id: "other" }), { q: "Data & AI", status: "current", starred: "1" });
    assert.deepEqual(normalizeEducationFilters({ q: "   ", status: "invalid", starred: "99" }), { q: "", status: "", starred: "" });
    assert.equal(educationEmptyMessage({}, false), "No education entries have been added yet.");
    assert.equal(educationEmptyMessage({ q: "missing" }, true), "No education entries match these filters.");
    assert.equal(educationEmptyMessage({ starred: "1" }, true), "No starred education entries match these filters.");
    assert.equal(educationEmptyMessage({ starred: "1" }, false), "Log in to view your starred entries.");
});

test("AJAX combines filters and clears old parameters rather than retaining them", async () => {
    const requests = [];
    const loader = createListLoader({ url: "/api/education/?q=old&status=completed&starred=1", baseUrl: "https://portfolio.test", onState() {},
        fetchImpl: async url => { requests.push(url); return response([]); },
    });
    await loader.load(normalizeEducationFilters({ q: "Data & AI", status: "current", starred: "1" }));
    assert.deepEqual(Object.fromEntries(requests[0].searchParams), { q: "Data & AI", status: "current", starred: "1" });
    await loader.load(normalizeEducationFilters());
    assert.equal(requests[1].search, "");
});

test("a late Education JSON parse cannot replace a newer filter result", async () => {
    const oldBody = deferred();
    const states = [];
    let call = 0;
    const loader = createListLoader({ url: "/api/education/", baseUrl: "https://portfolio.test", onState: value => states.push(value),
        fetchImpl: async () => ++call === 1 ? { ok: true, json: () => oldBody.promise } : response([entry()]),
    });
    const first = loader.load({ q: "old" });
    await Promise.resolve(); // first response is now waiting for JSON parsing
    await loader.load({ status: "current" });
    oldBody.resolve([]);
    await first;
    assert.deepEqual(states.filter(value => value.state === "ready").map(value => value.filters), [{ status: "current" }]);
});

test("star requests require the CSRF header and a real JSON 200 result", async () => {
    const body = await postForm(`/education/${pk}/star-ajax/`, new FormData(), "token", {
        label: "star", successStatus: 200,
        fetchImpl: async (url, options) => {
            assert.equal(options.method, "POST");
            assert.equal(options.headers["X-CSRFToken"], "token");
            assert.equal(options.credentials, "same-origin");
            return response({ pk, is_starred: true, star_count: 3 });
        },
    });
    assert.equal(body.star_count, 3);
    await assert.rejects(postForm("/star/", {}, "token", { successStatus: 200,
        fetchImpl: async () => response({ message: "Please log in" }, 403),
    }), /Please log in/);
});

// Small DOM substitutes test the shared submission controller, not browser layout.
function formHarness(t) {
    const handlers = {};
    const attributes = new Map([["aria-describedby", "id_institution_helptext"]]);
    const group = { append(node) { this.error = node; }, classList: { add() {}, remove() {} } };
    const field = { id: "id_institution", value: "Keep my input", closest: () => group,
        getAttribute: name => attributes.get(name), setAttribute: (name, value) => attributes.set(name, value), removeAttribute: name => attributes.delete(name) };
    const form = { elements: { namedItem: name => name === "institution" ? field : null },
        querySelectorAll: () => [], addEventListener: (name, handler) => { handlers[name] = handler; },
        setAttribute() {}, removeAttribute() {}, reset() { this.resets = (this.resets || 0) + 1; } };
    const modal = { addEventListener() {}, hidePopover() { this.hidden = true; } };
    const summary = { focus() { this.focused = true; } };
    const submit = { disabled: false, textContent: "Save education" };
    const notices = [];
    t.mock.method(globalThis, "FormData", function (source) { return { source }; });
    const previousDocument = globalThis.document;
    globalThis.document = { createElement: () => ({ dataset: {}, children: [], append(node) { this.children.push(node); } }) };
    t.after(() => { if (previousDocument === undefined) delete globalThis.document; else globalThis.document = previousDocument; });
    return { form, modal, summary, submit, field, group, attributes, notices, handlers,
        settings: { form, modal, summary, submit, firstField: "institution", label: "education", savedTitle: "Education saved",
            url: "/education/add-ajax/", csrfToken: "csrf", notify: (...args) => notices.push(args) } };
}

test("server validation keeps input and modal, safely presents field errors, and unlocks submit", async t => {
    const h = formHarness(t);
    bindAjaxForm({ ...h.settings, send: async () => { throw new AjaxError("Check the institution", { institution: [{ message: "<img src=x onerror=alert(1)>" }] }); }, onSuccess: () => assert.fail("Must not refresh on validation error") });
    await h.handlers.submit({ preventDefault() {} });
    assert.equal(h.field.value, "Keep my input");
    assert.equal(h.form.resets, undefined);
    assert.equal(h.modal.hidden, undefined);
    assert.equal(h.summary.focused, true);
    assert.equal(h.group.error.children[0].textContent, "<img src=x onerror=alert(1)>");
    assert.equal(h.group.error.children[0].innerHTML, undefined);
    assert.equal(h.attributes.get("aria-invalid"), "true");
    assert.equal(h.attributes.get("aria-describedby"), "id_institution_helptext id_institution_ajax_error");
    assert.equal(h.submit.disabled, false);
    assert.equal(h.notices[0][2], "error");
});

test("a pending form submits once and resets/closes/refreshes only after a successful save", async t => {
    const h = formHarness(t);
    const pending = deferred();
    let saves = 0, refreshes = 0;
    bindAjaxForm({ ...h.settings, send: () => { saves += 1; return pending.promise; }, onSuccess: () => { refreshes += 1; } });
    const saving = h.handlers.submit({ preventDefault() {} });
    assert.equal(h.submit.disabled, true);
    await h.handlers.submit({ preventDefault() {} });
    assert.equal(saves, 1);
    pending.resolve({ pk, message: "Saved" });
    await saving;
    assert.equal(h.form.resets, 1);
    assert.equal(h.modal.hidden, true);
    assert.equal(refreshes, 1);
    assert.equal(h.submit.disabled, false);
    assert.equal(h.submit.textContent, "Save education");
    assert.equal(h.notices[0][2], "success");
});
