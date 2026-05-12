# Laptop Setup — Claude Code + rent_roll_app

First-time setup guide for working on `rent_roll_app/` from a laptop. Assumes
you already work on the project from your desktop (the OneDrive-synced
`C:\One Drive Business\OneDrive - (na)\office\rent_roll_app\`). This doc gets
you to a working dev environment on the laptop in ~20-30 minutes.

**Decision up front:** the recommended setup uses **GitHub** for code sync
between machines, not OneDrive. OneDrive is used only for files that aren't in
git (the `Sample Files/` broker fixtures). See [ONEDRIVE-WORKFLOW.md](ONEDRIVE-WORKFLOW.md)
for the rationale.

---

## What you'll have when this is done

```
laptop:
  C:\code\rent_roll_app\          ← fresh git clone (NOT in OneDrive)
    .venv\                        ← Python venv (laptop-local)
    Sample Files\                 ← symlink into OneDrive (synced from desktop)
    ...

  C:\One Drive Business\...\office\rent-roll-fixtures\
    Sample Files\                 ← actual broker XLSX files (gitignored)
```

The git repo is outside OneDrive on the laptop. The fixtures live inside
OneDrive and are referenced via a symlink. This gives you:

- Fast, reliable git ops (no OneDrive race conditions)
- Cross-machine sync of broker files (which aren't in git)
- Cross-machine sync of code via GitHub push/pull

---

## Step 1 — Prerequisites (install once)

### 1a. Python (matching your desktop's version)

On the desktop, find the version:
```powershell
python --version
```

On the laptop, install the same major.minor version from
<https://www.python.org/downloads/>. Check **"Add Python to PATH"** during install.

Verify:
```powershell
python --version
pip --version
```

### 1b. Git for Windows

<https://git-scm.com/download/win>. Default options are fine. Verify:
```powershell
git --version
```

### 1c. GitHub authentication

Either configure git credentials or install the GitHub CLI:

**Option A — GitHub CLI** (recommended, simpler):
```powershell
winget install GitHub.cli
gh auth login
# Follow prompts: GitHub.com -> HTTPS -> Login with web browser
```

**Option B — Manual git credentials**: configure `git config --global` with
your name, email, and a personal access token via Windows Credential Manager.

Verify:
```powershell
gh auth status
# OR
git ls-remote https://github.com/ErikJ-Stack/rent-roll-normalizer.git
```

### 1d. Claude Code

Install from <https://claude.com/claude-code>. On Windows:
```powershell
# Native Windows install (recommended)
irm https://claude.ai/install.ps1 | iex
```

After install, restart your shell. Verify:
```powershell
claude --version
```

First time you run `claude` in any directory, it'll prompt for sign-in. Use
the same Anthropic account as your desktop so you keep your usage/billing
unified.

### 1e. OneDrive Business sign-in

Sign in to OneDrive Business with the same account as your desktop. **Wait for
the initial sync to complete** before proceeding — could be several minutes
depending on tenant size. The OneDrive tray icon shows "Up to date" when done.

After sync, you should see on the laptop:
```
C:\Users\<you>\OneDrive - (na)\office\rent_roll_app\    (or your tenant's equivalent path)
```

The path may differ from the desktop's `C:\One Drive Business\OneDrive - (na)`
because OneDrive defaults to `C:\Users\<user>\OneDrive - <Tenant>` unless
manually relocated. That's fine — we won't be working out of this folder
anyway.

---

## Step 2 — Clone the repo (fresh, outside OneDrive)

```powershell
mkdir C:\code
cd C:\code
git clone https://github.com/ErikJ-Stack/rent-roll-normalizer.git rent_roll_app
cd rent_roll_app
```

Verify:
```powershell
git status                   # clean, on main
git log --oneline -5         # latest commits visible
git remote -v                # origin = https://github.com/ErikJ-Stack/rent-roll-normalizer.git
```

---

## Step 3 — Python venv + dependencies

```powershell
cd C:\code\rent_roll_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks the activation script with an execution-policy error:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# answer Y; this is per-user, not system-wide
```

Verify the parser imports cleanly:
```powershell
python -c "from normalizer import normalize_rent_roll; print('ok')"
```

---

## Step 4 — Sample Files (broker fixtures, not in git)

These XLSX files are gitignored because they contain real property financials.
They sync via OneDrive instead.

### 4a. Find them on the laptop

On the laptop, after OneDrive finishes syncing, look at the OneDrive copy of
the repo:
```
C:\Users\<you>\OneDrive - (na)\office\rent_roll_app\Sample Files\
```

You should see (~5 files):
```
2026-03 Homestead Village Pensacola Financial Summary.xlsx
2026-04-24 Homestead Village Rent Roll v2.xlsx
Briar Glen T12 P&L Statement_2025.12.xlsx
Homestead - March 2026 T12.xlsx
Salem Road T-12 1.31.26.xlsx
```

If they're not there yet, OneDrive is still syncing — wait, then re-check.

### 4b. Link Sample Files into the laptop's clone

Option A — symlink (recommended; stays live as new fixtures sync):
```powershell
# Run as Administrator (one-time)
cd C:\code\rent_roll_app
$source = "C:\Users\$env:USERNAME\OneDrive - (na)\office\rent_roll_app\Sample Files"
New-Item -ItemType SymbolicLink -Path "Sample Files" -Target $source
```

Option B — copy once (simpler, but stales when new fixtures are added on desktop):
```powershell
cd C:\code\rent_roll_app
Copy-Item -Recurse "C:\Users\$env:USERNAME\OneDrive - (na)\office\rent_roll_app\Sample Files" .
```

Verify:
```powershell
ls "Sample Files"            # should list the 5 XLSX files
```

### 4c. Test the verify harness

```powershell
.\.venv\Scripts\Activate.ps1
python tools\verify_t12_v020.py
```

Should exit 0 with all four fixtures passing.

---

## Step 5 — Claude Code on the project

```powershell
cd C:\code\rent_roll_app
claude
```

On first launch in the project directory:

1. Claude Code prompts to allow the directory. Approve.
2. It reads `CLAUDE.md` automatically (the project's onboarding doc — already
   in the repo, syncs via git).
3. It then has access to `SPEC-RR.md`, `SPEC-T12.md`, `CHANGELOG-RR.md`,
   `CHANGELOG-T12.md`, and `journal.md` for context.

Try a quick smoke test:
```
> Read CLAUDE.md and confirm the current Track 1 / Track 2 versions match
> what's in app.py.
```

If it correctly reports `RR v1.16.x` and `T12 v0.2.1` (or whatever's current),
you're good.

### Claude Code settings (sync between machines)

User-level Claude Code settings live in `%USERPROFILE%\.claude\settings.json`.
These don't sync via the repo — each machine has its own. If you want them in
sync, you can either:

- Sign in with the same Anthropic account on both machines (sync of usage,
  not settings)
- Manually copy `~\.claude\settings.json` between machines (one-time, or via
  OneDrive in `~\OneDrive\...\claude-settings.json` with a symlink)

Project-level overrides (`.claude/settings.json` in the repo root) **do** sync
via git. Use these for project-specific permissions and hooks.

---

## Step 6 — First-day workflow

Now that everything is set up, here's the daily flow:

### Start of session
```powershell
cd C:\code\rent_roll_app
git pull                              # get any work from the desktop
.\.venv\Scripts\Activate.ps1
claude                                # if you want Claude Code in the loop
```

(No OneDrive sync check needed — the git repo is outside OneDrive on the laptop.)

### Working
```powershell
# edit files, run tests, etc.
streamlit run app.py                  # if you want to test the UI locally
python tools\verify_t12_v020.py       # if you touched T12 parsing
```

### End of session
```powershell
git status
git add <files>
git commit -m "..."
git push                              # push to GitHub immediately
```

### Switching back to desktop later

On the desktop:
```powershell
cd "C:\One Drive Business\OneDrive - (na)\office\rent_roll_app"
.\tools\check_onedrive_sync.ps1       # confirm OneDrive caught up first
git pull                              # pulls down your laptop's commits
```

---

## Common issues

### "OneDrive on the laptop doesn't see `Sample Files/`"

Initial sync hasn't finished. Check the OneDrive tray icon — wait for "Up to
date". If it's been hours and still incomplete, right-click the `rent_roll_app`
folder in File Explorer → **Always keep on this device** to force a full
download.

### "The symlink for Sample Files works on desktop but breaks on laptop (or vice versa)"

Symlinks point at absolute paths. If the OneDrive folder path differs between
machines (likely — desktop is at `C:\One Drive Business\...`, laptop is at
`C:\Users\<you>\OneDrive - (na)\...`), the symlink is machine-specific.

Solution: create the symlink fresh on each machine with that machine's actual
OneDrive path. The symlink itself isn't synced (it's gitignored by default
inside `Sample Files/`).

### "git pull says 'Your branch is behind' but I just pulled"

Your laptop and desktop made commits to the same branch independently. Resolve
the merge:
```powershell
git pull --rebase                     # if your local commits should land on top
# or
git pull                              # default merge commit
```

To avoid this: always `git push` immediately after committing, on both
machines.

### "Claude Code says I'm not authenticated"

Re-run `claude login` from the project directory. Sign in with the same
Anthropic account you use on the desktop.

### "I want to edit a fixture file on the laptop"

The `Sample Files/` directory is shared via OneDrive. Any edit propagates to
the desktop automatically. If you're worried about a half-saved file syncing
mid-edit:

1. Copy the file out of `Sample Files/` to `C:\temp\<copy>.xlsx`.
2. Edit there.
3. When done, copy back over the original.
4. Wait for OneDrive to sync (watch the tray icon).

For broker XLSX files specifically, treat them as read-only. If you need to
make a derivative (e.g., a cleaned version), save it elsewhere and don't sync
it back to `Sample Files/`.

---

## What's different from the desktop setup

| Aspect | Desktop | Laptop |
| --- | --- | --- |
| Repo location | Inside OneDrive (`C:\One Drive Business\...`) | Outside OneDrive (`C:\code\rent_roll_app\`) |
| OneDrive sync needed before work | **Yes** — run `tools\check_onedrive_sync.ps1` | No — only matters for `Sample Files/` |
| `Sample Files/` source | Lives directly in the repo dir (synced by OneDrive) | Symlinked from OneDrive into the clone |
| Risk profile for git ops | OneDrive can race git mid-sync (mitigated by tracker) | No OneDrive interaction; standard git workflow |
| Daily ritual | `check_onedrive_sync.ps1` → `git pull` → work → `git push` | `git pull` → work → `git push` |

The laptop is the "safer" setup. If git operations ever feel flaky on the
desktop, consider replicating the laptop pattern there too — move the repo to
`C:\code\rent_roll_app\` and keep only `Sample Files/` in OneDrive.

---

## Quick-reference card

Pin this somewhere:

```
# Start of session
cd C:\code\rent_roll_app
git pull
.\.venv\Scripts\Activate.ps1

# Run Streamlit locally
streamlit run app.py

# Run verification
python tools\verify_t12_v020.py

# Run Claude Code
claude

# End of session
git status
git add <files>
git commit -m "..."
git push
```
