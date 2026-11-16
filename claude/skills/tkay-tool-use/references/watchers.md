# A background watcher fails on a poll it cannot read

**A background watcher fails on a poll it cannot read; it never waits on
one.** A loop that polls until a state arrives reads an empty or
unparseable answer as "not yet" unless told otherwise, and then spins
forever doing nothing. It exits with a message when the parse fails or the
value it reads is empty, and its log is read once after its first poll, to
see it parse a real response:

```
S=$(glab api "..." | jq -r '...') || { echo "poll unreadable"; exit 1; }
[ -n "$S" ] || { echo "poll empty"; exit 1; }
```

The case that taught it: a watcher meant to start a pipeline's manual jobs
and restart deployments once they passed failed to parse every poll, took
the empty status for "not done yet", and spun until it was found by hand.
