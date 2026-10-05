import { escapeHtml, localUrl } from "./ajax.js?v=assignment5-20260930";

export function normalizeEducationFilters(values = {}) {
    return {
        q: String(values.q || "").trim(),
        status: ["current", "completed"].includes(values.status) ? values.status : "",
        starred: values.starred === "1" ? "1" : "",
    };
}

export function educationEmptyMessage(filters, authenticated) {
    if (filters.starred && !authenticated) return "Log in to view your starred entries.";
    if (filters.starred) return "No starred education entries match these filters.";
    if (filters.q || filters.status) return "No education entries match these filters.";
    return "No education entries have been added yet.";
}

function websiteLink(value) {
    try {
        const url = new URL(value);
        return ["https:", "http:"].includes(url.protocol) ? escapeHtml(url.href) : "";
    } catch {
        return "";
    }
}

export function renderEducationCard(entry, config) {
    const { pk, fields, urls } = entry;
    if (!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(pk)) throw new Error("Invalid education ID.");
    const institution = escapeHtml(fields.institution);
    const count = Number.isInteger(fields.star_count) && fields.star_count >= 0 ? fields.star_count : 0;
    const starred = fields.is_starred === true;
    const website = websiteLink(fields.website);
    const csrf = `<input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">`;
    const star = config.isAuthenticated
        ? `<button type="button" class="button button-star${starred ? " is-starred" : ""}" data-education-star="${pk}" data-url="${localUrl(urls.star)}" aria-pressed="${starred}" aria-label="${starred ? "Unstar" : "Star"} ${institution} (${count} stars)"><span aria-hidden="true">${starred ? "★" : "☆"}</span>${starred ? "Unstar" : "Star"}<span class="star-count">${count}</span></button>`
        : `<a href="${localUrl(config.loginUrl)}" class="button button-star" aria-label="Log in to star ${institution}"><span aria-hidden="true">☆</span>Log in to star<span class="star-count">${count}</span></a>`;
    const edit = config.canEdit ? `<a href="${localUrl(urls.edit)}" class="button button-secondary" aria-label="Edit education: ${institution}">Edit</a>` : "";
    const remove = config.canManage ? `
        <button type="button" class="button button-danger" popovertarget="delete-education-${pk}" aria-label="Delete education: ${institution}">Delete</button>
        <div id="delete-education-${pk}" class="project-delete-modal" popover="auto" role="dialog" aria-labelledby="delete-title-${pk}" aria-describedby="delete-description-${pk}">
            <h2 id="delete-title-${pk}">Delete education?</h2>
            <p id="delete-description-${pk}">This will permanently remove <strong>${institution}</strong> from your portfolio.</p>
            <div class="project-delete-modal-actions">
                <button type="button" class="button button-secondary" popovertarget="delete-education-${pk}" popovertargetaction="hide" autofocus>Cancel</button>
                <form method="post" action="${localUrl(urls.delete)}">${csrf}<button type="submit" class="button button-danger">Delete education</button></form>
            </div>
        </div>` : "";
    return `<article class="education-card" data-education-id="${pk}">
        <p class="education-year">${escapeHtml(fields.period_label)}</p>
        <h2>${institution}</h2>
        <p class="education-degree">${escapeHtml(fields.degree)}</p>
        ${fields.description ? `<p class="education-description">${escapeHtml(fields.description).replace(/\r?\n/g, "<br>")}</p>` : ""}
        <p class="education-status">${fields.is_current ? "Currently studying" : "Completed"}</p>
        ${website ? `<a href="${website}" class="project-link" target="_blank" rel="noopener noreferrer">Institution website <span class="visually-hidden">for ${institution} (opens in a new tab)</span></a>` : ""}
        <a href="${localUrl(urls.detail)}" class="project-link education-detail-link">View details <span class="visually-hidden">for ${institution}</span></a>
        <div class="education-card-stars">${star}</div>
        ${edit || remove ? `<div class="education-card-actions">${edit}${remove}</div>` : ""}
    </article>`;
}
