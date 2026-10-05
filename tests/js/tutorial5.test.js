import test from "node:test";
import assert from "node:assert/strict";
import { escapeHtml, renderProjectCard, createProjectLoader, debounce, submitProject } from "../../static/js/project-utils.js";
import { createToast } from "../../static/js/toast.js";

const pk = "65f44391-a5c3-4eaa-a97a-b19dcc4c6937";
const record = () => ({
    pk, urls: { detail: `/projects/${pk}/`, star: `/projects/${pk}/star/`, delete: `/projects/${pk}/delete/` },
    fields: { title: "My project", organization: "University", summary: "Summary", contribution: "First\nSecond",
        technology_list: ["Python", "SQL"], star_count: 2, is_starred: true,
        starred_by_names: "one, two", is_featured: true, award: "Data Insight" },
});
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const deferred = () => {
    let resolve;
    const promise = new Promise(done => { resolve = done; });
    return { resolve, promise };
};
function fakeTimers() {
    let id = 0;
    const pending = new Map();
    return {
        setTimeout(callback, delay) { pending.set(++id, { callback, delay }); return id; },
        clearTimeout(timer) { pending.delete(timer); },
        run() { const tasks = [...pending.values()]; pending.clear(); tasks.forEach(task => task.callback()); },
        get pending() { return [...pending.values()]; },
    };
}

test("escapes all HTML special characters including attribute quotes", () => {
    assert.equal(escapeHtml(`<a title="x'">&</a>`), "&lt;a title=&quot;x&#39;&quot;&gt;&amp;&lt;/a&gt;");
    assert.equal(escapeHtml(null), "");
});

test("cards keep portfolio styling, detail links, line breaks and POST controls", () => {
    const html = renderProjectCard(record(), { isSuperuser: true, csrfToken: "csrf-token" });
    assert.match(html, /project-card-featured/);
    assert.match(html, /First<br>Second/);
    assert.match(html, /<li>Python<\/li><li>SQL<\/li>/);
    assert.match(html, /aria-pressed="true"/);
    assert.match(html, /Unstar/);
    assert.match(html, /class="star-count">2<\/span>/);
    assert.match(html, new RegExp(`href="/projects/${pk}/"`));
    assert.equal((html.match(/method="post"/g) || []).length, 2);
    assert.equal((html.match(/name="csrfmiddlewaretoken"/g) || []).length, 2);
    assert.match(html, /popover="auto"/);
});

test("ordinary visitors get no delete controls; unstarred state is explicit", () => {
    const data = record();
    data.fields.is_starred = false;
    const html = renderProjectCard(data, { isSuperuser: false, csrfToken: "token" });
    assert.doesNotMatch(html, /delete-project|button-danger|Unstar/);
    assert.match(html, /aria-pressed="false"/);
    assert.match(html, /method="post"/);
});

