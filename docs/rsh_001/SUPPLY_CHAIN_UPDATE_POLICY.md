# Supply-Chain Update Policy

1. External GitHub Actions must be pinned to immutable full 40-character commit SHAs.
2. A human-readable release or major-version comment may accompany each SHA pin.
3. Dependabot may propose GitHub Actions updates on the configured cadence.
4. Every update requires human review before merge; no RSH-001 configuration enables auto-merge.
5. Major-version changes require explicit compatibility review.
6. CI PASS does not change Weaver authority or evidence status.
7. Action update PRs do not automatically modify canonical Weaver claims.
8. Security hardening must preserve existing claim ceilings unless separately reviewed.

Reviewers must confirm that the proposed SHA belongs to the intended upstream release,
inspect release notes and changed permissions/behavior, run repository validation, and
retain the immutable pin after approval.
