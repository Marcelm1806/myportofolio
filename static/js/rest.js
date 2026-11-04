import { AjaxError } from "./ajax.js?v=tutorial7-20261104";

/** JSON mutations use session cookies AND CSRF; a 204 has no JSON body. */
export async function requestJson(url, { method = "POST", data, csrfToken,
    successStatus = 200, fetchImpl = globalThis.fetch } = {}) {
    let response;
    try {
        response = await fetchImpl(url, {
            method, credentials: "same-origin",
            headers: { Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            ...(data === undefined ? {} : { body: JSON.stringify(data) }),
        });
    } catch {
        throw new AjaxError("Connection lost. Refresh the list before retrying; the change may have reached the server.");
    }
    if (response.status === 204 && successStatus === 204) return null;
    const body = await response.json().catch(() => null);
    if (!response.ok) {
        const errors = {};
        if (response.status === 400 && body && typeof body === "object" && !Array.isArray(body)) {
            for (const [field, messages] of Object.entries(body)) {
                if (Array.isArray(messages)) errors[field] = messages.map(message => ({ message: String(message) }));
            }
        }
        const firstError = Object.values(errors).flat()[0]?.message;
        const fallback = response.status === 403
            ? "Your session or permission has changed. Reload the page and sign in with an authorized account."
            : "The change could not be saved. Please refresh the list and try again.";
        const message = firstError ? `Please correct the highlighted fields. ${firstError}`
            : typeof body?.detail === "string" ? body.detail : fallback;
        throw new AjaxError(message, errors);
    }
    if (response.status !== successStatus || typeof body?.id !== "string") {
        throw new AjaxError("Unexpected response. Refresh the list before trying again.");
    }
    return body;
}

/** Explicit writable fields; unchecked checkboxes must become JSON false. */
export function formPayload(data, kind) {
    const textFields = kind === "project"
        ? ["title", "organization", "context_label", "summary", "contribution", "technologies", "award"]
        : ["institution", "degree", "description", "website"];
    const payload = Object.fromEntries(textFields.map(name => [name, String(data.get(name) ?? "")]));
    payload.display_order = data.get("display_order") === "" ? "" : Number(data.get("display_order") ?? 0);
    if (kind === "project") {
        payload.is_featured = data.has("is_featured");
    } else {
        payload.is_current = data.has("is_current");
        payload.start_year = data.get("start_year") === "" ? "" : Number(data.get("start_year"));
        payload.end_year = data.get("end_year") ? Number(data.get("end_year")) : null;
    }
    return payload;
}

export async function submitRestForm(url, data, csrfToken, { label, fetchImpl = globalThis.fetch }) {
    const result = await requestJson(url, {
        data: formPayload(data, label), csrfToken, successStatus: 201, fetchImpl,
    });
    return { ...result, message: label === "project" ? "Project added successfully." : "Education entry added successfully." };
}

/** Shared delegated star/delete actions survive replacing the AJAX card grid. */
export function bindRestCardActions({ grid, csrfToken, refresh, notify, fallbackFocus,
    send = requestJson }) {
    const pending = new Set();
    function syncPending() {
        for (const button of grid.querySelectorAll("[data-rest-id]")) {
            button.disabled = pending.has(button.dataset.restId);
        }
    }
    grid.addEventListener("click", async event => {
        const button = event.target.closest("button[data-rest-action]");
        if (!button || !grid.contains(button)) return;
        const { restId: id, restAction: action, url } = button.dataset;
        if (!["star", "delete"].includes(action) || pending.has(id)) return;
        pending.add(id);
        syncPending();
        try {
            const result = await send(url, {
                method: action === "delete" ? "DELETE" : "POST",
                csrfToken, successStatus: action === "delete" ? 204 : 200,
            });
            const hadFocus = document.activeElement === button;
            if (action === "delete") button.closest("[popover]")?.hidePopover();
            notify(action === "delete" ? "Entry deleted" : "Favourites updated",
                action === "delete" ? "The entry was removed." : result.is_starred ? "Star added." : "Star removed.", "success");
            await refresh();
            // Do not steal focus from a user who moved to another control.
            if (hadFocus && (document.activeElement === document.body || grid.contains(document.activeElement))) {
                const next = action === "star" ? grid.querySelector(`[data-rest-action="star"][data-rest-id="${id}"]`) : null;
                if (next) next.disabled = false;
                (next || fallbackFocus)?.focus();
            }
        } catch (error) {
            notify("Could not save change", error.message, "error", 6000);
        } finally {
            pending.delete(id);
            syncPending();
        }
    });
    return { syncPending };
}
