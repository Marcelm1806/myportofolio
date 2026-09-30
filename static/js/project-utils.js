/** Escape every dynamic value before inserting a card as HTML. */
export function escapeHtml(value) {
    const replacements = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return String(value ?? "").replace(/[&<>"']/g, character => replacements[character]);
}

function localUrl(value) {
    // HTML escaping alone does not make a javascript: URL safe.
    if (typeof value !== "string" || !/^\/(?!\/)[^\\\s]*$/.test(value)) {
        throw new Error("Invalid project link.");
    }
    return escapeHtml(value);
}

export function renderProjectCard(project, config) {
    const { fields, urls, pk } = project;
    if (!/^[0-9a-f-]{36}$/i.test(pk)) throw new Error("Invalid project ID.");
    const title = escapeHtml(fields.title);
    const csrf = `<input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">`;
    const count = Number.isInteger(fields.star_count) && fields.star_count >= 0 ? fields.star_count : 0;
    const starred = fields.is_starred === true;
    const tags = (fields.technology_list || []).map(tag => `<li>${escapeHtml(tag)}</li>`).join("");
    const deleteControls = config.isSuperuser ? `
        <button type="button" class="button button-danger" popovertarget="delete-project-${pk}" aria-label="Delete project: ${title}">Delete</button>
        <div id="delete-project-${pk}" class="project-delete-modal" popover="auto" role="dialog" aria-labelledby="delete-title-${pk}" aria-describedby="delete-description-${pk}">
            <h2 id="delete-title-${pk}">Delete project?</h2>
            <p id="delete-description-${pk}">This will permanently remove <strong>${title}</strong> from your portfolio.</p>
            <div class="project-delete-modal-actions">
                <button type="button" class="button button-secondary" popovertarget="delete-project-${pk}" popovertargetaction="hide" autofocus>Cancel</button>
                <form method="post" action="${localUrl(urls.delete)}">${csrf}<button type="submit" class="button button-danger">Delete project</button></form>
            </div>
        </div>` : "";
    return `<article class="project-card${fields.is_featured ? " project-card-featured" : ""}">
        <div class="project-header">
            <p class="project-company">${escapeHtml(fields.organization)}</p>
            ${fields.context_label ? `<p class="project-context">${escapeHtml(fields.context_label)}</p>` : ""}
        </div>
        <h2>${title}</h2>
        <p class="project-summary">${escapeHtml(fields.summary)}</p>
        ${fields.award ? `<p class="award-badge">${escapeHtml(fields.award)}</p>` : ""}
        ${tags ? `<ul class="tag-list" aria-label="Technologies and topics for ${title}">${tags}</ul>` : ""}
        <details class="project-details"><summary>My contribution</summary><p>${escapeHtml(fields.contribution).replace(/\r?\n/g, "<br>")}</p></details>
        <div class="project-card-actions">
            <a href="${localUrl(urls.detail)}" class="project-link" aria-label="View project: ${title}">View project &rarr;</a>
            <form method="post" action="${localUrl(urls.star)}" class="star-form">
                ${csrf}
                <button type="submit" class="button button-star${starred ? " is-starred" : ""}" aria-pressed="${starred}" aria-label="${starred ? "Unstar" : "Star"} project: ${title}" title="${escapeHtml(fields.starred_by_names ? `Starred by ${fields.starred_by_names}` : "No stars yet")}">
                    <span aria-hidden="true">${starred ? "★" : "☆"}</span>
                    ${starred ? "Unstar" : "Star"}<span class="star-count">${count}</span>
                </button>
            </form>
            ${deleteControls}
        </div>
    </article>`;
}

export function debounce(callback, delay = 300, timers = globalThis) {
    let timer;
    const debounced = (...args) => {
        timers.clearTimeout(timer);
        timer = timers.setTimeout(() => callback(...args), delay);
    };
    debounced.cancel = () => timers.clearTimeout(timer);
    return debounced;
}

/** Ignore stale responses even if cancellation arrives after fetch resolved. */
export function createProjectLoader({ url, baseUrl, onState, fetchImpl = globalThis.fetch }) {
    let controller;
    let generation = 0;
    function cancel() {
        generation += 1;
        controller?.abort();
    }
    async function load(value = "") {
        cancel();
        const current = generation;
        const query = value.trim();
        controller = new AbortController();
        const endpoint = new URL(url, baseUrl);
        if (query) endpoint.searchParams.set("title", query);
        else endpoint.searchParams.delete("title");
        onState({ state: "loading", query });
        try {
            const response = await fetchImpl(endpoint, {
                signal: controller.signal, credentials: "same-origin", cache: "no-store",
                headers: { Accept: "application/json" },
            });
            if (!response.ok) throw new Error("Projects could not be loaded.");
            const projects = await response.json();
            if (!Array.isArray(projects)) throw new Error("Invalid project response.");
            if (current === generation) onState({ state: "ready", query, projects });
        } catch (error) {
            if (current === generation && error.name !== "AbortError") {
                onState({ state: "error", query });
            }
        }
    }
    return { load, cancel };
}

export class ProjectSubmissionError extends Error {
    constructor(message, errors = {}) {
        super(message);
        this.errors = errors;
    }
}

export async function submitProject(url, data, csrfToken, fetchImpl = globalThis.fetch) {
    let response;
    try {
        response = await fetchImpl(url, {
            method: "POST", body: data, credentials: "same-origin",
            headers: { "X-CSRFToken": csrfToken, Accept: "application/json" },
        });
    } catch {
        throw new ProjectSubmissionError("Connection lost. Check the project list before retrying; the save may have reached the server.");
    }
    const body = await response.json().catch(() => null);
    if (!response.ok) {
        const fallback = response.status === 403
            ? "Your session or permission has changed. Reload the page and sign in as the owner."
            : "The project could not be saved. Please try again.";
        const firstError = Object.values(body?.errors || {}).flat()[0]?.message || "";
        throw new ProjectSubmissionError(body?.errors
            ? `Please correct the highlighted fields. ${firstError}`.trim()
            : body?.message || fallback, body?.errors);
    }
    // A login redirect can produce HTML with status 200; it is not a save.
    if (response.status !== 201 || !body?.pk) {
        throw new ProjectSubmissionError("Unexpected response. Reload the project list before trying again.");
    }
    return body;
}
