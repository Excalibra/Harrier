/**
 * Harrier UI enhancements (runtime overlay, no Vue source needed).
 *
 * Task detail page (/taskList/taskDetail?task_id=...):
 *  1. "Report" widget with XLSX / XML / HTML download links
 *     (/api/export/<task_id>?format=...).
 *  2. Live scan banner polling /api/task/?task_id=... every 5s: current
 *     stage (the backend writes it into task.status), elapsed time,
 *     completed stages and finding counts.
 *
 * Task list page (/taskList):
 *  3. Injects a spinner + progress percentage into the status cell of
 *     every running task row, refreshed every 5s.
 *
 * All widgets follow SPA navigation via a location watcher, so they
 * appear/disappear correctly without a full page reload.
 */
(function () {
  "use strict";

  var POLL_MS = 5000;
  var KNOWN_FINAL = { done: 1, stop: 1, error: 1, waiting: 1 };

  // Stage templates used for the progress percentage estimate.
  var STAGE_TOTAL = {
    "task": 10,          // port_scan ... web_info_hunter
    "risk_cruising": 10, // fetch_site ... PoC
    "default": 10
  };

  function getTaskId() {
    var m = location.search.match(/[?&]task_id=([0-9a-f]{24})/);
    return m ? m[1] : null;
  }

  function onDetailPage() {
    return location.pathname.indexOf("/taskList/taskDetail") === 0 && !!getTaskId();
  }

  function onTaskListPage() {
    return /\/taskList\/?$/.test(location.pathname);
  }

  function token() {
    try {
      return localStorage.getItem("token") || "";
    } catch (e) {
      return "";
    }
  }

  function fmtElapsed(sec) {
    sec = Math.max(0, Math.round(sec));
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    var s = sec % 60;
    if (h) return h + "h " + m + "m " + s + "s";
    if (m) return m + "m " + s + "s";
    return s + "s";
  }

  function parseTime(str) {
    if (!str || str === "-") return null;
    var d = new Date(str.replace(" ", "T"));
    return isNaN(d.getTime()) ? null : d;
  }

  function elapsedOf(t) {
    var start = parseTime(t.start_time);
    var end = parseTime(t.end_time);
    var byClock = start ? ((end || new Date()) - start) / 1000 : 0;
    // Fallback: sum of completed stage durations (start_time can lag).
    var byStages = 0;
    (t.service || []).forEach(function (s) { byStages += s.elapsed || 0; });
    return Math.max(byClock, byStages);
  }

  function injectStyle() {
    if (document.getElementById("harrier-report-style")) return;
    var st = document.createElement("style");
    st.id = "harrier-report-style";
    st.textContent =
      "@keyframes pred-spin{to{transform:rotate(360deg)}}" +
      ".pred-spinner{display:inline-block;width:10px;height:10px;margin-right:4px;" +
      "border:2px solid #1890ff;border-top-color:transparent;border-radius:50%;" +
      "animation:pred-spin .8s linear infinite;vertical-align:-1px}" +
      ".pred-progress{color:#1890ff;font-size:12px;white-space:nowrap}";
    document.head.appendChild(st);
  }

  // ---------- report widget (detail page) ----------

  function download(fmt) {
    var id = getTaskId();
    fetch("/api/export/" + id + "?format=" + fmt, { headers: { token: token() } })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.blob();
      })
      .then(function (blob) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "harrier-report-" + id + "." + fmt;
        document.body.appendChild(a);
        a.click();
        setTimeout(function () {
          URL.revokeObjectURL(a.href);
          a.remove();
        }, 1000);
      })
      .catch(function (e) {
        alert("Export failed: " + e.message);
      });
  }

  var banner, pollTimer = null, tickTimer = null, lastTask = null;

  function buildWidget() {
    var box = document.createElement("div");
    box.id = "harrier-report-widget";
    box.style.cssText = "position:fixed;left:16px;bottom:16px;z-index:100000;" +
      "background:#fff;border:1px solid #d9d9d9;border-radius:4px;padding:4px 10px;" +
      "font-size:12px;font-family:sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.15);";

    var label = document.createElement("span");
    label.textContent = "Report: ";
    label.style.color = "#666";
    box.appendChild(label);

    ["xlsx", "xml", "html"].forEach(function (fmt, i) {
      var a = document.createElement("a");
      a.textContent = fmt.toUpperCase();
      a.href = "javascript:void(0)";
      a.style.cssText = "color:#1890ff;cursor:pointer;";
      a.onclick = function () { download(fmt); };
      box.appendChild(a);
      if (i < 2) box.appendChild(document.createTextNode(" · "));
    });

    banner = document.createElement("div");
    banner.id = "harrier-scan-banner";
    banner.style.cssText = "position:fixed;left:16px;bottom:52px;z-index:100000;" +
      "background:#fff;border:1px solid #d9d9d9;border-radius:4px;padding:6px 12px;" +
      "font-size:12px;font-family:sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.15);" +
      "max-width:60vw;display:none;";

    document.body.appendChild(banner);
    document.body.appendChild(box);
  }

  function render() {
    if (!banner || !lastTask) return;
    var t = lastTask;
    var status = t.status || "?";
    var st = t.statistic || {};
    var stages = (t.service || []).map(function (s) { return s.name; });
    var total = STAGE_TOTAL[t.task_tag] || STAGE_TOTAL["default"];
    var pct = Math.min(99, Math.round(100 * stages.length / total));

    var counts = "sites " + (st.site_cnt || 0) +
      " · vulns " + ((st.vuln_cnt || 0) + (st.nuclei_result_cnt || 0)) +
      " · fileleak " + (st.fileleak_cnt || 0) +
      " · wih " + (st.wih_cnt || 0);

    var html;
    if (KNOWN_FINAL[status]) {
      var color = status === "done" ? "#52c41a" : (status === "waiting" ? "#999" : "#fa541c");
      html = "<b style='color:" + color + "'>■ " + status.toUpperCase() + "</b>" +
        " — " + stages.length + " stages, " + fmtElapsed(elapsedOf(t)) +
        "<br><span style='color:#666'>" + counts + "</span>";
    } else {
      html = "<span class='pred-spinner'></span>" +
        "<b style='color:#f5222d'>RUNNING</b>" +
        " stage: <b>" + status + "</b> · " + pct + "%" +
        " — elapsed " + fmtElapsed(elapsedOf(t)) +
        " · " + stages.length + "/" + total + " stages" +
        (stages.length ? " (" + stages.join(" → ") + ")" : "") +
        "<br><span style='color:#666'>" + counts + "</span>";
    }
    banner.innerHTML = html;
    banner.style.display = "block";
  }

  function pollDetail() {
    var id = getTaskId();
    if (!id) return;
    fetch("/api/task/?task_id=" + id, { headers: { token: token() } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.items && d.items.length) {
          lastTask = d.items[0];
          render();
        }
      })
      .catch(function () { /* keep polling */ });
  }

  // ---------- task list row progress ----------

  function pollList() {
    fetch("/api/task/", { headers: { token: token() } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.items) return;
        var rows = document.querySelectorAll(".ant-table-tbody tr");
        d.items.forEach(function (item) {
          if (KNOWN_FINAL[item.status]) return;
          for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            if (row.textContent.indexOf(item.name) === -1) continue;
            var cell = null;
            var tds = row.querySelectorAll("td");
            for (var j = 0; j < tds.length; j++) {
              if (tds[j].textContent.trim() === item.status ||
                  tds[j].querySelector(".pred-progress")) {
                cell = tds[j];
                break;
              }
            }
            if (!cell) continue;
            var stages = (item.service || []).length;
            var total = STAGE_TOTAL[item.task_tag] || STAGE_TOTAL["default"];
            var pct = Math.min(99, Math.round(100 * stages / total));
            var span = cell.querySelector(".pred-progress");
            if (!span) {
              span = document.createElement("div");
              span.className = "pred-progress";
              cell.appendChild(span);
            }
            span.innerHTML = "<span class='pred-spinner'></span>" + pct + "% " + item.status;
            break;
          }
        });
      })
      .catch(function () { /* keep polling */ });
  }

  // ---------- lifecycle: follow SPA navigation ----------

  var currentHref = null;

  function teardown() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    if (tickTimer) { clearInterval(tickTimer); tickTimer = null; }
    lastTask = null;
    ["harrier-scan-banner", "harrier-report-widget"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.remove();
    });
    banner = null;
  }

  function apply() {
    if (onDetailPage()) {
      buildWidget();
      pollDetail();
      pollTimer = setInterval(pollDetail, POLL_MS);
      tickTimer = setInterval(render, 1000);
    } else if (onTaskListPage()) {
      pollList();
      pollTimer = setInterval(pollList, POLL_MS);
    }
  }

  function watch() {
    if (location.href === currentHref) return;
    currentHref = location.href;
    teardown();
    apply();
  }

  function boot() {
    injectStyle();
    watch();
    setInterval(watch, 800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
