# JSON reaches jq straight from what produced it

**Never `echo` JSON into jq: pipe the producer into it.** The `echo` of
zsh, of macOS's `sh` and of dash, the `sh` of Debian and Ubuntu, expands
backslash escapes - only bash's leaves them alone - so the two
characters `\n` a JSON string carries for a newline become a raw control
character, and jq refuses the whole document with `Invalid string: control
characters from U+0000 through U+001F must be escaped`. A small test
response often holds no escaped newline and parses; the real one, carrying
a commit message or a log line, does not. When the JSON must sit in a
variable first, hand it over with `printf '%s\n'` or a here-string:

```
❌ J=$(glab api ".../jobs"); echo "$J" | jq '...'
✅ glab api ".../jobs" | jq '...'
✅ J=$(glab api ".../jobs"); printf '%s\n' "$J" | jq '...'
✅ J=$(glab api ".../jobs"); jq '...' <<< "$J"
```

The case that taught it: a pipeline watcher stored each `glab api` response
in a variable and echoed it into jq, so every poll failed to parse once the
job list carried a commit message.
