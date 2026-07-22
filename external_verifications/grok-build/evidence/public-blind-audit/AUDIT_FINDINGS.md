# Public blind audit — findings (summary)

The blind review found **strong** package design in identity pinning, safety boundaries (no product execution), classification intent, and evidence structure **at a conceptual level**.

Material gaps for **blind executability** included:

| Area | Finding |
|------|---------|
| Package identity | Weaver Forge instruction revision not pinned to an immutable release tag |
| Acquisition | No exact Weaver Forge clone + tag/checkout block with copyable commands |
| Variables | Host paths and pins not assigned through a single copyable command sequence |
| Docker | No one complete `docker run` with platform, network, mounts, env, and working directory |
| Bootstrap | DotSlash/protoc steps incomplete; LF-normalized writable `bin/protoc` descriptor procedure not exact |
| Environment | `RUSTUP_HOME` guidance could encourage unsafe empty override |
| Logging | stdout/stderr and exit-code capture filenames and semantics not exact |
| Target hygiene | Empty `CARGO_TARGET_DIR` proof commands not exact |
| Templates | Mostly skeletal placeholders |
| Classification | Precedence ordering incomplete |
| Discoverability | Weak root-level pointer to the Witness package |
| Submission | Run ID format, checksum manifest, correction/immutability policy incomplete |
| Secrets | Pre-submission review procedure incomplete |

Verdict at intake: **NOT READY** for blind execution (documentation-only review).
