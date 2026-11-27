(function () {
  const form = document.getElementById("login-form");
  const err = document.getElementById("login-error");
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    err.hidden = true;
    const fd = new FormData(form);
    const body = {
      username: fd.get("username"),
      password: fd.get("password"),
    };
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        err.textContent = data.error || "登录失败";
        err.hidden = false;
        return;
      }
      window.location.href = "/app/";
    } catch (e) {
      err.textContent = "网络异常，请稍后重试";
      err.hidden = false;
    }
  });
})();