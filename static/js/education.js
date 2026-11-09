import { submitRestForm, bindRestCardActions } from "./rest.js?v=assignment6-20261109";
import { createListLoader, debounce } from "./ajax.js?v=tutorial7-20261104";
import { bindAjaxForm } from "./ajax-form.js?v=assignment6-20261109";
import { bindEducationEditor } from "./education-edit.js?v=assignment6-20261109";
import { normalizeEducationFilters, educationEmptyMessage, renderEducationCard } from "./education-utils.js?v=assignment6-20261109";
import { showToast } from "./toast.js?v=tutorial5-20260930";

const config = JSON.parse(document.getElementById("education-config").textContent);
const grid = document.getElementById("education-grid");
const status = document.getElementById("education-list-status");
const empty = document.getElementById("education-empty-state");
const loadError = document.getElementById("education-load-error");
const searchForm = document.getElementById("education-search-form");
const searchInput = document.getElementById("education-search");
const statusSelect = document.getElementById("education-status");
const starSelect = document.getElementById("education-star-filter");
const clearButton = document.getElementById("clear-education-search");
let guestStarFilter = config.initialFilters.starred;

function currentFilters() {
    return normalizeEducationFilters({
        q: searchInput.value, status: statusSelect.value,
        starred: starSelect ? starSelect.value : guestStarFilter,
    });
}

const loader = createListLoader({
    url: config.jsonUrl, baseUrl: window.location.href,
    onState({ state, filters, records }) {
        grid.setAttribute("aria-busy", String(state === "loading"));
        grid.inert = state === "loading";
        empty.hidden = true;
        loadError.hidden = state !== "error";
        clearButton.hidden = !Object.values(filters).some(Boolean);
        if (state === "loading") {
            status.textContent = "Loading education…";
        } else if (state === "error") {
            grid.replaceChildren();
            status.textContent = "";
            showToast("Could not load education", "Check your connection and use Try again.", "error", 6000);
        } else {
            grid.innerHTML = records.map(entry => renderEducationCard(entry, config)).join("");
            cardActions.syncPending();
            empty.textContent = educationEmptyMessage(filters, config.isAuthenticated);
            empty.hidden = records.length !== 0;
            status.textContent = `${records.length} ${records.length === 1 ? "entry" : "entries"}`;
        }
    },
});

function refreshEducation() {
    const filters = currentFilters();
    const url = new URL(window.location.href);
    for (const [key, value] of Object.entries(filters)) {
        if (value) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
    }
    window.history.replaceState(null, "", url);
    return loader.load(filters);
}

const searchAfterTyping = debounce(refreshEducation, 300);
searchInput.addEventListener("input", () => { loader.cancel(); searchAfterTyping(); });
function searchNow() { searchAfterTyping.cancel(); return refreshEducation(); }
searchForm.addEventListener("submit", event => { event.preventDefault(); searchNow(); });
statusSelect.addEventListener("change", searchNow);
starSelect?.addEventListener("change", searchNow);
clearButton.addEventListener("click", () => {
    searchInput.value = "";
    statusSelect.value = "";
    if (starSelect) starSelect.value = "";
    guestStarFilter = "";
    searchInput.focus();
    searchNow();
});
document.getElementById("retry-education").addEventListener("click", searchNow);
window.addEventListener("popstate", () => {
    const filters = normalizeEducationFilters(Object.fromEntries(new URL(window.location.href).searchParams));
    searchInput.value = filters.q;
    statusSelect.value = filters.status;
    if (starSelect) starSelect.value = filters.starred;
    guestStarFilter = filters.starred;
    searchNow();
});

const cardActions = bindRestCardActions({
    grid, csrfToken: config.csrfToken, refresh: searchNow, notify: showToast, fallbackFocus: searchInput,
});

bindEducationEditor({
    grid, dialog: document.getElementById("edit-education-dialog"),
    csrfToken: config.csrfToken, refresh: searchNow, notify: showToast, fallbackFocus: searchInput,
});

bindAjaxForm({
    send: submitRestForm,
    form: document.getElementById("education-form"),
    modal: document.getElementById("add-education-modal"),
    summary: document.getElementById("education-form-error"),
    submit: document.getElementById("education-submit"),
    url: config.createUrl, csrfToken: config.csrfToken,
    firstField: "institution", label: "education", savedTitle: "Education saved", notify: showToast,
    onSuccess: searchNow,
});

loader.load(normalizeEducationFilters(config.initialFilters));
