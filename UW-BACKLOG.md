# UW-BACKLOG.md — forward-looking changes for the underwriting workbook

Items the analytical sheets need but haven't shipped yet. Each entry has a
track, a target version, and a status. Items move to **Shipped** when they
land; they keep their `BL-NNNN` ID so cross-references in CHANGELOG entries
stay stable.

**Numbering:** sequential `BL-NNNN`. New items get the next number; reuse is
forbidden. When closing, leave the ID in place and add a `Shipped in <release>`
line + a one-paragraph summary.

**Sort:** within each status section, by track then target version.

**Sources to sweep when adding new items:** "Out of scope" / "Carry-forwards
opened" sections in [CHANGELOG-T12.md](CHANGELOG-T12.md) and
[CHANGELOG-RR.md](CHANGELOG-RR.md), plus the "Open carry-forwards" section in
[CLAUDE.md](CLAUDE.md). Items here are the authoritative forward-looking
list — the CHANGELOG carry-forward notes are pointers, not the source of
truth.

---

## Pending

### [BL-0019] Persistent audit log for password gate (external store + manual sync)
- **Track:** RR (Track 1)
- **Target:** TBD (likely RR v1.18.0 + new `tools/sync_audit_log.py`)
- **Originally surfaced in:** chat 2026-05-19. Current `auth.py` `_log()` writes `[AUTH] <ts> user=<u> <event>` lines to stdout only; Streamlit Cloud captures the stream but logs are ephemeral (wiped on reboot), have no per-user query, and provide no long-term audit trail. User wants persistent login history that ends up in the repo folder and can be pulled to local.
- **Summary:** Adopt **option 3 architecture** (chosen over option 1 — App commits to GitHub via contents API, rejected for noisy git history; and option 2 — GitHub Actions cron sync, rejected for added Action complexity):
    - **Write side** — `auth.py` `_log()` posts each event (`login_ok` / `login_fail` / `logout`) to an external persistent store at write time. Candidate stores: Supabase (free tier — Postgres + REST, simplest), S3 (append-style one-object-per-event with daily prefix, no DB), or Logtail (logging-as-a-service, lightweight but adds vendor). Final pick deferred to implementation chat; recommend Supabase for SQL queryability and free-tier fit.
    - **Sync side** — new `tools/sync_audit_log.py` run locally by user on demand. Pulls events from the external store since the last successful sync (using a local `tools/.audit_sync_state` marker file with the last-fetched timestamp or event-id, gitignored), appends new rows to `audit_log.csv` at repo root. Idempotent — re-running pulls no duplicates. CSV columns: `timestamp_utc`, `username`, `event`.
    - **Repo-side decision deferred:** whether `audit_log.csv` is committed (audit trail in git history) or gitignored (privacy preference, plus avoids constant churn). Default recommendation: gitignored, with `audit_log.csv.example` committed showing the schema.
    - **Secrets** — new `[audit]` table in Streamlit Cloud Secrets with the external-store credentials. Also added to `.streamlit/secrets.toml` for local dev.
    - **Failure mode** — if the external-store write fails, `auth.py` falls back to the existing stdout `[AUTH]` line and does NOT block the login. Audit logging is best-effort, never a gate.
- **Notes:** User-deferred to "later" on 2026-05-19. Implementation should happen in a fresh Track 1 chat (this chat was Track 3 / substrate v0.2.7). Confirm with user before implementation: (a) external-store choice, (b) commit vs gitignore the CSV, (c) whether to also expose an in-app admin view of recent audit events.

---

## Shipped

