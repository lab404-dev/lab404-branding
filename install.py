#!/usr/bin/env python3
"""
LAB404 Branding — VS Code Extension Installer
Automatically builds and installs the lab404-branding extension.
"""

import os
import sys
import shutil
import subprocess
import platform
import json

# ── Paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(SCRIPT_DIR, "media", "avatar.png")
MEDIA_DIR  = os.path.join(SCRIPT_DIR, "media")

PACKAGE_JSON = os.path.join(SCRIPT_DIR, "package.json")

# ── Terminal colours ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
DIM    = "\033[2m"
BOLD   = "\033[1m"


def ok(msg):  print(f"  {GREEN}✓{RESET}  {msg}")
def err(msg): print(f"  {RED}✗{RESET}  {msg}"); sys.exit(1)
def info(msg):print(f"  {DIM}·{RESET}  {msg}")
def warn(msg):print(f"  {YELLOW}!{RESET}  {msg}")


# ── Checks ─────────────────────────────────────────────────────────────────────

def check_platform():
    if platform.system() != "Linux":
        err("This installer targets Linux. Detected: " + platform.system())
    ok("Linux detected")


def check_python():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        err(f"Python 3.6+ required. Found: {sys.version}")
    ok(f"Python {version.major}.{version.minor}.{version.micro}")


def require_cmd(name, install_hint=""):
    path = shutil.which(name)
    if not path:
        msg = f"'{name}' not found in PATH."
        if install_hint:
            msg += f"\n       {install_hint}"
        err(msg)
    return path


def check_vscode():
    path = shutil.which("code")
    if not path:
        print()
        print(f"  {RED}✗{RESET}  VS Code CLI not found.")
        print()
        print("     Make sure 'code' is available in your PATH.")
        print("     On Fedora/Nobara, VS Code CLI is usually added automatically.")
        print("     Try opening a new terminal or adding the VS Code bin directory to PATH:")
        print()
        print("       export PATH=\"$PATH:/usr/share/code/bin\"")
        print()
        sys.exit(1)
    ok(f"VS Code CLI: {path}")
    return path


def check_node():
    require_cmd(
        "node",
        "Install Node.js: https://nodejs.org  or  dnf install nodejs"
    )
    ok("node found")


def check_npm():
    require_cmd(
        "npm",
        "Install npm: dnf install npm  or install via Node.js"
    )
    ok("npm found")


def check_logo():
    if not os.path.isfile(LOGO_PATH):
        print()
        print(f"  {RED}✗{RESET}  LAB404 logo not found.")
        print()
        print("     Please put your logo here:")
        print()
        print(f"       media/avatar.png")
        print()
        sys.exit(1)
    ok("Logo detected: media/avatar.png")


# ── File generation ─────────────────────────────────────────────────────────────

