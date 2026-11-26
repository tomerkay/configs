# My Claude config

This repo is my user-level Claude Code config: the root `CLAUDE.md` is loaded
into every session on the machine, and the hooks, settings and `tkay-*`
skills are live the moment they are saved. This file holds how each of them
is changed, and the root `CLAUDE.md` points every session here before it
edits one.

## A staged change, installed on one question

**A file that is live the moment it is saved is never edited in place** - the
root `CLAUDE.md`, a file under `personal/`, a `tkay-*` skill, a hook, a
home file the sync publishes, a file of the `~/repos/configs` repo the sync
runs from. The sections below
name what each kind adds; the procedure itself is this one:

1. **Stage it.** Copy the file into this session's handoff directory and make
   every edit to the copy. Keep a second, untouched copy beside it: the base
   the edits were made on.
2. **Review the staged diff with the `tkay-review` standard**: a doc
   review when the diff touches only what that standard's doc review
   covers, a full CR with every section it gives otherwise. The diff
   stands in for the commit; a Full Assessment on its own is not a
   review.
   **Each review runs in a fresh agent**, never in the session that staged
   the change: it is told to load the review standard first and no
   writing standard, that it wrote none of the change, and **which review
   to write, by its name** - "a doc review" or "a CR", picked by the line
   above - since the standard writes a doc review only when asked for one
   by that name. It is handed the base and staged copies, the whole diff
   and each staged commit's own diff - made after the last edit - with its
   message, under its name S1, S2, and is told that its review names each
   commit by that name in place of a SHA; from the second round on, it is
   also handed the previous round's review file. It is handed **the spec:
   every decision I made on the change, each written out as a goal the
   change must meet**, in my own words where I gave them, and **the record
   of every test run on the staged copies** - a hook's selftest and the
   cases the change is about - kept as the `tkay-code` standard's
   `test-record.md` says, each entry naming the staged copies it read by
   the hash of their content. It gets nothing else of the session: none
   of its reasoning, and no hint of where to look. The review standard's
   exemption for this repo spares the session its question; it never
   keeps the review in the session.
   **Then fix and review again, up to three rounds, but only while the
   review holds a MUST HAVE still open**: a 🔴 or 🟠 finding on a staged
   commit, or a goal or promise the review calls ⏳ Not reached, ❌ Missed
   or ❌ Breaks callers - never a bycatch row, and not one a later staged
   commit already fixed: a fixed finding is not open, whatever its colour.
   A MUST HAVE or a bycatch fix the review leaves as 🙋 Your call is put to
   me as a ❓ of its own, and the round waits: it stages the option I pick,
   never one it picks itself. Such a round fixes every MUST HAVE still
   open, every bycatch row whose call is 🔧 Add fix, and every NICE TO HAVE
   finding and ⏸ Leave for now bycatch row in a file this procedure covers
   whose fix is rated super easy, or small and easy, with Evidence at least
   CONFIDENT - on the commit's Fix 🟡⚪ line or the row's own Fix Profile -
   then reviews the fixed copy in the same shape, since a fix lands in code
   the rest of the change depends on and can bring a problem of its own.
   **After a review with no MUST HAVE open, nothing is fixed**: what else
   it found stays as it is, and the install question lists it.
   **Each round's fixes are staged as new commits on top of the ones it
   reviewed, one for each commit they fix, never folded into them**, so
   every commit a round has judged keeps its diff and every fix commit
   folds into exactly one commit on the install. Each staged commit is
   named S1, S2 in order, and keeps a copy of the staged file as it stands
   after it and its own diff against the copy of the commit before it: the
   name stands in for the SHA the review standard names a commit by, and a
   commit whose own diff and the copy before it are byte for byte the ones
   the previous review saw is unchanged. The next round starts from the
   previous round's review as the review standard's repeat CR does: an
   unchanged commit keeps its findings and has its call decided again, so
   one whose MUST HAVE a later commit fixes reads 👌 Fixed later, and the
   round reads the new commits and judges the result at the top.
   **The staged commits shape the review, not the install**: on the install
   each fix commit is folded into the commit it fixes, so the change
   installs as the commits it was proposed as. The final staged copy
   installs in one `cp`, and each of those commits is cut from it hunk by
   hunk, holding its own lines and those of the fixes folded into it. A
   bycatch fix is staged as a commit of its own, installed on the same yes.
   The standard's question before code after a CR is not asked here: a
   session in this repo or in `~/repos/configs` is one it exempts. **The
   rounds end at the first review with no MUST HAVE open, or with the
   review after the third round**, which is the final one.
   When the final review's To do still holds a MUST HAVE, fix nothing more
   and do not ask the install question: explain the problem, propose a
   different fix as a ❓ of its own, and stop. The fix I pick is staged and
   reviewed in this same shape before the install question comes. Anything
   else the final review finds stays as it is.
