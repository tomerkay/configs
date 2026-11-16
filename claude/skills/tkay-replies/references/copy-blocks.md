# Bracket everything I am meant to copy

**Anything you hand me to copy-paste is SANDWICHED between two marker lines: a
line of exactly 32 `=` immediately BEFORE it, and a second line of exactly 32 `=`
immediately AFTER it.** Both sides, every time - a marker on top with nothing at
the bottom is not bracketing, it is a stray row of `=`. That covers a command to
run, a `! <command>` suggestion, a config or YAML snippet, a query, a commit
message, a chat message, a value to paste into a UI. If I am going to select it
with the mouse and paste it somewhere else, it is bracketed.

The exact shape, fence included:

````
================================
```
the thing I copy
```
================================
````

**The markers go OUTSIDE the code fence, on their own lines** - the fence opens
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
