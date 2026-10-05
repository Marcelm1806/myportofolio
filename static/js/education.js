import { createListLoader, debounce, postForm } from "./ajax.js?v=assignment5-20260930";
import { bindAjaxForm } from "./ajax-form.js?v=assignment5-20260930";
import { normalizeEducationFilters, educationEmptyMessage, renderEducationCard } from "./education-utils.js?v=assignment5-20260930";
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
let focusAfterRefresh = null;
const pendingStars = new Set();

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
            for (const button of grid.querySelectorAll("[data-education-star]")) {
                button.disabled = pendingStars.has(button.dataset.educationStar);
            }
            empty.textContent = educationEmptyMessage(filters, config.isAuthenticated);
            empty.hidden = records.length !== 0;
            status.textContent = `${records.length} ${records.length === 1 ? "entry" : "entries"}`;
        }
        // Restore keyboard focus after replacing the card, but never steal it
        // from someone who moved on to the search or another control meanwhile.
        if (state !== "loading" && focusAfterRefresh) {
            if (document.activeElement === document.body || grid.contains(document.activeElement)) {
                const target = grid.querySelector(`[data-education-star="${focusAfterRefresh}"]`);
                (target || searchInput).focus();
            }
            focusAfterRefresh = null;
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

grid.addEventListener("click", async event => {
    const button = event.target.closest("[data-education-star]");
    if (!button || !grid.contains(button)) return;
    const id = button.dataset.educationStar;
    if (pendingStars.has(id)) return;
    pendingStars.add(id);
    button.disabled = true;
    try {
        const result = await postForm(button.dataset.url, new FormData(), config.csrfToken, { successStatus: 200, label: "star" });
        pendingStars.delete(id);
        if (document.activeElement === button) focusAfterRefresh = id;
        showToast("Education favourites", result.message, "success");
        await searchNow();
    } catch (error) {
        showToast("Could not update star", error.message, "error", 6000);
    } finally {
        pendingStars.delete(id);
        button.disabled = false;
        const currentButton = grid.querySelector(`[data-education-star="${id}"]`);
        if (currentButton) currentButton.disabled = false;
    }
});

bindAjaxForm({
    form: document.getElementById("education-form"),
    modal: document.getElementById("add-education-modal"),
    summary: document.getElementById("education-form-error"),
    submit: document.getElementById("education-submit"),
    url: config.createUrl, csrfToken: config.csrfToken,
    firstField: "institution", label: "education", savedTitle: "Education saved", notify: showToast,
    onSuccess: searchNow,
});

loader.load(normalizeEducationFilters(config.initialFilters));
