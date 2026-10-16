// Paginate long notebook tables. The Colab `data_table` widget is interactive
// JS that cannot run in a static book, so its rendered fallback is one long
// table; this restores page-through navigation client-side, no dependencies.
(function () {
  var PAGE = 20;

  var style = document.createElement("style");
  style.textContent =
    ".nb-pagination{display:flex;gap:.25rem;flex-wrap:wrap;margin:.5rem 0 1rem}" +
    ".nb-pagination button{font:inherit;padding:.15rem .5rem;cursor:pointer;" +
    "border:1px solid var(--sidebar-active,#4183c4);border-radius:4px;" +
    "background:transparent;color:inherit;opacity:.7}" +
    ".nb-pagination button.active{opacity:1;background:var(--sidebar-active,#4183c4);" +
    "color:var(--sidebar-bg,#fff);border-color:transparent}";
  document.head.appendChild(style);

  function paginate(table) {
    var body = table.tBodies[0];
    if (!body) return;
    var rows = Array.prototype.slice.call(body.rows);
    if (rows.length <= PAGE) return;

    var pages = Math.ceil(rows.length / PAGE);
    var nav = document.createElement("div");
    nav.className = "nb-pagination";
    var buttons = [];

    function show(p) {
      rows.forEach(function (r, i) {
        r.style.display = i >= p * PAGE && i < (p + 1) * PAGE ? "" : "none";
      });
      buttons.forEach(function (b, i) {
        b.classList.toggle("active", i === p);
      });
    }

    for (var p = 0; p < pages; p++) {
      (function (p) {
        var b = document.createElement("button");
        b.type = "button";
        b.textContent = String(p + 1);
        b.addEventListener("click", function () {
          show(p);
        });
        nav.appendChild(b);
        buttons.push(b);
      })(p);
    }

    table.parentNode.insertBefore(nav, table.nextSibling);
    show(0);
  }

  function run() {
    document.querySelectorAll(".nb-output table").forEach(paginate);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
