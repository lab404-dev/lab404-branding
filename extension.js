'use strict';

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
