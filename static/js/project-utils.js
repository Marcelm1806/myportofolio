import { escapeHtml, localUrl, debounce, createListLoader, postForm, AjaxError } from "./ajax.js?v=assignment5-20260930";

// Preserve the Tutorial 5 imports while sharing these helpers with Education.
export { escapeHtml, debounce, AjaxError as ProjectSubmissionError };

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

export function createProjectLoader({ onState, ...options }) {
    const loader = createListLoader({ ...options,
        onState: ({ state, filters, records }) => onState({ state, query: filters.title || "", projects: records }),
    });
    return { cancel: loader.cancel, load: (query = "") => loader.load({ title: query.trim() }) };
}

export function submitProject(url, data, csrfToken, fetchImpl = globalThis.fetch) {
    return postForm(url, data, csrfToken, { fetchImpl, label: "project" });
}
