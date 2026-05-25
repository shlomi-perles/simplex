/* Auto-fit display math + viewer plumbing for the notes pane.
 *
 * KaTeX renders display equations at their natural width; long lines
 * overflow the .deck-notes column and force a horizontal scroll bar.
 * We measure each `.katex-display` against its container and apply a
 * `transform: scale(...)` to shrink it just enough to fit -- so the
 * reader never has to scroll for math that's only a little too wide.
 *
 * Equations narrower than the column are untouched. Equations that
 * would have to shrink past `MIN_SCALE` keep their scroll bar (we
 * don't want to render math at unreadable sizes).
 */

(function () {
  "use strict";

  var MIN_SCALE = 0.55;

  function fitOne(host) {
    var inner = host.querySelector(".katex");
    if (!inner) return;

    // Reset state from prior runs so resize re-measures naturally.
    inner.style.removeProperty("transform");
    inner.style.removeProperty("transform-origin");
    inner.style.removeProperty("display");
    host.style.removeProperty("min-height");
    host.classList.remove("katex-fitted");

    var available = host.clientWidth;
    var natural = inner.scrollWidth;
    if (!available || !natural || natural <= available) return;

    var scale = available / natural;
    if (scale < MIN_SCALE) return; // leave scrollbar -- too wide to scale.

    inner.style.transformOrigin = "left top";
    inner.style.transform = "scale(" + scale + ")";
    inner.style.display = "block";
    // `transform` doesn't affect layout, so we reclaim the height the
    // scaled equation would have used; otherwise an empty band appears
    // below the math.
    var scaledHeight = inner.offsetHeight * scale;
    host.style.minHeight = scaledHeight + "px";
    host.classList.add("katex-fitted");
  }

  function fitAll() {
    var hosts = document.querySelectorAll(".deck-notes .katex-display");
    for (var i = 0; i < hosts.length; i++) fitOne(hosts[i]);
  }

  function initSidenotePopovers() {
    var refs = document.querySelectorAll(".sidenote-ref[for]");
    if (!refs.length) return;

    var narrow = window.matchMedia ? window.matchMedia("(max-width: 1279px)") : null;
    var popover = null;
    var activeRef = null;

    function isNarrow() {
      return !narrow || narrow.matches;
    }

    function noteFor(ref) {
      var noteId = ref.getAttribute("aria-controls");
      var note = noteId ? document.getElementById(noteId) : null;
      if (!note) {
        var input = document.getElementById(ref.getAttribute("for") || "");
        note = input && input.nextElementSibling;
      }
      if (!note || !note.classList || !note.classList.contains("sidenote")) return null;
      return note;
    }

    function ensurePopover() {
      if (popover) return popover;
      popover = document.createElement("div");
      popover.className = "sidenote-popover";
      popover.setAttribute("role", "dialog");
      popover.setAttribute("aria-modal", "true");
      popover.setAttribute("aria-hidden", "true");
      popover.innerHTML =
        '<button type="button" class="sidenote-popover-backdrop" data-sidenote-close aria-label="Close note"></button>' +
        '<div class="sidenote-popover-sheet">' +
        '<div class="sidenote-popover-header">' +
        '<span data-sidenote-title>Note</span>' +
        '<button type="button" class="sidenote-popover-close" data-sidenote-close aria-label="Close note">x</button>' +
        "</div>" +
        '<div class="sidenote-popover-content" data-sidenote-content></div>' +
        "</div>";
      document.body.appendChild(popover);
      popover.querySelectorAll("[data-sidenote-close]").forEach(function (btn) {
        btn.addEventListener("click", close);
      });
      return popover;
    }

    function close() {
      if (!popover) return;
      popover.classList.remove("is-open");
      popover.setAttribute("aria-hidden", "true");
      document.body.classList.remove("sidenote-popover-open");
      if (activeRef) {
        activeRef.setAttribute("aria-expanded", "false");
        try { activeRef.focus({ preventScroll: true }); } catch (_) { activeRef.focus(); }
      }
      activeRef = null;
    }

    function open(ref) {
      var note = noteFor(ref);
      if (!note) return;
      var sheet = ensurePopover();
      var content = sheet.querySelector("[data-sidenote-content]");
      var title = sheet.querySelector("[data-sidenote-title]");
      var closeBtn = sheet.querySelector(".sidenote-popover-close");
      if (content) content.innerHTML = note.innerHTML;
      if (title) title.textContent = "Note " + ref.textContent.trim();
      activeRef = ref;
      ref.setAttribute("aria-expanded", "true");
      sheet.classList.add("is-open");
      sheet.setAttribute("aria-hidden", "false");
      document.body.classList.add("sidenote-popover-open");
      if (content && window.renderMathInElement) {
        try {
          window.renderMathInElement(content, {
            delimiters: [
              { left: "\\[", right: "\\]", display: true },
              { left: "\\(", right: "\\)", display: false },
            ],
            throwOnError: false,
            ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
          });
        } catch (_) {}
      }
      if (closeBtn) {
        try { closeBtn.focus({ preventScroll: true }); } catch (_) { closeBtn.focus(); }
      }
    }

    document.addEventListener("click", function (e) {
      var ref = e.target && e.target.closest ? e.target.closest(".sidenote-ref[for]") : null;
      if (!ref || !isNarrow()) return;
      e.preventDefault();
      open(ref);
    });

    refs.forEach(function (ref) {
      ref.addEventListener("keydown", function (e) {
        if (!isNarrow()) return;
        if (e.key !== "Enter" && e.key !== " ") return;
        e.preventDefault();
        open(ref);
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
    if (narrow && typeof narrow.addEventListener === "function") {
      narrow.addEventListener("change", function () {
        if (!isNarrow()) close();
      });
    }
  }

  // Expose for the KaTeX onload hook in base.html to call once math is
  // typeset.
  window.simplexFitMath = fitAll;

  // Re-fit on viewport changes (debounced via rAF).
  var pending = null;
  function schedule() {
    if (pending !== null) cancelAnimationFrame(pending);
    pending = requestAnimationFrame(function () {
      pending = null;
      fitAll();
    });
  }
  window.addEventListener("resize", schedule);
  window.addEventListener("load", schedule);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidenotePopovers);
  } else {
    initSidenotePopovers();
  }
})();
