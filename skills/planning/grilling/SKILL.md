---
name: grilling
description: Use when a person wants to sharpen a loose idea, plan, feature request or design before anything is built, asks to be grilled or interviewed about it, or when a request is too vague to build without decisions only they can make.
---

# Grilling

Applies to: turning a loose idea into decisions with the person who owns it, before a spec or code exists. It needs that person in the conversation; an agent working alone records its open decisions as assumptions instead.

Interview the person relentlessly until you reach a shared understanding. Map it as a **design tree**: every decision branches into the decisions that hang off it.

## Rounds

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask now without guessing at answers you haven't heard yet. Ask the whole frontier in one round. Number each question, give your recommended answer, and wait for the answers before the next round.

```
❓ **Q1** - **<question title>**: <the question, which may run to several paragraphs and offer choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <the question>

➡️ <your recommended answer>
```

Word each question so "yes" accepts your recommendation.

Each round of answers reshapes the tree: settled decisions push the frontier outward and unblock the questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a later round.

## Facts are yours, decisions are theirs

Finding facts is your job, never the person's. When a frontier question needs a fact from the code, the repository or a tool, look it up, or send a sub-agent with a fresh context to find it, rather than asking. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait; ask the rest of the frontier now. The decisions are the person's: put each one to them and wait.

Some questions can't be settled by talking, such as how an interaction should feel or whether one long form beats three pages. When you reach one, say so, and suggest a throwaway prototype to react to instead of rephrasing the question.

## Done

The session is done when the frontier is empty: every branch visited, nothing silently assumed. Summarise the settled decisions as a numbered list, and don't act on them until the person confirms you've reached a shared understanding.

Adapted from Matt Pocock's [grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md), invoked there as `grill-me` (MIT, see [LICENSE](LICENSE)).
