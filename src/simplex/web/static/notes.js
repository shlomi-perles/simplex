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
})();
