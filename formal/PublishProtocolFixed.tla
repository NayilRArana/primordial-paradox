----------------------------- MODULE PublishProtocolFixed -----------------------------
\* FV-1b: the publish_on_commit.py protocol, after the lost-wakeup fix.
\*
\* The fix (manager/tools/publish_on_commit.py run()): when take_lock() fails, the
\* loser now writes the AGAIN flag AND THEN retries take_lock() once. If the retry
\* wins (the holder released in the window), the loser becomes the holder and runs
\* the publish loop. If the retry loses, the still-alive holder sees the AGAIN flag
\* in its finally step and respawns. Either way the loser never leaves an AGAIN flag
\* with no one able to observe it.
\*
\* Modeled faithfully from the fixed run():
\*   - a commit's post-commit hook spawns a hidden --run publisher (Arrive)
\*   - take_lock(): acquire exclusively, or fail and write the AGAIN flag (SetAgain)
\*   - the loser retries take_lock() once (Retry): win -> holder (Work), lose -> leave
\*   - the holder publishes (Work), then finally removes the lock (Release) and checks
\*     AGAIN (Check), respawning if set
\*
\* Properties checked:
\*   NoTwo       - never two publishers inside the critical section
\*   Termination - every game commit is eventually published or reported refused
\*                 (toArrive = {} /\ pending = {})
EXTENDS Integers, TLC, FiniteSets

CONSTANTS Commits, Publishers
ASSUME /\ Commits # {}
       /\ Publishers # {}

VARIABLES holder, again, pending, published, refused, toArrive, pc

vars == <<holder, again, pending, published, refused, toArrive, pc>>

TypeOK ==
    /\ holder \in {"none"} \cup Publishers
    /\ again \in BOOLEAN
    /\ pending   \subseteq Commits
    /\ published \subseteq Commits
    /\ refused   \subseteq Commits
    /\ toArrive  \subseteq Commits
    /\ pending \cap published = {}
    /\ pending \cap refused   = {}
    /\ published \cap refused = {}
    /\ toArrive \cap (pending \cup published \cup refused) = {}
    /\ pc \in [Publishers -> {"idle","try","setagain","retry","work","release","check","done"}]

Init ==
    /\ holder = "none"
    /\ again = FALSE
    /\ pending = {}
    /\ published = {}
    /\ refused = {}
    /\ toArrive = Commits
    /\ pc = [p \in Publishers |-> "idle"]

\* The post-commit hook fires for a commit: it enters the pending set and spawns a
\* publisher (an idle one becomes "try").
Arrive ==
    /\ toArrive # {}
    /\ \E c \in toArrive, p \in Publishers :
          /\ pc[p] = "idle"
          /\ pending'  = pending \cup {c}
          /\ toArrive' = toArrive \ {c}
          /\ pc' = [pc EXCEPT ![p] = "try"]
          /\ UNCHANGED <<holder, again, published, refused>>

Try(p) ==
    /\ pc[p] = "try"
    /\ IF holder = "none"
         THEN /\ holder' = p
              /\ pc' = [pc EXCEPT ![p] = "work"]
         ELSE /\ UNCHANGED holder
              /\ pc' = [pc EXCEPT ![p] = "setagain"]
    /\ UNCHANGED <<again, pending, published, refused, toArrive>>

\* take_lock() returned False: write the AGAIN flag, then move on to the retry.
SetAgain(p) ==
    /\ pc[p] = "setagain"
    /\ again' = TRUE
    /\ pc' = [pc EXCEPT ![p] = "retry"]
    /\ UNCHANGED <<holder, pending, published, refused, toArrive>>

\* The retry: the loser tries take_lock() once more. If it wins it becomes the holder
\* and clears the AGAIN flag it just wrote (the loop starts by removing AGAIN); if it
\* loses it leaves, and the still-alive holder observes AGAIN in its Check step.
Retry(p) ==
    /\ pc[p] = "retry"
    /\ IF holder = "none"
         THEN /\ holder' = p
              /\ again' = FALSE
              /\ pc' = [pc EXCEPT ![p] = "work"]
         ELSE /\ UNCHANGED holder
              /\ again' = again
              /\ pc' = [pc EXCEPT ![p] = "done"]
    /\ UNCHANGED <<pending, published, refused, toArrive>>

\* publish_once(): resolves every pending commit, either published or reported refused.
Work(p) ==
    /\ pc[p] = "work"
    /\ \/ /\ published' = published \cup pending
          /\ pending'   = {}
          /\ refused'   = refused
       \/ /\ refused'   = refused \cup pending
          /\ pending'   = {}
          /\ published' = published
    /\ pc' = [pc EXCEPT ![p] = "release"]
    /\ UNCHANGED <<holder, again, toArrive>>

\* finally: remove the lock.
Release(p) ==
    /\ pc[p] = "release"
    /\ holder' = "none"
    /\ pc' = [pc EXCEPT ![p] = "check"]
    /\ UNCHANGED <<again, pending, published, refused, toArrive>>

\* ... then check the AGAIN flag: respawn (go round again) or leave.
Check(p) ==
    /\ pc[p] = "check"
    /\ IF again
         THEN /\ again' = FALSE
              /\ pc' = [pc EXCEPT ![p] = "try"]
         ELSE /\ again' = again
              /\ pc' = [pc EXCEPT ![p] = "done"]
    /\ UNCHANGED <<holder, pending, published, refused, toArrive>>

PublisherNext(p) == Try(p) \/ SetAgain(p) \/ Retry(p) \/ Work(p) \/ Release(p) \/ Check(p)

Next == Arrive \/ (\E p \in Publishers : PublisherNext(p))

Fairness ==
    /\ WF_vars(Arrive)
    /\ \A p \in Publishers : WF_vars(PublisherNext(p))

Spec == Init /\ [][Next]_vars /\ Fairness

\* Never two publishers holding the lock (inside the critical section: work or the
\* release step still holding it). "check" is excluded: by then the lock is gone.
NoTwo ==
    ~ \E p, q \in Publishers :
          /\ p # q
          /\ pc[p] \in {"work", "release"}
          /\ pc[q] \in {"work", "release"}

\* Every game commit is eventually published or reported refused.
Termination == <>(toArrive = {} /\ pending = {})
=============================================================================
