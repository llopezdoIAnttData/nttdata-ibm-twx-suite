"""NTTDATA terminal banner — ASCII art logo + suite info."""

import re
import sys

# ── ANSI ─────────────────────────────────────────────────────────────────────
_RS  = "\033[0m"
_BD  = "\033[1m"
_DM  = "\033[2m"

def _c(n: int) -> str:
    return f"\033[38;5;{n}m"

_BLUE   = _c(27)   # bright blue — borders & Shonai mark
_LBLUE  = _c(81)   # light cyan-blue — NTT DATA lettering (muy visible)
_WHITE  = _c(255)  # near-white
_SILVER = _c(252)  # secondary info
_AMBER  = _c(214)  # version highlight
_TEAL   = _c(43)   # commands


# ── Shonai mark  (all rows exactly 14 visible chars) ─────────────────────────
#
#  Official NTT DATA Shonai mark:
#    ●              ← small circle at ~10-o'clock
#    ▄██████▄       ← solid top arc
#   ██      ██      ← outer ring (hollow center = terminal background)
#   ██      ██
#   ██      ██
#    ▀██████▀       ← solid bottom arc
#                   (blank — aligns with last NTT DATA letter row)
#
_SYM_W = 14   # every row must be exactly this many visible chars

_SYM = [
    "  ●           ",  # 14: 2+●+11
    "  ▄██████▄    ",  # 14: 2+▄+6+▄+4
    " ██      ██   ",  # 14: 1+2+6+2+3
    " ██      ██   ",  # 14: same
    " ██      ██   ",  # 14: same
    "  ▀██████▀    ",  # 14: 2+▀+6+▀+4
    "              ",  # 14: blank — aligns with last NTT DATA row
]

# Verify all rows are the correct width at import time (strips ANSI just in case)
assert all(len(re.sub(r"\033\[[0-9;]*m", "", r)) == _SYM_W for r in _SYM), \
    "BUG: _SYM rows must all be exactly _SYM_W visible chars"


# ── "NTT DATA" block letters  (7 rows; row 0 blank aligns with ● dot) ────────
_TXT = [
    "",   # blank — aligns with ● dot row
    "███╗  ██╗ ████████╗████████╗  ██████╗  █████╗ ████████╗ █████╗ ",
    "████╗ ██║ ╚══██╔══╝╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗",
    "██╔████╗██║   ██║      ██║    ██║  ██║███████║   ██║   ███████║ ",
    "██║╚═██╗██║   ██║      ██║    ██║  ██║██╔══██║   ██║   ██╔══██║ ",
    "██║  ╚████║   ██║      ██║    ██████╔╝██║  ██║   ██║   ██║  ██║ ",
    "╚═╝   ╚═══╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝",
]

_GAP = "  "   # gap between Shonai symbol and NTT DATA text


# ── helpers ───────────────────────────────────────────────────────────────────

def _vlen(s: str) -> int:
    """Visible char count — strips ANSI escape sequences."""
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _row(content: str, inner_w: int, indent: int = 2) -> str:
    """Build a  ║  content  ║  line padded to inner_w."""
    pad = inner_w - _vlen(content) - indent
    return (
        f"{_BLUE}{_BD}║{_RS}"
        f"{' ' * indent}{content}{' ' * max(pad, 0)}"
        f"{_BLUE}{_BD}║{_RS}"
    )


# ── main banner ───────────────────────────────────────────────────────────────

def get_banner(
    version: str = "1.0.0",
    suite: str = "IBM TWX Reverse Engineering Suite",
) -> str:

    # inner_w = widest logo row + 4 (2 left indent + 2 right margin)
    inner_w = max(_vlen(s) + len(_GAP) + _vlen(t) for s, t in zip(_SYM, _TXT)) + 4

    top    = f"{_BLUE}{_BD}╔{'═' * inner_w}╗{_RS}"
    bottom = f"{_BLUE}{_BD}╚{'═' * inner_w}╝{_RS}"
    sep    = f"{_BLUE}{_BD}╠{'═' * inner_w}╣{_RS}"
    blank  = f"{_BLUE}{_BD}║{' ' * inner_w}║{_RS}"

    lines = ["", top, blank]

    # ── logo rows ─────────────────────────────────────────────────────────────
    for sym, txt in zip(_SYM, _TXT):
        pad = inner_w - _SYM_W - len(_GAP) - _vlen(txt) - 2
        lines.append(
            f"{_BLUE}{_BD}║{_RS}  "
            f"{_BLUE}{_BD}{sym}{_RS}"
            f"{_GAP}"
            f"{_LBLUE}{_BD}{txt}{_RS}"
            f"{' ' * max(pad, 0)}"
            f"{_BLUE}{_BD}║{_RS}"
        )

    lines += [blank, sep]

    # ── suite  +  version ─────────────────────────────────────────────────────
    lines.append(_row(
        f"{_WHITE}{_BD}{suite}{_RS}  "
        f"{_AMBER}{_BD}v{version}{_RS}  "
        f"{_SILVER}·  IBM BPM  ·  IBM BAW  ·  CP4BA{_RS}",
        inner_w,
    ))

    # ── corporate  +  author ──────────────────────────────────────────────────
    lines.append(_row(
        f"{_SILVER}Corporate: {_WHITE}{_BD}NTT DATA{_RS}  "
        f"{_SILVER}·  Author: {_WHITE}llopezdo@emeal.nttdata.com{_RS}",
        inner_w,
    ))

    lines += [blank, bottom, ""]
    return "\n".join(lines)


def print_banner(
    version: str = "1.0.0",
    suite: str = "IBM TWX Reverse Engineering Suite",
) -> None:
    print(get_banner(version, suite), file=sys.stderr)


# ── Compact markdown header for VS Code Copilot Chat ─────────────────────────
COPILOT_HEADER = (
    "```\n"
    "  ●\n"
    "   ╭──────╮   ███╗  ██╗ ████████╗████████╗  ██████╗  █████╗ ████████╗ █████╗\n"
    "  ╱ ╭────╮ ╲  ████╗ ██║ ╚══██╔══╝╚══██╔══╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗\n"
    " │  │    │  │ ██╔████╗██║   ██║      ██║    ██║  ██║███████║   ██║   ███████║\n"
    " │  ╰────╯  │ ██║╚═██╗██║   ██║      ██║    ██║  ██║██╔══██║   ██║   ██╔══██║\n"
    "  ╲         ╱  ██║  ╚████║   ██║      ██║    ██████╔╝██║  ██║   ██║   ██║  ██║\n"
    "   ╰──────╯   ╚═╝   ╚═══╝   ╚═╝      ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝\n"
    "  IBM TWX Reverse Engineering Suite  v1.0.0"
    "  ·  NTT DATA  ·  Author: llopezdo@emeal.nttdata.com\n"
    "```\n"
)