3. **Ask once**: show the diff, the last review and the message of each
   commit that installs,
   written by the `tkay-code` commit standard, then end the reply with
   "❓ Q<n> Install it into `<file>` and commit?", with the change's Full
   Assessment nested under it, as every proposal carries one: the call on
   installing it, the change's Profile, and its Why Yes and Why Not, which
   may repeat the commit's from the review. The last review judges
   the copy that installs; when rounds of fixes ran, a line per round
   above it says what that round's review found and what its fixes
   changed.
4. **On my yes, install and commit it yourself**, as plain commands with the
   sandbox off - it denies these paths, and gpg cannot sign inside it. Never
   hand me the `cp` to paste while that route is open: the question is the
   safeguard, and a paste is the same install with a round trip added.
   **Compare the live file with the base first, in the same command as its
   `cp`** - every file's `cmp -s <base> <live file>` chained with `&&`,
   then every `cp <staged copy> <live file>`, each path written out
   absolute, never with `~`, so one
   difference stops every copy and another session's change can land only
   in the moment between a file's compare and its copy. For a file the
   change adds, `test ! -e <live file>` stands in for its `cmp`, and
   `/dev/null` for its old base in the merge below. `-s` prints nothing,
   so on a non-zero exit compare each file again on its own to find the
   one that moved. When they differ - another session changed it since -
   the `cp` would overwrite that change, and the commit's diff would no
   longer be the reviewed one: install nothing, copy the live file in as
   the new base, beside the old one, and stage the edits again on it.
   **The edits move onto the new base with `git -C <this session's
   handoff directory> merge-file <staged copy> <old base> <new
   base>`**, which writes the merge into the staged copy. A non-zero exit up
   to 127 is the number of conflicts: make the edit again by hand on the new
   base's text in place of each marked block. An exit above 127 is an error,
   and the staged copy is untouched: fix the command and run it again. Then
   check the result with a plain `diff` against the new base: it must show
   the edits of the last reviewed diff and nothing else, every line read.
   Then run steps 2 and 3 again, with the staged commits started over on
   the new base as the commits that install - each fix commit folded into
   the one it fixes - named on from the last S<n>, so the next review finds
   none of them in the previous one and reads them in full. The macOS
   `diff3 -m` is never used for the merge: it can drop a line at the edge
   of a change and still report a clean merge.
5. **If the install or the commit is refused**, confirm the staged copy still
   exists, print the exact command for me as a `! <command>` and stop. Never
   reach the same change by another route.

## My home files are published - private values go in the PRIVATE block

**My dotfiles, the root `CLAUDE.md`, my Claude settings, my hooks and my
`tkay-*` skills are copied into a public GitHub repo on a schedule** by
`~/repos/configs/bin/sync-configs.sh`. It holds the list of home files it
copies; the Claude files it copies are whatever the `~/.claude` repo tracks,
`personal/` aside (see below). It copies the working tree, not the last
commit, and that is on purpose - do not raise it as a bug. Treat every one
of those files as public the moment you write to it.

**For this purpose an internal identifier IS a credential, and so is an
account identity.** A Slack channel ID, a Tailscale or internal hostname, a
cluster, context, node or namespace name, a firewall rule or cloud project
name; and on the personal side any e-mail address other than my work one, and
my username on any service - GitHub, GitLab or anything else. None of it may
sit in a published file in the clear, any more than a token may.

**Decided public, do not raise again:** my handle, my work e-mail, my employer
and my GPG fingerprint; Atero in any form or role - the word, the `atero`
namespace, a label prefix, a repo name; the names and URLs of our GitLab
repositories and chart registry; Slack channel names (IDs stay private); the
Crusoe CLI profile name; the product-level names my skills use - a monitor, a CRD
group, a chart; and Crusoe's own default firewall rule and network names,
which every customer has. A sweep that finds only these is clean.

