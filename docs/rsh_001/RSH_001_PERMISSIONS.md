# RSH-001 Permissions and Concurrency

`validate-receipts.yml` declares only:

```yaml
permissions:
  contents: read
```

The job checks out repository history and reads receipt files. It does not write contents,
checks, pull requests, issues, packages, security events, or identity tokens. No write
permission is granted. Checkout credential persistence is disabled.

The concurrency group is the workflow name plus the Git ref, with
`cancel-in-progress: true`. This cancels an older validation run only when a newer run for
the same workflow and ref exists. The job has no publishing or state-mutating step, so
cancellation cannot interrupt a repository update or partial release.
