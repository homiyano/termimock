# Termimock

Termimock is a terminal API mock server with a TUI. Define mock REST endpoints from your terminal while the HTTP server is already running, then point your frontend at it immediately.

Most mock tools make you switch to a GUI, export config, or restart a process. Termimock keeps the control panel and the mock server together in one terminal session.

## Features

- Live local HTTP server and terminal UI in the same process
- Add, edit, duplicate, delete, enable, and disable mock endpoints
- Match by HTTP method and path
- Custom status code, content type, response body, and headers
- Request log visible inside the TUI
- Save and load endpoint definitions as JSON
- Headless mode for CI, demos, and scripted frontend work
- Zero runtime dependencies

## Install

```bash
python3 -m pip install -e .
```

## Run the TUI

```bash
termimock
```

By default the server listens on `http://127.0.0.1:8080`.

```bash
termimock --host 127.0.0.1 --port 9000 --file examples/sample-routes.json
```

## Run Without the TUI

```bash
termimock --headless --file examples/sample-routes.json
```

Then test it:

```bash
curl http://127.0.0.1:8080/api/user
```

## TUI Shortcuts

| Key | Action |
| --- | --- |
| `a` | Add endpoint |
| `e` | Edit selected endpoint |
| `d` | Delete selected endpoint |
| `c` | Clone selected endpoint |
| `space` | Enable or disable selected endpoint |
| `s` | Save routes |
| `r` | Reload routes from disk |
| `j` / `k` or arrows | Move selection |
| `q` | Quit |

## Route File Format

```json
{
  "routes": [
    {
      "method": "GET",
      "path": "/api/user",
      "status": 200,
      "content_type": "application/json",
      "headers": {
        "X-Mock": "termimock"
      },
      "body": "{\"id\":1,\"name\":\"Ada\"}",
      "enabled": true
    }
  ]
}
```

## Project Status

This is an early, hackable version meant to prove the idea cleanly. Good next features are latency simulation, path parameters, request body matching, response presets, import from OpenAPI, and a richer route editor.

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
