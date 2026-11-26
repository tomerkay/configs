# Bracket everything I am meant to copy

**Anything you hand me to copy-paste is sandwiched between two marker lines: a
line of exactly 32 `=` immediately before it, and a second line of exactly 32 `=`
immediately after it.** Both sides, every time - a marker on top with nothing at
the bottom is not bracketing, it is a stray row of `=`. That covers a command to
run, a `! <command>` suggestion, a config or YAML snippet, a query, a commit
message, a chat message, a value to paste into a UI. If I am going to select it
with the mouse and paste it somewhere else, it is bracketed.

The exact shape, fence included - a block that quotes a markdown file, or
a diff, takes the four-backtick fence `before-and-after.md` gives:

````
================================
```
the thing I copy
```
================================
````

**The markers go outside the code fence, on their own lines** - the fence opens
below the top marker and closes above the bottom one. Everything between the
markers is then exactly what I paste and nothing more. Inside the fence they
become part of what I copy and the command breaks.

**Leave a blank line above the top marker and below the bottom one.** A row of
`=` sitting directly under a line of prose is a markdown heading underline: the
prose swells into a title and the marker itself disappears from my screen.

**Output I only read gets no markers** - explanations, findings, a diff you are
showing me, a summary you are about to post yourself, an illustrative snippet of
my own code. Bracketing those buries the real ones. Two blocks I am meant to copy
get two bracketed blocks, never one bracket around both.

## What I act on comes last

**Everything I am to run or paste goes at the end of the reply**, after
every explanation and right above the ❓ block, which stays last: a
command, a `! <command>`, a `/goal` line, a value for a UI. It is one
numbered list in the order to run, and every step another depends on is
listed before it, in the same reply - never a turn later. I read the
reasoning first, then act from top to bottom without scrolling back.

The case that taught it: a reply handed over a goal's `/goal` line, and
the `! cp` that had to run before it came a turn later, once I asked.

```
❌ reply 1: <the goal> ... paste: /goal <...>
   reply 2: yes, first run: ! cp <...>
✅ reply 1: <the goal and its reasoning>
   1. ! cp <...>
   2. /goal <...>
```

**A file I asked you to write is named at the end of the reply too**,
so I see where it landed without hunting for it: its full path, in
backticks and not bracketed - it is there to open, not to paste - on a
line of its own, below every explanation and the TL;DR, and above the
steps to run, the ❓ block and the closing "Are we done?" line, which
stay last; a note another rule puts right under the path stays there,
between it and them. A path given earlier in the reply, beside what the
file holds, does not stand in for it, and each file I asked for gets a
line of its own. The case that taught it:

```
❌ <the path, mid-reply, beside what the file holds>
   <a screen of findings>
   **TL;DR:** <the outcome>
✅ <a screen of findings>
   **TL;DR:** <the outcome>
   `<the full path of the file>`
```
