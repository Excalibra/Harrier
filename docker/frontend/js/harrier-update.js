/**
 * Harrier Nuclei self-update widget.
 *
 * Fixed panel (bottom-right, above the language switch) showing the nuclei
 * engine version, template version and last-updated time, with an Update
 * button that triggers a worker-side update via /api/update/nuclei/ and
 * polls until it finishes.
 */
(function () {
  "use strict";

  var box = null, timer = null;

  function token() {
    try {
      return localStorage.getItem("token") || "";
    } catch (e) {
      return "";
    }
  }

  function api(method) {
    return fetch("/api/update/nuclei/", { method: method, headers: { token: token() } })
      .then(function (r) { return r.json(); });
  }

  function fmtDate(s) {
    return (s || "never").split(" ")[0];
  }

  function render(d) {
    if (!box) return;
    var data = (d && d.data) || {};
    var running = data.status === "running" || (data.running === true);

    var version = data.templates_version
      ? "templates " + data.templates_version + " · engine " + (data.engine_version || "?") +
        " · updated " + fmtDate(data.updated_at)
      : "update status unknown";

    box.innerHTML = "";
    var label = document.createElement("span");
    label.style.color = "#666";
    label.textContent = running ? "Nuclei: updating… " : "Nuclei: " + version + " ";
    box.appendChild(label);

    if (running) {
      var sp = document.createElement("span");
      sp.className = "pred-spinner";
      box.appendChild(sp);
    } else {
      var btn = document.createElement("a");
      btn.textContent = "Update";
      btn.href = "javascript:void(0)";
      btn.style.cssText = "color:#1890ff;cursor:pointer;";
      btn.onclick = function () {
        btn.textContent = "starting…";
        api("POST").then(pollSoon).catch(function () { pollSoon(); });
      };
      box.appendChild(btn);
    }
  }

  function poll() {
    api("GET").then(function (d) {
      render(d);
      var running = d && d.data && d.data.status === "running";
      if (running && !timer) {
        timer = setInterval(poll, 5000);
      } else if (!running && timer) {
        clearInterval(timer);
        timer = null;
      }
    }).catch(function () { /* ignore */ });
  }

  function pollSoon() { setTimeout(poll, 1500); }

  function build() {
    if (document.getElementById("harrier-update-widget")) return;
    box = document.createElement("div");
    box.id = "harrier-update-widget";
    box.style.cssText = "position:fixed;right:16px;bottom:52px;z-index:100000;" +
      "background:#fff;border:1px solid #d9d9d9;border-radius:4px;padding:4px 10px;" +
      "font-size:12px;font-family:sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.15);";
    document.body.appendChild(box);
    poll();
  }

  function boot() {
    if (!token()) return; // login page: wait for first navigation
    build();
  }

  // SPA: the app never reloads, so retry until logged in
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  setInterval(function () { if (!box && token()) build(); }, 3000);
})();
