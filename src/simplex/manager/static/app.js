(function () {
  "use strict";

  var SETTINGS_KEY = "simplex-manager-settings-v1";
  var state = null;
  var settings = readSettings();
  var selectedDeck = settings.selectedDeck || "";
  var selectedScene = settings.selectedScene || "";
  var selectedJobId = "";
  var cache = settings.cache || "on";
  var dragged = null;
  var lastJobs = [];
  var runSettingsApplied = false;

  var el = {
    repo: document.getElementById("repo-label"),
    search: document.getElementById("deck-search"),
    deckList: document.getElementById("deck-list"),
    sectionLabel: document.getElementById("section-label"),
    title: document.getElementById("deck-title"),
    summary: document.getElementById("deck-summary"),
    entrypoints: document.getElementById("entrypoints"),
    available: document.getElementById("available"),
    defaultsEditor: document.getElementById("defaults-editor"),
    save: document.getElementById("save-order"),
    saveDefaults: document.getElementById("save-defaults"),
    refresh: document.getElementById("refresh"),
    openDeckPage: document.getElementById("open-deck-page"),
    quality: document.getElementById("quality"),
    slideTheme: document.getElementById("slide-theme"),
    openAfter: document.getElementById("open-after"),
    renderSelected: document.getElementById("render-selected"),
    renderDeck: document.getElementById("render-deck"),
    buildSelected: document.getElementById("build-selected"),
    buildNoRender: document.getElementById("build-no-render"),
    renderedStatus: document.getElementById("rendered-status"),
    jobsList: document.getElementById("jobs-list"),
    jobLog: document.getElementById("job-log"),
    jobPreview: document.getElementById("job-preview"),
    jobState: document.getElementById("job-state"),
    clearJobs: document.getElementById("clear-jobs"),
  };

  var ANSI_COLORS = {
    30: "#8b949e",
    31: "#ff7b72",
    32: "#7ee787",
    33: "#f2cc60",
    34: "#79c0ff",
    35: "#d2a8ff",
    36: "#56d4dd",
    37: "#f0f6fc",
    90: "#6e7681",
    91: "#ffa198",
    92: "#7ee787",
    93: "#f2cc60",
    94: "#a5d6ff",
    95: "#d2a8ff",
    96: "#56d4dd",
    97: "#ffffff",
  };

  function icons() {
    if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
  }

  function api(path, options) {
    return fetch(path, options).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) throw new Error(data.error || res.statusText);
        return data;
      });
    });
  }

  function readSettings() {
    try {
      var raw = window.localStorage.getItem(SETTINGS_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  }

  function saveSettings() {
    settings.selectedDeck = selectedDeck;
    settings.selectedScene = selectedScene;
    settings.quality = el.quality.value || "default";
    settings.slideTheme = el.slideTheme.value || "all";
    settings.cache = cache;
    settings.openAfter = el.openAfter.checked;
    try {
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch (_) {}
  }

  function currentDeck() {
    if (!state || !state.decks.length) return null;
    return state.decks.find(function (deck) { return deck.slug === selectedDeck; }) || state.decks[0];
  }

  function ensureSelection() {
    if (!state || !state.decks.length) return;
    var savedDeck = state.decks.find(function (deck) { return deck.slug === selectedDeck; });
    selectedDeck = savedDeck ? savedDeck.slug : state.decks[0].slug;
    var deck = currentDeck();
    if (!deck) return;
    var entries = deck.entrypoints || [];
    var selected = entries.find(function (entry) { return entry.scene === selectedScene; });
    if (!selected && settings.selectedScene) {
      selected = entries.find(function (entry) { return entry.scene === settings.selectedScene; });
    }
    selectedScene = selected ? selected.scene : (entries[0] ? entries[0].scene : "");
  }

  function load() {
    return api("/api/state").then(function (data) {
      state = data;
      ensureSelection();
      renderAll();
      return refreshJobs();
    }).catch(function (err) {
      el.title.textContent = "Manager error";
      el.summary.textContent = err.message;
    });
  }

  function refreshJobs() {
    return api("/api/jobs").then(function (data) {
      renderJobs(data.jobs || []);
    }).catch(function () {});
  }

  function renderAll() {
    renderQuality();
    applyRunSettings();
    renderDeckList();
    renderDeck();
    syncCacheButtons();
    icons();
  }

  function renderQuality() {
    if (!state) return;
    var current = el.quality.value || settings.quality || "default";
    el.quality.innerHTML = '<option value="default">Project default</option>';
    state.qualities.forEach(function (option) {
      var node = document.createElement("option");
      node.value = option.name;
      node.textContent = option.label + " (" + option.pixel_width + "x" + option.pixel_height + " @ " + option.frame_rate + "fps)";
      el.quality.appendChild(node);
    });
    if (Array.prototype.some.call(el.quality.options, function (option) { return option.value === current; })) {
      el.quality.value = current;
    } else {
      el.quality.value = "default";
    }
  }

  function applyRunSettings() {
    if (runSettingsApplied) return;
    el.quality.value = settings.quality || "default";
    el.slideTheme.value = settings.slideTheme || "all";
    el.openAfter.checked = Boolean(settings.openAfter);
    cache = settings.cache || "on";
    runSettingsApplied = true;
  }

  function syncCacheButtons() {
    document.querySelectorAll("[data-cache]").forEach(function (item) {
      item.classList.toggle("active", item.dataset.cache === cache);
    });
  }

  function renderDeckList() {
    var q = (el.search.value || "").trim().toLowerCase();
    el.deckList.innerHTML = "";
    state.decks.filter(function (deck) {
      return !q || (deck.title + " " + deck.slug + " " + deck.summary).toLowerCase().includes(q);
    }).forEach(function (deck) {
      var btn = document.createElement("button");
      btn.className = "deck-item" + (deck.slug === selectedDeck ? " active" : "");
      btn.type = "button";
      btn.innerHTML = '<i data-lucide="presentation"></i><span>' + escapeHtml(deck.title || deck.slug) + '</span>';
      btn.addEventListener("click", function () {
        selectedDeck = deck.slug;
        selectedScene = "";
        ensureSelection();
        saveSettings();
        renderAll();
      });
      el.deckList.appendChild(btn);
    });
  }

  function renderDeck() {
    var deck = currentDeck();
    if (!deck) return;
    selectedDeck = deck.slug;
    if (!selectedScene && deck.entrypoints.length) selectedScene = deck.entrypoints[0].scene;
    el.repo.textContent = state.brand || "Manager";
    el.sectionLabel.textContent = deck.section || "Deck";
    el.title.textContent = deck.title || deck.slug;
    el.summary.textContent = deck.summary || deck.path;
    el.openDeckPage.href = "/../site/decks/" + deck.slug + "/index.html";
    renderEntryPoints(deck);
    renderAvailable(deck);
    renderDefaults(deck);
    renderStatus(deck);
    icons();
  }

  function renderEntryPoints(deck) {
    el.entrypoints.innerHTML = "";
    deck.entrypoints.forEach(function (entry) {
      var row = entryRow(entry, true);
      row.draggable = true;
      row.addEventListener("dragstart", function () {
        dragged = row;
        row.classList.add("dragging");
      });
      row.addEventListener("dragend", function () {
        row.classList.remove("dragging");
        dragged = null;
      });
      row.addEventListener("dragover", function (event) {
        event.preventDefault();
        if (!dragged || dragged === row) return;
        var box = row.getBoundingClientRect();
        var after = event.clientY > box.top + box.height / 2;
        el.entrypoints.insertBefore(dragged, after ? row.nextSibling : row);
      });
      el.entrypoints.appendChild(row);
    });
  }

  function entryRow(entry, configured) {
    var row = document.createElement("div");
    row.className = "entry-row" + (entry.scene === selectedScene ? " selected" : "");
    row.dataset.value = entry.value;
    row.dataset.scene = entry.scene;
    row.innerHTML =
      '<button class="drag icon-only" type="button" title="Drag"><i data-lucide="grip-vertical"></i></button>' +
      '<div class="entry-main">' +
        '<div class="entry-title"><span class="entry-scene">' + escapeHtml(entry.scene) + '</span>' +
        badge(entry.renderer) + '</div>' +
        '<div class="entry-target">' + escapeHtml(entry.value) + '</div>' +
      '</div>' +
      '<button class="icon-only render-one" type="button" title="Render"><i data-lucide="play"></i></button>' +
      '<button class="icon-only hide-one" type="button" title="' + (configured ? "Remove from entrypoints" : "Add to entrypoints") + '">' +
        '<i data-lucide="' + (configured ? "eye-off" : "plus") + '"></i></button>';
    row.addEventListener("click", function (event) {
      if (event.target.closest("button")) return;
      selectedScene = entry.scene;
      saveSettings();
      renderDeck();
    });
    row.querySelector(".render-one").addEventListener("click", function () {
      selectedScene = entry.scene;
      saveSettings();
      startJob("render_scene");
    });
    row.querySelector(".hide-one").addEventListener("click", function () {
      if (configured) removeEntry(entry.value);
      else addEntry(entry.value);
    });
    return row;
  }

  function badge(renderer) {
    var cls = renderer === "opengl" ? "badge opengl" : "badge";
    return '<span class="' + cls + '">' + escapeHtml(renderer || "cairo") + '</span>';
  }

  function renderAvailable(deck) {
    el.available.innerHTML = "";
    if (!deck.available.length) {
      el.available.innerHTML = '<p class="entry-target">No extra scene classes found.</p>';
      return;
    }
    deck.available.forEach(function (entry) {
      el.available.appendChild(entryRow(entry, false));
    });
  }

  function renderDefaults(deck) {
    el.defaultsEditor.innerHTML = "";
    var specs = state.deckOptions || [];
    var grouped = {};
    specs.forEach(function (spec) {
      if (!grouped[spec.group]) grouped[spec.group] = [];
      grouped[spec.group].push(spec);
    });
    Object.keys(grouped).forEach(function (groupName) {
      var group = document.createElement("section");
      group.className = "defaults-group";
      var heading = document.createElement("h4");
      heading.textContent = groupName;
      group.appendChild(heading);
      grouped[groupName].forEach(function (spec) {
        group.appendChild(defaultRow(deck, spec));
      });
      el.defaultsEditor.appendChild(group);
    });
  }

  function defaultRow(deck, spec) {
    var current = (deck.defaults && deck.defaults[spec.path]) || { value: "", present: false };
    var row = document.createElement("label");
    row.className = "default-row";
    row.dataset.optionPath = spec.path;
    row.dataset.kind = spec.kind;
    row.dataset.readonly = spec.readonly ? "true" : "false";
    row.innerHTML =
      '<span class="default-label">' +
        '<span>' + escapeHtml(spec.label) + '</span>' +
        '<button class="help-dot" type="button" title="' + escapeHtml(spec.help || "") + '">?</button>' +
      '</span>' +
      '<span class="default-control"></span>';
    row.querySelector(".help-dot").addEventListener("click", function (event) {
      event.preventDefault();
    });
    row.querySelector(".default-control").appendChild(defaultControl(spec, current));
    return row;
  }

  function defaultControl(spec, current) {
    if (spec.kind === "boolean") {
      var boolSelect = document.createElement("select");
      boolSelect.innerHTML = '<option value="default">Default</option><option value="true">On</option><option value="false">Off</option>';
      boolSelect.value = current.present ? String(Boolean(current.value)) : "default";
      return boolSelect;
    }
    if (spec.kind === "select") {
      var select = document.createElement("select");
      select.innerHTML = '<option value="default">Default</option>';
      (spec.choices || []).forEach(function (choice) {
        var option = document.createElement("option");
        option.value = choice;
        option.textContent = choice;
        select.appendChild(option);
      });
      select.value = current.present && current.value ? String(current.value) : "default";
      return select;
    }
    var input = document.createElement("input");
    input.type = spec.kind === "integer" ? "number" : spec.kind === "date" ? "date" : "text";
    input.value = current.present || spec.required ? formatOptionValue(current.value) : "";
    input.placeholder = defaultPlaceholder(spec);
    input.disabled = Boolean(spec.readonly);
    return input;
  }

  function defaultPlaceholder(spec) {
    if (spec.required) return "";
    if (!Object.prototype.hasOwnProperty.call(spec, "default") || spec.default == null) return "Default";
    if (Array.isArray(spec.default)) return "Default";
    return "Default: " + formatOptionValue(spec.default);
  }

  function formatOptionValue(value) {
    if (Array.isArray(value)) return value.join(", ");
    if (value == null) return "";
    return String(value);
  }

  function saveDefaults() {
    var values = {};
    el.defaultsEditor.querySelectorAll("[data-option-path]").forEach(function (row) {
      if (row.dataset.readonly === "true") return;
      var control = row.querySelector("input, select");
      if (!control) return;
      values[row.dataset.optionPath] = control.value;
    });
    return api("/api/decks/" + encodeURIComponent(selectedDeck) + "/defaults", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values: values }),
    }).then(function (data) {
      state = data;
      ensureSelection();
      renderAll();
    }).catch(function (err) {
      alert(err.message);
    });
  }

  function renderStatus(deck) {
    var rendered = deck.rendered || {};
    var themes = (rendered.themes || []).map(function (theme) {
      return theme.id + (theme.hasMp4 ? " mp4" : "");
    }).join(", ");
    el.renderedStatus.innerHTML =
      '<strong>Rendered</strong><br>' +
      'Slides: ' + (rendered.slideCount || 0) + '<br>' +
      'Duration: ' + Math.round(rendered.duration || 0) + 's<br>' +
      'Themes: ' + escapeHtml(themes || "none");
  }

  function currentEntrypoints() {
    return Array.prototype.slice.call(el.entrypoints.querySelectorAll(".entry-row"))
      .map(function (row) { return row.dataset.value; })
      .filter(Boolean);
  }

  function saveEntrypoints(values) {
    return api("/api/decks/" + encodeURIComponent(selectedDeck) + "/entrypoints", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entrypoints: values }),
    }).then(function (data) {
      state = data;
      ensureSelection();
      renderAll();
    }).catch(function (err) {
      alert(err.message);
    });
  }

  function removeEntry(value) {
    saveEntrypoints(currentEntrypoints().filter(function (item) { return item !== value; }));
  }

  function addEntry(value) {
    var values = currentEntrypoints();
    if (!values.includes(value)) values.push(value);
    saveEntrypoints(values);
  }

  function selectedDeckPayload() {
    return {
      deckSlug: selectedDeck,
      scene: selectedScene,
      slideTheme: el.slideTheme.value,
      quality: el.quality.value,
      cache: cache,
      openAfter: el.openAfter.checked,
    };
  }

  function startJob(action, extra) {
    saveSettings();
    var payload = Object.assign({ action: action }, selectedDeckPayload(), extra || {});
    if (action === "build") {
      payload.deckSlugs = [selectedDeck];
      delete payload.deckSlug;
      delete payload.scene;
    }
    api("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(function (data) {
      var job = data.job || null;
      if (job) selectedJobId = job.id;
      renderJobs(data.jobs || []);
    }).catch(function (err) {
      alert(err.message);
    });
  }

  function renderJobs(jobs) {
    lastJobs = jobs;
    if (selectedJobId && !jobs.some(function (job) { return job.id === selectedJobId; })) {
      selectedJobId = "";
    }
    if (!selectedJobId && jobs.length) selectedJobId = jobs[0].id;

    el.jobsList.innerHTML = "";
    el.jobState.textContent = jobs.some(function (job) { return job.status === "running" || job.status === "queued"; }) ? "Running" : "Idle";
    jobs.slice(0, 12).forEach(function (job) {
      el.jobsList.appendChild(jobRow(job));
    });

    var selected = jobs.find(function (job) { return job.id === selectedJobId; });
    if (selected) showJobLog(selected);
    else {
      el.jobPreview.textContent = "";
      el.jobLog.textContent = "";
    }
    icons();
  }

  function jobRow(job) {
    var item = document.createElement("div");
    item.className = "job-item " + job.status + (job.id === selectedJobId ? " active" : "");

    var select = document.createElement("button");
    select.className = "job-select";
    select.type = "button";
    select.innerHTML =
      '<span class="job-name">' + escapeHtml(job.name || job.action) + '</span>' +
      '<strong>' + escapeHtml(job.status) + '</strong>';
    select.addEventListener("click", function () {
      selectedJobId = job.id;
      renderJobs(lastJobs);
    });
    item.appendChild(select);

    var tools = document.createElement("div");
    tools.className = "job-tools";
    if (canOpenJob(job)) {
      tools.appendChild(jobTool("play", "Open output", function () {
        postJobAction(job.id, "open");
      }));
    }
    if (job.status === "running" || job.status === "queued") {
      tools.appendChild(jobTool("square", "Stop job", function () {
        postJobAction(job.id, "stop");
      }));
    }
    item.appendChild(tools);
    return item;
  }

  function jobTool(icon, title, action) {
    var btn = document.createElement("button");
    btn.className = "icon-only";
    btn.type = "button";
    btn.title = title;
    btn.innerHTML = '<i data-lucide="' + icon + '"></i>';
    btn.addEventListener("click", function (event) {
      event.stopPropagation();
      action();
    });
    return btn;
  }

  function canOpenJob(job) {
    if (job.action === "render_scene" || job.action === "render_deck") return true;
    return job.action === "build" && !job.noRender;
  }

  function postJobAction(jobId, action) {
    api("/api/jobs/" + encodeURIComponent(jobId) + "/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }).then(function (data) {
      renderJobs(data.jobs || []);
    }).catch(function (err) {
      alert(err.message);
    });
  }

  function clearJobs() {
    api("/api/jobs/clear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }).then(function (data) {
      renderJobs(data.jobs || []);
    }).catch(function (err) {
      alert(err.message);
    });
  }

  function showJobLog(job) {
    el.jobPreview.textContent = (job.name || job.action) + " - " + job.status;
    el.jobLog.innerHTML = logToHtml(job.logs || []);
    el.jobLog.scrollTop = el.jobLog.scrollHeight;
  }

  function logToHtml(lines) {
    return lines.map(function (line) {
      return '<span class="' + logLineClass(line) + '">' + ansiToHtml(line) + '</span>';
    }).join("\n");
  }

  function logLineClass(line) {
    var text = String(line || "");
    if (text.includes("\x1b[")) return "";
    var lower = text.toLowerCase();
    if (text.startsWith("$ ")) return "log-command";
    if (
      lower.includes("traceback") ||
      lower.includes("error") ||
      lower.includes("failed") ||
      lower.includes("exception") ||
      lower.includes("runtimewarning") ||
      lower.includes("valueerror")
    ) return "log-error";
    if (lower.includes("warning") || lower.includes("warn") || lower.includes("stopping")) {
      return "log-warning";
    }
    if (
      lower.includes("rendered ") ||
      lower.includes("built ") ||
      lower.includes("opened ") ||
      lower === "success" ||
      lower.startsWith("ok")
    ) return "log-success";
    return "";
  }

  function ansiToHtml(text) {
    text = stripAnsiLinks(String(text || ""));
    var style = { bold: false, dim: false, color: "" };
    var open = false;
    var html = "";
    var lastIndex = 0;
    var re = /\x1b\[([0-9;]*)m/g;
    var match;

    function closeSpan() {
      if (open) {
        html += "</span>";
        open = false;
      }
    }

    function openSpan() {
      var classes = [];
      var attrs = [];
      if (style.bold) classes.push("ansi-bold");
      if (style.dim) classes.push("ansi-dim");
      if (style.color) attrs.push("color:" + style.color);
      if (!classes.length && !attrs.length) return;
      html += '<span class="' + classes.join(" ") + '" style="' + attrs.join(";") + '">';
      open = true;
    }

    while ((match = re.exec(text)) !== null) {
      html += escapeHtml(stripNonSgrAnsi(text.slice(lastIndex, match.index)));
      closeSpan();
      applyAnsiCodes(match[1], style);
      openSpan();
      lastIndex = re.lastIndex;
    }
    html += escapeHtml(stripNonSgrAnsi(text.slice(lastIndex)));
    closeSpan();
    return html;
  }

  function stripAnsiLinks(text) {
    return text.replace(/\x1b\][^\x07]*(?:\x07|\x1b\\)/g, "");
  }

  function stripNonSgrAnsi(text) {
    return text
      .replace(/\x1b\[[0-?]*[ -/]*[@-l-n-z]/g, "")
      .replace(/\x1b[()][A-Za-z0-9]/g, "");
  }

  function applyAnsiCodes(raw, style) {
    var codes = raw ? raw.split(";").map(function (part) { return Number(part || 0); }) : [0];
    for (var index = 0; index < codes.length; index += 1) {
      var code = codes[index];
      if (code === 0) {
        style.bold = false;
        style.dim = false;
        style.color = "";
      } else if (code === 1) {
        style.bold = true;
      } else if (code === 2) {
        style.dim = true;
      } else if (code === 22) {
        style.bold = false;
        style.dim = false;
      } else if (code === 39) {
        style.color = "";
      } else if (code === 38 && codes[index + 1] === 5 && Number.isFinite(codes[index + 2])) {
        style.color = ansi256ToHex(codes[index + 2]);
        index += 2;
      } else if (
        code === 38 &&
        codes[index + 1] === 2 &&
        Number.isFinite(codes[index + 2]) &&
        Number.isFinite(codes[index + 3]) &&
        Number.isFinite(codes[index + 4])
      ) {
        style.color = rgbToHex(codes[index + 2], codes[index + 3], codes[index + 4]);
        index += 4;
      } else if (ANSI_COLORS[code]) {
        style.color = ANSI_COLORS[code];
      }
    }
  }

  function ansi256ToHex(code) {
    if (code < 16) {
      var base = [
        "#000000", "#800000", "#008000", "#808000", "#000080", "#800080", "#008080", "#c0c0c0",
        "#808080", "#ff0000", "#00ff00", "#ffff00", "#0000ff", "#ff00ff", "#00ffff", "#ffffff",
      ];
      return base[Math.max(0, Math.min(15, code))];
    }
    if (code >= 16 && code <= 231) {
      var n = code - 16;
      var r = Math.floor(n / 36);
      var g = Math.floor((n % 36) / 6);
      var b = n % 6;
      var scale = [0, 95, 135, 175, 215, 255];
      return rgbToHex(scale[r], scale[g], scale[b]);
    }
    var gray = 8 + (Math.max(232, Math.min(255, code)) - 232) * 10;
    return rgbToHex(gray, gray, gray);
  }

  function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(function (value) {
      var clamped = Math.max(0, Math.min(255, Number(value) || 0));
      return clamped.toString(16).padStart(2, "0");
    }).join("");
  }

  function connectEvents() {
    var events = new EventSource("/api/events");
    events.addEventListener("jobs", function (event) {
      try {
        var data = JSON.parse(event.data);
        renderJobs(data.jobs || []);
      } catch (_) {}
    });
    events.onerror = function () {
      window.setTimeout(function () {
        refreshJobs();
      }, 1200);
    };
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch];
    });
  }

  el.search.addEventListener("input", renderDeckList);
  el.refresh.addEventListener("click", load);
  el.save.addEventListener("click", function () { saveEntrypoints(currentEntrypoints()); });
  el.saveDefaults.addEventListener("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
    saveDefaults();
  });
  document.querySelectorAll("[data-cache]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      cache = btn.dataset.cache;
      syncCacheButtons();
      saveSettings();
    });
  });
  el.quality.addEventListener("change", saveSettings);
  el.slideTheme.addEventListener("change", saveSettings);
  el.openAfter.addEventListener("change", saveSettings);
  el.renderSelected.addEventListener("click", function () { startJob("render_scene"); });
  el.renderDeck.addEventListener("click", function () { startJob("render_deck"); });
  el.buildSelected.addEventListener("click", function () { startJob("build"); });
  el.buildNoRender.addEventListener("click", function () { startJob("build", { noRender: true }); });
  el.clearJobs.addEventListener("click", clearJobs);

  load();
  connectEvents();
})();
