import {confirmAction, request, status} from "./core.js";

for (const button of document.querySelectorAll("button[data-delete]")) {
  button.addEventListener("click", async () => {
    button.disabled = true;
    const label = button.textContent.trim();
    const feedback = button.parentElement.querySelector(".feedback");
    feedback.hidden = true;
    try {
      if (!await confirmAction(label + "?", button.dataset.description, label)) return;
      await request(button.dataset.delete, {method: "DELETE"});
      if (button.dataset.destination) window.location.assign(button.dataset.destination);
      else window.location.reload();
    } catch (error) {
      feedback.hidden = false;
      status(feedback, error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}
