# A before and after is a section per snippet, each side fenced

**When I ask to see how a change will look - "the snippets", "before and
after", "how will it read", in whatever words - each snippet that changes
is a section of its own**, headed by the file and the place, with a
`### Before` and a `### After` under it, each a fenced block so it renders,
and a `---` between sections. A snippet that stays as it is gets no section,
only a line in the opening that says so.

The case that taught it: asked for `=====` before and after each snippet,
with the text between `"""`, I pasted both literally and nothing rendered.
A marker I am given is the separator it stands for - a heading, a rule, a
fence - never text to copy in.

**A diff, and every block that quotes a markdown file, is wrapped in four
backticks, always**, whether or not a fence line shows in it, and in more
when it holds a four-backtick fence line. A fence closes on the first line
with at least as many backticks as the one that opened it, and the fence
line inside such a block - a fence line in a diff's context, the closing
line of an example - is the one a look over the block misses, so the kind
of block decides the fence, never a search for the line. Any other block
whose content holds a fence line takes a fence longer than that line. A
fence that closes early flips every fence after it, and the rest of the
reply renders as raw code.

The case that taught it: a diff of a markdown file whose context held the
closing line of an example.

```
❌ ```diff ... ```      the diff's own ``` line closed the fence
✅ ````diff ... ````    only a four-backtick line closes it
```
