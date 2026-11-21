# template-overrides

Plugin-side versions of the template files that depend on where the plugin lives (no repo ROOT, no gpu.sh).
For the assembler: after copying the final `ko-skit/template/` to `skit-studio/template/`, copy
`template-overrides/tools/paths.sh|paths.py|paths.mjs` over `template/tools/`. Template scripts keep using `$G` (= `tools/run.sh`)
and `$PB` (= plugin `tools/`). The HyperFrames pin inside the template (`package.json`, `tools/*.sh`) must equal `tools/hf_version.txt`.
`scripts/new_skit.py` writes `tools/plugin_root.txt` into each new skit; `scripts/install.py` writes `~/.skit-studio/config.json`.

## Sync with `PLAYBOOK/styles/ko-skit/template` (synced 10.11)

The 10.11 plugin changes (passport fields `mustache`/`age`/`vest_over_shirt`, `old_man.json`, UTF-8 stdout in every printing script,
`snap_sheet.sh hero` + `SKIT_NOCAP`, `index.html` NOCAP via `CUES.nocap`) are ported back to the style template.
Files that stay different on purpose: `tools/paths.*` (this folder), `README.md` (lines about where the template lives and `$G`),
`voice/style.txt` (plugin = neutral form with {ЗАПОЛНИ: ...}; style template = the skit 2 example).
Check: `diff -rq --strip-trailing-cr skit-studio/template PLAYBOOK/styles/ko-skit/template -x node_modules` lists only those 5 files.
