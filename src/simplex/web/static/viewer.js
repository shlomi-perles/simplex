/* Simplex portal and timeline player. */
(function () {
  "use strict";

  function normalizeThemeName(theme) {
    return theme === "light" ? "light" : "dark";
  }

  function currentDocumentTheme() {
    return normalizeThemeName(document.documentElement.dataset.theme || "dark");
  }
  function nextFrame(fn) {
    var done = false;
    function run() {
      if (done) return;
      done = true;
      fn();
    }
    if (typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(run);
    }
    window.setTimeout(run, 50);
  }
  function monotonicNow() {
    if (window.performance && typeof window.performance.now === "function") {
      return window.performance.now();
    }
    return Date.now();
  }

  function themedAsset(el, name, theme) {
    var normalized = normalizeThemeName(theme);
    return el.getAttribute("data-" + name + "-" + normalized) ||
      el.getAttribute("data-" + name + "-default") ||
      el.getAttribute("data-" + name) ||
      "";
  }

  function initIcons() {
    if (!window.lucide || typeof window.lucide.createIcons !== "function") return;
    try {
      window.lucide.createIcons({
        icons: window.lucide.icons,
        nameAttr: "data-lucide",
        attrs: { "stroke-width": 1.9, "aria-hidden": "true" },
      });
      document.querySelectorAll(".icon-fallback").forEach(function (fallback) {
        var parent = fallback.parentElement;
        if (parent && parent.querySelector("svg[data-lucide]")) fallback.classList.add("is-hidden");
      });
    } catch (_) {
      document.querySelectorAll(".icon-fallback").forEach(function (fallback) {
        fallback.classList.remove("is-hidden");
      });
    }
  }

  function initTheme() {
    var root = document.documentElement;
    var button = document.querySelector("[data-theme-toggle]");
    var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
    function storedTheme() {
      try { return localStorage.getItem("simplex-theme"); } catch (_) { return null; }
    }
    function systemTheme() {
      return media && media.matches ? "dark" : "light";
    }
    function apply(theme, persist) {
      root.dataset.theme = theme;
      root.style.colorScheme = theme;
      if (persist) {
        try { localStorage.setItem("simplex-theme", theme); } catch (_) {}
      }
      if (button) {
        button.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
        button.setAttribute("title", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
      }
      try {
        window.dispatchEvent(new CustomEvent("simplex.theme", { detail: { theme: theme } }));
      } catch (_) {}
    }
    apply(storedTheme() || root.dataset.theme || systemTheme(), false);
    if (button) {
      button.addEventListener("click", function () {
        apply(root.dataset.theme === "dark" ? "light" : "dark", true);
      });
    }
    if (media && typeof media.addEventListener === "function") {
      media.addEventListener("change", function () {
        if (!storedTheme()) apply(systemTheme(), false);
      });
    }
  }

  function initThemedDeckCards() {
    var images = Array.prototype.slice.call(document.querySelectorAll(
      "img[data-card-thumb-default], img[data-card-thumb-dark], img[data-card-thumb-light]"
    ));
    if (!images.length) return;
    function apply(theme) {
      var currentTheme = normalizeThemeName(theme);
      images.forEach(function (img) {
        var preview = img.dataset.previewLoaded === "true" ? themedAsset(img, "preview-gif", currentTheme) : "";
        var src = preview || themedAsset(img, "card-thumb", currentTheme);
        if (src && img.getAttribute("src") !== src) img.setAttribute("src", src);
      });
    }
    apply(currentDocumentTheme());
    window.addEventListener("simplex.theme", function (e) {
      apply(e.detail && e.detail.theme ? e.detail.theme : currentDocumentTheme());
    });
  }

  function initPreviewGifs() {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var saveData = navigator.connection && navigator.connection.saveData;
    if (reduce || saveData) return;
    var images = Array.prototype.slice.call(document.querySelectorAll(
      "img[data-preview-gif], img[data-preview-gif-dark], img[data-preview-gif-light]"
    ));
    if (!images.length) return;
    function loadPreview(img, src) {
      if (!src || img.dataset.previewLoadedSrc === src) return;
      img.dataset.previewLoadingSrc = src;
      var gif = new Image();
      gif.decoding = "async";
      gif.onload = function () {
        if (img.dataset.previewLoadingSrc !== src) return;
        img.dataset.previewLoaded = "true";
        img.dataset.previewLoadedSrc = src;
        img.src = src;
        img.classList.add("is-preview-gif");
      };
      gif.src = src;
    }
    function load() {
      var theme = currentDocumentTheme();
      images.forEach(function (img) { loadPreview(img, themedAsset(img, "preview-gif", theme)); });
    }
    if ("requestIdleCallback" in window) window.requestIdleCallback(load, { timeout: 1800 });
    else window.setTimeout(load, 500);
  }

  function initCarousels() {
    document.querySelectorAll(".carousel-section").forEach(function (section) {
      var track = section.querySelector(".carousel-track");
      if (!track) return;
      var prev = section.querySelector('.carousel-arrow[data-dir="prev"]');
      var next = section.querySelector('.carousel-arrow[data-dir="next"]');
      function step(delta) { track.scrollBy({ left: delta, behavior: "smooth" }); }
      function syncArrows() {
        if (!prev || !next) return;
        var atStart = track.scrollLeft <= 4;
        var atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
        prev.hidden = atStart;
        next.hidden = atEnd;
      }
      if (prev) prev.addEventListener("click", function () { step(-track.clientWidth * 0.9); });
      if (next) next.addEventListener("click", function () { step(track.clientWidth * 0.9); });
      track.addEventListener("scroll", syncArrows, { passive: true });
      track.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight") { e.preventDefault(); step(track.clientWidth * 0.9); }
        else if (e.key === "ArrowLeft") { e.preventDefault(); step(-track.clientWidth * 0.9); }
      });
      nextFrame(syncArrows);
      window.addEventListener("resize", syncArrows);
    });
  }

  function initResourceMenus() {
    document.querySelectorAll("[data-resource-menu]").forEach(function (menu) {
      var toggle = menu.querySelector("[data-resource-toggle]");
      var panel = menu.querySelector("[data-resource-panel]");
      if (!toggle || !panel) return;
      function close() {
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
      }
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        panel.hidden = !panel.hidden;
        toggle.setAttribute("aria-expanded", panel.hidden ? "false" : "true");
      });
      panel.addEventListener("click", close);
      document.addEventListener("click", function (e) {
        if (!menu.contains(e.target)) close();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") close();
      });
    });
  }

  function initDeck() {
    var deck = document.querySelector("[data-deck-slug]");
    if (!deck) return;
    var frame = deck.querySelector(".deck-viewer-frame");
    var stage = deck.querySelector("[data-player-stage]");
    var manifestEl = deck.querySelector("[data-player-manifest]");
    var preview = deck.querySelector("[data-player-preview]");
    var freeze = deck.querySelector("[data-player-freeze]");
    var empty = deck.querySelector("[data-player-empty]");
    var video = deck.querySelector("[data-player-video]");
    var counter = deck.querySelector("[data-counter]");
    var playBtn = deck.querySelector('[data-control="toggle-play"]');
    var slideButtons = Array.prototype.slice.call(deck.querySelectorAll("[data-slide-target]"));
    var slideList = deck.querySelector(".deck-slide-list");
    var sidebar = deck.querySelector(".deck-sidebar");
    var controls = deck.querySelectorAll("[data-control]");
    var settings = deck.querySelector("[data-settings]");
    var settingsToggle = deck.querySelector("[data-settings-toggle]");
    var settingsPanel = deck.querySelector("[data-settings-panel]");
    var slideThemeSetting = deck.querySelector('[data-setting="slide-theme"]');
    var slideThemeLabel = deck.querySelector("[data-slide-theme-label]");
    var slideNumberSetting = deck.querySelector('[data-setting="slide-number"]');
    var clockSetting = deck.querySelector('[data-setting="clock"]');
    var watchModeSetting = deck.querySelector('[data-setting="watch-mode"]');
    var stopwatchSetting = deck.querySelector('[data-setting="stopwatch"]');
    var stopwatchToggle = deck.querySelector('[data-stopwatch-action="toggle"]');
    var stopwatchReset = deck.querySelector('[data-stopwatch-action="reset"]');
    var clockEl = deck.querySelector("[data-player-clock]");
    var stopwatchEl = deck.querySelector("[data-player-stopwatch]");
    var slideNumberEl = deck.querySelector("[data-player-slide-number]");
    var progressBar = deck.querySelector("[data-player-progress-bar]");
    var tapZones = deck.querySelectorAll("[data-tap]");
    var slidesPdfLink = document.querySelector("[data-slides-pdf-link]");
    var manifest = readManifest();
    var cues = Array.isArray(manifest.cues) ? manifest.cues : [];
    var themes = Array.isArray(manifest.themes) ? manifest.themes : [];
    var slideCues = cues.filter(function (cue) { return cue.kind === "slide"; });
    if (!slideCues.length) slideCues = cues.slice();
    var totalSlides = slideCues.length || parseInt(deck.dataset.slideCount || "0", 10) || 0;
    var defaultTheme = normalizeThemeName(deck.dataset.defaultSlideTheme || "dark");
    var state = {
      cueIndex: initialCueIndex(),
      globalTheme: normalizeThemeName(document.documentElement.dataset.theme || defaultTheme),
      slideThemeOverride: null,
      activeTheme: defaultTheme,
      mode: initialPlaybackMode(),
      mediaKey: "",
      loadingSeq: 0,
      seeking: false,
      pendingPlay: false,
      shaka: null,
      engine: "native",
      stopwatchElapsedMs: 0,
      stopwatchStartedAt: 0,
      stopwatchRunning: false,
      stopwatchTimer: 0,
      activeSlideOrdinal: 0,
    };
    var clockFormatter = new Intl.DateTimeFormat(undefined, { timeStyle: "medium" });

    function readManifest() {
      if (!manifestEl) return {};
      try { return JSON.parse(manifestEl.textContent || "{}"); } catch (_) { return {}; }
    }
    function finiteNumber(value) {
      return typeof value === "number" && Number.isFinite(value);
    }
    function cueAt(index) {
      return cues[Math.max(0, Math.min(index, cues.length - 1))] || null;
    }
    function themeById(theme) {
      var normalized = normalizeThemeName(theme);
      return themes.find(function (entry) { return entry && entry.id === normalized; }) ||
        themes.find(function (entry) { return entry && entry.id === defaultTheme; }) ||
        themes[0] ||
        null;
    }
    function initialCueIndex() {
      var hash = decodeURIComponent((window.location.hash || "").replace(/^#/, ""));
      if (!hash) return 0;
      var idx = cues.findIndex(function (cue) { return cue.id === hash; });
      return idx >= 0 ? idx : 0;
    }
    function initialPlaybackMode() {
      var fromData = deck.dataset.defaultPlayerMode === "watch" ? "watch" : "presentation";
      try {
        var params = new URLSearchParams(window.location.search || "");
        if (params.get("watch") === "1" || params.get("mode") === "watch") return "watch";
      } catch (_) {}
      return fromData;
    }
    function effectiveTheme() {
      return normalizeThemeName(state.slideThemeOverride || state.globalTheme || defaultTheme);
    }
    function currentCue() {
      return cueAt(state.cueIndex);
    }
    function slideOrdinalForCue(cue) {
      if (!cue) return 1;
      var current = 1;
      for (var i = 0; i < slideCues.length; i += 1) {
        if (slideCues[i].ordinal <= cue.ordinal) current = i + 1;
      }
      return current;
    }
    function cueIndexForOrdinal(ordinal) {
      var idx = cues.findIndex(function (cue) { return cue.ordinal === ordinal; });
      return idx >= 0 ? idx : 0;
    }
    function cueAtTime(time) {
      var current = 0;
      for (var i = 0; i < cues.length; i += 1) {
        if (time + 0.02 >= Number(cues[i].start || 0)) current = i;
        if (time < Number(cues[i].end || 0) - 0.02) break;
      }
      return current;
    }
    function cueTimingEpsilon() {
      return Math.max(1 / Math.max(1, Number(manifest.fps || 60)), 0.03);
    }
    function cueBoundaryGrace() {
      return Math.max(cueTimingEpsilon() * 4, 0.25);
    }
    function cueLocalProgress(cue) {
      if (!cue || !video) return 0;
      return Math.max(0, Math.min(Number(video.currentTime || 0) - Number(cue.start || 0), Math.max(0, Number(cue.end || 0) - Number(cue.start || 0))));
    }
    function targetTime(cue, localProgress) {
      if (!cue) return 0;
      var start = Number(cue.start || 0);
      var end = Number(cue.end || start);
      return Math.max(start, Math.min(end, start + (localProgress || 0)));
    }
    function isVideoPlaying() {
      return !!(video && !video.paused && !video.ended);
    }
    function requestPlay(seq) {
      if (!video) return;
      state.pendingPlay = true;
      setPlayState(true);
      [0, 80, 240, 600].forEach(function (delay, index, delays) {
        window.setTimeout(function () {
          if (seq !== state.loadingSeq || !state.pendingPlay || !video || video.ended) return;
          if (!video.paused) {
            if (index === delays.length - 1) state.pendingPlay = false;
            setPlayState(true);
            return;
          }
          var p = video.play();
          if (p && typeof p.catch === "function") {
            p.catch(function () {
              if (index === delays.length - 1) {
                state.pendingPlay = false;
                setPlayState(false);
              }
            });
          }
        }, delay);
      });
    }
    function posterFor(cue, theme) {
      if (!cue) return "";
      var poster = cue.poster || cue.thumbnail || "";
      if (poster && theme) poster = poster.replace(/posters\/[^/]+\//, "posters/" + normalizeThemeName(theme) + "/");
      return poster;
    }
    function mediaFor(themeEntry) {
      if (!themeEntry || !themeEntry.media) return { hls: "", mp4: "" };
      return { hls: themeEntry.media.hls || "", mp4: themeEntry.media.mp4 || "" };
    }
    function mediaKeyFor(themeEntry) {
      var media = mediaFor(themeEntry);
      return [themeEntry ? themeEntry.id : "", themeEntry ? themeEntry.strategy : "", media.hls, media.mp4].join("|");
    }
    function showEmpty(show, message) {
      if (!empty) return;
      empty.hidden = !show;
      if (show && message) {
        var span = empty.querySelector("span");
        if (span) span.textContent = message;
      }
    }
    function applyThumbnailThemes() {
      var theme = state.activeTheme;
      deck.querySelectorAll(".deck-slide-thumb img").forEach(function (img) {
        var src = img.getAttribute("data-thumb-" + theme) ||
          img.getAttribute("data-thumb-" + defaultTheme) ||
          img.getAttribute("data-thumb-default") ||
          img.getAttribute("data-thumb-dark") ||
          img.getAttribute("data-thumb-light");
        if (src && img.getAttribute("src") !== src) img.setAttribute("src", src);
      });
    }
    function applySlidesPdfTheme(theme) {
      if (!slidesPdfLink) return;
      var href = themedAsset(slidesPdfLink, "pdf", theme);
      if (href) slidesPdfLink.setAttribute("href", href);
    }
    function slideBackgroundFor(theme) {
      return deck.getAttribute("data-slide-background-" + normalizeThemeName(theme)) ||
        deck.getAttribute("data-slide-background-" + defaultTheme) ||
        deck.getAttribute("data-slide-background-default") ||
        "";
    }
    function applySlideBackground(theme) {
      var background = slideBackgroundFor(theme);
      if (background) deck.style.setProperty("--deck-slide-bg", background);
    }
    function applyThemeDom(themeEntry) {
      var theme = normalizeThemeName(themeEntry ? themeEntry.id : effectiveTheme());
      state.activeTheme = theme;
      deck.dataset.currentSlideTheme = theme;
      applySlideBackground(theme);
      deck.classList.toggle("is-slide-theme-light", theme === "light" && themeEntry && themeEntry.strategy === "css_filter_fallback");
      deck.classList.toggle("is-true-slide-theme-light", theme === "light" && (!themeEntry || themeEntry.strategy === "rendered"));
      if (stage) {
        stage.dataset.slideTheme = theme;
        stage.style.filter = "";
      }
      applySlidesPdfTheme(theme);
      if (slideThemeSetting) {
        slideThemeSetting.dataset.slideTheme = theme;
        slideThemeSetting.setAttribute("aria-label", theme === "dark" ? "Switch slides to light theme" : "Switch slides to dark theme");
        slideThemeSetting.setAttribute("title", theme === "dark" ? "Switch slides to light theme" : "Switch slides to dark theme");
      }
      if (slideThemeLabel) slideThemeLabel.textContent = theme === "dark" ? "Dark" : "Light";
      applyThumbnailThemes();
    }
    function centerActiveCard(btn) {
      [slideList, sidebar].some(function (scroller) {
        if (!scroller) return false;
        var canX = scroller.scrollWidth > scroller.clientWidth + 1;
        var canY = scroller.scrollHeight > scroller.clientHeight + 1;
        if (!canX && !canY) return false;
        var cardRect = btn.getBoundingClientRect();
        var scrollRect = scroller.getBoundingClientRect();
        var options = { behavior: "smooth" };
        if (canX) options.left = scroller.scrollLeft + cardRect.left - scrollRect.left - (scrollRect.width - cardRect.width) / 2;
        if (canY) options.top = scroller.scrollTop + cardRect.top - scrollRect.top - (scrollRect.height - cardRect.height) / 2;
        scroller.scrollTo(options);
        return true;
      });
    }
    function renderCounter() {
      var cue = currentCue();
      var slideOrdinal = slideOrdinalForCue(cue);
      if (counter) counter.textContent = slideOrdinal + " / " + Math.max(1, totalSlides);
      if (slideNumberEl) slideNumberEl.textContent = slideOrdinal + " / " + Math.max(1, totalSlides);
    }
    function renderProgress() {
      if (!progressBar) return;
      var denom = Math.max(1, cues.length - 1);
      var value = cues.length <= 1 ? 0 : state.cueIndex / denom;
      progressBar.style.transform = "scaleX(" + Math.max(0, Math.min(1, value)) + ")";
    }
    function setActiveCue(index, options) {
      state.cueIndex = Math.max(0, Math.min(index, cues.length - 1));
      var cue = currentCue();
      var activeSlideOrdinal = slideOrdinalForCue(cue);
      var shouldCenter = state.activeSlideOrdinal !== activeSlideOrdinal ||
        Boolean(options && options.center === true);
      state.activeSlideOrdinal = activeSlideOrdinal;
      renderCounter();
      renderProgress();
      slideButtons.forEach(function (btn) {
        var target = parseInt(btn.dataset.slideTarget, 10);
        var activeSlide = slideCues[activeSlideOrdinal - 1];
        if (cue && activeSlide && target === activeSlide.ordinal) {
          btn.setAttribute("aria-current", "true");
          if (shouldCenter) centerActiveCard(btn);
        } else {
          btn.removeAttribute("aria-current");
        }
      });
      if (!options || options.hash !== false) {
        if (cue && window.history && window.history.replaceState) {
          window.history.replaceState(null, "", "#" + encodeURIComponent(cue.id));
        }
      }
    }
    function setPlayState(playing) {
      if (!playBtn) return;
      playBtn.dataset.state = playing ? "playing" : "paused";
      playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
      playBtn.setAttribute("title", playing ? "Pause" : "Play");
    }
    function captureFreeze() {
      if (!freeze || !video || video.readyState < 2) return false;
      try {
        var rect = video.getBoundingClientRect();
        freeze.width = Math.max(1, Math.round(rect.width * (window.devicePixelRatio || 1)));
        freeze.height = Math.max(1, Math.round(rect.height * (window.devicePixelRatio || 1)));
        var ctx = freeze.getContext("2d");
        ctx.drawImage(video, 0, 0, freeze.width, freeze.height);
        freeze.hidden = false;
        return true;
      } catch (_) {
        return false;
      }
    }
    function hideFreeze() {
      if (freeze) freeze.hidden = true;
    }
    function setPreview(src) {
      if (!preview) return;
      if (src) {
        if (preview.getAttribute("src") !== src) preview.setAttribute("src", src);
        preview.hidden = false;
      } else {
        preview.hidden = true;
      }
    }
    function hidePreview() {
      if (preview) preview.hidden = true;
    }
    function seekVideoTo(time, seq) {
      if (!video || !finiteNumber(time)) return;
      var target = Math.max(0, Number(time));
      var tolerance = Math.max(1 / Math.max(1, Number(manifest.fps || 60)), 0.04);
      function apply() {
        if (seq !== state.loadingSeq || !state.seeking || !video) return;
        if (video.currentTime >= target - tolerance && video.currentTime <= target + 0.25) return;
        try {
          if (typeof video.fastSeek === "function") video.fastSeek(target);
          else video.currentTime = target;
        } catch (_) {
          try { video.currentTime = target; } catch (_) {}
        }
      }
      apply();
      [60, 160, 360, 800, 1400].forEach(function (delay) {
        window.setTimeout(apply, delay);
      });
    }
    function waitForDecodedFrame(seq, expectedTime) {
      return new Promise(function (resolve) {
        if (!video || seq !== state.loadingSeq) { resolve(false); return; }
        var done = false;
        var timer = window.setTimeout(function () { finish(false); }, 3600);
        var target = finiteNumber(expectedTime) ? Number(expectedTime) : null;
        function cleanup() {
          video.removeEventListener("seeked", onReady);
          video.removeEventListener("loadeddata", onReady);
          video.removeEventListener("canplay", onReady);
          video.removeEventListener("timeupdate", onReady);
          window.clearTimeout(timer);
        }
        function finish(ok) {
          if (done) return;
          done = true;
          cleanup();
          resolve(ok);
        }
        function onReady() {
          var reachedTarget = target === null ||
            video.currentTime >= target - Math.max(1 / Math.max(1, Number(manifest.fps || 60)), 0.04);
          if (video.readyState >= 2 && reachedTarget) finish(true);
        }
        video.addEventListener("seeked", onReady);
        video.addEventListener("loadeddata", onReady);
        video.addEventListener("canplay", onReady);
        video.addEventListener("timeupdate", onReady);
        if ("requestVideoFrameCallback" in video) {
          video.requestVideoFrameCallback(function () { onReady(); });
        }
        onReady();
      });
    }
    function pauseAtCueEnd(cue, epsilon) {
      state.pendingPlay = false;
      video.pause();
      setPlayState(false);
      var start = Number(cue.start || 0);
      var end = Number(cue.end || cue.start || 0);
      var holdTime = Math.max(start, end - epsilon);
      if (video.currentTime > holdTime + epsilon) {
        try { video.currentTime = holdTime; } catch (_) {}
      }
    }
    function loadNative(media) {
      return new Promise(function (resolve, reject) {
        var src = media.mp4 || media.hls || "";
        if (!src) { reject(new Error("No media URL available")); return; }
        if (video.getAttribute("src") !== src) {
          video.setAttribute("src", src);
          video.load();
        }
        state.engine = "native";
        resolve();
      });
    }
    function loadShaka(media, startTime) {
      if (!media.hls || !window.shaka || !window.shaka.Player) return Promise.reject(new Error("Shaka unavailable"));
      try {
        window.shaka.polyfill.installAll();
        if (!window.shaka.Player.isBrowserSupported()) return Promise.reject(new Error("Shaka unsupported"));
      } catch (err) {
        return Promise.reject(err);
      }
      var player = state.shaka;
      var created = false;
      if (!player) {
        player = new window.shaka.Player();
        state.shaka = player;
        created = true;
      }
      function attachAndLoad() {
        player.addEventListener("error", function (event) {
          var detail = event && event.detail;
          if (detail && detail.severity && window.shaka && window.shaka.util &&
              detail.severity === window.shaka.util.Error.Severity.CRITICAL) {
            showEmpty(true, "Streaming error. Use the MP4 fallback from the resources menu.");
          }
        });
        return player.load(media.hls, finiteNumber(startTime) ? Math.max(0, Number(startTime)) : undefined).then(function () {
          state.engine = "shaka";
        });
      }
      if (created && typeof player.attach === "function") {
        return player.attach(video).then(attachAndLoad);
      }
      if (typeof player.unload === "function") {
        return player.unload().then(attachAndLoad);
      }
      return attachAndLoad();
    }
    function ensureMedia(themeEntry, options) {
      options = options || {};
      var key = mediaKeyFor(themeEntry);
      if (key === state.mediaKey && video && (video.src || video.currentSrc)) return Promise.resolve(true);
      state.mediaKey = key;
      var media = mediaFor(themeEntry);
      return loadShaka(media, options.startTime)
        .catch(function () {
          if (state.shaka && typeof state.shaka.unload === "function") {
            return state.shaka.unload().catch(function () {}).then(function () {
              return loadNative(media);
            });
          }
          return loadNative(media);
        })
        .then(function () {
          video.classList.add("is-active");
          showEmpty(false);
          return true;
        })
        .catch(function () {
          showEmpty(true, "No playable timeline media is available yet.");
          if (options.poster) setPreview(options.poster);
          return false;
        });
    }
    function seekToCue(index, options) {
      options = options || {};
      var cue = cueAt(index);
      if (!cue) return Promise.resolve(false);
      var targetTheme = themeById(effectiveTheme());
      var themeChanged = normalizeThemeName(targetTheme ? targetTheme.id : defaultTheme) !== state.activeTheme ||
        mediaKeyFor(targetTheme) !== state.mediaKey;
      var time = targetTime(cue, options.localProgress || 0);
      var longSeek = video && Math.abs((video.currentTime || 0) - time) > 1.5;
      var seq = state.loadingSeq + 1;
      state.loadingSeq = seq;
      state.seeking = true;
      setActiveCue(index, { hash: options.hash });
      applyThemeDom(targetTheme);
      var poster = posterFor(cue, targetTheme ? targetTheme.id : defaultTheme);
      if (themeChanged || longSeek || options.initial) {
        var showPoster = !options.initial && !options.preserveFrame;
        if (!captureFreeze() && showPoster) setPreview(poster);
      }
      return ensureMedia(targetTheme, { poster: poster, startTime: time }).then(function (ok) {
        if (!ok || seq !== state.loadingSeq) {
          if (seq === state.loadingSeq) state.seeking = false;
          return false;
        }
        seekVideoTo(time, seq);
        return waitForDecodedFrame(seq, time).then(function () {
          if (seq !== state.loadingSeq) return false;
          state.seeking = false;
          hidePreview();
          hideFreeze();
          if (options.play) {
            requestPlay(seq);
          } else {
            state.pendingPlay = false;
            video.pause();
            setPlayState(false);
          }
          return true;
        });
      });
    }
    function syncFromPlayback() {
      if (!video || !cues.length) return;
      if (state.seeking) return;
      var time = Number(video.currentTime || 0);
      var cue = currentCue();
      if (!cue) return;
      if (state.mode === "presentation") {
        var start = Number(cue.start || 0);
        var end = Number(cue.end || cue.start || 0);
        var epsilon = cueTimingEpsilon();
        var boundaryGrace = cueBoundaryGrace();
        if (cue.kind === "loop" && time >= end - epsilon) {
          try { video.currentTime = Number(cue.start || 0); } catch (_) {}
          return;
        }
        if (time >= end - epsilon && end > start) {
          var next = cues[state.cueIndex + 1];
          if (next && next.kind === "slide") {
            setActiveCue(state.cueIndex + 1, { hash: false });
            return;
          }
          pauseAtCueEnd(cue, epsilon);
          return;
        }
        if (time < start - boundaryGrace || time > end + boundaryGrace) {
          var presentationIdx = cueAtTime(time);
          if (presentationIdx !== state.cueIndex) setActiveCue(presentationIdx, { hash: false });
        }
        return;
      }
      var idx = cueAtTime(time);
      if (idx !== state.cueIndex) setActiveCue(idx, { hash: false });
    }
    function nextCue() {
      if (state.cueIndex + 1 < cues.length) seekToCue(state.cueIndex + 1, { play: true });
    }
    function previousCue() {
      var cue = currentCue();
      var threshold = cue ? Number(cue.start || 0) + 1.25 : 0;
      if (video && video.currentTime > threshold) {
        seekToCue(state.cueIndex, { play: false, localProgress: 0 });
      } else if (state.cueIndex > 0) {
        seekToCue(state.cueIndex - 1, { play: true });
      }
    }
    function restartCue() {
      seekToCue(state.cueIndex, { play: true, localProgress: 0 });
    }
    function goToNextMain() {
      var cue = currentCue();
      var currentSlide = slideOrdinalForCue(cue);
      var next = slideCues[currentSlide];
      if (next) seekToCue(cueIndexForOrdinal(next.ordinal), { play: true });
    }
    function goToPrevMainOrReset() {
      var cue = currentCue();
      var currentSlide = slideOrdinalForCue(cue);
      if (cue && cue.kind !== "slide") {
        seekToCue(cueIndexForOrdinal(slideCues[currentSlide - 1].ordinal), { play: true });
      } else if (currentSlide > 1) {
        seekToCue(cueIndexForOrdinal(slideCues[currentSlide - 2].ordinal), { play: true });
      } else {
        restartCue();
      }
    }
    function toggleCurrentVideo() {
      if (!video || !video.currentSrc && !video.src) return;
      if (video.paused) {
        var p = video.play();
        if (p && typeof p.catch === "function") p.catch(function () {});
      } else {
        video.pause();
      }
      window.setTimeout(function () { setPlayState(!video.paused); }, 0);
    }
    function syncChromeSettings() {
      if (slideNumberEl) slideNumberEl.hidden = !(slideNumberSetting && slideNumberSetting.checked);
      if (clockEl) clockEl.hidden = !(clockSetting && clockSetting.checked);
      if (stopwatchEl) stopwatchEl.hidden = !(stopwatchSetting && stopwatchSetting.checked);
      renderCounter();
      renderStopwatch();
    }
    function closeSettings() {
      if (!settingsPanel || !settingsToggle) return;
      settingsPanel.hidden = true;
      settingsToggle.setAttribute("aria-expanded", "false");
    }
    function toggleSettings() {
      if (!settingsPanel || !settingsToggle) return;
      var open = settingsPanel.hidden;
      settingsPanel.hidden = !open;
      settingsToggle.setAttribute("aria-expanded", open ? "true" : "false");
    }
    function stopwatchElapsed() {
      if (!state.stopwatchRunning) return state.stopwatchElapsedMs;
      return state.stopwatchElapsedMs + monotonicNow() - state.stopwatchStartedAt;
    }
    function formatDuration(ms) {
      var totalSeconds = Math.floor(Math.max(0, ms) / 1000);
      var hours = Math.floor(totalSeconds / 3600);
      var minutes = Math.floor((totalSeconds % 3600) / 60);
      var seconds = totalSeconds % 60;
      return String(hours).padStart(2, "0") + ":" +
        String(minutes).padStart(2, "0") + ":" +
        String(seconds).padStart(2, "0");
    }
    function renderStopwatch() {
      if (!stopwatchEl) return;
      stopwatchEl.textContent = formatDuration(stopwatchElapsed());
      stopwatchEl.classList.toggle("is-running", state.stopwatchRunning);
    }
    function setStopwatchButton() {
      if (!stopwatchToggle) return;
      stopwatchToggle.dataset.state = state.stopwatchRunning ? "running" : "stopped";
      stopwatchToggle.setAttribute("aria-label", state.stopwatchRunning ? "Stop stopwatch" : "Start stopwatch");
      stopwatchToggle.setAttribute("title", state.stopwatchRunning ? "Stop stopwatch" : "Start stopwatch");
    }
    function scheduleStopwatchRender() {
      if (state.stopwatchTimer) window.clearTimeout(state.stopwatchTimer);
      renderStopwatch();
      if (state.stopwatchRunning) state.stopwatchTimer = window.setTimeout(scheduleStopwatchRender, 250);
      else state.stopwatchTimer = 0;
    }
    function toggleStopwatch() {
      if (state.stopwatchRunning) {
        state.stopwatchElapsedMs = stopwatchElapsed();
        state.stopwatchRunning = false;
      } else {
        state.stopwatchStartedAt = monotonicNow();
        state.stopwatchRunning = true;
      }
      setStopwatchButton();
      scheduleStopwatchRender();
    }
    function resetStopwatch() {
      state.stopwatchElapsedMs = 0;
      state.stopwatchStartedAt = monotonicNow();
      setStopwatchButton();
      scheduleStopwatchRender();
    }
    function startClock() {
      if (!clockEl) return;
      function tick() { clockEl.textContent = clockFormatter.format(new Date()); }
      tick();
      window.setInterval(tick, 1000);
    }
    function fullscreenTarget() {
      return frame || stage;
    }
    function toggleFullscreen() {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(function () {});
      } else if (fullscreenTarget() && fullscreenTarget().requestFullscreen) {
        fullscreenTarget().requestFullscreen().catch(function () {});
      }
    }
    function scrollViewerBelowNav() {
      var target = frame || stage;
      if (!target) return;
      var nav = document.querySelector(".site-nav-wrap");
      var navHeight = nav ? nav.getBoundingClientRect().height : 0;
      var y = window.scrollY + target.getBoundingClientRect().top - navHeight - 12;
      window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
    }

    slideButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var ordinal = parseInt(btn.dataset.slideTarget, 10);
        if (Number.isInteger(ordinal)) seekToCue(cueIndexForOrdinal(ordinal), { play: true });
      });
    });
    controls.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var ctl = btn.dataset.control;
        if (ctl === "next") nextCue();
        else if (ctl === "prev") previousCue();
        else if (ctl === "restart") restartCue();
        else if (ctl === "toggle-play") toggleCurrentVideo();
        else if (ctl === "fullscreen") toggleFullscreen();
      });
    });
    tapZones.forEach(function (zone) {
      zone.addEventListener("click", function (e) {
        e.preventDefault();
        if (zone.dataset.tap === "prev") previousCue();
        else nextCue();
      });
    });
    document.addEventListener("click", function (e) {
      var a = e.target && e.target.closest ? e.target.closest(".slide-ref[data-slide]") : null;
      if (!a || a.classList.contains("slide-ref-stale")) return;
      e.preventDefault();
      var ordinal = parseInt(a.dataset.slide, 10);
      if (!Number.isInteger(ordinal)) return;
      seekToCue(cueIndexForOrdinal(ordinal), { play: true });
      scrollViewerBelowNav();
    });
    document.addEventListener("keydown", function (e) {
      var t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      if (e.key === " " || e.code === "Space" || e.key === "Spacebar") {
        e.preventDefault();
        toggleCurrentVideo();
      } else if (e.ctrlKey && !e.altKey && !e.metaKey && e.key === "ArrowRight") {
        e.preventDefault();
        goToNextMain();
      } else if (e.ctrlKey && !e.altKey && !e.metaKey && e.key === "ArrowLeft") {
        e.preventDefault();
        goToPrevMainOrReset();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        nextCue();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        previousCue();
      }
    });
    if (slideThemeSetting) {
      slideThemeSetting.addEventListener("click", function () {
        var cue = currentCue();
        var local = cueLocalProgress(cue);
        var wasPlaying = isVideoPlaying();
        state.slideThemeOverride = state.activeTheme === "dark" ? "light" : "dark";
        seekToCue(state.cueIndex, { play: wasPlaying, localProgress: local, hash: false, preserveFrame: true });
      });
    }
    if (slideNumberSetting) {
      slideNumberSetting.checked = deck.dataset.defaultSlideNumber === "true";
      slideNumberSetting.addEventListener("change", syncChromeSettings);
    }
    if (clockSetting) {
      clockSetting.checked = deck.dataset.defaultClock === "true";
      clockSetting.addEventListener("change", syncChromeSettings);
    }
    if (watchModeSetting) {
      watchModeSetting.checked = state.mode === "watch";
      watchModeSetting.addEventListener("change", function () {
        state.mode = watchModeSetting.checked ? "watch" : "presentation";
        syncFromPlayback();
      });
    }
    if (stopwatchSetting) {
      stopwatchSetting.checked = deck.dataset.defaultStopwatch === "true";
      stopwatchSetting.addEventListener("change", syncChromeSettings);
    }
    if (stopwatchToggle) stopwatchToggle.addEventListener("click", toggleStopwatch);
    if (stopwatchReset) stopwatchReset.addEventListener("click", resetStopwatch);
    if (settingsToggle) {
      settingsToggle.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        toggleSettings();
      });
    }
    document.addEventListener("click", function (e) {
      if (!settings || settings.contains(e.target)) return;
      closeSettings();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeSettings();
    });
    window.addEventListener("simplex.theme", function (e) {
      state.globalTheme = normalizeThemeName(e.detail && e.detail.theme ? e.detail.theme : currentDocumentTheme());
      if (!state.slideThemeOverride) {
        var cue = currentCue();
        seekToCue(state.cueIndex, {
          play: isVideoPlaying(),
          localProgress: cueLocalProgress(cue),
          hash: false,
          preserveFrame: true,
        });
      } else {
        applyThumbnailThemes();
      }
    });
    if (video) {
      video.addEventListener("play", function () { setPlayState(true); });
      video.addEventListener("pause", function () { setPlayState(false); });
      video.addEventListener("timeupdate", syncFromPlayback);
      video.addEventListener("ended", function () {
        setPlayState(false);
        if (state.mode === "watch") syncFromPlayback();
      });
      if ("requestVideoFrameCallback" in video) {
        var frameLoop = function () {
          syncFromPlayback();
          video.requestVideoFrameCallback(frameLoop);
        };
        video.requestVideoFrameCallback(frameLoop);
      }
    }

    startClock();
    setStopwatchButton();
    syncChromeSettings();
    setActiveCue(state.cueIndex, { hash: false });
    applyThemeDom(themeById(effectiveTheme()));
    hidePreview();
    nextFrame(function () {
      seekToCue(state.cueIndex, { initial: true, play: true, hash: false });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initTheme();
      initIcons();
      initThemedDeckCards();
      initPreviewGifs();
      initCarousels();
      initResourceMenus();
      initDeck();
    });
  } else {
    initTheme();
    initIcons();
    initThemedDeckCards();
    initPreviewGifs();
    initCarousels();
    initResourceMenus();
    initDeck();
  }
})();