EXTENSION_JS = r"""'use strict';

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

let homePanel = null;
let statusBarItem = null;

function activate(context) {
    const openHomeCommand = vscode.commands.registerCommand('lab404-branding.openHome', () => {
        openHomePanel(context);
    });

    context.subscriptions.push(openHomeCommand);

    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 0);
    statusBarItem.text = 'LAB404-DEV';
    statusBarItem.tooltip = 'LAB404: Open Home';
    statusBarItem.command = 'lab404-branding.openHome';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    const config = vscode.workspace.getConfiguration('lab404-branding');
    const openOnStartup = config.get('openOnStartup', true);
    if (openOnStartup) {
        openHomePanel(context);
    }
}

function openHomePanel(context) {
    if (homePanel) {
        homePanel.reveal(vscode.ViewColumn.One);
        return;
    }

    homePanel = vscode.window.createWebviewPanel(
        'lab404Home',
        'LAB404-DEV',
        vscode.ViewColumn.One,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.file(path.join(context.extensionPath, 'media'))
            ]
        }
    );

    homePanel.webview.html = getWebviewContent(homePanel.webview, context);

    homePanel.webview.onDidReceiveMessage(
        async (message) => {
            switch (message.command) {
                case 'openFolder':
                    await vscode.commands.executeCommand('workbench.action.files.openFolder');
                    break;
                case 'openGitHub':
                    await vscode.env.openExternal(
                        vscode.Uri.parse('https://github.com/lab404-dev')
                    );
                    break;
                case 'openRecentProject':
                    if (message.uri) {
                        const uri = vscode.Uri.file(message.uri);
                        await vscode.commands.executeCommand('vscode.openFolder', uri, false);
                    }
                    break;
            }
        },
        undefined,
        context.subscriptions
    );

    homePanel.onDidDispose(() => {
        homePanel = null;
    }, null, context.subscriptions);
}

function getWebviewContent(webview, context) {
    const mediaPath = path.join(context.extensionPath, 'media', 'avatar.png');
    let logoUri = '';

    if (fs.existsSync(mediaPath)) {
        logoUri = webview.asWebviewUri(vscode.Uri.file(mediaPath)).toString();
    }

    const recentWorkspaces = context.globalState.get('recentWorkspaces', []);
    const recentItems = recentWorkspaces.slice(0, 5).map(ws => {
        const label = require('path').basename(ws);
        return `<button class="recent-item" onclick="openRecent('${ws.replace(/\\/g, '\\\\\\\\').replace(/'/g, "\\'")}')">
                    <span class="recent-icon">⬡</span><span>${label}</span>
                </button>`;
    }).join('\n');

    const recentSection = recentItems || '<p class="empty-state">No recent projects</p>';
    const logoHtml = logoUri
        ? `<img src="${logoUri}" alt="LAB404" class="logo" />`
        : `<div class="logo-placeholder">LAB404</div>`;

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta http-equiv="Content-Security-Policy"
      content="default-src 'none'; img-src ${webview.cspSource} data:; style-src 'unsafe-inline'; script-src 'unsafe-inline';" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>LAB404-DEV</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:      #0d0d0d;
    --surface: #111111;
    --border:  #1e1e1e;
    --accent:  #4a9eff;
    --text:    #c9c9c9;
    --muted:   #555555;
    --heading: #e8e8e8;
    --radius:  4px;
    --mono:    'SF Mono','Fira Code','Cascadia Code',monospace;
    --sans:    -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  }
  html, body { background: var(--bg); color: var(--text); font-family: var(--sans); height: 100%; overflow-x: hidden; }
  .page { max-width: 680px; margin: 0 auto; padding: 80px 32px 120px; display: flex; flex-direction: column; align-items: center; }
  .logo { width: 72px; height: 72px; object-fit: contain; border-radius: 50%; filter: brightness(0.95); margin-bottom: 28px; }
  .logo-placeholder { width: 72px; height: 72px; border: 1px solid var(--border); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: var(--mono); font-size: 11px; color: var(--muted); letter-spacing: 0.1em; margin-bottom: 28px; }
  .org-name { font-family: var(--mono); font-size: 20px; font-weight: 600; letter-spacing: 0.25em; color: var(--heading); text-transform: uppercase; margin-bottom: 10px; }
  .tagline { font-family: var(--mono); font-size: 10px; letter-spacing: 0.3em; color: var(--muted); text-transform: uppercase; margin-bottom: 56px; }
  .divider { width: 100%; height: 1px; background: var(--border); margin-bottom: 48px; }
  .section { width: 100%; margin-bottom: 44px; }
  .section-label { font-family: var(--mono); font-size: 9px; letter-spacing: 0.35em; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }
  .actions { display: flex; gap: 10px; flex-wrap: wrap; }
  .btn { background: var(--surface); border: 1px solid var(--border); color: var(--text); font-family: var(--mono); font-size: 12px; letter-spacing: 0.05em; padding: 10px 22px; border-radius: var(--radius); cursor: pointer; transition: border-color 0.15s, color 0.15s; outline: none; user-select: none; }
  .btn:hover { border-color: var(--accent); color: var(--heading); }
  .btn:active { opacity: 0.75; }
  .btn.primary { border-color: #2a2a2a; }
  .recent-item { display: flex; align-items: center; gap: 10px; background: none; border: none; color: var(--text); font-family: var(--sans); font-size: 13px; cursor: pointer; padding: 6px 0; width: 100%; text-align: left; transition: color 0.15s; outline: none; }
  .recent-item:hover { color: var(--heading); }
  .recent-icon { color: var(--muted); font-size: 11px; flex-shrink: 0; }
  .empty-state { font-size: 12px; color: var(--muted); font-family: var(--mono); }
  .footer { margin-top: 48px; font-family: var(--mono); font-size: 10px; letter-spacing: 0.2em; color: #2a2a2a; text-transform: lowercase; }
</style>
</head>
<body>
<div class="page">
  ${logoHtml}
  <div class="org-name">LAB404-DEV</div>
  <div class="tagline">Open Source &nbsp;·&nbsp; Security &nbsp;·&nbsp; Development</div>
  <div class="divider"></div>
  <div class="section">
    <div class="section-label">Workspace</div>
    <div class="actions">
      <button class="btn primary" onclick="openFolder()">Open Project</button>
      <button class="btn" onclick="openGitHub()">GitHub</button>
    </div>
  </div>
  <div class="section">
    <div class="section-label">Recent Projects</div>
    ${recentSection}
  </div>
  <div class="footer">lab404-dev</div>
</div>
<script>
  const vscode = acquireVsCodeApi();
  function openFolder() { vscode.postMessage({ command: 'openFolder' }); }
  function openGitHub() { vscode.postMessage({ command: 'openGitHub' }); }
  function openRecent(uri) { vscode.postMessage({ command: 'openRecentProject', uri }); }
</script>
</body>
</html>`;
}

function deactivate() {
    if (homePanel) homePanel.dispose();
    if (statusBarItem) statusBarItem.dispose();
}

module.exports = { activate, deactivate };
"""

