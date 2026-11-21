// Curation › Accounts: create accounts, deactivate or reactivate them, and delete unused ones.
import {bindForm, confirmAction, endpoint, find, request, status} from "./core.js";

bindForm("new-account", async (data) => {
  const path = data.get("role") === "curator" ? "/api/users/add-new-super-user" : "/api/users/add-new-user";
  await request(path, {method: "POST", json: {name: data.get("name").trim(), surname: data.get("surname").trim(),
                                              email: data.get("email").trim(), password: data.get("password")}});
  window.location.reload();
  return "Account created.";
});

for (const row of find("accounts").querySelectorAll("li[data-user]")) {
  const message = row.querySelector(".feedback");
  const user = endpoint(row.dataset.user);
  row.querySelector("[data-active]")?.addEventListener("click", async (event) => {
    const active = event.currentTarget.dataset.active === "true";
    try {
      await request(`/api/users/update/is_active?user_id=${user}&is_active=${active}`, {method: "PUT"});
      window.location.reload();
    } catch (error) {
      status(message, error.message, true);
    }
  });
  row.querySelector("[data-delete]")?.addEventListener("click", async () => {
    if (!await confirmAction(`Delete ${row.dataset.name}?`,
      "Only accounts that never recorded anything can be deleted. Otherwise deactivate the account instead.", "Delete")) return;
    try {
      await request(`/api/users/delete-user?user_id=${user}`, {method: "DELETE"});
      row.remove();
    } catch (error) {
      status(message, error.message, true);
    }
  });
}
