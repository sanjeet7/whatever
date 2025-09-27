# Dynamic Agent Platform Frontend

A lightweight dashboard that interacts with the FastAPI backend to create templates, register tools, deploy agents, and exercise the self-improvement flow.

## Getting Started

1. Start the backend server (see `../backend/README.md`).
2. Serve the static frontend files. Any static server works; for example:

```bash
cd frontend
python -m http.server 5173
```

3. Open <http://localhost:5173> in your browser.

The frontend assumes the backend is available at `http://localhost:8000`. To point to a different host, open the browser console and run:

```js
localStorage.setItem('dap-api-base', 'http://your-host:port');
location.reload();
```

## Features

- Template creation with instant list updates.
- Tool registry management.
- Agent deployment picker tied to available templates.
- Request routing console with live JSON responses.
- One-click self-improvement trigger showing generated metadata.

## Development Notes

The UI uses vanilla JavaScript and modern CSS so no build tooling is required. Adjust `styles.css` and `app.js` as needed for custom workflows.
