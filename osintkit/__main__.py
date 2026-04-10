"""Entry point for python -m osintkit"""
import sys

# CLI shortcuts — intercept before Typer parses argv:
#   osintkit          → osintkit list
#   osintkit <id>     → osintkit open <id>
#   osintkit -v       → osintkit version
_KNOWN_COMMANDS = {
    "new", "list", "refresh", "open", "export",
    "setup", "delete", "version", "update", "tag",
}

if len(sys.argv) == 1:
    # bare `osintkit` → show list
    sys.argv.append("list")
elif len(sys.argv) == 2:
    arg = sys.argv[1]
    if arg in ("-v",):
        sys.argv[1] = "version"
    elif not arg.startswith("-") and arg not in _KNOWN_COMMANDS:
        # `osintkit <id>` → open that profile
        sys.argv = [sys.argv[0], "open", arg]

from osintkit.cli import app
app()
