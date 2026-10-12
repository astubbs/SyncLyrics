"""
Lyrics Flow - the whole-song sheet behind the "Lyrics Flow" display mode.

The page renders every line of the song as one sheet and glides it so the current line stays at a
fixed spot. The server still decides which line is current (lyrics._find_current_lyric_index, with
its latency offsets and intro/outro handling); this module only shapes that decision for the page:

- sheet_rows():    the song's lines plus a leading "Intro" row and a trailing "End" row
- sheet_id():      a short content hash, so the page re-fetches the sheet only when it changes
                   (the server replaces lyrics mid-song: placeholder -> fetched, provider switches)
- row_for_index(): maps the server's line index (including -1/-2/-3) onto a sheet row
- flow_fragment(): the `flow` object added to /lyrics when the page asks for it

Pure functions with no app imports, so scripts/test_lyrics_flow.py runs with the standard library.
"""
import hashlib
import json

LEAD_TEXT = "Intro"
TRAIL_TEXT = "End"
EMPTY_LINE_TEXT = "♪"  # same substitution as the six-line window in lyrics.py

# Single-line lyric lists that are placeholders, not songs - same list as lyrics.py / server.py
SEARCHING_TEXT = "searching lyrics..."
INSTRUMENTAL_TEXTS = {"instrumental", "music only", "no lyrics", "non-lyrical", "♪", "♫", "♬",
                      "(instrumental)", "[instrumental]"}


def sheet_rows(lines):
    """Rows for the page, or None when there is no sheet to show (no lyrics or a placeholder)."""
    if not lines:
        return None
    if len(lines) == 1:
        text = (lines[0][1] or "").lower().strip()
        if text == SEARCHING_TEXT or text in INSTRUMENTAL_TEXTS:
            return None
    return [LEAD_TEXT] + [(text or EMPTY_LINE_TEXT) for _, text in lines] + [TRAIL_TEXT]


def sheet_id(lines):
    """Short hash of the timed lines; identical lyrics re-saved keep the same id."""
    payload = json.dumps([[time, text or EMPTY_LINE_TEXT] for time, text in lines], ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def row_for_index(index, line_count):
    """Sheet row for a lyrics index: -2 (intro) and -1 -> leading row, -3 (outro) -> trailing row."""
    if index == -3:
        return line_count + 1
    if 0 <= index < line_count:
        return index + 1
    return 0


def flow_fragment(lines, index, known_sheet_id):
    """The `flow` field for /lyrics: sheet id and row always, the rows only when the page lacks them."""
    rows = sheet_rows(lines)
    if rows is None:
        return {"sheet_id": None, "row": None}
    current_id = sheet_id(lines)
    fragment = {"sheet_id": current_id, "row": row_for_index(index, len(lines))}
    if known_sheet_id != current_id:
        fragment["sheet"] = rows
    return fragment
