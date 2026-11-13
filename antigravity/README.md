# antigravity: a Claude Code skill

Claude writes the spec and audits the result; Gemini, through Google's Antigravity CLI (`agy`), writes the code. Unofficial, not affiliated with Google or Anthropic. Full documentation: https://github.com/lnminh1411/claude-antigravity-skill

## Install

Extract the zip, then run the installer inside the `antigravity` folder:

| System | Command |
|---|---|
| Windows | double-click `install.cmd`, or `powershell -ExecutionPolicy Bypass -File install.ps1` |
| macOS, Linux, Git Bash | `bash install.sh` |

That installs for you, in every project: `~/.claude/skills/antigravity`, or `$CLAUDE_CONFIG_DIR/skills/antigravity` if you set that variable. For one repository only, add `-Project <repo>` (Windows) or `--project <repo>` (bash). An existing copy is moved to `.claude/skill-backups/antigravity-<time>`, never deleted; it goes outside `skills/` so Claude Code does not load it as a second skill.

Installing by hand works too: copy this folder so that `SKILL.md` sits at `<skills dir>/antigravity/SKILL.md`.

## First run

1. Run `agy` once and finish the browser sign-in. Skip this if Antigravity Desktop is already signed in; the CLI shares its session.
2. In Claude Code: `/antigravity setup`

Setup installs `agy` if it is missing, reads which account is signed in and how it is billed, picks Gemini 4 Hydrogen (or the newest Gemini Flash where Hydrogen is not available yet), offers an optional bundle of office-document skills for Gemini, and runs a smoke test.

## Requirements

- Claude Code with a shell, `git`, and your project's test tools
- Python 3.8 or newer (standard library only)
- A Google account signed in to Antigravity
- Windows, macOS, or Linux

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | the skill |
| `agy_watch.py` | streams Gemini's progress and carries the two-way chat |
| `install.sh`, `install.ps1`, `install.cmd` | installers; not copied into the skills folder |
| `LICENSE` | MIT |
