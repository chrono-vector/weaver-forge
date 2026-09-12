# Network rules

Allowed modes: `NO_NETWORK`, `READ_ONLY_NETWORK`, `LOCAL_FORK_READ_ONLY`, `LOCAL_FORK_BOUNDED_MUTATION` (only if procedure requires).

Forbidden: live mutation, broadcast, real wallet, real private key, real credentials.

IW v1 requires: REAL_WALLET=NO, REAL_PRIVATE_KEY=NO, REAL_CREDENTIAL=NO, LIVE_BROADCAST=NO, LIVE_MUTATION=NO.
