# claude-second-brain

A second brain for Claude Code that writes itself, remembers at the right moment and learns from its mistakes.
Plain Markdown in an Obsidian vault, four hooks in one Python file (standard library only), one skill.

## Why this exists

I ran an autonomous agent project with Claude Code for seven weeks. It earned **USD 0.37**. Looking back, the
problem was not the model: the system kept repeating the same mistakes. It built products before checking that
anyone wanted them, it re-proposed options already discarded, and a store stayed down for 68 hours while every
health check said «green». Claude Code does not learn between sessions; whatever is not written down and read
back gets repeated.

So I built this. It does not change the model. It makes the notes good enough that the model behaves as if it
had learned.

## What it does

| When | Hook | What happens |
|---|---|---|
| Session starts (and after compaction) | `SessionStart` | Loads `Lessons.md` and `Direction.md`, backs up memory and notes once a day (14 days kept), writes `Alerts.md` if a front has been at zero for 5 days in a row |
| You send a request | `UserPromptSubmit` | Brings back the 3 lessons or memories most related to that request (recall at decision time) |
| Claude finishes an answer | `Stop` | Appends one line to today's diary, including scheduled tasks and messages you send while it works; detects your corrections and confirmations into `Corrections.md` |
| The chat gets compacted | `PostCompact` | Keeps the compaction summary as a session note |

The `brain` skill is the part that needs judgment: reflect after each task, curate lessons one item at a time
with a «helped / failed» counter and concrete evidence (the ACE pattern: Agentic Context Engineering), distill the
diary daily, propose new experiments only with a demand signal, and turn any procedure repeated three times into
a new skill.

## Install (5 minutes)

1. Copy `hooks/brain.py` to `<your project>/.claude/hooks/brain.py`.
2. Copy `skills/brain/` to `<your project>/.claude/skills/brain/`.
3. Copy `vault/` to `<your project>/brain/` and open that folder as a vault in Obsidian (optional, but you will
   want to see it).
4. Merge `settings.example.json` into `<your project>/.claude/settings.local.json`. On Windows, use the full path
   to `python.exe` if `python` is not on your PATH.
5. Start Claude Code in the project. The first answer creates `brain/Diary/<today>.md`.

Optional: set `BRAIN_VAULT` to keep the vault somewhere else, and edit the `STAGNATION` patterns at the top of
`brain.py` to match your own fronts. Claude Code's own auto memory and Auto Dream work alongside this; the start
hook backs that memory up before Auto Dream reorganizes it.

## What it does not do

- It does not retrain anything. Learning lives in the notes and in what gets loaded and recalled.
- The judgment steps (distilling, counting, proposing) run when Claude runs them: from the skill, a scheduled
  task or your request. The hooks only guarantee that nothing gets lost and the right lesson shows up.
- Content from outside (emails, web pages, other agents) should never become a lesson without your own evidence.
  Memory poisoning is real; the skill says so explicitly.

## Status

Built and tested on 24 Nov 2026 in a real project (Windows 11, Claude Code, Obsidian 1.15). It is young: the
honest measure is whether repeated mistakes go down over the next weeks. Issues and stories welcome.

## Want it adapted to your repo, or your current setup checked?

Fixed price, USD 50 each, in writing, no calls, delivered within 48 h:

- **Adaptation**: I adapt the notes, the recall stopwords and the alert rules to ONE repository of yours.
- **Memory check**: you already have hooks or a memory setup for an agent; I test whether it really keeps the
  user's messages, recalls the right instruction and reports its own failures, using your real transcripts' shapes,
  and hand you the reproducing cases. (This template failed exactly those checks three times before it passed.)

Open an issue titled **Adaptation** or **Memory check** with a line about your project; payment and delivery go
through a freelance platform, never off-platform.

Made by Martin Pisacreta, working with Claude Code. MIT license.