**A published file with no block cannot hold a value from the first list at
all.** The Claude settings file is one: a value that has to live there is
either accepted as public, which widens the list above, or the file stops
being published - ask which, do not decide alone.

**In a shell rc, such a value goes ONLY between the markers the sync script
defines as `PRIVATE_OPEN` and `PRIVATE_CLOSE`**, exported as a variable; the
sync deletes those blocks before it commits. A function or alias outside the
block reads the variable, never the literal. **A hook or a skill has no block**,
so it carries no such value at all: it reads it from a file under `~/.config`
that nothing syncs - not from a shell variable, which a desktop-launched
session never sees - and treats a missing file as the feature being off. A
missing file must never fall back to a built-in default that would then be
published.

The sync has Claude read every added line and refuses the commit on a finding,
so a slip stalls the sync rather than leaking - but it is the last line, not
the rule. When you put a value in the block, say so in one line.

**A change to a home file the sync publishes is reviewed and committed with
its reason, in the turn it is made.** These are the `HOME_FILES` of
`~/repos/configs/bin/sync-configs.sh`, and only a sync run given `-m` and the
files it covers commits them; a run without `-m` only logs them as waiting.
Each is read by its tool the moment that tool starts - the shell rc files by
every new shell, this session's included - so a broken one is live the moment
it is saved. It goes through "A staged change, installed on one question",
and two things are its own:

- **The install and the commit are one command**: the compare and the
  `cp` of step 4, then `sync-configs.sh --no-push -m "<message>" <file>...`,
  chained with `&&`, so no scheduled run commits the change first.
  Pushing is left to the next scheduled run.
- **A refused run names the other home files with a pending change.** Each
  gets its own reason from me before this one is committed, never folded into
  this message.

## The sync's own repo takes the same staged change

**A file of `~/repos/configs` that the sync does not copy in - the scripts
under `bin/`, the README, the `.gitignore` - goes through "A staged change,
installed on one question"**, and is committed in that repo, on `main`,
in the same turn. The scripts are live: launchd runs the sync on its
schedule and cron runs the daily updates, so a half-made edit runs on the
next tick, and the sync pushes whatever that repo has committed.

**Its `claude/` and `home/` are copies the sync rebuilds on every run.** A
change goes to the source - the file in `~/.claude` or under the home
directory - never to the copy, which the next run overwrites.

## My Claude config is a git repo - every change is reviewed and committed

**`~/.claude` is a local git repo.** Its `.gitignore` ignores everything and
then allows back only the files I hand-write; `git -C ~/.claude ls-files`
lists them. Everything else in `~/.claude` - sessions, memory, caches,
installed skills - stays untracked.

**It has no remote: the commit is the last step, and publishing is the
sync's job.**

**I change it often, in other sessions too, so it moves under you.**
Before each step of work on it - staging a copy, each review round, the
install question, the install - list the commits since the tip you last
saw and the changes not yet committed:

```
git -C ~/.claude log --oneline --stat <that tip>..HEAD
git -C ~/.claude status --short
```

The first look of a session records the tip it starts from. When either
shows something new - the `model` line below aside - say so in one line
and judge each new commit or uncommitted change against the proposal:

- **It touches a file the proposal changes, or a rule the proposal rests
  on or restates**: read it, stage the proposal again on top of it, as
  the install step of "A staged change, installed on one question" moves
  the edits onto a new base, and review it again before the step goes on.
- **It does not**: name it as unrelated in that same line, and go on.

The install's comparison of the live file with the base, in "A staged
change, installed on one question", still runs: it catches a change to
the file itself, and this check catches the rest, and earlier.

**No change to a tracked file is ever left uncommitted.** Every edit,
deletion, rename and move is reviewed and committed in the same turn as the
change, whatever task it came up in. A deletion is the dangerous one: git
lists a file until a commit records that it is gone, and the sync stops on a
tracked file that is missing at home and publishes nothing, dotfiles
included.

- **A change to the root `CLAUDE.md`, a file under `personal/` or a
  `tkay-*` skill goes through "A staged change, installed on one
  question"**, and its commit follows the
  `tkay-code` commit standard, signed, deciding squash or new commit like
  anywhere else. A hook adds its own steps below.
