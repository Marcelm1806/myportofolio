import { showToast } from "./toast.js?v=tutorial5-20260930";
import { createProjectLoader, debounce, renderProjectCard, submitProject } from "./project-utils.js?v=tutorial5-20260930";

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

const form = document.getElementById("project-form");
if (form) {
    const modal = document.getElementById("add-project-modal");
    const submit = document.getElementById("project-submit");
    const summary = document.getElementById("project-form-error");

    function clearErrors() {
        summary.hidden = true;
        summary.textContent = "";
        form.querySelectorAll("[data-ajax-error]").forEach(element => element.remove());
        form.querySelectorAll(".form-group-invalid").forEach(group => group.classList.remove("form-group-invalid"));
        form.querySelectorAll("[aria-invalid]").forEach(field => {
            field.removeAttribute("aria-invalid");
            const ids = (field.getAttribute("aria-describedby") || "").split(" ").filter(id => id && !id.endsWith("_ajax_error"));
            if (ids.length) field.setAttribute("aria-describedby", ids.join(" "));
            else field.removeAttribute("aria-describedby");
        });
    }

    function displayErrors(error) {
        summary.textContent = error.message;
        summary.hidden = false;
        for (const [name, errors] of Object.entries(error.errors || {})) {
            const field = form.elements.namedItem(name);
            if (!field || !Array.isArray(errors)) continue;
            const group = field.closest(".form-group");
            if (!group) continue;
            const list = document.createElement("ul");
            list.id = `${field.id}_ajax_error`;
            list.className = "form-errors";
            list.dataset.ajaxError = "true";
            for (const error of errors) {
                const item = document.createElement("li");
                item.textContent = error.message;
                list.append(item);
            }
            group.append(list);
            group.classList.add("form-group-invalid");
            field.setAttribute("aria-invalid", "true");
            field.setAttribute("aria-describedby", `${field.getAttribute("aria-describedby") || ""} ${list.id}`.trim());
        }
        summary.focus();
    }

    modal.addEventListener("toggle", event => {
        if (event.newState === "open") form.elements.namedItem("title").focus();
    });
    form.addEventListener("submit", async event => {
        event.preventDefault();
        if (submit.disabled) return;
        clearErrors();
        submit.disabled = true;
        submit.textContent = "Saving…";
        form.setAttribute("aria-busy", "true");
        try {
            const result = await submitProject(config.createUrl, new FormData(form), config.csrfToken);
            modal.hidePopover();
            form.reset();
            showToast("Project saved", result.message, "success");
            searchAfterTyping.cancel();
            await refreshProjects();
        } catch (error) {
            displayErrors(error);
            showToast("Could not save project", error.message, "error", 6000);
        } finally {
            submit.disabled = false;
            submit.textContent = "Save project";
            form.removeAttribute("aria-busy");
        }
    });
}

loader.load(config.initialQuery);
