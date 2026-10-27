# Commit discipline: a lane commits a coherent set, never code alone

For card t_26dbea7d (GATE-HEAD-GREEN), 2026-10-26, after hold-to-walk could not be committed for two
days. None of that was the walking lane's fault.

## The rule

One `lane_commit` carries every path the change needs in order to be TRUE in a fresh checkout of the
commit it lands in: the code, the project entry (`.yyp` and any `.yy` that lists it), the data the code
reads, the provenance row, the cleanroom row, and the test that measures it. If a path is needed to make
the commit pass in a worktree of HEAD plus this commit, it belongs in this commit.

## Why

On 2026-10-26 committed HEAD was 8 failed, 28 passed in `tests/test_project.py` and
`tests/test_no_network_in_build.py`, on commits days old. The bridge and live talk work shipped its GML
and left the rest of itself behind: two untracked event files its own `.yy` declared, two untracked data
files, the provenance row, four cleanroom rows, the regenerated `.yyp`, and the test exemption for the
module's two loopback `http_request` calls. Every lane after it inherited a red gate, because the gate
starts from HEAD.

## Before you commit

1. Run `python tools/check_project.py` and the no-network test file.
2. Run `python tools/gen_project.py`; commit the regenerated `.yyp` with the change that caused it.
3. `git status`: any untracked file your module names or reads goes in this commit.
4. A new module needs its `knowledge/PROVENANCE.md` and `knowledge/CLEANROOM-REVIEW.md` rows here too.
5. Never weaken a test to pass. Either the behaviour is right and the test's own documented exemption is
   added with its reason, or the code changes.

## The trap

`guard/head_green.py` (check C29 in `run_checks.py`) measures HEAD's two test files in a throwaway
worktree, once per commit, and fails while HEAD is red.
