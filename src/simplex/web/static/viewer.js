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
    var controls = deck.querySelectorAll("[data-control]");
    var slideRefs = deck.querySelectorAll(".slide-ref[data-slide]");
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
          // Keep the active card in view in the sidebar.
          if (btn.scrollIntoView) {
            btn.scrollIntoView({ block: "nearest", behavior: "smooth" });
          }
        } else {
          btn.removeAttribute("aria-current");
        }
      });
    }

    function setPlayState(playing) {
      if (!playBtn) return;
      playBtn.dataset.state = playing ? "playing" : "paused";
      playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
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
      btn.addEventListener("click", function () {
        var ctl = btn.dataset.control;
        if (ctl === "next") send({ type: "simplex.next" });
        else if (ctl === "prev") send({ type: "simplex.prev" });
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initCarousels();
      initDeck();
    });
  } else {
    initCarousels();
    initDeck();
  }
})();
