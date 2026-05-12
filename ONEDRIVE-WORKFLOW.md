# OneDrive + git Workflow

The `rent_roll_app/` repo lives inside OneDrive Business at
`C:\One Drive Business\OneDrive - (na)\office\rent_roll_app\`. This doc explains
how to work safely with git inside an actively-syncing OneDrive folder.

**TL;DR — Daily start-of-session ritual:**

```powershell
cd "C:\One Drive Business\OneDrive - (na)\office\rent_roll_app"
.\tools\check_onedrive_sync.ps1
git pull
```

If the sync check exits with `OK -- safe to work`, you're cleared to edit. If it
exits `WAIT`, re-run with `-Wait` to block until OneDrive catches up.

---

## Why this exists

OneDrive's sync engine doesn't understand git's atomicity. A `git commit` writes
to multiple files inside `.git/` in a specific order; if OneDrive syncs a partial
state mid-operation (or replicates an out-of-order write from another machine),
the repo can wedge. Worst case: `loose object corrupt` errors that require
re-cloning to recover.

The mitigations in this doc reduce that risk to near-zero without requiring you
to pause OneDrive (which you can't).

---

## The sync tracker

[`tools/check_onedrive_sync.ps1`](tools/check_onedrive_sync.ps1) reads three signals:

| Signal | Why it matters |
| --- | --- |
| **OneDrive.exe is running** | If OneDrive is dead, nothing is syncing — but you also can't tell whether the latest remote changes are local yet. Restart it before working. |
| **No sync-lock artifacts** (`*.tmp`, `~$*`, `.partial`, `.~lock.*`) anywhere in the repo | OneDrive writes these during active sync. If they're present, a sync is in flight — wait for it to finish before any git operation. |
| **No cloud-only files** (offline / recall-on-open / recall-on-data-access attributes) | A file with these attributes is a placeholder, not actual content. `git` reading one will fail with cryptic errors. Caused by OneDrive's "Files On-Demand" feature freeing up disk space. Fix: right-click the folder → **Always keep on this device**. |

### Usage

**Quick check** (returns immediately, exit 0 if safe):
```powershell
.\tools\check_onedrive_sync.ps1
```

**Wait mode** (polls every 5s, blocks until safe or timeout):
```powershell
.\tools\check_onedrive_sync.ps1 -Wait
```

**Verbose** (full file lists in the report):
```powershell
.\tools\check_onedrive_sync.ps1 -VerboseLists
```

**Wrap your workflow:**
```powershell
.\tools\check_onedrive_sync.ps1 -Wait
if ($LASTEXITCODE -eq 0) {
    git pull
    # ... your work ...
} else {
    Write-Host "OneDrive sync failed. Aborting." -ForegroundColor Red
}
```

### Exit codes

- `0` — safe to work
- `1` — OneDrive is still syncing or has cloud-only files; wait or fix
- `2` — repo path not found

### What it doesn't catch

The tracker tells you the **local** state is clean. It can't tell you whether
the **remote** OneDrive copy has changes you haven't pulled yet. For that, run
`git fetch && git status` after the sync check — git is the source of truth for
"is there work I don't have yet?"

---

## "I can't pause OneDrive" workarounds

Pausing OneDrive is the textbook answer for safe git operations. If your tenant
has pause disabled (group policy, enterprise lockdown), use these instead.

### Workaround 1 — Run-and-verify (default for most ops)

For routine git operations (`commit`, `push`, `pull`, single-file edits), just:

1. Run the sync tracker first.
2. Do the git operation.
3. Run the sync tracker again to confirm the operation's file writes have
   propagated cleanly to OneDrive.

This is sufficient for **99% of daily git work**. The risk window is small.

### Workaround 2 — Shutdown OneDrive (poor-man's pause)

If "Pause" is greyed out, the underlying `OneDrive.exe /shutdown` command often
still works. Run from any shell:

```powershell
# Stop sync entirely
& "$env:LOCALAPPDATA\Microsoft\OneDrive\OneDrive.exe" /shutdown

# ... do your destructive git op here (rebase, reset --hard, gc, etc.) ...

