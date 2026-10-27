# Formal specs

TLA+ specifications for the build and publish machinery behind Primordial Paradox, with the model
checking configs. Each spec models a concurrency protocol and states the safety and liveness
properties TLC checks.

Run a check with the TLA+ Tools release (`tla2tools.jar`) on the classpath:

```sh
java -Xmx256m -cp tla2tools.jar tlc2.TLC -workers 1 -config <spec>.cfg <spec>.tla
```

| spec | models | expected TLC result |
| --- | --- | --- |
| `CommitProtocol` | the commit gate: per-file HEAD versions, private snapshots, the atomic compare-and-swap | no error; NoRevert and NoRedHead hold |
| `CommitProtocolBroken` | the same protocol with the compare-and-swap removed and a full stale snapshot write | NoRevert violated (the reversion the real code prevents) |
| `PublishProtocol` | the publish lock and AGAIN flag, with the release and the flag check as separate steps | Termination violated (the lost wakeup) |
| `PublishProtocolFixed` | the publish protocol after the lost-wakeup fix (write AGAIN, then retry the lock once) | no error; NoTwo and Termination hold |

Properties:

- NoRevert: no commit lowers any file's version, so no commit reverts another agent's files.
- NoRedHead: HEAD is never red after a commit that passed the gate.
- NoTwo: never two publishers inside the critical section at once.
- Termination: every game commit is eventually published or reported refused.

The full account of what these prove, the lost-wakeup bug they found, and the honest limits is in
`../docs/FORMAL-VERIFICATION.md`.
