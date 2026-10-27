# Formal verification

This page records how the build and publish machinery behind Primordial Paradox is checked
formally, not just by testing examples. It says what was proven, how, the real bug the work
found, the commands to reproduce the checks, and the honest limits.

## In plain English

The game is built and published by a fleet of AI agents that share one git repository and one
publish pipeline. Formal verification is a different kind of check from a test. A test tries one
input and watches one run. A formal check reasons over every possible behaviour of a small model
of the system, so a property like "no agent's commit undoes another agent's files" can be shown
to hold always, not just in the cases someone thought to try.

The work is in four layers, cheapest first:

1. Model check the concurrency protocols (the commit gate, the publish pipeline) with TLA+ and
   the TLC model checker. These are the layers where the real bugs lived.
2. Property test the guards with Hypothesis, and state contracts with CrossHair, so the privacy
   scrub and the guard decisions hold for every generated input, not the examples on hand.
3. Monitor the fleet's own logs with past-time temporal checks, so a violation that already
   happened shows up as a trap instead of a surprise.
4. Encode the music engine's counterpoint rules as constraints for the Z3 solver, so a generated
   line is rule-clean by construction. This layer is in progress.

A model is smaller than the real system on purpose: a model small enough to exhaust is what makes
"always" a meaningful word. The honest limits section says what that abstraction leaves out.

## What was proven

### 1. The commit protocol (TLA+ and TLC)

