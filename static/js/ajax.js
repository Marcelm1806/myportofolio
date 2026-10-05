/** Shared by Projects and Education: plain text, local links and HTTP handling. */
export function escapeHtml(value) {
    const replacements = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return String(value ?? "").replace(/[&<>"']/g, character => replacements[character]);
}

export function localUrl(value) {
    if (typeof value !== "string" || !/^\/(?!\/)[^\\\s]*$/.test(value)) {
        throw new Error("Invalid local link.");
    }
    return escapeHtml(value);
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

/** Cancellation plus a generation guard also covers responses already parsing. */
export function createListLoader({ url, baseUrl, onState, fetchImpl = globalThis.fetch }) {
    let controller;
    let generation = 0;
    function cancel() {
        generation += 1;
        controller?.abort();
    }
    async function load(filters = {}) {
        cancel();
        const current = generation;
        const snapshot = { ...filters };
        controller = new AbortController();
        const endpoint = new URL(url, baseUrl);
        for (const [key, value] of Object.entries(snapshot)) {
            if (value) endpoint.searchParams.set(key, value);
            else endpoint.searchParams.delete(key);
        }
        onState({ state: "loading", filters: snapshot });
        try {
            const response = await fetchImpl(endpoint, {
                signal: controller.signal, credentials: "same-origin", cache: "no-store",
                headers: { Accept: "application/json" },
            });
            if (!response.ok) throw new Error("The list could not be loaded.");
            const records = await response.json();
            if (!Array.isArray(records)) throw new Error("Invalid list response.");
            if (current === generation) onState({ state: "ready", filters: snapshot, records });
        } catch (error) {
            if (current === generation && error.name !== "AbortError") {
                onState({ state: "error", filters: snapshot });
            }
        }
    }
    return { load, cancel };
}

export class AjaxError extends Error {
    constructor(message, errors = {}) {
        super(message);
        this.errors = errors;
    }
}

/** FormData supplies its own Content-Type boundary; never set it manually. */
export async function postForm(url, data, csrfToken, {
    fetchImpl = globalThis.fetch, successStatus = 201, label = "entry",
} = {}) {
    let response;
    try {
        response = await fetchImpl(url, {
            method: "POST", body: data, credentials: "same-origin",
            headers: { "X-CSRFToken": csrfToken, Accept: "application/json" },
        });
    } catch {
        throw new AjaxError(`Connection lost. Refresh the list before retrying; the ${label === "star" ? "change" : "save"} may have reached the server.`);
    }
    const body = await response.json().catch(() => null);
    if (!response.ok) {
        const fallback = response.status === 403
            ? "Your session or permission has changed. Reload the page and sign in with an authorized account."
            : `The ${label} could not be saved. Please try again.`;
        const firstError = Object.values(body?.errors || {}).flat()[0]?.message || "";
        throw new AjaxError(body?.errors
            ? `Please correct the highlighted fields. ${firstError}`.trim()
            : body?.message || fallback, body?.errors);
    }
    // A followed login redirect returning HTML 200 is not a successful save.
    if (response.status !== successStatus || !body?.pk) {
        throw new AjaxError("Unexpected response. Refresh the list before trying again.");
    }
    return body;
}
