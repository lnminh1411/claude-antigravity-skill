# claude-antigravity-skill

A [Claude Code](https://claude.com/claude-code) skill that splits coding work between two models. Claude writes the spec and audits the result; Gemini, driven through Google's Antigravity CLI (`agy`), writes the code.

```
Claude ── spec ──▶ agy (Gemini Flash) ── writes files ──▶ repo
  ▲                    │                                    │
  └──── ASK: / DONE: ──┘                                    │
  └──────────── git diff + tests + lint (audit) ◀───────────┘
                    │
          pass: stage   ·   minor: fix by hand   ·   major: send back
```

Unofficial. Not affiliated with Google or Anthropic.

## Why split the work

Gemini Flash now writes code about as well as Claude's top model on coding benchmarks, at a fraction of the price, but falls well behind it on general agentic judgment. This skill puts each model where it is strong: Gemini types, Claude decides what to build and whether what came back is right. Nothing Gemini writes is staged until Claude has read the diff and run the project's checks.

## Install

Copy the `antigravity` folder into your Claude Code skills directory:

| Scope | Path |
|---|---|
| You, all projects | `~/.claude/skills/antigravity/` |
| One project | `<repo>/.claude/skills/antigravity/` |

```bash
git clone https://github.com/lnminh1411/claude-antigravity-skill
cp -r claude-antigravity-skill/antigravity ~/.claude/skills/
```

`SKILL.md` is self-contained: its appendix carries the same `agy_watch.py` that ships beside it, so uploading `SKILL.md` alone also works where only one Markdown file is accepted.

Then, in Claude Code:

```
/antigravity setup
```

Setup installs `agy` if it is missing, reads which Google account is signed in and how it is billed, picks the newest Gemini Flash model the account offers, optionally installs a bundle of office-document skills for Gemini, and runs a smoke test.

Signing in is yours to do: run `agy` once and complete the browser sign-in. Setup cannot do OAuth for you.

## What it does

- **Spec, dispatch, audit, resolve.** Claude writes a spec with acceptance criteria, dispatches it, then reads the full `git diff`, runs tests, type checker and linter, checks every new import resolves, and hunts regressions and out-of-scope edits. A clean result is staged; a small flaw is fixed by hand; a real failure goes back to Gemini with the logs.
- **Live progress.** Dispatches stream NDJSON. `agy_watch.py --follow` prints a line per step as Gemini works (each file write, each command with its duration, each error) and stops on completion, on a stall, or before Claude Code's 600-second tool limit.
- **Two-way chat.** A live session keeps one `agy` conversation open. Gemini ends a turn with `ASK: <question>` when it needs a decision; Claude answers with `agy_watch.py --send`. Audit failures go back into the same context instead of a cold restart.
- **Pay-as-you-go first.** A Google Cloud pay-as-you-go account has no daily quota wall, so setup prefers it when the signed-in account is one.
- **Model pinned at run time.** The skill reads `agy models` rather than hardcoding a model id, so it keeps working as the CLI updates itself and new Flash releases appear.
- **Knows when not to delegate.** Small, surgical changes are faster to write than to specify, so the skill writes those itself.

## Facts it relies on

All measured against `agy` 1.1 to 1.4.8 while building this. The skill text explains each one where it matters.

| Behaviour | Consequence |
|---|---|
| Every dispatch spends ~20k input tokens on agy's preamble | small jobs are cheaper to write directly |
| In print mode, every file write outside your home directory is denied, and neither `--add-dir` nor `trustedWorkspaces` lifts it | dispatch uses `--dangerously-skip-permissions`, contained by the audit |
| Without `--add-dir`, Gemini works in `~/.gemini/antigravity-cli/scratch` | the diff comes back empty |
| Effort is part of the model id (`…-flash-low`); `--effort` conflicts with it | the skill passes the id alone |
| `ask_question` does nothing headless | Gemini asks through an `ASK:` line instead |
| Stream input accepts only `{"event":"user","message":{"content":…}}`; `interrupt` and `cancel` are ignored | messages queue between turns; cutting in means stop and resume with `-c --conversation <id>`, which keeps context |
| The run's final status can say `SUCCESS` with nothing written, or `ERROR` with files written | `git status` decides, not the status field |
| `~/.gemini/google_accounts.json` can name the wrong account | the account comes from the `applyAuthResult` line in `~/.gemini/antigravity-cli/cli.log` |

## Requirements

- Claude Code, with a shell, `git`, and whatever the project's tests need. The audit cannot run without them, so this is not a skill for chat-only surfaces.
- Python 3 for `agy_watch.py` (standard library only) and the optional office-skills installer.
- A Google account signed in to Antigravity.
- Windows, macOS or Linux. Developed and tested on Windows.

## Known limits

- **`--dangerously-skip-permissions` is on for every dispatch.** It is what makes writes outside the home directory work, and it also lets Gemini run shell commands on your machine. The audit gate is the containment: nothing is staged before Claude has read the diff and run the checks. If that trade is wrong for you, keep work inside your home directory and remove the flag.
- **Subscription accounts can hit a daily quota mid-task.** The skill stops and reports what was finished; it does not switch accounts on its own.
- **The office bundle** comes from [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills). Its Gmail, Drive and Sheets skills need their own sign-in, and its text mentions five `libreoffice-*` skills that do not exist upstream; the Word, Excel and PowerPoint skills cover the same work.

## License

MIT. See [LICENSE](LICENSE).