# Restart sync
& "$env:LOCALAPPDATA\Microsoft\OneDrive\OneDrive.exe"
```

OneDrive will re-scan and catch up on restart. If group policy auto-restarts
the process within seconds, this won't help — skip to workaround 3.

### Workaround 3 — Do destructive ops outside OneDrive

For high-risk operations (`git rebase`, `git reset --hard`, `git gc`, big
merges, anything that rewrites history or repacks objects), don't do them in
the OneDrive copy at all. Clone fresh to a non-OneDrive location:

```bash
# One-time setup of a "scratch" clone outside OneDrive
mkdir C:\code
cd C:\code
git clone https://github.com/ErikJ-Stack/rent-roll-normalizer.git rr-scratch
cd rr-scratch
```

Then for any destructive op:

```bash
cd C:\code\rr-scratch
git fetch origin
git checkout <branch>
# ... rebase / reset / whatever ...
git push origin <branch> --force-with-lease     # if needed
```

Then in the OneDrive copy, sync via GitHub:
```bash
cd "C:\One Drive Business\OneDrive - (na)\office\rent_roll_app"
.\tools\check_onedrive_sync.ps1
git fetch origin
git reset --hard origin/<branch>                 # only if you actually want this
```

GitHub is the source of truth. OneDrive becomes a passive cache.

### Workaround 4 — `git push` aggressively

After every meaningful commit, push immediately. If the local OneDrive copy
ever corrupts, you've lost at most one commit's worth of work (recoverable from
git's reflog or from your editor's autosave). The longer commits sit
locally-only, the more pain a corrupted repo causes.

```bash
git commit -m "..." && git push
```

Yes, every time.

---

## Recovery procedures

### "I see weird `~$<filename>` files in `git status`"

These are OneDrive's transient lock files. Wait 30 seconds, run the sync
tracker, then re-check `git status`. They should disappear on their own.

If they persist for more than ~2 minutes:
1. The file they're locking might be open in another app (Excel, Word). Close it.
2. OneDrive may be wedged. Restart it: `OneDrive.exe /shutdown` then `OneDrive.exe`.

### "git says `loose object corrupt` or `unable to open object pack`"

OneDrive corrupted a `.git/objects/...` file mid-sync. Recovery options:

**Option A — re-clone fresh** (safest, ~5 min):
```bash
# Stash any uncommitted work (write the diff to a file outside the corrupt repo)
cd "C:\One Drive Business\OneDrive - (na)\office\rent_roll_app"
git diff > C:\temp\uncommitted-work.patch

# Move the corrupted copy aside, clone fresh
cd ..
mv rent_roll_app rent_roll_app.broken
git clone https://github.com/ErikJ-Stack/rent-roll-normalizer.git rent_roll_app
cd rent_roll_app
git apply C:\temp\uncommitted-work.patch          # if you stashed something
```

**Option B — `git fsck` and selective repair** (only if you're comfortable with git internals):
```bash
git fsck --full
# Find the bad object, try to fetch it from origin
git fetch origin
git fsck --full       # retry
```

If `fsck` still fails after a fetch, fall back to Option A.

### "git push fails: refusing to update ref"

Often a sign that the local refs in `.git/refs/` got synced inconsistently.

```bash
git fetch origin
git push origin <branch> --force-with-lease
```

`--force-with-lease` (not `--force`) is safe — it refuses to overwrite if
origin has changes you haven't seen.

### "I edited the same file on both machines"

OneDrive will produce a conflict file: `<filename>-<MachineName>.<ext>`. Git
won't see it as a conflict (it's just an extra file). Workflow:

1. Run the sync tracker.
2. `git status` shows both the conflict file and your changes.
3. Manually merge the changes into one version (use diff tooling).
4. Delete the conflict file.
5. `git add . && git commit -m "..." && git push`.

The way to avoid this entirely: always `git pull` at the start of a session and
`git push` at the end. Don't rely on OneDrive to merge two simultaneous edits.

---

## Things that are safe and unsafe

### Safe in the OneDrive copy

- Reading files (parsing, running Streamlit, running tests)
- Single-file edits (one file per few minutes)
- Committing changes one at a time
- Pulling small numbers of new commits (`git pull` with fast-forward)
- Pushing
- Branch creation and checkout (small ref updates)

### Risky in the OneDrive copy

These can produce corruption mid-sync. Use the workarounds:

- `git rebase` (especially interactive)
- `git reset --hard`
- `git gc` / `git repack`
- Large merges that touch many files
- Switching between branches with many divergent files
- Cloning into the OneDrive folder (do it elsewhere then move)

### Never in the OneDrive copy

- `git filter-branch` or `git filter-repo` (massive history rewrites)
- Restoring from a backup or arbitrary snapshot

---

## When in doubt

The fail-safe answer is always: **re-clone from GitHub to a non-OneDrive
location and copy your uncommitted work over manually**. Takes 5 minutes, has
no failure modes. GitHub is the source of truth — the OneDrive copy is just
sync convenience.