PACKAGE_JSON = {
    "name": "lab404-branding",
    "displayName": "LAB404 Branding",
    "description": "Custom VS Code branding for LAB404-DEV — dark, minimal, cyber developer environment.",
    "version": "1.0.0",
    "publisher": "lab404-dev",
    "license": "MIT",
    "engines": {"vscode": "^1.75.0"},
    "categories": ["Other"],
    "icon": "media/avatar.png",
    "activationEvents": ["onStartupFinished"],
    "main": "./extension.js",
    "contributes": {
        "commands": [
            {
                "command": "lab404-branding.openHome",
                "title": "LAB404: Open Home",
                "category": "LAB404"
            }
        ],
        "configuration": {
            "title": "LAB404 Branding",
            "properties": {
                "lab404-branding.openOnStartup": {
                    "type": "boolean",
                    "default": True,
                    "description": "Open LAB404 home page on VS Code startup."
                }
            }
        }
    },
    "keywords": ["lab404", "branding", "dark", "minimal", "cyber"],
    "repository": {"type": "git", "url": "https://github.com/lab404-dev"}
}

LAUNCH_JSON = {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Extension",
            "type": "extensionHost",
            "request": "launch",
            "args": ["--extensionDevelopmentPath=${workspaceFolder}"],
            "outFiles": ["${workspaceFolder}/**/*.js"],
            "preLaunchTask": "${defaultBuildTask}"
        }
    ]
}

README_MD = """# LAB404 Branding

Custom VS Code branding extension for **LAB404-DEV**.

## Installation

```bash
python3 install.py
```

## Features

- LAB404 home page (opens on startup)
- Status bar brand mark
- `LAB404: Open Home` command

## Development

Open in VS Code, press **F5** to launch Extension Development Host.

## License

MIT — LAB404-DEV
"""


# ── Write helpers ───────────────────────────────────────────────────────────────

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ── Build ───────────────────────────────────────────────────────────────────────

def run(cmd, cwd=None, capture=False):
    result = subprocess.run(
        cmd,
        cwd=cwd or SCRIPT_DIR,
        capture_output=capture,
        text=True
    )
    if result.returncode != 0:
        if capture:
            print(result.stderr or result.stdout)
        err(f"Command failed: {' '.join(cmd)}")
    return result


