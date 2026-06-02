/* Simplex parent-side viewer glue.
 *
 *   - Wires carousel arrows + keyboard nav on the home page.
 *   - Drives the deck media player, sidebar, controls, and slide refs from
 *     one parent-owned state store.
 */

(function () {
  "use strict";

  function normalizeThemeName(theme) {
    return theme === "light" ? "light" : "dark";
  }

  function currentDocumentTheme() {
    return normalizeThemeName(document.documentElement.dataset.theme || "dark");
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
        attrs: {
          "stroke-width": 1.9,
          "aria-hidden": "true",
        },
      });
      document.querySelectorAll(".icon-fallback").forEach(function (fallback) {
        var parent = fallback.parentElement;
        if (parent && parent.querySelector("svg[data-lucide]")) {
          fallback.classList.add("is-hidden");
        }
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
      try { return localStorage.getItem("simplex-theme"); }
      catch (_) { return null; }
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
        button.setAttribute(
          "aria-label",
          theme === "dark" ? "Switch to light theme" : "Switch to dark theme"
        );
        button.setAttribute(
          "title",
          theme === "dark" ? "Switch to light theme" : "Switch to dark theme"
        );
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
        var preview = img.dataset.previewLoaded === "true"
          ? themedAsset(img, "preview-gif", currentTheme)
          : "";
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
      images.forEach(function (img) {
        loadPreview(img, themedAsset(img, "preview-gif", theme));
      });
    }

    function schedule() {
      if ("requestIdleCallback" in window) {
        window.requestIdleCallback(load, { timeout: 1800 });
      } else {
        window.setTimeout(load, 500);
      }
    }

    if (document.readyState === "complete") schedule();
    else window.addEventListener("load", schedule, { once: true });
    window.addEventListener("simplex.theme", function (e) {
      var theme = e.detail && e.detail.theme ? e.detail.theme : currentDocumentTheme();
      images.forEach(function (img) {
        if (img.dataset.previewLoaded === "true") {
          loadPreview(img, themedAsset(img, "preview-gif", theme));
        }
      });
    });
  }

  // ------------------------------------------------------------------
  // Carousel (home page).
  // ------------------------------------------------------------------
  function initCarousels() {
    document.querySelectorAll(".carousel-section").forEach(function (section) {
      var track = section.querySelector(".carousel-track");
      if (!track) return;
      var prev = section.querySelector('.carousel-arrow[data-dir="prev"]');
      var next = section.querySelector('.carousel-arrow[data-dir="next"]');
      function step(delta) {
        track.scrollBy({ left: delta, behavior: "smooth" });
      }
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
      // Initial state -- after layout.
      requestAnimationFrame(syncArrows);
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
      function open() {
        panel.hidden = false;
        toggle.setAttribute("aria-expanded", "true");
      }
      function isOpen() {
        return !panel.hidden;
      }

      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (isOpen()) close();
        else open();
      });
      panel.addEventListener("click", function () { close(); });
      document.addEventListener("click", function (e) {
        if (menu.contains(e.target)) return;
        close();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") close();
      });
    });
  }

  // ------------------------------------------------------------------
  // Deck page: media player + sidebar + controls + slide-refs.
  // ------------------------------------------------------------------
  function initDeck() {
    var deck = document.querySelector("[data-deck-slug]");
    if (!deck) return;

    var frame = deck.querySelector(".deck-viewer-frame");
    var stage = deck.querySelector("[data-player-stage]");
    var manifestEl = deck.querySelector("[data-player-manifest]");
    var preview = deck.querySelector("[data-player-preview]");
    var freeze = deck.querySelector("[data-player-freeze]");
    var empty = deck.querySelector("[data-player-empty]");
    var videos = Array.prototype.slice.call(deck.querySelectorAll("[data-player-video]"));
    var counter = deck.querySelector("[data-counter]");
    var playBtn = deck.querySelector('[data-control="toggle-play"]');
    var slideButtons = deck.querySelectorAll("[data-slide-target]");
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
    var slides = Array.isArray(manifest.slides) ? manifest.slides : [];
    var timeline = [];
    var total = parseInt(deck.dataset.slideCount || manifest.slideCount || "0", 10) ||
      slides.length ||
      slideButtons.length;
    var slideThemeMode = deck.dataset.slideThemeMode || manifest.mode || "filter";
    var availableSlideThemes = (deck.dataset.availableSlideThemes || "dark,light")
      .split(",")
      .filter(Boolean);
    if (Array.isArray(manifest.availableThemes) && manifest.availableThemes.length) {
      availableSlideThemes = manifest.availableThemes.slice();
    }
    slideButtons.forEach(function (btn) {
      var img = btn.querySelector(".deck-slide-thumb img");
      if (img) img.dataset.mainIndex = btn.dataset.slideTarget || "";
    });
    slides.forEach(function (slide) {
      subslidesFor(slide).forEach(function (sub) {
        timeline.push({
          mainIndex: slide.mainIndex,
          subIndex: sub.subIndex || 0,
        });
      });
    });

    var state = {
      globalTheme: chooseSlideTheme(document.documentElement.dataset.theme || deck.dataset.defaultSlideTheme || "dark"),
      currentMain: slides[0] ? slides[0].mainIndex : 1,
      currentSub: 0,
      playbackStatus: "paused",
      currentTime: 0,
      duration: 0,
      effectiveSlideTheme: "dark",
      slideThemeOverride: null,
      activeVideoIndex: 0,
      mediaKey: "",
      pendingAutoplay: false,
      pendingMain: slides[0] ? slides[0].mainIndex : 1,
      pendingSub: 0,
      pendingSeekMode: "start",
      pendingSeekTime: 0,
      renderSeq: 0,
    };
    var stopwatchState = {
      elapsedMs: 0,
      startedAt: 0,
      running: false,
      timer: 0,
    };
    var reduceMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var saveData = navigator.connection && navigator.connection.saveData;
    var clockFormatter = new Intl.DateTimeFormat(undefined, { timeStyle: "medium" });
    var hourCycle = clockFormatter.resolvedOptions().hourCycle || "";
    var durationHourDigits = hourCycle === "h11" || hourCycle === "h12" ? 1 : 2;

    function readManifest() {
      if (!manifestEl) return {};
      try { return JSON.parse(manifestEl.textContent || "{}"); }
      catch (_) { return {}; }
    }
    function normalizeTheme(theme) {
      return theme === "light" ? "light" : "dark";
    }
    function themeAvailable(theme) {
      if (theme !== "dark" && theme !== "light") return false;
      if (slideThemeMode !== "true") return true;
      return availableSlideThemes.indexOf(theme) !== -1;
    }
    function chooseSlideTheme(theme) {
      var normalized = normalizeTheme(theme);
      if (themeAvailable(normalized)) return normalized;
      if (themeAvailable(deck.dataset.defaultSlideTheme)) return normalizeTheme(deck.dataset.defaultSlideTheme);
      return themeAvailable("dark") ? "dark" : "light";
    }
    function pageTheme() {
      return normalizeTheme(document.documentElement.dataset.theme || "dark");
    }
    function finiteNumber(value) {
      return typeof value === "number" && Number.isFinite(value);
    }
    function saveThemeOverride(theme) {
      state.slideThemeOverride = chooseSlideTheme(theme);
    }
    function effectiveTheme() {
      return chooseSlideTheme(state.slideThemeOverride || state.globalTheme);
    }
    function applyThumbnailThemes() {
      deck.querySelectorAll(".deck-slide-thumb img").forEach(function (img) {
        var theme = effectiveTheme();
        var key = theme === "light" ? "thumbLight" : "thumbDark";
        var src = img.dataset[key];
        if (src && img.getAttribute("src") !== src) img.setAttribute("src", src);
      });
    }
    function applySlidesPdfTheme(theme) {
      if (!slidesPdfLink) return;
      var href = themedAsset(slidesPdfLink, "pdf", theme);
      if (href) slidesPdfLink.setAttribute("href", href);
    }
    function applySlideThemeDom(theme) {
      state.effectiveSlideTheme = chooseSlideTheme(theme);
      deck.dataset.currentSlideTheme = state.effectiveSlideTheme;
      deck.classList.toggle("is-slide-theme-light", slideThemeMode === "filter" && state.effectiveSlideTheme === "light");
      deck.classList.toggle("is-true-slide-theme-light", state.effectiveSlideTheme === "light");
      if (stage) stage.dataset.slideTheme = state.effectiveSlideTheme;
      applySlidesPdfTheme(state.effectiveSlideTheme);
      if (slideThemeSetting) {
        slideThemeSetting.dataset.slideTheme = state.effectiveSlideTheme;
        slideThemeSetting.setAttribute(
          "aria-label",
          state.effectiveSlideTheme === "dark" ? "Switch slides to light theme" : "Switch slides to dark theme"
        );
        slideThemeSetting.setAttribute(
          "title",
          state.effectiveSlideTheme === "dark" ? "Switch slides to light theme" : "Switch slides to dark theme"
        );
      }
      if (slideThemeLabel) slideThemeLabel.textContent = state.effectiveSlideTheme === "dark" ? "Dark" : "Light";
    }
    function syncThemeSetting() {
      applySlideThemeDom(effectiveTheme());
      applyThumbnailThemes();
    }
    function centerActiveCard(btn) {
      var candidates = [slideList, sidebar];
      for (var i = 0; i < candidates.length; i += 1) {
        var scroller = candidates[i];
        if (!scroller) continue;
        var canX = scroller.scrollWidth > scroller.clientWidth + 1;
        var canY = scroller.scrollHeight > scroller.clientHeight + 1;
        if (!canX && !canY) continue;
        var cardRect = btn.getBoundingClientRect();
        var scrollRect = scroller.getBoundingClientRect();
        var options = { behavior: "smooth" };
        if (canX) {
          options.left = scroller.scrollLeft + cardRect.left - scrollRect.left -
            (scrollRect.width - cardRect.width) / 2;
        }
        if (canY) {
          options.top = scroller.scrollTop + cardRect.top - scrollRect.top -
            (scrollRect.height - cardRect.height) / 2;
        }
        scroller.scrollTo(options);
        return;
      }
    }
    function renderSlideNumber() {
      if (slideNumberEl) slideNumberEl.textContent = state.currentMain + " / " + total;
    }
    function timelineIndex() {
      for (var i = 0; i < timeline.length; i += 1) {
        if (
          timeline[i].mainIndex === state.currentMain &&
          timeline[i].subIndex === state.currentSub
        ) return i;
      }
      return Math.max(0, slidePosition(state.currentMain));
    }
    function renderProgress() {
      if (!progressBar) return;
      var denom = Math.max(1, timeline.length - 1);
      var value = timeline.length <= 1 ? 0 : timelineIndex() / denom;
      progressBar.style.transform = "scaleX(" + Math.max(0, Math.min(1, value)) + ")";
    }
    function setActive(idx) {
      state.currentMain = idx;
      if (counter) counter.textContent = idx + " / " + total;
      renderSlideNumber();
      renderProgress();
      slideButtons.forEach(function (btn) {
        var t = parseInt(btn.dataset.slideTarget, 10);
        if (t === idx) {
          btn.setAttribute("aria-current", "true");
          centerActiveCard(btn);
        } else {
          btn.removeAttribute("aria-current");
        }
      });
    }
    function setPlayState(playing) {
      state.playbackStatus = playing ? "playing" : "paused";
      if (!playBtn) return;
      playBtn.dataset.state = playing ? "playing" : "paused";
      playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
      playBtn.setAttribute("title", playing ? "Pause" : "Play");
    }
    function boolAttr(name) {
      return deck.dataset[name] === "true";
    }
    function syncChromeSettings() {
      if (slideNumberEl) slideNumberEl.hidden = !(slideNumberSetting && slideNumberSetting.checked);
      if (clockEl) clockEl.hidden = !(clockSetting && clockSetting.checked);
      if (stopwatchEl) stopwatchEl.hidden = !(stopwatchSetting && stopwatchSetting.checked);
      renderSlideNumber();
      renderStopwatch();
    }
    function setStopwatchState(running) {
      if (!stopwatchToggle) return;
      stopwatchToggle.dataset.state = running ? "running" : "stopped";
      stopwatchToggle.setAttribute("aria-label", running ? "Stop stopwatch" : "Start stopwatch");
      stopwatchToggle.setAttribute("title", running ? "Stop stopwatch" : "Start stopwatch");
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
    function findSlide(mainIndex) {
      return slides.find(function (slide) {
        return slide && slide.mainIndex === mainIndex;
      }) || null;
    }
    function slidePosition(mainIndex) {
      for (var i = 0; i < slides.length; i += 1) {
        if (slides[i] && slides[i].mainIndex === mainIndex) return i;
      }
      return -1;
    }
    function currentSlide() {
      return findSlide(state.currentMain) || slides[0] || null;
    }
    function subslidesFor(slide) {
      return slide && Array.isArray(slide.subslides) && slide.subslides.length ? slide.subslides : [];
    }
    function currentSubslide() {
      var slide = currentSlide();
      var subs = subslidesFor(slide);
      return subs[state.currentSub] || subs[0] || null;
    }
    function pendingMatchesCurrent() {
      return state.pendingMain === state.currentMain && state.pendingSub === state.currentSub;
    }
    function rememberPendingSeek(mode, time, autoplay) {
      state.pendingMain = state.currentMain;
      state.pendingSub = state.currentSub;
      state.pendingSeekMode = mode || "start";
      state.pendingSeekTime = finiteNumber(time) ? Math.max(0, time) : 0;
      state.pendingAutoplay = !!autoplay;
    }
    function assetFor(sub, theme) {
      if (!sub || !sub.themes) return {};
      return sub.themes[theme] ||
        sub.themes[manifest.defaultTheme] ||
        sub.themes.dark ||
        sub.themes.light ||
        {};
    }
    function activeVideo() {
      return videos[state.activeVideoIndex] || videos[0] || null;
    }
    function videoRepresentsCurrent(video) {
      return !!video &&
        video.dataset.mainIndex === String(state.currentMain) &&
        video.dataset.subIndex === String(state.currentSub);
    }
    function targetVideo() {
      return videos[0] || activeVideo();
    }
    function waitForAny(el, names, timeoutMs) {
      return new Promise(function (resolve) {
        var done = false;
        var timer = window.setTimeout(finish, timeoutMs || 1400);
        function finish() {
          if (done) return;
          done = true;
          window.clearTimeout(timer);
          names.forEach(function (name) { el.removeEventListener(name, finish); });
          resolve();
        }
        names.forEach(function (name) { el.addEventListener(name, finish, { once: true }); });
      });
    }
    function absoluteUrl(src) {
      try { return new URL(src || "", location.href).href; }
      catch (_) { return src || ""; }
    }
    function sourceMatchesExpected(video) {
      if (!video) return false;
      var expected = video.dataset.expectedSrc || "";
      if (!expected) return true;
      return absoluteUrl(video.currentSrc || video.src) === expected;
    }
    function markMetadataReady(video) {
      if (!video || video.readyState < 1 || !sourceMatchesExpected(video)) return;
      video.dataset.metadataSeq = video.dataset.loadSeq || "";
    }
    function hasExpectedMetadata(video) {
      return !!video &&
        video.readyState >= 1 &&
        video.dataset.metadataSeq === video.dataset.loadSeq &&
        sourceMatchesExpected(video);
    }
    function waitForMetadata(video, seq) {
      if (!video) return Promise.resolve(false);
      markMetadataReady(video);
      if (hasExpectedMetadata(video)) return Promise.resolve(true);
      return waitForAny(video, ["loadedmetadata", "loadeddata"], 2500).then(function () {
        if (!videoOwnsSeq(video, seq)) return false;
        markMetadataReady(video);
        return hasExpectedMetadata(video);
      });
    }
    function waitForCanPlay(video) {
      if (!video || video.readyState >= 3) return Promise.resolve();
      return waitForAny(video, ["canplay", "canplaythrough", "loadeddata"], 1800);
    }
    function decodePreview(src, seq, revealImmediately) {
      if (!preview || !src) {
        if (preview) preview.hidden = true;
        return Promise.resolve(false);
      }
      if (preview.getAttribute("src") === src && !preview.hidden) return Promise.resolve(true);
      if (revealImmediately) {
        preview.setAttribute("src", src);
        preview.hidden = false;
      }
      var img = new Image();
      img.decoding = "async";
      img.src = src;
      var decoded = img.decode ? img.decode().catch(function () {}) : waitForAny(img, ["load", "error"], 1200);
      return decoded.then(function () {
        if (seq !== state.renderSeq) return false;
        preview.setAttribute("src", src);
        preview.hidden = false;
        return true;
      });
    }
    function showEmpty(show) {
      if (empty) empty.hidden = !show;
    }
    function captureFreeze(onlyCurrent) {
      var video = activeVideo();
      if (onlyCurrent && !videoRepresentsCurrent(video)) return false;
      if (!freeze || !video || video.readyState < 2 || !video.videoWidth || !video.videoHeight) return false;
      try {
        freeze.width = video.videoWidth;
        freeze.height = video.videoHeight;
        var ctx = freeze.getContext("2d");
        if (!ctx) return false;
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
    function hideVideos() {
      videos.forEach(function (video) {
        try { video.pause(); } catch (_) {}
        video.classList.remove("is-active");
        video.dataset.loadSeq = "";
      });
      setPlayState(false);
    }
    function deactivateStaleActiveVideos(seq) {
      videos.forEach(function (video) {
        if (!video.classList.contains("is-active")) return;
        if (videoOwnsSeq(video, seq) && videoRepresentsCurrent(video)) return;
        try { video.pause(); } catch (_) {}
        video.classList.remove("is-active");
      });
    }
    function setVideoSource(video, src, poster, seq, meta) {
      if (!video) return;
      video.dataset.loadSeq = String(seq);
      video.dataset.mainIndex = String(meta.mainIndex);
      video.dataset.subIndex = String(meta.subIndex);
      video.dataset.theme = meta.theme;
      video.dataset.mediaKey = meta.mediaKey;
      video.dataset.expectedSrc = absoluteUrl(src);
      if (poster) video.poster = poster;
      video.preload = "auto";
      video.classList.remove("is-active");
      try { video.pause(); } catch (_) {}
      video.dataset.metadataSeq = "";
      video.dataset.src = src;
      video.src = src;
      try { video.load(); } catch (_) {}
    }
    function videoOwnsSeq(video, seq) {
      return !!video && video.dataset.loadSeq === String(seq) && seq === state.renderSeq;
    }
    function seekVideo(video, sub, seekMode, seq) {
      if (!video || seekMode === "none") return Promise.resolve(true);
      return waitForMetadata(video, seq).then(function (ready) {
        if (!ready || !videoOwnsSeq(video, seq)) return false;
        var target = 0;
        if (seekMode === "end") {
          var duration = finiteNumber(video.duration) && video.duration > 0
            ? video.duration
            : Number(sub && sub.duration) || 0;
          target = Math.max(0, duration - 0.05);
        } else if (seekMode === "time") {
          var requested = Number(video.dataset.seekTime);
          var limit = finiteNumber(video.duration) && video.duration > 0
            ? video.duration
            : Number(sub && sub.duration) || 0;
          target = Math.max(0, requested || 0);
          if (limit > 0) target = Math.min(target, Math.max(0, limit - 0.05));
        }
        var ready = target > 0 ? waitForCanPlay(video) : Promise.resolve();
        return ready.then(function () {
          if (!videoOwnsSeq(video, seq)) return false;
          try { video.currentTime = target; } catch (_) {}
          if (target <= 0) return true;
          return waitForAny(video, ["seeked"], 1600).then(function () {
            if (!videoOwnsSeq(video, seq)) return false;
            if (Math.abs((video.currentTime || 0) - target) <= 0.08) return true;
            try { video.currentTime = target; } catch (_) {}
            return waitForAny(video, ["seeked"], 1200).then(function () {
              if (!videoOwnsSeq(video, seq)) return false;
              return Math.abs((video.currentTime || 0) - target) <= 0.08;
            });
          });
        });
      });
    }
    function activateVideo(video, autoplay, seq) {
      if (!videoOwnsSeq(video, seq)) return;
      videos.forEach(function (candidate, index) {
        var active = candidate === video;
        candidate.classList.toggle("is-active", active);
        if (active) {
          state.activeVideoIndex = index;
        } else {
          try { candidate.pause(); } catch (_) {}
          candidate.dataset.loadSeq = "";
        }
      });
      if (preview) preview.hidden = true;
      hideFreeze();
      showEmpty(false);
      state.duration = finiteNumber(video.duration) ? video.duration : state.duration;
      state.pendingAutoplay = !!autoplay;
      if (autoplay) {
        var p = video.play();
        if (p && typeof p.catch === "function") p.catch(function () {
          state.pendingAutoplay = false;
          setPlayState(false);
        });
        window.setTimeout(function () { setPlayState(!video.paused); }, 0);
      } else {
        try { video.pause(); } catch (_) {}
        setPlayState(false);
      }
    }
    function catchUpVideo(video, target, seq) {
      if (!video || target <= 0) return Promise.resolve(true);
      return waitForCanPlay(video).then(function () {
        if (!videoOwnsSeq(video, seq)) return false;
        return new Promise(function (resolve) {
          var done = false;
          var timeout = Math.min(Math.max(target * 1000 + 700, 900), 5000);
          var timer = window.setTimeout(function () { finish(false); }, timeout);
          function cleanup() {
            video.removeEventListener("timeupdate", check);
            video.removeEventListener("ended", check);
            window.clearTimeout(timer);
          }
          function finish(ok) {
            if (done) return;
            done = true;
            cleanup();
            resolve(ok);
          }
          function check() {
            if (!videoOwnsSeq(video, seq)) {
              finish(false);
              return;
            }
            if ((video.currentTime || 0) >= Math.max(0, target - 0.08) || video.ended) {
              finish(true);
            }
          }
          video.addEventListener("timeupdate", check);
          video.addEventListener("ended", check);
          try { video.currentTime = 0; } catch (_) {}
          var p = video.play();
          if (p && typeof p.catch === "function") p.catch(function () { finish(false); });
          check();
        });
      });
    }
    function mediaKeyFor(main, sub, theme, asset) {
      return [main, sub, theme, asset.video || "", asset.firstFrame || "", asset.lastFrame || ""].join("|");
    }
    function activeVideoSnapshot() {
      var video = activeVideo();
      if (!video || !video.classList.contains("is-active") || !videoRepresentsCurrent(video)) {
        return { video: null, time: 0, playing: false, ended: false };
      }
      var time = finiteNumber(video.currentTime) ? video.currentTime : 0;
      var duration = finiteNumber(video.duration) ? video.duration : 0;
      return {
        video: video,
        time: time,
        playing: !video.paused && !video.ended,
        ended: video.ended || (duration > 0 && time >= Math.max(0, duration - 0.05)),
      };
    }
    function renderCurrent(options) {
      options = options || {};
      var slide = currentSlide();
      var sub = currentSubslide();
      if (!slide || !sub) return;
      var theme = effectiveTheme();
      var asset = assetFor(sub, theme);
      var seq = state.renderSeq + 1;
      var isThemeSwap = options.reason === "theme";
      var prior = activeVideoSnapshot();
      var usePendingSeek = isThemeSwap && !prior.video && pendingMatchesCurrent() && state.pendingSeekMode;
      var preserveThemeTime = isThemeSwap && prior.video && !prior.ended;
      var themeSeekMode = "start";
      var seekTime = 0;
      if (preserveThemeTime) themeSeekMode = "time";
      else if (isThemeSwap && prior.video && prior.ended) themeSeekMode = "end";
      else if (usePendingSeek) themeSeekMode = state.pendingSeekMode;
      if (preserveThemeTime) seekTime = prior.time || 0;
      else if (usePendingSeek) seekTime = state.pendingSeekTime || 0;
      var previewSrc = themeSeekMode === "time" && asset.video
        ? null
        : isThemeSwap && themeSeekMode === "end"
        ? (asset.lastFrame || asset.firstFrame || asset.thumbnail)
        : (asset.firstFrame || asset.lastFrame || asset.thumbnail);
      var autoplay = options.autoplay === true;
      if (isThemeSwap) {
        if (preserveThemeTime) autoplay = prior.playing;
        else if (themeSeekMode === "end") autoplay = false;
        else if (usePendingSeek) autoplay = !!state.pendingAutoplay;
        else autoplay = !!state.pendingAutoplay;
      }
      var key = mediaKeyFor(state.currentMain, state.currentSub, theme, asset);
      state.currentTime = 0;
      state.duration = Number(sub.duration) || 0;
      setActive(state.currentMain);
      applySlideThemeDom(theme);
      applyThumbnailThemes();
      showEmpty(false);
      if (!options.force && key === state.mediaKey && !isThemeSwap) return;
      state.renderSeq = seq;
      state.mediaKey = key;
      rememberPendingSeek(isThemeSwap ? themeSeekMode : "start", seekTime, autoplay);
      var shouldFreeze = !options.initial && isThemeSwap && themeSeekMode === "time";
      var freezeCaptured = shouldFreeze && (
        preserveThemeTime ? captureFreeze(true) : !!(freeze && !freeze.hidden)
      );
      if (shouldFreeze && !freezeCaptured) {
        previewSrc = asset.firstFrame || asset.lastFrame || asset.thumbnail;
      }
      if (isThemeSwap && !prior.video) {
        var staleActive = activeVideo();
        if (staleActive && staleActive.classList.contains("is-active")) {
          try { staleActive.pause(); } catch (_) {}
        }
      }
      var holdFreezeUntilVideo = preserveThemeTime && freezeCaptured;
      var revealPreviewImmediately = !shouldFreeze || !freezeCaptured;
      var previewReady = decodePreview(previewSrc, seq, revealPreviewImmediately);
      if (revealPreviewImmediately) deactivateStaleActiveVideos(seq);
      previewReady.then(function () {
        if (seq !== state.renderSeq) return;
        if (!holdFreezeUntilVideo) hideFreeze();
      });
      if (!asset.video) {
        previewReady.then(function () {
          if (seq !== state.renderSeq) return;
          hideVideos();
          showEmpty(!previewSrc);
        });
        preloadNearby(!!options.initial);
        return;
      }
      var video = targetVideo();
      setVideoSource(video, asset.video, previewSrc, seq, {
        mainIndex: state.currentMain,
        subIndex: state.currentSub,
        theme: theme,
        mediaKey: key,
      });
      if (themeSeekMode === "time") video.dataset.seekTime = String(seekTime || 0);
      else video.dataset.seekTime = "";
      seekVideo(video, sub, isThemeSwap ? themeSeekMode : "start", seq)
        .then(function (seekOk) {
          if (!seekOk && isThemeSwap && themeSeekMode === "time" && autoplay) {
            return catchUpVideo(video, seekTime, seq).then(function (caughtUp) {
              if (!caughtUp) setPlayState(false);
              return caughtUp;
            });
          }
          if (!seekOk && isThemeSwap && themeSeekMode !== "start") {
            if (preview && previewSrc) preview.hidden = false;
            setPlayState(false);
            return Promise.resolve(false);
          }
          return waitForCanPlay(video).then(function () { return true; });
        })
        .then(function (ready) {
          if (ready) activateVideo(video, autoplay, seq);
        });
      preloadNearby(!!options.initial);
    }
    function goTo(mainIndex, subIndex, options) {
      var slide = findSlide(mainIndex);
      if (!slide) return;
      var subs = subslidesFor(slide);
      var nextSub = Math.max(0, Math.min(subIndex || 0, Math.max(0, subs.length - 1)));
      state.currentMain = mainIndex;
      state.currentSub = nextSub;
      renderCurrent(options || { autoplay: true });
    }
    function next() {
      var slide = currentSlide();
      if (!slide) return;
      var subs = subslidesFor(slide);
      if (state.currentSub + 1 < subs.length) {
        goTo(state.currentMain, state.currentSub + 1, { autoplay: true });
        return;
      }
      var pos = slidePosition(state.currentMain);
      if (pos >= 0 && pos + 1 < slides.length) goTo(slides[pos + 1].mainIndex, 0, { autoplay: true });
    }
    function prev() {
      if (state.currentSub > 0) {
        goTo(state.currentMain, state.currentSub - 1, { autoplay: true });
        return;
      }
      var pos = slidePosition(state.currentMain);
      if (pos > 0) {
        var previous = slides[pos - 1];
        goTo(previous.mainIndex, Math.max(0, subslidesFor(previous).length - 1), { autoplay: true });
      }
    }
    function goToNextMain() {
      var pos = slidePosition(state.currentMain);
      if (pos >= 0 && pos + 1 < slides.length) goTo(slides[pos + 1].mainIndex, 0, { autoplay: true });
    }
    function goToPrevMainOrReset() {
      if (state.currentSub > 0) {
        goTo(state.currentMain, 0, { autoplay: true, force: true });
        return;
      }
      var pos = slidePosition(state.currentMain);
      if (pos > 0) goTo(slides[pos - 1].mainIndex, 0, { autoplay: true });
    }
    function restart() {
      goTo(state.currentMain, 0, { autoplay: true, force: true });
    }
    function toggleCurrentVideo() {
      var video = activeVideo();
      if (!video || !video.classList.contains("is-active")) return;
      if (video.paused) {
        if (video.ended || video.currentTime >= Math.max(0, (video.duration || 0) - 0.05)) {
          try { video.currentTime = 0; } catch (_) {}
        }
        var p = video.play();
        if (p && typeof p.catch === "function") p.catch(function () {});
      } else {
        video.pause();
      }
      window.setTimeout(function () { setPlayState(!video.paused); }, 0);
    }
    function preloadImage(src) {
      if (!src) return;
      var img = new Image();
      img.decoding = "async";
      img.src = src;
      if (img.decode) img.decode().catch(function () {});
    }
    function preloadNearby(immediate) {
      if (reduceMotion || saveData) return;
      var work = function () {
        var currentTheme = effectiveTheme();
        var alternate = currentTheme === "dark" ? "light" : "dark";
        var sub = currentSubslide();
        preloadImage(assetFor(sub, alternate).lastFrame);
        var slide = currentSlide();
        var subs = subslidesFor(slide);
        var nextSub = null;
        if (state.currentSub + 1 < subs.length) nextSub = subs[state.currentSub + 1];
        else {
          var pos = slidePosition(state.currentMain);
          nextSub = pos >= 0 && pos + 1 < slides.length ? subslidesFor(slides[pos + 1])[0] : null;
        }
        preloadImage(assetFor(nextSub, currentTheme).firstFrame);
        preloadImage(assetFor(nextSub, alternate).firstFrame);
      };
      if (immediate) work();
      else if ("requestIdleCallback" in window) window.requestIdleCallback(work, { timeout: 1500 });
      else window.setTimeout(work, 500);
    }
    function formatDuration(ms) {
      var totalSeconds = Math.floor(Math.max(0, ms) / 1000);
      var hours = Math.floor(totalSeconds / 3600);
      var minutes = Math.floor((totalSeconds % 3600) / 60);
      var seconds = totalSeconds % 60;
      return String(hours).padStart(durationHourDigits, "0") +
        ":" + String(minutes).padStart(2, "0") +
        ":" + String(seconds).padStart(2, "0");
    }
    function stopwatchElapsed() {
      if (!stopwatchState.running) return stopwatchState.elapsedMs;
      return stopwatchState.elapsedMs + performance.now() - stopwatchState.startedAt;
    }
    function renderStopwatch() {
      if (!stopwatchEl) return;
      stopwatchEl.textContent = formatDuration(stopwatchElapsed());
      stopwatchEl.classList.toggle("is-running", stopwatchState.running);
    }
    function scheduleStopwatchRender() {
      if (stopwatchState.timer) window.clearTimeout(stopwatchState.timer);
      renderStopwatch();
      if (stopwatchState.running) stopwatchState.timer = window.setTimeout(scheduleStopwatchRender, 250);
      else stopwatchState.timer = 0;
    }
    function toggleStopwatch() {
      if (stopwatchState.running) {
        stopwatchState.elapsedMs = stopwatchElapsed();
        stopwatchState.running = false;
      } else {
        stopwatchState.startedAt = performance.now();
        stopwatchState.running = true;
      }
      scheduleStopwatchRender();
      setStopwatchState(stopwatchState.running);
    }
    function resetStopwatch() {
      stopwatchState.elapsedMs = 0;
      stopwatchState.startedAt = performance.now();
      scheduleStopwatchRender();
      setStopwatchState(stopwatchState.running);
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
    function nativeFullscreen(el) {
      if (!el) return false;
      var fn = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen;
      if (!fn) return false;
      try {
        var p = fn.call(el);
        if (p && typeof p.catch === "function") p.catch(function () {});
        return true;
      } catch (_) { return false; }
    }
    function exitFullscreen() {
      var fn = document.exitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen;
      if (fn) { try { fn.call(document); } catch (_) {} }
    }
    function isFullscreen() {
      return !!(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement);
    }
    function toggleFullscreen() {
      if (isFullscreen()) { exitFullscreen(); return; }
      nativeFullscreen(fullscreenTarget());
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
        var t = parseInt(btn.dataset.slideTarget, 10);
        if (Number.isInteger(t)) goTo(t, 0, { autoplay: true });
      });
    });
    controls.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var ctl = btn.dataset.control;
        if (ctl === "next") next();
        else if (ctl === "prev") prev();
        else if (ctl === "restart") restart();
        else if (ctl === "toggle-play") toggleCurrentVideo();
        else if (ctl === "fullscreen") toggleFullscreen();
      });
    });
    tapZones.forEach(function (zone) {
      zone.addEventListener("click", function (e) {
        e.preventDefault();
        if (zone.dataset.tap === "prev") prev();
        else next();
      });
    });
    document.addEventListener("click", function (e) {
      var a = e.target && e.target.closest ? e.target.closest(".slide-ref[data-slide]") : null;
      if (!a) return;
      e.preventDefault();
      if (a.classList.contains("slide-ref-stale")) return;
      var idx = parseInt(a.dataset.slide, 10);
      if (!Number.isInteger(idx)) return;
      goTo(idx, 0, { autoplay: true });
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
        next();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        prev();
      }
    });
    if (slideThemeSetting) {
      slideThemeSetting.addEventListener("click", function () {
        var nextTheme = state.effectiveSlideTheme === "dark" ? "light" : "dark";
        saveThemeOverride(nextTheme);
        renderCurrent({ reason: "theme", force: true });
      });
    }
    if (slideNumberSetting) {
      slideNumberSetting.checked = boolAttr("defaultSlideNumber");
      slideNumberSetting.addEventListener("change", syncChromeSettings);
    }
    if (clockSetting) {
      clockSetting.checked = boolAttr("defaultClock");
      clockSetting.addEventListener("change", syncChromeSettings);
    }
    if (stopwatchSetting) {
      stopwatchSetting.checked = boolAttr("defaultStopwatch");
      stopwatchSetting.addEventListener("change", syncChromeSettings);
    }
    if (stopwatchToggle) stopwatchToggle.addEventListener("click", toggleStopwatch);
    if (stopwatchReset) stopwatchReset.addEventListener("click", resetStopwatch);
    videos.forEach(function (video) {
      video.addEventListener("loadedmetadata", function () {
        markMetadataReady(video);
      });
      video.addEventListener("loadeddata", function () {
        markMetadataReady(video);
      });
      video.addEventListener("play", function () {
        if (video === activeVideo() && videoRepresentsCurrent(video)) setPlayState(true);
      });
      video.addEventListener("pause", function () {
        if (video === activeVideo() && videoRepresentsCurrent(video)) setPlayState(false);
      });
      video.addEventListener("timeupdate", function () {
        if (video !== activeVideo() || !videoRepresentsCurrent(video)) return;
        state.currentTime = finiteNumber(video.currentTime) ? video.currentTime : 0;
        state.duration = finiteNumber(video.duration) ? video.duration : state.duration;
        rememberPendingSeek("time", state.currentTime, !video.paused && !video.ended);
      });
      video.addEventListener("ended", function () {
        if (video === activeVideo() && videoRepresentsCurrent(video)) {
          rememberPendingSeek("end", video.currentTime || state.duration || 0, false);
          setPlayState(false);
        }
      });
    });
    window.addEventListener("simplex.theme", function (e) {
      var nextTheme = chooseSlideTheme(e.detail && e.detail.theme ? e.detail.theme : pageTheme());
      state.globalTheme = nextTheme;
      applyThumbnailThemes();
      if (!state.slideThemeOverride) {
        renderCurrent({ reason: "theme", force: true });
      } else {
        syncThemeSetting();
      }
    });
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

    startClock();
    syncChromeSettings();
    setStopwatchState(false);
    setActive(state.currentMain);
    syncThemeSetting();
    window.requestAnimationFrame(function () {
      renderCurrent({ initial: true, autoplay: true, force: true });
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