- **A turn that changed anything in `~/.claude` ends with
  `git -C ~/.claude status --short` printing nothing.** Run it before the last message. Anything it
  lists is reviewed and committed before you reply, including a change you
  did not make - with the one exception below.
- **The `model` line of `settings.json` is never committed.** The harness
  rewrites it on every model switch, and the tracked copy keeps the value
  it has. Stage that file hunk by hunk (`git add -p`) and skip the model
  hunk every time; never commit it with a pathspec, which takes the whole
  file. A working tree whose only difference is that line is clean for the
  status check above, and that line is never a review finding either - not
  bycatch.

**A new file joins the allowlist only after I agree.** Tracking a file
publishes it: the sync copies whatever this repo tracks into the public repo,
all but `personal/`.

## A hook is live the moment it is saved

**A file under `~/.claude/hooks` is never edited in place.** Every session on
this machine runs it the moment it is saved, so a half-applied edit is not a
draft there. `tool-gate.py` fails closed: if it raises, it denies every
command it touches, in every session, including the commands that would undo
the edit. A permission layer can refuse one edit of a change and allow the
next, which is exactly how that state arises.

It goes through "A staged change, installed on one question", with steps
of its own:

- **Test the staged copy before the question.** Run its `--selftest` where it
  has one, and put every case the change is about through the copy before
  the live file is touched. Time it there too, as "A hook is small and
  fast" says.
- **A change to a file another hook imports tests that hook too**: a
  change to `skills/tkay-tools/hooks/command_parser.py` runs the gate's
  selftest and `skills/tkay-cluster/hooks/pin_guard.py --selftest`
  against the staged parser, since either one failing to import blocks
  every Bash call. Neither reaches it as it stands - the gate imports the
  parser from its live path, the pin guard through the link beside it -
  so each runs with the staged parser put in the live one's place.
- **Install it in one `cp`**, behind step 4's compare, then run the same
  tests against the live file before the commit. No allow rule passes a
  hook's install: a wildcard rule matched copies out of the hooks
  directory too, so each install goes to my permission prompt, which
  shows the exact command.
- **A failure in the live tests is undone with `git -C ~/.claude restore
  <file>` before anything else**; when the broken hook denies that, print it
  for me as a `! <command>` and stop.

**If a hook is already broken**, the first line of your reply says so, names
what it now denies, and gives the `! git -C ~/.claude restore <file>` that
undoes it.

## A hook is small and fast

**Every call a hook sits on waits for it, so a hook costs about what
starting its interpreter costs, and adds nothing to the context on the
normal path** - a hook in `settings.json` and one in a skill's frontmatter
alike.

- **It decides from its payload and a small state file of its own.** It
  never reads the transcript, walks a directory tree, or calls the network
  or a model. A subprocess runs only where the answer needs one - `git` for
  a repo's state - with a timeout.
- **It prints only when it denies, asks or reports.** What a hook adds to
  the context is paid for in tokens on every turn it fires, and a Stop hook
  that sends a reply back costs a whole turn, so its check is one that
  rarely fires.
- **It is timed on the largest real input it will meet**, and the time is
  given with the diff. One that cannot stay that cheap is not built: say
  so, and propose another route.

The case that taught it: a hook designed to find the session's title in the
transcript on every prompt, which took seconds on the largest transcript.

## My `tkay-*` skills are standalone and generic

I hand my `tkay-*` skills to other people as-is, so each one must work in a
session that has never seen a CLAUDE.md of mine or any other skill. When
you write or edit one:

- **It points at nothing outside itself** - no CLAUDE.md, no other skill, no
  path on my machine. Its own `references/` and `hooks/` are fine.
- **It names no other skill, anywhere**: not in its description, its body,
  its references, its hooks' comments or its test labels - not as a
  pointer, not as the owner of a job, not as a sibling "handed out
  together". A name assumes the other skill is installed and carries its
  rules in by the back door. Another skill's job is described by its role -
  "a skill that sets the standards code is written to" - and a rule this
  skill needs is written into it, or into a file shared by symlink. Its own
  `name:` line, a hook naming its own skill, and the frontmatter a file
  lent by symlink keeps from its owner are the only names. The case that
  set it: a code skill that said "the CR standard lives in the review
  skill" by name, which no review checked, since the rule above reads as a
  ban on paths alone.