def ensure_vsce():
    if shutil.which("vsce"):
        return "vsce"
    if shutil.which("npx"):
        result = subprocess.run(
            ["npx", "--yes", "@vscode/vsce", "--version"],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return None  # will use npx
    warn("vsce not found globally; attempting: npm install -g @vscode/vsce")
    run(["npm", "install", "-g", "@vscode/vsce"])
    if not shutil.which("vsce"):
        err("vsce still not found after install. Add npm global bin to PATH.")
    return "vsce"


def build_vsix():
    vsce_bin = ensure_vsce()

    if vsce_bin:
        cmd = [vsce_bin, "package", "--out", "lab404-branding.vsix"]
    else:
        cmd = ["npx", "@vscode/vsce", "package", "--out", "lab404-branding.vsix"]

    result = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr or result.stdout)
        err("vsce package failed.")
    ok("Extension built: lab404-branding.vsix")


def install_vsix(code_bin):
    vsix_path = os.path.join(SCRIPT_DIR, "lab404-branding.vsix")
    if not os.path.isfile(vsix_path):
        err("VSIX not found after build step.")

    result = subprocess.run(
        [code_bin, "--install-extension", vsix_path, "--force"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout)
        err("Failed to install extension.")
    ok("Extension installed")


def verify_install(code_bin):
    result = subprocess.run(
        [code_bin, "--list-extensions"],
        capture_output=True, text=True
    )
    installed = result.stdout.lower()
    if "lab404-branding" in installed or "lab404-dev.lab404-branding" in installed:
        ok("Verified: lab404-dev.lab404-branding is active")
        return True
    warn("Extension installed but not yet listed (may need VS Code restart).")
    return False


# ── Summary ─────────────────────────────────────────────────────────────────────

def print_summary(logo_ok, built, installed):
    def check(cond): return f"{GREEN}✓{RESET}" if cond else f"{YELLOW}~{RESET}"
    print()
    print(f"  {BOLD}╭────────────────────────────────────╮{RESET}")
    print(f"  {BOLD}│        LAB404-BRANDING             │{RESET}")
    print(f"  {BOLD}│                                    │{RESET}")
    print(f"  {BOLD}│  {check(built)} Extension built                 {BOLD}│{RESET}")
    print(f"  {BOLD}│  {check(installed)} Extension installed             {BOLD}│{RESET}")
    print(f"  {BOLD}│  {check(logo_ok)} Logo detected                   {BOLD}│{RESET}")
    print(f"  {BOLD}│                                    │{RESET}")
    print(f"  {BOLD}│  Restart VS Code if necessary.     │{RESET}")
    print(f"  {BOLD}╰────────────────────────────────────╯{RESET}")
    print()


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    print()
    print(f"  {BOLD}LAB404 Branding — Installer{RESET}")
    print(f"  {DIM}{'─' * 36}{RESET}")
    print()

    check_platform()
    check_python()
    code_bin = check_vscode()
    check_node()
    check_npm()
    check_logo()

    print()
    info("Writing extension files...")

    ext_js_path  = os.path.join(SCRIPT_DIR, "extension.js")
    pkg_json     = os.path.join(SCRIPT_DIR, "package.json")
    launch_json  = os.path.join(SCRIPT_DIR, ".vscode", "launch.json")
    readme       = os.path.join(SCRIPT_DIR, "README.md")
    media_dir    = os.path.join(SCRIPT_DIR, "media")

    write_file(ext_js_path, EXTENSION_JS)
    write_json(pkg_json, PACKAGE_JSON)
    write_json(launch_json, LAUNCH_JSON)
    write_file(readme, README_MD)
    os.makedirs(media_dir, exist_ok=True)

    ok("Files written")

    print()
    info("Building VSIX...")
    build_vsix()

    print()
    info("Installing extension...")
    install_vsix(code_bin)

    print()
    info("Verifying installation...")
    installed = verify_install(code_bin)

    print_summary(logo_ok=True, built=True, installed=installed)


if __name__ == "__main__":
    main()