### [BL-0022] `Cover!B5` doesn't auto-resolve the property name
- **Shipped in:** substrate v0.2.8 (2026-05-20)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** User report 2026-05-19 — "The Cover sheet isn't being populated by the actual name of the property that's in T12 analytics" — against the populated Homestead Village v0.2.5 Analyzer fixture (`Sample Files/Analyzer with 2026-04-24 Homestead Village Rent Roll v2 + March 2026 T12 2026-04-24.xlsx`).
- **Summary:** `Cover!B5` (the `Property_Name` named-range source) was a static manual-entry cell while RR v1.15.0 + T12 v0.2.1 writers had been auto-stamping the property name into `Rent Roll Input!A3` / `T12 Input!A10` since 2026-05-11. `T12 Analytics!B2`'s 3-priority resolver (RR → T12 → `Property_Name`) picked up the name via path 1, but Cover itself stayed blank — and with it `Dashboard!B2`'s title formula (which references `Cover!B5` directly), `UW Export!B3` (`=IFERROR(Property_Name,"(not set)")`), `Workbook Health!B27`/`C27`, and Pre-Export Gate `B49` all reported "missing" / "(not set)" / empty even though the writer-stamped inputs were present. v0.2.8 rewrites `Cover!B5` to a 2-priority resolver formula (`Rent Roll Input!A3` → `T12 Input!A10` → "") — same priority-1/priority-2 chain that `T12 Analytics!B2` already used, minus the priority-3 `Property_Name` fallback (would be circular since `Property_Name → Cover!B5`). All 5 downstream consumers cascade automatically. `Cover!A19` docstring also updated — old text described B5 as a manual-entry cell, new text describes the auto-resolve. **Defensive skip:** if `Cover!B5` already contains static (non-formula) text at migration time, the rewrite is bypassed and the user's typed value is preserved. Migration via `migrate_to_v028.py` (4 ops, 10-check verify, idempotent — gate on `Cover!B8 == "v0.2.8"`). Pure substrate change — no row inserts, no other-sheet formula edits, no named-range additions, no sheet additions. Chain-tested clean v0.2.4 → v0.2.5 → v0.2.6 → v0.2.7 → v0.2.8 from the bundled file baseline. **Bundled `ALF_Financial_Analyzer_Only.xlsx` not bumped** per the BL-0021 (2026-05-19) "wholesale-replace" directive — migration script is the deliverable; users run the chain against their own workbook.

