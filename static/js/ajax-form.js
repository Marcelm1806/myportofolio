import { postForm } from "./ajax.js?v=assignment5-20260930";

/** No role-specific elements are accessed until the authorized form exists. */
export function bindAjaxForm({ form, modal, summary, submit, url, csrfToken,
    firstField, label, savedTitle, notify, onSuccess, send = postForm }) {
    if (!form) return;
    const submitLabel = submit.textContent;

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
        if (event.newState === "open") form.elements.namedItem(firstField)?.focus();
    });
    form.addEventListener("submit", async event => {
        event.preventDefault();
        if (submit.disabled) return;
        clearErrors();
        submit.disabled = true;
        submit.textContent = "Saving…";
        form.setAttribute("aria-busy", "true");
        try {
            const result = await send(url, new FormData(form), csrfToken, { label });
            modal.hidePopover();
            form.reset();
            notify(savedTitle, result.message, "success");
            await onSuccess();
        } catch (error) {
            displayErrors(error);
            notify(`Could not save ${label}`, error.message, "error", 6000);
        } finally {
            submit.disabled = false;
            submit.textContent = submitLabel;
            form.removeAttribute("aria-busy");
        }
    });
    return { clearErrors };
}
