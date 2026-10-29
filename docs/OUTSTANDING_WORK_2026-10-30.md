# AgentWitness / AgentCheck — central outstanding work

**Canonical source:** https://github.com/Parris-Tech-Services/AgentCheck (the older `joshualparris/AgentCheck` URL redirects here). **Branch:** `main`. **Review job:** RepoClean `GRA-006`. **Audit date:** 30 October 2026. **Scope:** [PR #5](https://github.com/Parris-Tech-Services/AgentCheck/pull/5), `fix/s02-secure-new-key-permissions` into `main`, **three changed files only**; not a full repository review.

**Evidence:** Greptile completed runs [`36488518`](https://app.greptile.com/parris-tech-services/github/Parris-Tech-Services/agentcheck/-/pull/5) (initial reviewed head `00aca64b1f1b742c0b8fdcfd82d5a0d8c4ec2d79`) and **`36489466`** (same current PR head `ce7888c5e3435a45902e77e351375ef9cf44c361`, completed 29 Oct 2026 08:52:30 UTC, confidence 5/5, no new inline findings). The first review published **1 P1 + 2 P2** comments, still stored as unaddressed, but all three have *apparent code-level mitigations* in the newer PR head. They are not automatically fixed in `main`, nor marked resolved by the reviewer. Exact-head [CI run 40844915488](https://github.com/Parris-Tech-Services/AgentCheck/actions/runs/40844915488) and [run 40844907462](https://github.com/Parris-Tech-Services/AgentCheck/actions/runs/40844907462) both report SUCCESS for the narrow S02 signing-key workflow; these do **not** establish full-suite, Windows ACL, legacy-key, or deployment acceptance.

**Task-register discovery:** Root `AGENTS.md`, `TODO.md`, `WORK_CHECKPOINT.md`, `TASKS.md`, and general outstanding-work docs were absent from the default-branch tree. `podcasttodo.md` is a separate, unrelated podcast decision tracker and is left unchanged. This file is the new central engineering handoff; existing README roadmap, podcast checkbox states and other files are preserved. Do not assign another ID for any of the same review comments.

## Prioritised numbered tasks

- [x] **AW-GR-001** [REVIEW ONLY] Reconcile the completed same-head Greptile review without a duplicate trigger.
  - **Start/triage:** Inspect [PR #5](https://github.com/Parris-Tech-Services/AgentCheck/pull/5) and Greptile runs `36488518` / `36489466`; compare GitHub head `ce7888c5e3435a45902e77e351375ef9cf44c361`.
  - **Evidence:** The three older review comments are individually mapped below; newer review reports no blocking new comment. Provider addressed flags remain false.
  - **Dependencies:** None; read README, `codingprinciples.md`, and check branch ownership before changing source.
  - **Proposed minimal fix:** No code change in this documentation-only review.
  - **Acceptance/closure:** Completed review IDs, exact head and CI evidence recorded here. **This checked item is not a claim that any repair is merged.**

- [ ] **AW-GR-002** [P1 / SECURITY, MAIN BRANCH] Stop newly created unencrypted private signing keys inheriting permissive filesystem modes.
  - **Start/triage:** On `main`, inspect `src/agentwitness/crypto.py::_ensure_keys`: `open(private_key_path, "wb")` inherits umask and may create mode `0644`. Compare PR #5 head where `os.open(O_EXCL, 0o600)` and a private directory are used. Check source branch claims before edits.
  - **Evidence:** Independently inspected current `main` and PR head; this is a source-level exposure **possibility**, not evidence that any real installed key is world-readable. [PR #5](https://github.com/Parris-Tech-Services/AgentCheck/pull/5); Greptile latest run `36489466` reviews the proposed mitigation.
  - **Dependencies:** `AW-GR-003`–`005` validation and `AW-GR-007` release gate; never copy, print, upload, or rotate real private PEMs as part of automated triage.
  - **Proposed minimal fix:** Reconcile and merge the already-authored exclusive `0600` creation path after acceptance; do not create a competing fix branch or overwrite existing keys.
  - **Acceptance/closure:** POSIX umask 000/022/077 tests, signing/verification and collision negatives, exact-head CI, safe merge to `main`, post-merge SHA and CI proof. Keep OPEN until default branch actually uses the fix.

- [ ] **AW-GR-003** [P1 / DATA INTEGRITY] Confirm incomplete public/private keypairs cannot create unverifiable signed receipts.
  - **Start/triage:** Inspect `src/agentwitness/crypto.py::_ensure_keys` on PR #5 head and `tests/test_secure_key_permissions.py::test_public_key_only_collision_fails_before_private_creation`, `test_mismatched_existing_private_and_public_are_rejected`; reproduce repeated constructor failure with synthetic keys only.
  - **Evidence:** [Original Greptile P1 comment](https://github.com/Parris-Tech-Services/AgentCheck/pull/5#discussion_r315858274), run `36488518`; initial head could save `private.pem` before refusing an existing public key. New head preflights public-only state and compares keypairs before signing; source mitigation visible, not yet merged.
  - **Dependencies:** `AW-GR-002`, `AW-GR-007`; coordinate with PR #5 owner and avoid real ledger mutations.
  - **Proposed minimal fix:** Preserve preflight refusal and keypair-consistency validation; strengthen repeat-constructor, crash/concurrency, and ledger append/verify negative tests if needed.
  - **Acceptance/closure:** Both synthetic collision paths fail without writing an inconsistent usable keypair, existing valid pairs continue signing, focused/full CI evidence, reviewed source merge and provider comment addressed with proof.

- [ ] **AW-GR-004** [P2 / KEY LOSS] Verify failure cleanup never unlinks a replacement signing key.
  - **Start/triage:** Inspect `src/agentwitness/crypto.py::_ensure_keys` near the private-key `fdopen/write/fsync` sequence and `tests/test_secure_key_permissions.py::test_write_failure_cannot_unlink_replaced_key` on PR #5 head.
  - **Evidence:** [Original Greptile P2 comment](https://github.com/Parris-Tech-Services/AgentCheck/pull/5#discussion_r315858273), run `36488518`; initial exception cleanup could unlink a different file after replacement. Current head deliberately leaves the failed path intact and has a synthetic replacement regression. No destructive reproduction on live keys.
  - **Dependencies:** `AW-GR-002`, `AW-GR-003`; preserve original signing material and check competing source claims.
  - **Proposed minimal fix:** Retain fail-closed non-unlink semantics; if a more robust atomic creation design is chosen, prove ownership and recovery before any deletion.
  - **Acceptance/closure:** Failure injection proves replacement bytes survive, no existing keys are overwritten, focused and full CI pass on final head, Greptile comment addressed only after verified merge.

- [ ] **AW-GR-005** [P2 / PORTABILITY] Verify symlink tests do not fail spuriously on unprivileged Windows.
  - **Start/triage:** Inspect `tests/test_secure_key_permissions.py` on PR #5 head: three symlink fixtures are now guarded by `@pytest.mark.skipif(os.name != "posix")`; check Windows runner behaviour separately.
  - **Evidence:** [Original Greptile P2 comment](https://github.com/Parris-Tech-Services/AgentCheck/pull/5#discussion_r315858275), run `36488518`; initial `hasattr(os, "symlink")` check did not imply permission. New head avoids the affected Windows fixture path.
  - **Dependencies:** `AW-GR-007`; Windows filesystem ACL behaviour is not covered by POSIX tests.
  - **Proposed minimal fix:** Keep OS/capability-specific skip and add Windows-specific safe key-ACL tests only on an authorised runner.
  - **Acceptance/closure:** POSIX tests run, Windows collection/skip succeeds on a real Windows runner, no false passing claim for ACL enforcement, reviewed merge and addressed comment.

- [ ] **AW-GR-006** [TRIAGE / POTENTIAL P1 PRIVACY] Assess pre-existing signing keys and Windows ACLs without exposing material.
  - **Start/triage:** Inspect the code path for loading existing PEMs, the user-approved host inventory and key-directory permissions **locally**; record mode/ACL metadata only, never secret contents. Verify actual installation and access controls before severity assignment.
  - **Evidence:** [PR #5 description](https://github.com/Parris-Tech-Services/AgentCheck/pull/5) explicitly excludes remediation of old keys and Windows ACLs. No current real-world exposure or compromise is verified.
  - **Dependencies:** Human owner approval for host-level audit/rotation; `AW-GR-002` before new key generation; avoid overwriting existing keypairs or invalidating receipts without a signed recovery plan.
  - **Proposed minimal fix:** If a real overly permissive key is found, use a separately approved key-permission/rotation and ledger-trust migration procedure with backup/recovery; otherwise document no issue.
  - **Acceptance/closure:** Authorised host-specific mode/ACL evidence, tested sign/verify and legacy receipt compatibility, rotation/recovery test if needed, zero PEM disclosure, reviewer approval.

- [ ] **AW-GR-007** [P1 / RELEASE GATE] Reconcile PR #5, verify broad checks and resolve comments after evidence.
  - **Start/triage:** Re-fetch [PR #5](https://github.com/Parris-Tech-Services/AgentCheck/pull/5), check head and base SHAs, status checks, three old Greptile comments and branch ownership; confirm the two exact-head narrow S02 CI runs, then run the project's full test/contract gates.
  - **Evidence:** Greptile latest completed `36489466` says safe to merge but did **not** execute tests; the three older comments are still provider-UNADDRESSED. [Narrow S02 CI](https://github.com/Parris-Tech-Services/AgentCheck/actions/runs/40844915488) SUCCESS on `ce7888c5`, not proof of full coverage.
  - **Dependencies:** `AW-GR-002`–`005` source validation, `AW-GR-006` risk disposition and approval where applicable. Do not merge if a trust-root regression is discovered.
  - **Proposed minimal fix:** Reuse PR #5 rather than creating a duplicate review or competing patch; address any reproducible residual defect on the existing branch.
  - **Acceptance/closure:** Focused/full pytest and contract verification with exit logs, Windows checks or explicit platform limitation, independent review resolution, approved merge SHA, post-merge CI and final `main` source verification. Do not claim deployment where none exists.

## Work handoff
**Suggested order:** `AW-GR-003` → `AW-GR-004` → `AW-GR-005` → `AW-GR-002` / `AW-GR-007`; investigate `AW-GR-006` separately with owner approval. **No source fixes, live key inspection, merge or deployment were performed by this audit.**
