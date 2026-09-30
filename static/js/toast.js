/** A manual popover stays above the add-project popover without closing it. */
export function createToast(element, timers = globalThis) {
    const title = element.querySelector("#toast-title");
    const message = element.querySelector("#toast-message");
    let dismissTimer;
    let hideTimer;

    function dismiss() {
        timers.clearTimeout(dismissTimer);
        timers.clearTimeout(hideTimer);
        element.classList.remove("is-visible");
        hideTimer = timers.setTimeout(() => element.hidePopover(), 180);
    }

    function show(titleText, messageText, type = "normal", duration = 3000) {
        timers.clearTimeout(dismissTimer);
        timers.clearTimeout(hideTimer);
        // No HTML from a form or server error is interpreted here.
        title.textContent = titleText;
        message.textContent = messageText;
        element.dataset.type = ["success", "error"].includes(type) ? type : "normal";
        // Reopen so an existing toast also moves above a newly opened form.
        element.hidePopover();
        element.showPopover();
        element.classList.add("is-visible");
        dismissTimer = timers.setTimeout(dismiss, duration);
    }

    element.querySelector("#toast-close").addEventListener("click", dismiss);
    return { show, dismiss };
}

let toast;
export function showToast(title, message, type = "normal", duration = 3000) {
    toast ??= createToast(document.getElementById("toast"));
    toast.show(title, message, type, duration);
}

// Convenient for the tutorial's console exercises and other pages.
if (typeof window !== "undefined") window.showToast = showToast;
