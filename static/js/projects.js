import { bindAjaxForm } from "./ajax-form.js?v=assignment5-20260930";
import { showToast } from "./toast.js?v=tutorial5-20260930";
import { createProjectLoader, debounce, renderProjectCard } from "./project-utils.js?v=assignment5-20260930";

const config = JSON.parse(document.getElementById("project-config").textContent);
const grid = document.getElementById("project-grid");
const status = document.getElementById("project-list-status");
const empty = document.getElementById("project-empty-state");
const loadError = document.getElementById("project-load-error");
const searchForm = document.getElementById("project-search-form");
const searchInput = document.getElementById("project-title-search");
const clearButton = document.getElementById("clear-project-search");

const loader = createProjectLoader({
    url: config.jsonUrl,
    baseUrl: window.location.href,
    onState({ state, query, projects }) {
        grid.setAttribute("aria-busy", String(state === "loading"));
        grid.inert = state === "loading";
        empty.hidden = true;
        loadError.hidden = state !== "error";
        clearButton.hidden = !searchInput.value;
        if (state === "loading") {
            status.textContent = "Loading projects…";
        } else if (state === "error") {
            grid.replaceChildren();
            status.textContent = "";
        } else {
            // renderProjectCard escapes all dynamic text and validates URLs.
            grid.innerHTML = projects.map(project => renderProjectCard(project, config)).join("");
            empty.textContent = query ? "No projects match your search." : "No projects have been added yet.";
            empty.hidden = projects.length !== 0;
            status.textContent = `${projects.length} project${projects.length === 1 ? "" : "s"}${query ? " found" : ""}.`;
        }
    },
});

function refreshProjects() {
    const query = searchInput.value.trim();
    const url = new URL(window.location.href);
    if (query) url.searchParams.set("title", query);
    else url.searchParams.delete("title");
    window.history.replaceState(null, "", url);
    return loader.load(query);
}

const searchAfterTyping = debounce(refreshProjects, 300);
searchInput.addEventListener("input", () => {
    // Invalidate immediately, including while the next debounce is pending.
    loader.cancel();
    clearButton.hidden = !searchInput.value;
    searchAfterTyping();
});
searchForm.addEventListener("submit", event => {
    event.preventDefault();
    searchAfterTyping.cancel();
    refreshProjects();
});
clearButton.addEventListener("click", () => {
    searchAfterTyping.cancel();
    searchInput.value = "";
    searchInput.focus();
    refreshProjects();
});
document.getElementById("retry-projects").addEventListener("click", refreshProjects);
window.addEventListener("popstate", () => {
    searchAfterTyping.cancel();
    searchInput.value = new URL(window.location.href).searchParams.get("title") || "";
    refreshProjects();
});

bindAjaxForm({
    form: document.getElementById("project-form"),
    modal: document.getElementById("add-project-modal"),
    summary: document.getElementById("project-form-error"),
    submit: document.getElementById("project-submit"),
    url: config.createUrl, csrfToken: config.csrfToken,
    firstField: "title", label: "project", savedTitle: "Project saved", notify: showToast,
    onSuccess: () => { searchAfterTyping.cancel(); return refreshProjects(); },
});

loader.load(config.initialQuery);
