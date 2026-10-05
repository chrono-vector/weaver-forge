"""Dedicated Local Software Ed25519 Custody Helper v0.

Implements the frozen D1-R1 profile (design commit
73942f18b5089c48795039d2fe8f24bf01b0c2f7): one generator call, encrypted
PKCS#8 PEM custody in a fixed protected directory, two fresh-process public
derivations against the protected candidate, fixed restore-v0 checks,
no-argument abandon, and a pre-PREPARE display only. It exposes no signing
API, no arbitrary-message signing, no Admission action, and no identity,
role, authorization, or trust semantics. ACLs do not defeat same-user
compromise. Real key generation requires separate Human authorization.
"""

from __future__ import annotations
