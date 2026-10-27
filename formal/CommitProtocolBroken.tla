-------------------------- MODULE CommitProtocolBroken --------------------------
\* FV-1 layer 2 (a): the commit protocol with the CAS REMOVED.
\*
\* This is the counterfactual model: the drift check (snap[l] = ver) and the commit
\* are two SEPARATE steps with no atomic guard, and the commit writes the FULL stale
\* snapshot back. This is the bug lane_commit.py closes (cards t_50a45d94 and
\* t_0877703c): a lane built its index from an old HEAD and a commit landing while
\* it holds that index reverts the other lane's files.
\*
\* Run this next to CommitProtocol.tla to prove the two safety properties are not
\*    vacuous: TLC finds a reversion counterexample here that the faithful model rejects.
EXTENDS Integers, TLC

CONSTANT MaxV
ASSUME MaxV >= 1

Files == {"a", "b"}
Lanes == {"A", "B"}
own == [l \in Lanes |-> IF l = "A" THEN "a" ELSE "b"]

VARIABLES ver, snap, seen, driftOK

vars == <<ver, snap, seen, driftOK>>

TypeOK ==
    /\ ver     \in [Files -> 0..MaxV]
    /\ snap    \in [Lanes -> [Files -> 0..MaxV]]
    /\ seen    \in [Files -> 0..MaxV]
    /\ driftOK \in [Lanes -> BOOLEAN]

Init ==
    /\ ver  = [f \in Files |-> 0]
    /\ snap = [l \in Lanes |-> [f \in Files |-> 0]]
    /\ seen = ver
    /\ driftOK = [l \in Lanes |-> FALSE]

Red(h) == h["a"] = 1 /\ h["b"] = 1

Max2(x, y) == IF x >= y THEN x ELSE y

Prep(l) ==
    /\ snap' = [snap EXCEPT ![l] = ver]
    /\ driftOK' = [driftOK EXCEPT ![l] = FALSE]
    /\ UNCHANGED <<ver, seen>>

\* The drift check, alone (not atomic with the commit).
CheckDrift(l) ==
    /\ driftOK[l] = FALSE
    /\ snap[l] = ver
    /\ driftOK' = [driftOK EXCEPT ![l] = TRUE]
    /\ UNCHANGED <<ver, snap, seen>>

\* The commit: writes the FULL stale snapshot plus the lane's own bump, with no CAS.
Land(l) ==
    /\ driftOK[l] = TRUE
    /\ snap[l][own[l]] < MaxV
    /\ ~Red([snap[l] EXCEPT ![own[l]] = @ + 1])
    /\ ver'  = [snap[l] EXCEPT ![own[l]] = @ + 1]
    /\ seen' = [f \in Files |-> Max2(seen[f], ver'[f])]
    /\ driftOK' = [driftOK EXCEPT ![l] = FALSE]
    /\ UNCHANGED snap

Next == \E l \in Lanes : Prep(l) \/ CheckDrift(l) \/ Land(l)

Spec == Init /\ [][Next]_vars

NoRevert == ver = seen
NoRedHead == ~Red(ver)
=============================================================================