- **A file two skills need is shared by symlink**, as `tkay-docs`
  says for any catalog. For mine, the sync's `cp` follows the link and
  publishes a real copy into each skill, which it rebuilds on every run,
  so the copies never drift. Two skills' hooks never check the
  same thing: each checks only its own skill's side, so nothing is
  checked twice when both are loaded, and code the hooks share is a module
  symlinked like any other file. The case that
  set it: `tkay-review` reading `../tkay-code/references/`, which broke
  for anyone who installed the review skill alone.
- **It states every rule it relies on**, in its own words: a cluster command
  in it carries `--context`/`--kube-context` and `-n`, a safety rule it
  depends on is written into it. A copy of a rule from a CLAUDE.md of mine
  is the price of standalone; keep it to what that skill actually needs.
- **Knowledge specific to my workplace, Crusoe and its Atero site, stays
  in `tkay-cluster`, the root `CLAUDE.md` and `personal/`** - its
  clusters, cells, backoffice, charts and repos: what an operation on a
  cluster or a cell needs goes in `tkay-cluster`, everything else in
  the root `CLAUDE.md` or `personal/`. Every other `tkay-*` skill works
  for an engineer anywhere, `tkay-house-rules` included; an example taken
  from my work that names no Crusoe or Atero system is fine.
- **It names nobody and nowhere**: not me, no cluster, node,
  namespace or label value. It says "me" and "my", which reads as whoever
  loaded it, and derives anything personal at run time (`git config
  user.email`) or asks for it.
- **A rule I taught in a session is best given a real example from it**, a
  recommendation, not a requirement. When I point out how I want something
  and ask you to put it in a skill, add the case that taught it when it
  makes the rule easier to recognise: a before/after snippet of the actual
  code, the label or the message, cut to the lines that show it and
  stripped of names as "It names nobody and nowhere" says. Leave it out
  when the rule reads plainly without one. A rule read cold is easy to
  agree with and hard to apply; the example is what makes it recognisable
  the next time.

This applies to `tkay-*` only. Team and repo skills - `atero-skills` and the
rest - follow their own catalog's conventions and may point across skills and
repos.

My skills are edited under `skills/`.

## `tkay-house-rules` holds my taste

**A rule goes in `tkay-house-rules` when every other skill still does its
whole job without it, and another engineer could install it as it is**: a
choice one could reasonably make the other way - where work lands, what is
never offered. A rule that is part of what a skill is for - a commit body
for the commit standard - stays in that skill. Every rule lands on one
side, so `tkay-house-rules` and the other skills never hold the same rule.

- **It is standalone and generic like every `tkay-*` skill**: all of "My
  `tkay-*` skills are standalone and generic" binds it. A fact about me or
  my setup is no taste, and goes in `personal/`, below.
- **The root `CLAUDE.md` `@`-imports its `SKILL.md`, which `@`-imports
  every reference of its own**, so every session loads them before the
  first change. A new reference joins by its own import line in
  `SKILL.md`; one linked from another skill is named there, not imported.
- **The gate and the commands that need my words stay in the root
  `CLAUDE.md`**, beside the hook that enforces them, whatever this test
  says of each row - and so does every line that names the gate, which
  lives in that file alone. The skill states the habit - what is never
  offered, how a rewrite I asked for runs - and never which command needs
  my words.

## `personal/` holds what is mine alone, and is never published

**A fact about me or my setup goes in a file under `~/.claude/personal/`**:
my name and handle, my machine, a path, a repo, an account, what my
sandbox or my org's policy blocks. No skill carries one.

- **The root `CLAUDE.md` `@`-imports `personal/index.md`, which `@`-imports
  every file beside it**, so every session loads them. A new file joins by
  its own import line there.
- **It is tracked here and never published.** The sync skips the
  directory, refuses to commit when its copy holds one, and tells its
  review that any line under it is unsafe; `sync-configs.sh` names the
  directory once. So a file there may hold what a published file may not -
  an internal hostname, a channel ID - and still no token or password,
  which stay in a file under `~/.config`.
- **It may point anywhere** - at the root `CLAUDE.md`, at a skill - since
  nobody installs it.
