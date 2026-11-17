# My Claude config

This repo is my user-level Claude Code config: the root `CLAUDE.md` is loaded
into every session on the machine, and the hooks, settings and `tkay-*`
skills are live the moment they are saved. This file holds how each of them
is changed, and the root `CLAUDE.md` points every session here before it
edits one.

## A staged change, installed on one question

**A file that is live the moment it is saved is never edited in place** - the
root `CLAUDE.md`, a `tkay-*` skill, a hook, a home file the sync publishes,
a file of the `~/repos/configs` repo the sync runs from. The sections below
name what each kind adds; the procedure itself is this one:

1. **Stage it.** Copy the file into this session's handoff directory and make
   every edit to the copy.
2. **Review the staged diff with the `tkay-review` standard**, in the
   full shape that standard gives a one-commit branch: the FINDINGS line and
   the commit's Full Assessment, both buckets, the branch overview, the
   commits table and the bycatch table. The diff stands in for the
   commit; a Full Assessment on its own is not a review.
   **Then fix, in one round, on the staged copy**: every MUST HAVE finding,
   every bycatch row whose call is 🔧 Add fix, and the NICE TO HAVE findings
   when the commit's Fix 🟡⚪ line rates their fix super easy. A bycatch fix
   is staged as a commit of its own, installed on the same yes. The
   standard's warning before a fix stays silent here: a session in this
   repo or in `~/repos/configs` is one it exempts. **Then review the fixed copy once more, in the same
   shape** - a fix lands in code the rest of the change depends on, and can
   bring a problem of its own. When that review still finds a MUST HAVE,
   fix nothing more: ask me about it as a ❓ of its own, and the install
   question waits for my answer. Anything else it finds stays as it is.
3. **Ask once**: show the diff, the last review and the commit message,
   written by the `tkay-code` commit standard, then end the reply with
   "❓ Q<n> Install it into `<file>` and commit?". The last review judges
   the copy that installs; when a round of fixes ran, one line above it
   says what the first review found and what the fixes changed.
4. **On my yes, install and commit it yourself**, as plain commands with the
   sandbox off - it denies these paths, and gpg cannot sign inside it. Never
   hand me the `cp` to paste while that route is open: the question is the
   safeguard, and a paste is the same install with a round trip added.
5. **If the install or the commit is refused**, confirm the staged copy still
   exists, print the exact command for me as a `! <command>` and stop. Never
   reach the same change by another route.

## My home files are published - private values go in the PRIVATE block

**My dotfiles, the root `CLAUDE.md`, my Claude settings, my hooks and my
`tkay-*` skills are copied into a public GitHub repo on a schedule** by
`~/repos/configs/bin/sync-configs.sh`. It holds the list of home files it
copies; the Claude files it copies are whatever the `~/.claude` repo tracks
(see below). It copies the working tree, not the last commit, and that is on
purpose - do not raise it as a bug. Treat every one of those files as public
the moment you write to it.

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

- **The install and the commit are one command**: the `cp` over the live
  file, then `sync-configs.sh --no-push -m "<message>" <file>...`, so no
  scheduled run commits the change first. Pushing is left to the next
  scheduled run.
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

**No change to a tracked file is ever left uncommitted.** Every edit,
deletion, rename and move is reviewed and committed in the same turn as the
change, whatever task it came up in. A deletion is the dangerous one: git
lists a file until a commit records that it is gone, and the sync stops on a
tracked file that is missing at home and publishes nothing, dotfiles
included.

- **A change to the root `CLAUDE.md` or to a `tkay-*` skill goes through "A
  staged change, installed on one question"**, and its commit follows the
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
publishes it: the sync copies whatever this repo tracks into the public repo.

## A hook is live the moment it is saved

**A file under `~/.claude/hooks` is never edited in place.** Every session on
this machine runs it the moment it is saved, so a half-applied edit is not a
draft there. `tool-gate.py` fails closed: if it raises, it denies every
command it touches, in every session, including the commands that would undo
the edit. A permission layer can refuse one edit of a change and allow the
next, which is exactly how that state arises.

It goes through "A staged change, installed on one question", with three
steps of its own:

- **Test the staged copy before the question.** Run its `--selftest` where it
  has one, and put every case the change is about through the copy before
  the live file is touched.
- **Install it in one `cp`**, passed by the `cp` allow rule in
  `settings.json`, then run the same tests against the live file before the
  commit.
- **A failure in the live tests is undone with `git -C ~/.claude restore
  <file>` before anything else**; when the broken hook denies that, print it
  for me as a `! <command>` and stop.

**If a hook is already broken**, the first line of your reply says so, names
what it now denies, and gives the `! git -C ~/.claude restore <file>` that
undoes it.

## My `tkay-*` skills are standalone and generic

I hand my `tkay-*` skills to other people as-is, so each one must work in a
session that has never seen a CLAUDE.md of mine or any other skill. When you
write or edit one:

- **It points at nothing outside itself** - no CLAUDE.md, no other skill, no
  path on my machine. Its own `references/` and `hooks/` are fine.
- **A file two skills need is shared by symlink**, as `tkay-writing-mds`
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
