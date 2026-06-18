# static/

Browser assets for `simplex manager`.

## Public surface

- `index.html` -- manager shell and controls.
- `app.css` -- compact responsive layout, badges, job drawer, and ANSI log
  styling.
- `app.js` -- deck selection, entrypoint reorder/remove/add-back, defaults
  editing, render/build requests, job polling, persisted controls, and log
  rendering.

## Don't

- Don't add a frontend build step. These files are packaged directly.
- Don't duplicate deck or Manim defaults in JavaScript; use `/api/state`.
- Don't persist job state in the browser. The server owns the running jobs.
