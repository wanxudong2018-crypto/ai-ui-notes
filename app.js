(function () {
  "use strict";

  var data = window.APP_DATA || [];
  var grid = document.getElementById("grid");
  var catList = document.getElementById("cat-list");
  var search = document.getElementById("search");
  var empty = document.getElementById("empty");
  var activeCat = "全部";
  var cur = null; // 当前弹窗里的流程记录
  var idx = 0;    // 当前步骤索引

  function imgs(d) {
    if (Array.isArray(d.images) && d.images.length) return d.images;
    if (d.img) return [d.img];
    return [];
  }
  function steps(d) {
    return Array.isArray(d.steps) ? d.steps : [];
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (m) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m];
    });
  }

  function categories() {
    var set = {};
    data.forEach(function (d) { set[d.problem || "未分类"] = 1; });
    return ["全部"].concat(Object.keys(set));
  }

  function renderCats() {
    catList.innerHTML = "";
    categories().forEach(function (c) {
      var li = document.createElement("li");
      li.textContent = c;
      li.className = c === activeCat ? "active" : "";
      li.onclick = function () { activeCat = c; renderCats(); renderGrid(); };
      catList.appendChild(li);
    });
  }

  function placeholder(d) {
    var el = document.createElement("div");
    el.className = "ph";
    el.innerHTML = esc(d.app || "?") + "<br>" + esc(d.problem || "");
    return el;
  }

  // 一个 App 流程 = 一张卡片，里面竖向堆叠这个流程的所有截图
  function createCard(record) {
    var arr = imgs(record);
    var st = steps(record);
    var card = document.createElement("div");
    card.className = "card";

    var stack = document.createElement("div");
    stack.className = "card-stack";

    if (arr.length) {
      arr.forEach(function (url, i) {
        var img = document.createElement("img");
        img.loading = "lazy";
        img.src = url;
        img.alt = (record.app || "") + " 步骤" + (i + 1);
        img.onerror = function () {
          this.style.display = "none";
          stack.appendChild(placeholder(record));
        };
        stack.appendChild(img);
      });
    } else {
      stack.appendChild(placeholder(record));
    }

    card.appendChild(stack);

    var body = document.createElement("div");
    body.className = "card-body";
    body.innerHTML =
      '<span class="chip">' + esc(record.problem || "") + "</span>" +
      '<div class="card-app">' + esc(record.app || "") + "</div>" +
      '<div class="card-note">' + esc(st[0] || record.note || "") + "</div>";
    card.appendChild(body);

    card.onclick = function () { openModal(record, 0); };
    return card;
  }

  function renderGrid() {
    var q = (search.value || "").trim().toLowerCase();
    var items = data.filter(function (d) {
      var okCat = activeCat === "全部" || d.problem === activeCat;
      var hay = [d.app, d.problem, d.note].concat(steps(d)).join(" ").toLowerCase();
      var okQ = !q || hay.indexOf(q) !== -1;
      return okCat && okQ;
    });

    grid.innerHTML = "";
    empty.hidden = items.length > 0;
    items.forEach(function (d) {
      grid.appendChild(createCard(d));
    });
  }

  function renderStage() {
    var arr = imgs(cur);
    var stage = document.getElementById("modal-img");
    stage.innerHTML = "";
    var url = arr[idx] || "";
    if (url) {
      var img = document.createElement("img");
      img.src = url;
      img.onerror = function () { stage.innerHTML = ""; stage.appendChild(placeholder(cur)); };
      stage.appendChild(img);
    } else {
      stage.appendChild(placeholder(cur));
    }

    var dots = document.getElementById("modal-dots");
    dots.innerHTML = "";
    if (arr.length > 1) {
      arr.forEach(function (_, i) {
        var dot = document.createElement("span");
        dot.className = "dot" + (i === idx ? " on" : "");
        dot.onclick = function () { idx = i; renderStage(); };
        dots.appendChild(dot);
      });
    }

    var st = steps(cur);
    var cap;
    if (arr.length > 1) {
      cap = "步骤 " + (idx + 1) + " / " + arr.length + (st[idx] ? "：" + st[idx] : "");
    } else {
      cap = st[0] || "";
    }
    document.getElementById("modal-step").textContent = cap;

    var show = arr.length > 1;
    document.getElementById("nav-prev").style.display = show ? "flex" : "none";
    document.getElementById("nav-next").style.display = show ? "flex" : "none";
  }

  function openModal(d, startIdx) {
    cur = d;
    idx = startIdx || 0;
    document.getElementById("modal-problem").textContent = d.problem || "";
    document.getElementById("modal-app").textContent = d.app || "";
    document.getElementById("modal-platform").textContent = d.platform ? "平台：" + d.platform : "";
    document.getElementById("modal-note").textContent = d.note || "";
    renderStage();
    document.getElementById("modal").hidden = false;
  }
  function closeModal() {
    document.getElementById("modal").hidden = true;
    cur = null;
  }
  function stepBy(delta) {
    var arr = imgs(cur);
    idx = (idx + delta + arr.length) % arr.length;
    renderStage();
  }

  document.getElementById("modal-close").onclick = closeModal;
  document.querySelector(".modal-backdrop").onclick = closeModal;
  document.getElementById("nav-prev").onclick = function (e) { e.stopPropagation(); stepBy(-1); };
  document.getElementById("nav-next").onclick = function (e) { e.stopPropagation(); stepBy(1); };
  document.addEventListener("keydown", function (e) {
    if (document.getElementById("modal").hidden) return;
    if (e.key === "Escape") closeModal();
    else if (e.key === "ArrowLeft") stepBy(-1);
    else if (e.key === "ArrowRight") stepBy(1);
  });
  search.addEventListener("input", renderGrid);

  renderCats();
  renderGrid();
})();