The fleet shares one git index, and a commit that stages the wrong files would sweep in another
agent's half finished work. The commit protocol is modeled in `formal/CommitProtocol.tla`: HEAD is
a set of per-file versions, each lane holds a private snapshot, and a commit is an atomic
compare-and-swap (the fast path is the drift check, the atomic guard is git's ref lock). Two safety
properties are checked:

- **NoRevert**: no commit lowers any file's version, so no commit reverts another agent's files.
- **NoRedHead**: HEAD is never left red after a commit that passed the gate.

TLC reports no error on this model (21 states generated, 9 distinct). The companion
`formal/CommitProtocolBroken.tla` removes the atomic compare-and-swap and writes the full stale
snapshot, and TLC finds the reversion the real code prevents: two lanes both pass the drift check on
the same HEAD, then each lands its own file and the second reverts the first. That counterexample is
what proves the safety property is real, not vacuous.

### 2. The publish protocol (TLA+ and TLC)

The publish pipeline is guarded by a lock file and an AGAIN flag, so two publishers never run at
once. `formal/PublishProtocol.tla` models it faithfully, including the gap between removing the lock
and checking the AGAIN flag. Two properties are checked:

- **NoTwo**: never two publishers inside the critical section at once.
- **Termination**: every game commit is eventually published or reported refused.

TLC proves NoTwo but refutes Termination in the original model (327 states generated, 198 distinct),
and the counterexample is the real bug described below. `formal/PublishProtocolFixed.tla` models the
fixed code, and TLC reports no error: after the fix, every commit is eventually published or
reported refused.

### 3. The privacy scrub and the guards (property tests)

Property tests with Hypothesis, plus CrossHair contracts, target the scripts that keep private data
off the public export and keep the agents' actions gated:

- The privacy scrub: no exported byte sequence keeps a host path, the workspace name, a user name,
  or the protected profile name, over adversarial inputs (escaped, mixed slashes, case variants).
  The property tests found three real defects in the scrub rules: a case variant of the protected
  profile name survived, a backslash or case-variant home path kept the user name, and the bare user
  name had no rule at all. All three are pinned so a fix cannot silently regress.
- The guard decisions: every outward action (send, post, like, submit, publish) asks for approval, a
  credential reference is denied, and a write to a protected profile is asked about.
- The file-host hook: a local media file uploaded to a non allowlisted host is refused, and an
  upload with no resolvable destination fails closed.
- The leak scan: planted key shapes are caught, and a fake or vendored value is not flagged.
- The commit claim check: the staged set equals the claimed set, under any interleaving.

The suite reports 26 passed with 3 expected failures (the three pinned defects). The CrossHair
contracts exit clean, but their postconditions read "Not confirmed": the symbolic executor proves
nothing and refutes nothing on set reasoning, so the concrete guarantee comes from the Hypothesis
siblings. The regex rules are Hypothesis only, because symbolic execution cannot invert a compiled
regex.

### 4. The fleet logs (runtime monitors)

Six past-time temporal monitors watch the logs the fleet already writes, and each is wired as a
trap so a violation fails the health check:

- AUDIT-ACTIONS: every outward action is preceded by an enabled switch and followed by an audit
  row, and the rate windows hold.
- KANBAN-CLOSURE: no card reaches done without closure text.
- DISPATCH-AFTER-402: after a credit outage, a dispatch is not spawned until an auth reset.
- BACKUP-FIRST: a write is always preceded by a backup row for that id.
- NO-THIRD-PARTY-HOST: no upload command names a third party host.
- PUBLISH-GATE: a publish that returns 0 carries a clean pre-push gate line, and a refusal says so.

Each trap passes on the real logs today and fails on a planted bad log, which is the proof that a
green trap is not a green nothing. The monitors read counts and ids only; message text and names
never appear in a detail string, and a unit test plants private text to prove that.

### 5. The counterpoint rules (in progress)

The music engine writes three NES voices (two pulse waves and a triangle). The counterpoint rules
are species counterpoint plus free Baroque style: consonance on strong beats, dissonance only as
prepared passing or neighbour tones, no parallel or hidden fifths and octaves, leading tones and
chordal sevenths resolved, voices in range with spacing, leap recovery. The rules are written as a
checker and calibrated against 20 public-domain Bach works (about 8,900 notes), so the thresholds
are measured, not invented.

Layer four turns those rules into constraints for the Z3 solver: each voice is a sequence of
integer pitch variables over the NES range, and each rule becomes a constraint, so any pitch grid
the solver returns is rule-clean by construction. The plan is to sample solver models and re-run the
real checker over every one, then mutate each rule block off in turn to prove no block is written
too weakly to bind. This layer is in progress and is not yet claimed as a completed proof.

## The real bug it found: the lost wakeup

The publisher holds a lock while it publishes, then, in its cleanup, removes the lock and checks the
AGAIN flag in two separate statements. A second publisher that fails to take the lock writes the
AGAIN flag, but it can do so after the first publisher has already checked the flag and left. The
result: the lock is free, the flag is set, and no publisher is alive to see it, so the waiting
commit is neither published nor reported refused until some later commit happens to spawn a
publisher.

TLC found exactly this race. The trace is: the first publisher holds the lock and publishes; the
second fails to take it and sets AGAIN; the first releases the lock and checks AGAIN (still false)
and leaves; the second sets AGAIN and leaves; the pending commit never resolves.

The fix: when taking the lock fails, the loser writes the AGAIN flag and then retries taking the
lock once. If the retry wins (the holder released in the window), the loser becomes the holder and
publishes. If the retry loses, the still-alive holder sees the flag in its cleanup and goes round
again. Either way the loser never leaves an AGAIN flag with no one able to observe it. The fixed
model checks clean.

## How

- **TLA+ with TLC**: the concurrency protocols are written as state machines and their safety and
  liveness properties are model checked over every reachable state.
- **Hypothesis**: property-based testing generates adversarial inputs (escaped and case-variant
  strings, mixed separators) and checks the scrub and guard rules against all of them.
- **CrossHair**: symbolic execution of the pure predicates, as a second, incomplete pass over the
  same rules.
- **Runtime monitors**: past-time temporal logic compiled to Python checks over the JSONL and
  audit logs the fleet already writes, wired into the health checks as traps.
- **Z3**: the counterpoint rules become integer constraints, so line generation is a satisfiability
  problem whose answer is provably rule-clean.

## Reproduce

The TLA+ checks run from this folder against the TLA+ Tools release (`tla2tools.jar` on the
classpath). Expected results are written under each command.

```sh
java -Xmx256m -cp tla2tools.jar tlc2.TLC -workers 1 -config CommitProtocol.cfg CommitProtocol.tla
# "No error has been found" (NoRevert and NoRedHead hold)

java -Xmx256m -cp tla2tools.jar tlc2.TLC -workers 1 -config CommitProtocolBroken.cfg CommitProtocolBroken.tla
# NoRevert is violated (a reversion counterexample)

java -Xmx256m -cp tla2tools.jar tlc2.TLC -workers 1 -config PublishProtocol.cfg PublishProtocol.tla
# Termination is violated (the lost wakeup)

java -Xmx256m -cp tla2tools.jar tlc2.TLC -workers 1 -config PublishProtocolFixed.cfg PublishProtocolFixed.tla
# "No error has been found" (NoTwo and Termination hold)
```

The property tests and the runtime monitors target the fleet's own guard scripts and its own logs,
so they are not reproduced from this public repository alone. Their results are summarised above:
the property suite reports 26 passed with 3 pinned defects, the contracts exit clean, and the six
monitors each pass on the real logs and fail on a planted bad log.

## Honest limits

- **The models abstract the code.** The commit model has two lanes, two files and one version step;
  the publish model has two commits and two publishers. The real fleet has more of each. The models
  capture the concurrency and the ordering that the bugs lived in, not the full system.
- **A model check proves the model, not the program.** The link from model to code is argued, not
  proven: the compare-and-swap stands for git's ref update, the flag steps stand for the lock file.
  A code change that drifts from the model would need the model updated, and the check does not
  notice on its own.
- **The property tests cover the strings they generate.** Hypothesis checks a large, adversarial
  space, but not every possible byte sequence, and the CrossHair contracts prove nothing about the
  regex rules.
- **The monitors read the logs, not the system.** A violation that leaves no log row is invisible to
  them, and several gaps are known: the audit log does not witness the switch itself, the completion
  gate does not record which text it judged, and the auth reset leaves no trace. Each gap is recorded
  with a proposed fix.
- **The counterpoint layer is not done.** The checker is written and calibrated, but the Z3 solver
  and its proof harness are in progress, and nothing above claims a completed proof for generated
  music.
