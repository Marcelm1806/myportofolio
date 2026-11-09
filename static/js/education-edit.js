import { createFormFeedback } from "./ajax-form.js?v=assignment6-20261109";
import { formPayload, requestJson } from "./rest.js?v=assignment6-20261109";

/** Edit the current record in place; the link still works as a full-page fallback. */
export function bindEducationEditor({ grid, dialog, csrfToken, refresh, notify, fallbackFocus, send = requestJson }) {
    if (!dialog?.showModal) return;
    const form = dialog.querySelector("form");
    const fields = form.querySelector("fieldset");
    const submit = form.querySelector('[type="submit"]');
    const restore = form.querySelector("[data-edit-restore]");
    const status = form.querySelector("[data-edit-status]");
    const loading = dialog.querySelector("[data-edit-load]");
    const closeButtons = dialog.querySelectorAll("[data-edit-close]");
    const feedback = createFormFeedback(form, form.querySelector("[data-edit-error]"));
    const labels = Object.fromEntries([...fields.elements].map(field => [
        field.name, field.labels?.[0]?.textContent.replace(/\s*\*\s*$/, "").trim() || field.name,
    ]));
    let edit = null;

    function populate(values) {
        for (const field of fields.elements) {
            if (!Object.hasOwn(values, field.name)) continue;
            if (field.type === "checkbox") field.checked = values[field.name] === true;
            else field.value = values[field.name] ?? "";
        }
    }

    function payload() {
        return formPayload(new FormData(form), "education");
    }

    function changes() {
        if (!edit?.original) return {};
        return Object.fromEntries(Object.entries(payload()).filter(([name, value]) =>
            !Object.is(value, edit.original[name])));
    }

    function updateChanges() {
        if (edit?.saving) return;
        const changed = Object.keys(changes());
        const message = changed.length
            ? "Unsaved changes: " + changed.map(name => labels[name]).join(", ") + "."
            : "No unsaved changes.";
        if (status.textContent !== message) status.textContent = message;
        submit.disabled = restore.disabled = changed.length === 0;
    }

    function dismiss() {
        edit?.controller.abort();
        edit = null;
        dialog.close();
    }

    grid.addEventListener("click", async event => {
        const link = event.target.closest("a[data-education-edit]");
        if (!link || !grid.contains(link) || event.defaultPrevented || event.button !== 0 ||
            event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        if (dialog.open) return;
        const session = {
            id: link.dataset.educationEdit, url: link.dataset.url, link,
            controller: new AbortController(), original: null, saving: false,
        };
        edit = session;
        feedback.clearErrors();
        fields.disabled = form.hidden = true;
        loading.hidden = false;
        loading.textContent = "Loading education entry…";
        dialog.showModal();
        try {
            const entry = await send(session.url, { method: "GET", signal: session.controller.signal });
            // Ignore an earlier read if the editor closed the dialog or opened another entry.
            if (edit !== session || !dialog.open) return;
            if (entry.id !== session.id) throw new Error("The server returned a different entry.");
            populate(entry);
            fields.disabled = form.hidden = false;
            loading.hidden = true;
            session.original = payload();
            updateChanges();
            form.elements.namedItem("institution")?.focus();
        } catch (error) {
            if (edit !== session || !dialog.open) return;
            loading.textContent = "Could not open this entry. Close the form and try again.";
            notify("Could not load education", error.message, "error", 6000);
        }
    });

    for (const button of closeButtons) {
        button.addEventListener("click", () => { if (!edit?.saving) dismiss(); });
    }
    dialog.addEventListener("cancel", event => {
        event.preventDefault();
        if (!edit?.saving) dismiss();
    });
    form.addEventListener("input", updateChanges);
    restore.addEventListener("click", () => {
        if (!edit?.original || edit.saving) return;
        populate(edit.original);
        feedback.clearErrors();
        updateChanges();
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();
        const session = edit;
        if (!session?.original || session.saving) return;
        const data = changes();
        if (!Object.keys(data).length) return;
        feedback.clearErrors();
        session.saving = true;
        fields.disabled = submit.disabled = restore.disabled = true;
        closeButtons.forEach(button => { button.disabled = true; });
        submit.textContent = "Saving…";
        form.setAttribute("aria-busy", "true");
        try {
            await send(session.url, { method: "PATCH", data, csrfToken });
        } catch (error) {
            feedback.displayErrors(error);
            notify("Could not save education", error.message, "error", 6000);
            return;
        } finally {
            session.saving = false;
            fields.disabled = false;
            closeButtons.forEach(button => { button.disabled = false; });
            submit.textContent = "Save changes";
            form.removeAttribute("aria-busy");
            updateChanges();
        }
        dismiss();
        notify("Education updated", "Your changes have been saved.", "success");
        await refresh();
        // Restore focus to the updated card, or to search if it no longer matches.
        if (!dialog.open && [document.body, session.link].includes(document.activeElement)) {
            const replacement = [...grid.querySelectorAll("[data-education-edit]")]
                .find(link => link.dataset.educationEdit === session.id);
            (replacement || fallbackFocus)?.focus();
        }
    });
}
