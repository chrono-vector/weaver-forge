"""Process entry: <venv>\\Scripts\\python.exe -I <helper-root>\\ed25519_custody_v0\\__main__.py <subcommand>

Under isolated mode the helper root is not on sys.path, so this entry
appends exactly that root at the end of sys.path. Standard library and the
dedicated environment therefore take precedence, and the manifest preflight
verifies every module location before any secret is read.
"""

import os
import sys

if __name__ == "__main__":
    if not __package__:
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.append(_root)
        from ed25519_custody_v0.cli import main
    else:
        from .cli import main
    raise SystemExit(main(sys.argv[1:]))
