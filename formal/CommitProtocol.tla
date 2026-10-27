------------------------------ MODULE CommitProtocol ------------------------------
\* FV-1 layer 2 (a): the lane_commit.py commit protocol.
\*
\* Model of HEAD as per-file versions, each lane's private-index snapshot, and the
\* commit as an atomic compare-and-swap (the CAS is git's ref update with an
\* expected old value; lane_commit.py's drift check is the fast path, git's ref
\* lock is the atomic guard). This is the FAITHFUL model of the current code.
\*
\* Safety properties checked:
\*   NoRevert  - no commit lowers any file's version (no commit reverts another lane's files)
\*   NoRedHead - HEAD is never red after any commit
\*
\* The gate is modeled as a predicate Red(h) on the tree: a commit is only enabled
\* when the tree it would produce is green, and the CAS makes that produced tree
\*    exactly the tree that becomes HEAD.
EXTENDS Integers, TLC

CONSTANT MaxV
ASSUME MaxV >= 1

Files == {"a", "b"}
Lanes == {"A", "B"}
own == [l \in Lanes |-> IF l = "A" THEN "a" ELSE "b"]

VARIABLES ver, snap, seen

vars == <<ver, snap, seen>>

TypeOK ==
    /\ ver  \in [Files -> 0..MaxV]
    /\ snap \in [Lanes -> [Files -> 0..MaxV]]
    /\ seen \in [Files -> 0..MaxV]

Init ==
    /\ ver  = [f \in Files |-> 0]
    /\ snap = [l \in Lanes |-> [f \in Files |-> 0]]
    /\ seen = ver

\* Red: the only tree a gate refuses is both files at version 1. This is the
\* "each lane's change is green alone, red together" shape that forces a re-gate.
Red(h) == h["a"] = 1 /\ h["b"] = 1

Bumped(l) == [ver EXCEPT ![own[l]] = @ + 1]

Max2(x, y) == IF x >= y THEN x ELSE y

\* A lane reads HEAD into its private-index snapshot (prepare()).
Prep(l) ==
    /\ snap' = [snap EXCEPT ![l] = ver]
    /\ UNCHANGED <<ver, seen>>

\* A lane commits: atomic CAS on HEAD, gate on the exact resulting tree, and only
\* its OWN file's version changes. The CAS (snap[l] = ver) is what stops a stale
\* snapshot from reverting a file another lane just bumped.
Commit(l) ==
    /\ snap[l] = ver
    /\ ver[own[l]] < MaxV
    /\ ~Red(Bumped(l))
    /\ ver'  = [ver EXCEPT ![own[l]] = @ + 1]
    /\ seen' = [f \in Files |-> Max2(seen[f], ver'[f])]
    /\ UNCHANGED snap

Next == \E l \in Lanes : Prep(l) \/ Commit(l)

Spec == Init /\ [][Next]_vars

\* seen tracks the highest version each file ever reached; ver = seen iff the
\* version has never moved backwards (no reversion).
NoRevert == ver = seen
NoRedHead == ~Red(ver)
=============================================================================