test("stored XSS text is escaped in every card field and username hint", () => {
    const data = record();
    const payload = `"><img src=x onerror='alert(1)'><script>alert(2)</script>&`;
    for (const name of ["title", "organization", "summary", "context_label", "contribution", "award", "starred_by_names"]) {
        data.fields[name] = payload;
    }
    data.fields.technology_list = [payload];
    const html = renderProjectCard(data, { isSuperuser: true, csrfToken: '"<token>' });
    assert.doesNotMatch(html, /<img|<script|src=x onerror='/);
    assert.match(html, /&lt;img/);
    assert.match(html, /&quot;&lt;token&gt;/);
    assert.match(html, /&#39;alert\(1\)&#39;/);
});

test("dangerous link schemes, external URLs and malformed IDs are rejected", () => {
    for (const url of ["javascript:alert(1)", "https://example.com", "//example.com", "/\\example.com"]) {
        const data = record();
        data.urls.detail = url;
        assert.throws(() => renderProjectCard(data, {}), /Invalid local link/);
    }
    assert.throws(() => renderProjectCard({ ...record(), pk: '\"><img src=x>' }, {}), /Invalid project ID/);
});

test("debounce sends only the latest input and can cancel pending Enter duplicates", () => {
    const timers = fakeTimers();
    const calls = [];
    const search = debounce(value => calls.push(value), 300, timers);
    search("d"); search("dj"); search("django");
    assert.equal(timers.pending.length, 1);
    assert.equal(timers.pending[0].delay, 300);
    timers.run();
    assert.deepEqual(calls, ["django"]);
    search("cancelled"); search.cancel(); timers.run();
    assert.deepEqual(calls, ["django"]);
});

test("loader trims and encodes query and uses a fresh same-origin JSON request", async () => {
    const states = [];
    const calls = [];
    const loader = createProjectLoader({ url: "/api/projects/", baseUrl: "https://portfolio.test/projects/", onState: state => states.push(state),
        fetchImpl: async (url, options) => { calls.push({ url, options }); return response([record()]); },
    });
    await loader.load("  Data & AI  ");
    assert.equal(calls[0].url.searchParams.get("title"), "Data & AI");
    assert.equal(calls[0].options.credentials, "same-origin");
    assert.equal(calls[0].options.cache, "no-store");
    assert.equal(states.at(-1).projects[0].pk, pk);
    await loader.load("   ");
    assert.equal(calls[1].url.searchParams.has("title"), false);
});

test("late responses never overwrite a newer search even if fetch ignores abort", async () => {
    const first = deferred();
    const states = [];
    const signals = [];
    const loader = createProjectLoader({ url: "/api/projects/", baseUrl: "https://portfolio.test", onState: state => states.push(state),
        fetchImpl: async (url, options) => {
            signals.push(options.signal);
            return url.searchParams.get("title") === "old" ? first.promise : response([record()]);
        },
    });
    const old = loader.load("old");
    await loader.load("new");
    first.resolve(response([]));
    await old;
    assert.equal(signals[0].aborted, true);
    assert.deepEqual(states.filter(state => state.state === "ready").map(state => state.query), ["new"]);
});

test("cancelling a pending fetch does not report a spurious failure", async () => {
    const pending = deferred();
    const states = [];
    const loader = createProjectLoader({ url: "/api/projects/", baseUrl: "https://portfolio.test", onState: state => states.push(state), fetchImpl: () => pending.promise });
    const request = loader.load("old");
    loader.cancel();
    pending.resolve(response([], 500));
    await request;
    assert.deepEqual(states.map(state => state.state), ["loading"]);
});

test("HTTP errors and invalid JSON shape report errors; retry can succeed", async () => {
    const states = [];
    let result = response({}, 500);
    const loader = createProjectLoader({ url: "/api/projects/", baseUrl: "https://portfolio.test", onState: state => states.push(state), fetchImpl: async () => result });
    await loader.load();
    assert.equal(states.at(-1).state, "error");
    result = response({ not: "an array" });
    await loader.load();
    assert.equal(states.at(-1).state, "error");
    result = response([]);
    await loader.load();
    assert.equal(states.at(-1).state, "ready");
    assert.deepEqual(states.at(-1).projects, []);
});

test("AJAX creation sends FormData and CSRF header without overriding its boundary", async () => {
    const data = new FormData();
    data.set("title", "Example");
    const result = await submitProject("/projects/add-ajax/", data, "csrf", async (url, options) => {
        assert.equal(url, "/projects/add-ajax/");
        assert.equal(options.method, "POST");
        assert.equal(options.body, data);
        assert.equal(options.headers["X-CSRFToken"], "csrf");
        assert.equal(options.headers["Content-Type"], undefined);
        return response({ pk, message: "Saved" }, 201);
    });
    assert.equal(result.pk, pk);
});

test("validation errors, non-JSON CSRF denial, login HTML and network errors are not success", async () => {
    const errors = { title: [{ message: "Enter text", code: "invalid" }] };
    await assert.rejects(submitProject("/add/", {}, "csrf", async () => response({ errors }, 400)), error => error.errors === errors);
    const html = status => ({ ok: status === 200, status, json: async () => { throw new SyntaxError(); } });
    await assert.rejects(submitProject("/add/", {}, "csrf", async () => html(403)), /session or permission/);
    await assert.rejects(submitProject("/add/", {}, "csrf", async () => html(200)), /Unexpected response/);
    await assert.rejects(submitProject("/add/", {}, "csrf", async () => { throw new TypeError(); }), /save may have reached/);
});

test("toast treats HTML as text, replaces old timers and allows dismissal", () => {
    const timers = fakeTimers();
    const title = {}, message = {}, close = {};
    let opened = false;
    const element = { dataset: {}, classList: { add() {}, remove() {} },
        querySelector(selector) { return { "#toast-title": title, "#toast-message": message, "#toast-close": close }[selector]; },
        showPopover() { opened = true; }, hidePopover() { opened = false; },
    };
    close.addEventListener = (name, handler) => { close.handler = handler; };
    const toast = createToast(element, timers);
    toast.show("Saved", "First", "success");
    timers.run(); // Start dismiss animation; another message arrives meanwhile.
    toast.show("<script>test</script>", "<img src=x>", "error", 6000);
    assert.equal(title.textContent, "<script>test</script>");
    assert.equal(message.textContent, "<img src=x>");
    assert.equal(element.dataset.type, "error");
    assert.equal(opened, true);
    assert.equal(timers.pending.length, 1);
    assert.equal(timers.pending[0].delay, 6000);
    close.handler();
    timers.run();
    assert.equal(opened, false);
});
