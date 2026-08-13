# Claude Usage Monitor for Windows

A polished, high-craft Windows system-tray application that monitors your **Claude Code** usage limits (5-hour and 7-day windows) in real time.

Designed with an **editorial monochrome technical visual language**, avoiding AI dashboard cliches like rainbow circular gauges, heavy gradients, excessive rounded cards, or generic SaaS templates.

---

## Features

- **System Tray Native**: Lives cleanly in the Windows system tray with a dynamic monochrome status icon (Green, Orange, Red, Grey).
- **Dual Window Monitoring**: Real-time tracking of both 5-hour and weekly utilization limits and relative reset countdowns.
- **Secure Windows Credential Integration**: Automatically reads Claude Code credentials from Windows Credential Manager (`Claude Code-credentials`), environment variables (`CLAUDE_OAUTH_TOKEN`), or encrypted keyring storage. Never logs secrets.
- **Background Polling**: Polling loop runs quietly every 15 minutes without blocking the UI.
- **Monochrome Editorial Dashboard**: Built with lightweight native `pywebview` rendering pixel-perfect HTML/CSS with smooth transitions.
- **Usage History & Analytics**: SQLite database tracking historical utilization (30-day retention) with interactive SVG line charts and velocity analytics (%/hr).
- **Windows Startup**: Optional seamless startup integration via Windows registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- **Standalone Binary**: Easily packageable into a single windowless `.exe` via PyInstaller.

---

## Visual Design Philosophy

Inspired by black-and-white editorial typography and minimal technical interfaces:

- **Palette**: Dark Mode (near-black `#0a0a0a`, charcoal surfaces, subtle grey borders) & Light Mode (off-white `#f7f7f7`, crisp typography).
- **Restrained Semantics**: Status colors (SAFE, WARNING, CRITICAL, OFFLINE) are kept minimal and restrained.
- **Typography as Hierarchy**: Bold numeric callouts (`42%`, `67%`) over cards or rounded rectangles.

---

## Architecture Overview

```
claude_usage_monitor/
├── app.py                 # Application entry point & process coordinator
├── config.py              # Configuration constants & AppData paths
├── models/
│   └── usage.py           # Data models, status levels & utilization normalization
├── services/
│   ├── credentials.py     # Secure token retrieval (Win32 Credential Manager / keyring / env)
│   ├── claude_api.py      # Anthropic API client (isolated endpoint call & error handling)
│   ├── storage.py         # SQLite database manager (30-day history & retention)
│   ├── analytics.py       # Velocity rate, trend, & peak usage calculations
│   ├── monitor.py         # Background polling worker thread
│   ├── startup.py         # Windows startup registry manager
│   └── notifications.py   # Windows toast notification dispatcher
├── ui/
│   ├── theme.py           # Design tokens (Dark & Light monochrome)
│   ├── icons.py           # Dynamic Pillow tray icon renderer
│   ├── tray.py            # pystray system tray controller & context menu
│   ├── dashboard.py       # pywebview window manager & JS-Python IPC bridge
│   └── assets/            # Editorial HTML, CSS & JS frontend
│       ├── index.html
│       ├── style.css
│       └── app.js
├── tests/                 # Unit test suite (pytest)
├── build.py               # PyInstaller packaging script
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### Prerequisites

- Windows 10 / 11
- Python 3.11+

### 1. Environment Setup

```powershell
# Clone or navigate to the project directory
cd C:\Users\naren\.gemini\antigravity-ide\scratch\claude_usage_monitor

# Install dependencies using uv or pip
uv pip install -r requirements.txt
# OR
pip install -r requirements.txt
```

---

## Credential Setup

The application automatically checks the following sources in order:

1. Custom token saved in Windows Credential Manager under `Claude Usage Monitor`.
2. Environment variables: `CLAUDE_OAUTH_TOKEN` or `CLAUDE_CODE_OAUTH_TOKEN`.
3. Windows Credential Manager target `Claude Code-credentials` (created by Claude Code CLI).
4. Local configuration files (`~/.claude.json`).

*Note: You can also manually input an OAuth token override in the Settings tab of the Dashboard.*

---

## Running Locally

To run the application directly in development mode:

```powershell
python app.py
```

The application will launch directly into the system tray. Right-click the tray icon to view quick status, refresh data, toggle startup, or open the full Dashboard window.

---

## Running Tests

Run the full unit test suite using `pytest`:

```powershell
python -m pytest tests/
```

All API requests are mocked in unit tests — no live Claude token is required to test.

---

## Building the Standalone `.exe`

To compile the application into a standalone Windows executable (`Claude Usage Monitor.exe`):

```powershell
python build.py
```

The compiled binary will be placed in `dist/Claude Usage Monitor.exe`.

- Built with `--noconsole` (no command prompt window appears).
- Embedded high-res `.ico` application icon.
- Self-contained web assets.

---

## API Endpoint Note

> [!IMPORTANT]
> The Anthropic usage endpoint (`https://api.anthropic.com/api/oauth/usage`) is an internal/OAuth API endpoint used by Claude Code. All API calls are isolated inside `services/claude_api.py` so that endpoint or header changes can be updated in a single file without modifying the rest of the application.

---

## Privacy & Security

- **Local First**: All data (usage history, SQLite DB, preferences) is stored locally on your machine in `%APPDATA%\ClaudeUsageMonitor`.
- **Zero Telemetry**: No tracking, analytics, or external requests leave your machine except the direct Anthropic usage API query.
- **Redacted Logging**: Log files automatically redact OAuth tokens and authorization headers.

---

## License

MIT License. Developed with craft for Claude Code users on Windows.
