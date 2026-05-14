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
    var counter = deck.querySelector("[data-counter]");
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
    function setActive(idx) {
      currentIdx = idx;
      if (counter) counter.textContent = (idx + 1) + " / " + total;
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

    window.addEventListener("message", function (e) {
      var d = e.data || {};
      if (typeof d !== "object" || d.type !== "simplex.slide") return;
      if (Number.isInteger(d.total) && d.total > 0) total = d.total;
      if (Number.isInteger(d.idx)) setActive(d.idx);
    });

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
        else if (ctl === "fullscreen" && iframe) {
          var fn = iframe.requestFullscreen || iframe.webkitRequestFullscreen;
          if (fn) fn.call(iframe);
        }
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