### [BL-0021] Bundled Analyzer reset to user-authored copy + Dashboard "Last updated" stamp
- **Shipped in:** 2026-05-19 (NOT a substrate version bump — see below)
- **Track:** Substrate-adjacent (Track 3) — bundled-file management, not a migration
- **Originally surfaced in:** chat 2026-05-19, user request after v0.2.7 + v0.2.8 work landed (the latter unmerged on `claude/bl-0020-dashboard-data-link-fixes`).
- **Summary:** User opted to wholesale-replace the bundled `ALF_Financial_Analyzer_Only.xlsx` with their hand-edited Excel copy from `C:\One Drive Business\OneDrive - (na)\office\rent_roll_app\ALF_Financial_Analyzer_Only.xlsx` rather than continue forward-rolling via the substrate migration chain. This is a **regression** relative to `main`'s state (v0.2.7): the bundled file now has `Cover!B8 = "v0.2.4"` and lacks BL-0012 (Section M6), BL-0016 (AH4 fill), BL-0017 (144-cell intentional-blank styling), and BL-0018 (v0.2.7 Dashboard structural — though the user's own Dashboard inherits the chart-data-link fixes from the closed-unmerged BL-0020). The migration chain v0.2.5 → v0.2.8 stays in `tools/migration/` for reproducibility but is no longer derivable-from for the bundled file. Per user request, a new cell `Dashboard!N1` is stamped `"Last updated: 2026-05-19"` (static text, Calibri 10pt italic gray, right-aligned) to surface the bundled file's edit date in the workbook itself. **Implications going forward:** the bundled file is now a user-managed artifact rather than a substrate-derived one. Future Track 3 substrate work that wants to add new features will either need to (a) apply on top of the user's v0.2.4-baseline file and accept the regressions, or (b) re-forward-roll first (run `migrate_to_v025.py` through `migrate_to_v028.py` against the bundled file, then add new work on top — but this would override the user's Dashboard customizations unless v0.2.8 is re-applied last).

### [BL-0020] Dashboard chart-data-link bug fixes
- **Shipped in:** substrate **v0.2.9** (2026-05-21) via `tools/migration/migrate_to_v029.py`. (Earlier history: the fixes were first present informally in the user's local file, then in the bundled Analyzer via the BL-0021 wholesale-replace 2026-05-19. The original `migrate_to_v028.py` on branch `claude/bl-0020-dashboard-data-link-fixes` / PR #34 was **closed unmerged** — that v0.2.8 number was re-used on `main` for BL-0022. v0.2.9 ports the fixes onto the chain so a forward-rolled workbook gets correct charts; that closed branch's `migrate_to_v028.py` is now **superseded** — do not revive it.)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** user noticed in Excel after the v0.2.7 release (same day, hours later). The v0.2.7 Dashboard was inherited from the user's authored copy and shipped with three stale / incorrect cross-sheet references that hadn't been caught in the v0.2.7 verification (which only confirmed cells resolved to *populated* targets, not that the targets matched chart titles).
- **Summary:** Three Dashboard bugs corrected by `migrate_to_v029.py` (surgical cell + chart patch, no template asset): **(1) Monthly EGI Trend** line chart was plotting **Housekeeping Income** — `Dashboard!C97:C108` referenced `Monthly Trending!B21:M21` (row 21 = Housekeeping Income since v0.1.7), corrected to row 26 (EGI). **(2) Payer Mix — Revenue Share** pie chart was plotting **unit counts** instead of revenue ratios — `Dashboard!F90:F93` referenced `Rent Roll Recon!B40:B43` (COUNTIFS for unit counts), corrected to `I40:I43` (`H/H47` revenue-ratio formulas matching the chart title). **(3) Doughnut chart [1] series range** covered `$O$8:$O$19` (12 rows) but payer labels sat at `O8` + `O14:O19` with a 5-row gap (`O9:O13` empty), rendering empty slices in Excel; corrected by moving the `O14:O19` payer rows up to `O9:O14` (contiguous with `O8`), clearing `O15:O19`, and shrinking the series range to `$O$8:$O$14` / `$P$8:$P$14` with rebuilt 7-point caches. Idempotent (gate on `Cover!B8 == "v0.2.9"`; data-move guarded to the buggy state so re-runs / already-fixed Dashboards aren't corrupted). Full chain v0.2.4 → v0.2.9 tested clean. **Resolves the v0.2.8 collision** (BL-0020 = v0.2.9, BL-0022 = v0.2.8). Lesson for future Dashboard work: substrate-migration verification should spot-check chart titles vs source row labels, not just "do refs resolve to populated cells."

### [BL-0018] Dashboard sheet redesign — replace Investment Dashboard with chart-rich Dashboard
- **Shipped in:** substrate v0.2.7 (2026-05-19)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** user-authored externally in Excel and dropped in on 2026-05-19. Replaces the v0.2.4 Investment Dashboard (BL ticket retroactively assigned at close).
- **Summary:** Removes the v0.2.4 `Investment Dashboard` sheet (340 cells, 0 charts, 52-col layout) and inserts a redesigned `Dashboard` sheet at the same index 1 position (437 cells, **6 native Excel charts**, 72 merged ranges, 17-col visible layout, navy tab color `FF1F4E79`). Sheet count remains 15. Pure formula-reference layer over T12 Analytics + Rent Roll Recon + Monthly Trending + Cover — 96 unique cross-sheet refs total, 95 resolve to populated cells on the v0.2.6 baseline; the one outlier is `Cover!B5` (Property Name) which is user-populated at runtime via the `Property_Name` named range. Migration via `migrate_to_v027.py` — sources from committed template asset at `tools/migration/v027_assets/dashboard_template.xlsx` (26 KB single-sheet workbook), 14-check verify, idempotent (gate checks Cover!B8 == v0.2.7 AND Dashboard at index 1 AND Investment Dashboard absent). Charts copied via `copy.deepcopy(chart)` since openpyxl Chart objects carry their series references as string formulas that survive deep-copy. The user's source file was based on v0.2.4 and had drifted (Google Sheets / LibreOffice round-trip artifacts plus accidental T12 Analytics anchor relocation AZ→AM); **none of those regressions were carried forward** — the migration starts from the current v0.2.6 base and only adds the Dashboard. v0.2.5 (Section M6) + v0.2.6 (BL-0016 AH4 fill, BL-0017 144-cell intentional-blank styling) work confirmed intact post-migration.

### [BL-0016] Rent Roll Input!AH4 — header invisible (white-bold font on transparent fill)
- **Shipped in:** substrate v0.2.6 (2026-05-18) — bundled with BL-0017.
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** User report 2026-05-16 ("rent roll input tab has a missing label on row 4") against the populated Homestead v0.2.3 Analyzer.
- **Summary:** When the AH "Total Ancillary $" column was added in substrate v0.2.2, the header cell received correct white-bold font but `fill_type=None` (transparent). White-on-default renders as a blank cell — the column header was invisible. v0.2.6 applies the green `FF1F6B52` `PatternFill` matching `T4`/`U4` (substrate's computed-column header palette; navy is for input cols, green for formula cols). Originally implemented in PR #26 (2026-05-16) bundled with BL-0017 but closed unmerged after user chose to handle manually in Excel; re-confirmed on 2026-05-18 to ship via substrate migration after all. Implementation ported from the abandoned commit `fac129d` on branch `claude/serene-panini-3ad41d`. One-cell change. Header text + bold font preserved.

### [BL-0017] Workbook-wide "intentionally blank" visual convention
- **Shipped in:** substrate v0.2.6 (2026-05-18) — bundled with BL-0016.
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** User report 2026-05-16 ("T12 Analytics E36:E37 doesn't add up") against the populated Homestead v0.2.3 Analyzer. Diagnosis identified T12 Analytics E36/G36 as storing the literal 3-character string `"-"` (with quote chars in the text payload), rendering as `"-"` with visible quote marks in Excel. Pre-flight migration sweep revealed the same literal in 144 cells workbook-wide.
- **Summary:** User-approved treatment applied to all 144 placeholder cells: `value="—"` (em-dash plain text — no quote chars) + `fill=PatternFill("FFF2F2F2", solid)` (light gray) + `font color=FFA0A0A0` (medium gray, preserving size/bold/italic/name/underline/strike) + `horizontal alignment=center` (preserving vertical/wrap/indent/shrink/rotation). New user-facing rule: **gray + em-dash = "blank by design"; truly empty = "data not yet populated"**. Cell inventory (144 total): T12 Analytics E36/G36 (2) + Rent Roll Recon D109 (1) + UW Output cols B/C/D × rows {8-12, 22-28, 30-36, 38-56, 58-60, 62-64, 66-68} (141). Originally implemented in PR #26 (2026-05-16) bundled with BL-0016 but closed unmerged after user chose manual Excel handling; re-confirmed on 2026-05-18 to ship via substrate migration. Implementation ported from abandoned commit `fac129d` on branch `claude/serene-panini-3ad41d`. **Out of scope (intentionally deferred):** formula-conditional blanks like `T12 Analytics!E37/G37/H38` that return `""` only when source data is missing — permanent styling would mislead when they populate. Defer to a future v0.2.7+ if a clean Excel-conditional-formatting approach surfaces.

### [BL-0012] Section M — Misc/Diabetes credit reconciliation against T12 `Concessions & specials`
- **Shipped in:** substrate v0.2.5 (2026-05-16)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** RR v1.17.0 (BL-0003) "Side observation worth tracking" in CHANGELOG-RR.md.
- **Summary:** New Section M6 on `Rent Roll Recon` (rows 178-183). Fires only on **negative** residuals on the M5 "Misc. Income" bucket (`B173 < 0`); positive residuals are still M5's domain — the two sections are non-overlapping. Three data rows:
    - R179: Residual from M5 (`=B173`)
    - R180: T12 `Concessions & specials` annual (`=IFERROR(VLOOKUP("Concessions & specials", 'T12 Raw Data'!$B:$R, 17, 0), 0)`)
    - R181: `=IFERROR(ABS(B179)/ABS(B180), 0)` (residual / T12 Concessions, abs)
  And a 4-branch conditional note at R183 (merged A:I): empty when residual is positive; ⚠ when residual exists but T12 has no Concessions line for reconciliation; ⚠ when ratio > 10% ("Likely misposted concessions — review GL"); ✓ when ratio ≤ 10% ("Within reconciliation tolerance"). Threshold hard-coded at 10% — easy to surface to a tunable cell in a future v0.2.6+ if multiple deals show the ratio varying meaningfully. Styling mirrors the existing M5 block (R169 header, R170 data row, R176 note). Migration via `migrate_to_v025.py` — 9-check verify, idempotent (gate checks `Cover!B8 == "v0.2.5"` AND `Rent Roll Recon!A178` starts with "M6"). The original BL ticket gated this on "observing the same negative-residual pattern in one more deal"; user ungated to close out the remaining backlog item.

### [BL-0011] Function/class renames — `populate_t12()` → `populate_rr_input()` + `T12CapacityError` → `AnalyzerRRCapacityError`
- **Shipped in:** RR v1.17.5 (2026-05-15)
- **Track:** Refactor (Track 1)
- **Originally surfaced in:** RR v1.17.2 (BL-0010) `analyzer_rr_writer.py` rename — the CLAUDE.md note explicitly deferred the function/class renames as a "separate, more invasive follow-up."
- **Summary:** Completes the Track 1 misnamed-T12-symbol cleanup at file + function + class level. Changed: function `populate_t12()` → `populate_rr_input()` (mirrors the partner `populate_t12_input()` on `t12_normalizer_writer.py` which correctly populates `T12 Input`); exception `T12CapacityError` → `AnalyzerRRCapacityError` (matches the 2026-05-10 file rename); also took the opportunity to rename the function-body parameter `t12_bytes` → `analyzer_bytes` and clean up two "T12 workbook" → "Analyzer workbook" references in inline error text. Updated callers in `app.py` (1 import, 1 call site, 1 except clause). Updated live docs (CLAUDE.md "Module naming gotcha" table, SPEC-T12.md module-naming-history paragraph). Historical CHANGELOG / journal references to the old names left intact (records of what shipped at past versions). Verified: `analyzer_rr_writer` imports cleanly with new symbols, old symbols confirmed removed; `app.py` parses cleanly; zero remaining live `populate_t12\b` / `T12CapacityError` references in `*.py`. The only surviving `t12_*` symbol on the Track 1 side is the function name `translate_for_t12()` on `analyzer_rr_translator.py` — left alone since `for_t12` reads as "for the destination workbook" and renaming it would touch every caller of the translator. Bundled in one tidy-up PR with BL-0013 + BL-0014.

### [BL-0013] README.md modernization — T12 + bundled-Analyzer framing
- **Shipped in:** RR v1.17.5 (2026-05-15)
- **Track:** Documentation (cross-cutting)
- **Originally surfaced in:** RR v1.14.0 and earlier releases. Flagged as a known carry-forward across multiple chats.
- **Summary:** Targeted README updates (NOT a full rewrite — README had been substantially modernized since the BL ticket was opened, with dual-pipeline framing and T12 coverage already in place). Bumped the versions table to RR v1.17.5 / 2026-05-15. Refreshed the Data-capture coverage section from "RR v1.16.0 + substrate v0.1.10 (cols A-AB)" to "RR v1.17.4 + substrate v0.2.2 (cols A-AH)" — adds the v0.1.13 per-fee ancillary cols (AC-AG), the v0.2.2 Total Ancillary rollup (AH), the v0.2.1 5 finer T12 Labels closing the per-fee attribution gap on Section M, and the v1.17.4 parser-side Notes-rerouter for Homestead concession patterns. Reframed the Analyzer-at-a-glance section as "Track 3 four-branch roadmap fully closed at substrate v0.2.0" with Section M description and the v0.2.0 UW Export sheet + Pre-Export Gate descriptions. Updated the Versioning section (substrate convention `v0.1.N` → `v0.X.Y`) and added UW-BACKLOG.md mentions in both the Versioning section and the Further Reading table. Bundled in one tidy-up PR with BL-0011 + BL-0014.

### [BL-0014] CLAUDE.md hygiene — refresh "Open carry-forwards" + expand openpyxl quirk #4
- **Shipped in:** RR v1.17.5 (2026-05-15)
- **Track:** Documentation (Track 3-adjacent)
- **Originally surfaced in:** Sweep 2026-05-14, post-substrate v0.2.1.
- **Summary:** Two CLAUDE.md sections fixed. (1) **Open carry-forwards section** — header date refreshed to 2026-05-15 / post-substrate v0.2.3 + RR v1.17.5; the entire "Medium priority (still open)" + "Low priority" sub-sections deleted (they were stale by weeks — "Branch 2 — Handoff readiness" was listed as open while it had shipped as BL-0009 / substrate v0.2.0; "Substrate version-detection bug suspected" was listed while it had shipped as BL-0008). Replaced with a single sentence pointing readers at UW-BACKLOG.md as the source of truth. (2) **openpyxl quirk #4** — expanded with the qualified-range-endpoint trap from BL-0001's migration. Documents both the failure mode (`T12_Calc!$N$1:$N$500`'s endpoint is mis-caught by the unqualified-ref regex and shifted on row inserts, causing off-by-N SUMIF/SUMIFS drift after migrations) and the canonical fix (capture template formulas AFTER the shift sweep, not before — see `tools/migration/migrate_to_v021.py:312-321`). Section heading bumped from "Three" to "Four" since quirk #4 is now substantive. Module naming gotcha table also updated as part of BL-0011. Bundled in one tidy-up PR with BL-0011 + BL-0013. Did NOT include the journal.md back-fill of v0.1.11 → v0.2.2 entries — that observation remains unstaffed.

### [BL-0015] Rent Roll Recon row 16 — GPR realignment (`$H` × occupied → `$G` × all units)
- **Shipped in:** substrate v0.2.3 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** user-reported on 2026-05-12 against the populated Homestead v0.1.10 Analyzer ("Row 16 says Gross RR at 100% occupancy is $565k but the market rate total is $809k"). First implementation shipped as substrate v0.1.11 in [PR #12](https://github.com/ErikJ-Stack/rent-roll-normalizer/pull/12); PR went stale while main moved through v0.1.12 → v0.2.2, was closed unmerged + re-implemented here as v0.2.3 with the current 14-sheet anchor list and the v0.1.11 substrate number reused on main for an unrelated chart-axis fix.
- **Summary:** Realigns `Rent Roll Recon!B16:D16` with the intent already documented in column H ("Gross contracted rates before concessions"). Old formula summed Actual Rate (`'Rent Roll Input'!$H`) over occupied units only — producing "current contracted at actual rate" rather than the Gross Potential Rent at 100% occupancy that the row's role as the underwriting anchor demands. New formula sums Market Rate (`$G`) over all units regardless of status, by care type. On Homestead populated: E16 reconciles from $565,140 → **$809,567** (IL $167k + AL $328k + MC $315k). Row 17 (effective net after concessions) is unchanged — its `H + I` is already correct because concessions are negative-signed (per [SPEC-RR.md L184](SPEC-RR.md)). A16 label rewritten to "RR Gross Potential Rent / mo  (Market × all units)" ("contracted" was misleading once vacants are included). H16 note rewritten to state GPR semantics + identify the row16-vs-row17 gap as vacancy + market-vs-actual premium ($244k on Homestead). Migration via `migrate_to_v023.py` — 3 ops, 9-check verify, idempotent. Closes the loop on the user-reported issue from 2026-05-12.

### [BL-0001] Finer ancillary Labels in `Description_Map`
- **Shipped in:** substrate v0.2.1 (2026-05-14) + RR v1.17.3 (companion `_detect_substrate_version()` widening)
- **Track:** Substrate (Track 3) + companion patch on RR (Track 1)
- **Originally surfaced in:** substrate v0.1.12 Section M (the analytical
  surface that exposed the per-fee attribution gap)
- **Summary:** 5 new Labels added to the closed vocabulary (55 → 60):
  `Meal Income`, `Housekeeping Income`, `Laundry Income`,
  `Scooter Fee Revenue`, `Transfer Fee Revenue`. Each gets (a) a row in
  T12 Raw Data with SUMIF formulas against `T12_Calc` (cols F-R), (b) a
  row in Monthly Trending with INDEX/MATCH formulas against T12 Raw
  Data (cols B-N), (c) typical Description→Label mappings appended to
  Description_Map (14 new rows, 2-4 per Label). Section M D-column on
  Rent Roll Recon re-pointed: 5 of the 7 default fees (rows 124-129
  except 127) move from `Other community revenue` → their new specific
  Labels. M3's `(shared — see row N)` heuristic resolves automatically
  since each row's COUNTIF finds no duplicates. EGI on Monthly
  Trending R26 (was R21) rewritten to include the 5 new rows.
  Migration via `migrate_to_v021.py` — single 5-row insert at each
  destination (`insert_rows(target, amount=5)`), full-workbook shift
  sweep for row refs ≥ threshold, idempotent gate, 13-check
  verification. Companion `app.py` patch widens the version-detection
  regex `v0\.1\.\d+` → `v\d+\.\d+\.\d+` so v0.2.x reports accurately;
  bundled in the same PR. **UW-BACKLOG is now empty** for the first
  time since this file was introduced in substrate v0.1.12.

### [BL-0010] Module rename — `t12_translator.py` → `analyzer_rr_translator.py`
- **Shipped in:** RR v1.17.2 (2026-05-14)
- **Track:** Refactor (Track 1)
- **Originally surfaced in:** 2026-05-10 partial rename (`t12_writer.py` →
  `analyzer_rr_writer.py`); the partner module was deferred to "whenever
  bundled."
- **Summary:** `git mv` rename. Single live import in `app.py` line 50
  updated; one docstring reference in `analyzer_rr_writer.py` updated.
  Function name `translate_for_t12()`, translation tables, and the
  exception class `T12CapacityError` (still exported by
  `analyzer_rr_writer.py`) all retained for surgical scope. CLAUDE.md
  "Module naming gotcha" rewritten to reflect that the Track 1 file
  disambiguation is now complete; only the legitimate Track 2 `t12_*`
  files (`t12_normalizer.py`, `t12_normalizer_writer.py`) remain with
  the prefix.

### [BL-0009] Branch 2 — Handoff readiness (UW Export + Pre-Export Gate + metadata header)
- **Shipped in:** substrate v0.2.0 (2026-05-14, flagship release)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** CLAUDE.md "Open carry-forwards" — long-standing
  Track 3 roadmap item from the four-branch plan.
- **Summary:** Three coordinated additions ship the final piece of the
  Track 3 roadmap. (1) New **`UW Export` sheet** at index 8 — title +
  italic instructions + 5-row metadata header (Property / RR period /
  T12 period / Substrate version / Generated timestamp) + 71-row × 8-col
  values-only mirror of UW Output via `='UW Output'!{cell}` formulas.
  When opened in Excel the cells evaluate to values; downstream consumer
  copies-as-values into their template. (2) New **Pre-Export Gate**
  section on Workbook Health (rows 46-52) aggregating existing V1-V8
  validation checks into four P-checks plus a single ✓/⚠ "READY FOR
  EXPORT" aggregate cell at row 52. (3) **Workbook Map extension**
  adding `UW Export` row at Workbook Health row 19. **The four-branch
  Track 3 roadmap is now fully closed** (Branches 1+4 in v0.1.6, Branch 3
  in v0.1.8 through v0.1.14, Branch 2 in this v0.2.0 release).

### [BL-0008] Substrate version-detection in `app.py`
- **Shipped in:** RR v1.17.1 (2026-05-14)
- **Track:** RR (Track 1)
- **Originally surfaced in:** CLAUDE.md "Open carry-forwards"
- **Summary:** Rewrote `_detect_substrate_version()` with a three-tier
  resolution strategy. Primary path reads `Cover!B8` (the canonical
  version stamp set by every migration since v0.1.4). Fallback uses
  newest-to-oldest sentinel cells (Rent Roll Recon!I87, T12 Analytics!A168,
  Rent Roll Input!AC4, Rent Roll Recon!A119, Rent Roll Input!V4). Legacy
  Description_Map heuristic preserved for pre-v0.1.10 Analyzers. The
  prior implementation was stale-capped at `v0.1.5` since v1.12.0.
  Sanity-checked on the bundled v0.1.14 Analyzer (reports `v0.1.14`) and
  user's populated Homestead workbook at v0.1.10 (reports `v0.1.10`).

### [BL-0002] V5 chart — empty rendering for broker-format rent rolls
- **Shipped in:** substrate v0.1.15 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.11 verification on Homestead
- **Summary:** Improved V5 (AL Acuity Mix) empty-state UX without
  restructuring the chart. (1) Wrapped `Rent Roll Recon!D59:D66` formulas
  with `IF($B$67=0, "", ...)` so the doughnut renders as a true empty
  frame (no zero-valued slices) when source has no acuity data.
  (2) Applied bold + pale-yellow fill styling to `T12 Analytics!K45`
  (the existing v0.1.8 conditional note "Property has no AL acuity data
  — flat-rate AL or unpopulated.") so the empty-state message reads as
  a warning attached to the chart instead of an ignorable label.
  
  Chose option (a) "accept and document" with strengthened styling rather
  than option (b) "fallback Care Type breakdown" because Homestead has
  $0 Care Level $ total across all 176 beds — a Care Type fallback
  chart would also be empty for the user's headline fixture. Option (c)
  "hide the chart" wasn't available in openpyxl without chart XML
  manipulation. When a flat-rate-AL fixture surfaces (Care Level $ > 0
  but no acuity tiers), revisit option (b) as a follow-up.

### [BL-0004] T12 Analytics — 2P revenue reconciliation row
- **Shipped in:** substrate v0.1.14 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added per-bed SP capture at col V)
- **Summary:** 3-row block on T12 Analytics rows 168-170 (after the existing
  KPI Dashboard color key at row 166). Compares `=SUM('Rent Roll Input'!$V$7:$V$606)*12`
  (RR-projected annual 2P revenue) against `=IFERROR('T12 Raw Data'!$R$15,0)`
  (T12 actual annual 2P revenue). Variance % + conditional note fires when
  \|variance\| > 10%. Placement chose rows 168+ because the natural slot at
  rows 42-44 had pre-existing horizontal merges (A43:H43, A45:H45) for visual
  breaks between GPR Waterfall and Other Revenue Normalization Bridge.

### [BL-0005] Workbook Health — total AR / Balance aggregation
- **Shipped in:** substrate v0.1.14 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added Balance column at `Rent Roll Input!X`)
- **Summary:** 3 new rows extending the Workbook Health DIAGNOSTICS section.
  Row 43: `G9 · Total outstanding AR` = `SUM('Rent Roll Input'!$X$7:$X$606)`.
  Row 44: `G10 · AR ÷ monthly EGI` = `B43 / ('Monthly Trending'!$N$21/12)`.
  Row 45: conditional note (merged A:D) — ⚠ fires when AR > 5% of monthly
  EGI; ✓ "within 5%" otherwise. Slots after the existing G8 'Last opened'
  volatile timestamp at row 42.

### [BL-0006] Rent Roll Recon Section K — Avg Actual PSF column
- **Shipped in:** substrate v0.1.14 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added Actual PSF at `Rent Roll Input!AA`)
- **Summary:** New col I "Avg Actual PSF" on Section K IL unit-type table.
  I87 header + I88-I92 per-unit-type AVERAGEIFS on `Rent Roll Input!$AA$7:$AA$606`
  (Actual PSF) + I93 Total IL row. Same filter pattern as existing col D
  (Avg Rate). Sources from per-bed data captured at v1.16.0; cell-only
  extension of the existing table (cols A-H untouched, dispersion rows
  95-100 untouched). Complements the existing derived `$/Sq Ft` column at H
  (which divides Avg Rate ÷ Avg Sq Ft) — col I pulls the direct per-bed PSF
  average for cross-validation.

### [BL-0003] RR Input expansion — per-fee ancillary columns
- **Shipped in:** RR v1.17.0 + substrate v0.1.13 (2026-05-13)
- **Track:** RR (Track 1) + Substrate (Track 3) — cross-cutting single PR
- **Originally surfaced in:** substrate v0.1.12 Section M2 (4 of 7 default
  fees fell through to "no per-fee RR column yet" notes pointing here)
- **Summary:** Per-fee ancillary columns added at `Rent Roll Input!AC-AG`
  (`Meal Plan $`, `Scooter Fee $`, `Housekeeping $`, `Laundry $`, `Pet $`).
  `mappings.py` extended with 8 new bucket-routing rules; `normalizer.py`
  bucket_sums + bed record + CONDENSED_COLUMNS extended (25 → 30);
  `analyzer_rr_writer.py` writes the new fields. Substrate v0.1.13 adds the
  RRI columns, extends Total LOC $ formula to include AC-AG, adds a 5th
  "RR Input Col" mapping column to Section M1, and rewrites M2/M4 with
  universal `INDIRECT` formulas off that mapping. M2 eligibility unified
  to all-occupied beds (was IL-only for SP).
  **End-to-end on Homestead**: Pet $100, Housekeeping $1,450, Laundry $630
  split out from Other LOC $; Total LOC $ unchanged ($-9,966.75 of
  ancillary preserved across the 5 split + Other LOC catchall). Salem /
  Briar Glen / Beaufort baselines all green; Beaufort surfaces $65 in
  `Laundry $` previously buried in Other LOC $.

### [BL-0007] RR Other LOC keyword expansion — meal / scooter / mobility / transport
- **Shipped in:** RR v1.16.2 (2026-05-13, PR #15)
- **Track:** RR (Track 1)
- **Originally surfaced in:** substrate v0.1.12 Section M (M2 fees that "fall
  into Misc.")
- **Summary:** Added `meal`, `scooter`, `mobility`, `transport` to the
  `_looks_care` keyword list in `detect_care_groups` (`normalizer.py`).
  Matches v1.15.1's prior keyword broadening pattern. Future-proofs the
  parser for operators whose source rent rolls expose those services as
  named columns. **No impact on Homestead specifically** — its broker
  format bundles optional services into a single `Misc.` column rather
  than breaking them out. Regression-verified against all three baseline
  fixtures (Salem, Briar Glen, Beaufort) with no drift.

*(Pre-v0.1.12 closed items are documented in CHANGELOG-T12.md and
CHANGELOG-RR.md; no retroactive backfill needed here.)*
