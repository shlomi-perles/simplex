/* Simplex parent-side viewer glue.
 *
 *   - Wires carousel arrows + keyboard nav on the home page.
 *   - Bridges the deck iframe (RevealJS) <-> sidebar / controls / slide-refs
 *     via postMessage. The iframe template is at
 *     src/simplex/web/templates/revealjs.html.j2 and emits
 *     {type:'simplex.slide', idx, total} on every slide change.
 */

(function () {
  "use strict";

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

  function initPreviewGifs() {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var saveData = navigator.connection && navigator.connection.saveData;
    if (reduce || saveData) return;

    var images = Array.prototype.slice.call(document.querySelectorAll("img[data-preview-gif]"));
    if (!images.length) return;

    function load() {
      images.forEach(function (img) {
        var src = img.dataset.previewGif;
        if (!src || img.dataset.previewLoaded === "true") return;
        img.dataset.previewLoaded = "true";
        var gif = new Image();
        gif.decoding = "async";
        gif.onload = function () {
          img.src = src;
          img.classList.add("is-preview-gif");
        };
        gif.src = src;
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

  // ------------------------------------------------------------------
  // Deck page: iframe bridge + sidebar + controls + slide-refs.
  // ------------------------------------------------------------------
  function initDeck() {
    var deck = document.querySelector("[data-deck-slug]");
    if (!deck) return;
    var iframe = deck.querySelector("iframe.deck-iframe");
    var frame = deck.querySelector(".deck-viewer-frame");
    var counter = deck.querySelector("[data-counter]");
    var playBtn = deck.querySelector('[data-control="toggle-play"]');
    var slideButtons = deck.querySelectorAll("[data-slide-target]");
    var slideList = deck.querySelector(".deck-slide-list");
    var sidebar = deck.querySelector(".deck-sidebar");
    var controls = deck.querySelectorAll("[data-control]");
    var slideRefs = deck.querySelectorAll(".slide-ref[data-slide]");
    var settings = deck.querySelector("[data-settings]");
    var settingsToggle = deck.querySelector("[data-settings-toggle]");
    var settingsPanel = deck.querySelector("[data-settings-panel]");
    var colorSetting = deck.querySelector('[data-setting="slide-color"]');
    var slideNumberSetting = deck.querySelector('[data-setting="slide-number"]');
    var clockSetting = deck.querySelector('[data-setting="clock"]');
    var total = parseInt(deck.dataset.slideCount || "0", 10) || slideButtons.length;
    var currentIdx = 0;

    function targetOrigin() {
      if (!iframe || !iframe.src) return "*";
      try { return new URL(iframe.src, location.href).origin; }
      catch (_) { return "*"; }
    }
    function send(message) {
      if (!iframe || !iframe.contentWindow) return;
      iframe.contentWindow.postMessage(message, targetOrigin());
    }
    function syncThemeSetting() {
      send({
        type: "simplex.set-theme",
        theme: document.documentElement.dataset.theme || "dark",
      });
    }
    function sendChromeSettings() {
      window.setTimeout(function () {
        syncChromeSettings();
        syncThemeSetting();
      }, 0);
      window.setTimeout(function () {
        syncChromeSettings();
        syncThemeSetting();
      }, 250);
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
          options.left =
            scroller.scrollLeft +
            cardRect.left -
            scrollRect.left -
            (scrollRect.width - cardRect.width) / 2;
        }
        if (canY) {
          options.top =
            scroller.scrollTop +
            cardRect.top -
            scrollRect.top -
            (scrollRect.height - cardRect.height) / 2;
        }
        scroller.scrollTo(options);
        return;
      }
    }

    // ``idx`` is the 1-based main-slide number broadcast by the iframe
    // (extracted from ``data-main-index`` on the current section's main
    // ancestor). It matches ``MainSlide.index`` and ``data-slide-target``
    // on each sidebar card, so highlight + counter share one vocabulary
    // and the active card stays highlighted while the user scrubs through
    // sub-stops of the same main slide.
    function setActive(idx) {
      currentIdx = idx;
      if (counter) counter.textContent = idx + " / " + total;
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
      if (!playBtn) return;
      playBtn.dataset.state = playing ? "playing" : "paused";
      playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
      playBtn.setAttribute("title", playing ? "Pause" : "Play");
    }

    function boolAttr(name) {
      return deck.dataset[name] === "true";
    }

    function syncChromeSettings() {
      send({
        type: "simplex.set-chrome",
        slideNumber: !!(slideNumberSetting && slideNumberSetting.checked),
        clock: !!(clockSetting && clockSetting.checked),
      });
    }

    function syncColorSetting() {
      if (!colorSetting) return;
      deck.classList.toggle("is-light-preview", colorSetting.checked);
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

    window.addEventListener("message", function (e) {
      var d = e.data || {};
      if (typeof d !== "object") return;
      if (d.type === "simplex.slide") {
        if (Number.isInteger(d.total) && d.total > 0) total = d.total;
        if (Number.isInteger(d.idx)) setActive(d.idx);
      } else if (d.type === "simplex.play-state") {
        setPlayState(!!d.playing);
      }
    });

    function fullscreenTarget() {
      // Prefer the viewer-frame container so the controls stay visible
      // around the slide. Fall back to the iframe itself if the container
      // is missing (older markup) or rejected by the browser.
      return frame || iframe;
    }
    function nativeFullscreen(el) {
      if (!el) return false;
      var fn =
        el.requestFullscreen ||
        el.webkitRequestFullscreen ||
        el.mozRequestFullScreen;
      if (!fn) return false;
      try {
        var p = fn.call(el);
        if (p && typeof p.catch === "function") { p.catch(function () {}); }
        return true;
      } catch (_) { return false; }
    }
    function exitFullscreen() {
      var fn =
        document.exitFullscreen ||
        document.webkitExitFullscreen ||
        document.mozCancelFullScreen;
      if (fn) { try { fn.call(document); } catch (_) {} }
    }
    function isFullscreen() {
      return !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement
      );
    }
    function toggleFullscreen() {
      if (isFullscreen()) { exitFullscreen(); return; }
      if (nativeFullscreen(fullscreenTarget())) return;
      // Parent-side request was blocked or not available -- ask the iframe
      // to enter fullscreen on its own document (works even when the parent
      // path is gated by permission policy).
      send({ type: "simplex.fullscreen" });
    }

    slideButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var t = parseInt(btn.dataset.slideTarget, 10);
        if (!Number.isInteger(t)) return;
        send({ type: "simplex.goto", idx: t });
      });
    });

    controls.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var ctl = btn.dataset.control;
        if (ctl === "next") send({ type: "simplex.next" });
        else if (ctl === "prev") send({ type: "simplex.prev" });
        else if (ctl === "restart") send({ type: "simplex.restart" });
        else if (ctl === "toggle-play") send({ type: "simplex.toggle-play" });
        else if (ctl === "fullscreen") toggleFullscreen();
      });
    });

    slideRefs.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        if (a.classList.contains("slide-ref-stale")) return;
        var idx = parseInt(a.dataset.slide, 10);
        if (!Number.isInteger(idx)) return;
        send({ type: "simplex.goto", idx: idx });
        if (iframe && iframe.scrollIntoView) {
          iframe.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    });

    // Forward parent keyboard arrows to the iframe (when nothing else is focused).
    document.addEventListener("keydown", function (e) {
      var t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      if (e.key === "ArrowRight") { e.preventDefault(); send({ type: "simplex.next" }); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); send({ type: "simplex.prev" }); }
    });

    if (colorSetting) {
      colorSetting.checked = true;
      colorSetting.addEventListener("change", syncColorSetting);
      syncColorSetting();
    }
    if (slideNumberSetting) {
      slideNumberSetting.checked = boolAttr("defaultSlideNumber");
      slideNumberSetting.addEventListener("change", syncChromeSettings);
    }
    if (clockSetting) {
      clockSetting.checked = boolAttr("defaultClock");
      clockSetting.addEventListener("change", syncChromeSettings);
    }
    if (iframe) iframe.addEventListener("load", sendChromeSettings);
    window.addEventListener("simplex.theme", syncThemeSetting);
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initTheme();
      initIcons();
      initPreviewGifs();
      initCarousels();
      initDeck();
    });
  } else {
    initTheme();
    initIcons();
    initPreviewGifs();
    initCarousels();
    initDeck();
  }
})();
