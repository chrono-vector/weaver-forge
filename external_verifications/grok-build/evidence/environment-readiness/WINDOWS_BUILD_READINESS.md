# Windows compiler / SDK readiness (read-only)

Date: 2026-07-17
Scope: discovery only; no installer launched.

## Visual Studio / Build Tools

| Check | Result |
|-------|--------|
| vswhere.exe | **MISSING** (default Installer paths) |
| `C:\Program Files\Microsoft Visual Studio` | **not present** |
| `C:\Program Files (x86)\Microsoft Visual Studio` | **not present** |
| `C:\Program Files (x86)\Microsoft Visual C++ Build Tools` | **not present** |
| `C:\BuildTools` | **not present** |
| `cl` on PATH | **unavailable** |
| `where.exe cl` | exit 1 (not found) |

## Windows SDK

| Check | Result |
|-------|--------|
| `C:\Program Files (x86)\Windows Kits\10` | **not present** |
| `C:\Program Files\Windows Kits\10` | **not present** |
| SDK Include/bin version folders | n/a |

## Compiler-related environment variables

Recorded by **name** and set/unset only (no values dumped):

All of INCLUDE, LIB, LIBPATH, VCINSTALLDIR, VSINSTALLDIR, WindowsSdkDir, WindowsSDKVersion, VCToolsInstallDir, VSCMD_ARG_TGT_ARCH: **unset** in process/user/machine for this inspection.

## Conclusion

Microsoft Visual C++ Build Tools and Windows SDK are **not visible** on this host.
For a Rust Windows source build that needs a native linker/C toolchain (common for crates with `cc`/`windows`/`ring`/etc.), this is a **blocker** independent of Rust presence.

This does **not** prove a source build is impossible forever; it proves the **current** host is not ready.
