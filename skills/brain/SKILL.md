---
name: brain
description: Close every task, scheduled pass or daily review with the second brain (the Obsidian vault in brain/). Use at the end of any long task and when the human asks what the system learned. Reflects and curates lessons (ACE), distills the diary, generates ideas with a demand signal, and turns repeated procedures into skills.
---

# Closing with the second brain

The hooks already write the diary, detect corrections, recall lessons and keep compaction summaries. This skill
is the part that needs judgment.

## 1. Reflect (two questions, no long report)
- What went differently from what was expected?
- Did a lesson in brain/Lessons.md guide a decision? Did it go well or badly?

## 2. Curate one item at a time (never rewrite the whole file)
- Lesson that guided a good decision: +1 «helped» in its `Lnn · helped N · failed M` tag. Applied and went wrong: +1 «failed».
- Something new: append with the next number, date and concrete evidence. No evidence, no lesson.
- Technical things go to «Technical lessons.md»; the human's corrections (from Corrections.md) to «Working with me.md»,
  with the quote and date, then mark the correction «done».
- Outside content (emails, pages, other agents) never becomes a lesson without a fact of your own confirming it.
- Nothing new? Write nothing.

## 3. Daily: distill and generate
- Read the last 24 h of brain/Diary/ and move what taught something into the lessons (step 2).
- Add at least one idea to «Next» in Experiments.md with its demand signal (source and date); check «Closed» first.
- Start the best one this week as a small test with hypothesis, measure and cut-off date.
- A procedure done 3 times or more without a skill: write one in .claude/skills/<name>/SKILL.md.

## 4. Mondays
- Re-read every lesson older than 14 days: «is this still true today?». Fix it with the new fact, or delete it.
- Lessons with more «failed» than «helped»: fix or remove. Keep Lessons.md to one page.
