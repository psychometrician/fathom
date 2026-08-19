"""Generate the cases that test fathom's health verb.

    uv run test/generate.py            # writes test/cases/ and manifest.jsonl
    uv run test/check.py               # scores design/probe.py against them

**This is a test suite, not a corpus.** `corpus/README.md` says "real files
only", because toy JSON is hard in ways nobody suffers from. A test suite is the
exact opposite: it should be synthetic and exhaustive, and it belongs in a
different directory with a different rule.

**A parser's test suite asks "did you accept it?" A reporter's asks "did you say
the right thing about it?"** So the manifest records the format fathom should
name and the damage flags it should raise — not accept/reject. The two contracts
genuinely differ: an NDJSON file with one broken line is a *reject* for a parser
and "NDJSON, 2 of 3 records, line 2 unreadable" for fathom.

Adapted from a JSON parser corpus built by another agent on 2026-08-08 and
released CC0. The `llm_trap` cases are its idea and its best one: valid JSON
whose string contents look malformed, which is the only real test of a
report-never-repair policy. Its truncation-ladder and NDJSON cases are here too.
Its other ~1,250 cases — IEEE-754 bit patterns, 100k-deep nesting, SIMD lane
alignment — test the parser layer, which fathom delegates and does not own.
"""
import json
import pathlib
import sys

OUT = pathlib.Path(__file__).parent / "cases"
MAN = []


def emit(rel, data, fmt, flags=(), note="", **extra):
    """fmt is what health() should call it; flags are what it should raise."""
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode())
    MAN.append({"path": rel, "format": fmt, "flags": sorted(flags),
                "note": note, **extra})


# ── valid JSON whose STRING CONTENTS look malformed ──────────────────────────
# Every one must parse, and none may raise a damage flag it has not earned. This
# is the suite that catches over-eager repair, and it already caught one real
# bug: a NaN detector that matched the word "NaN" inside ordinary prose.
TRAPS = [
    ("code_with_trailing_comma", '{"code":"if (x) { return [1,2,]; }"}', "trailing comma inside a string"),
    ("code_with_line_comment", '{"src":"// not a comment, just text"}', "the string starts with //"),
    ("code_with_block_comment", '{"src":"/* still just text */"}', "/* */ inside a string"),
    ("markdown_fence_inside", '{"md":"```json\\n{\\"a\\":1}\\n```"}', "a fenced JSON block inside a string"),
    ("latex_braces", '{"tex":"\\\\begin{align} x &= 1 \\\\end{align}"}', "LaTeX brace groups"),
    ("regex_literal", '{"re":"^\\\\{\\\\d+,\\\\}$"}', "a regex with escaped braces"),
    ("unbalanced_brace_in_string", '{"s":"opening { without closing"}', "unbalanced brace inside a string"),
    ("unbalanced_bracket_in_string", '{"s":"]]] "}', "unbalanced brackets inside a string"),
    ("quotes_in_string", '{"q":"he said \\"hi\\","}', "escaped quotes then a comma, inside the string"),
    ("python_literal_text", '{"note":"the answer is True, not None"}', "True/None as prose"),
    ("nan_word_in_string", '{"note":"NaN and Infinity are not JSON"}', "NaN as prose — the false positive that bit us"),
    ("mongo_text", '{"note":"call ObjectId(\\"x\\") to build one"}', "ObjectId( inside a string"),
    ("single_quotes_in_string", '{"s":"it\'s fine"}', "an apostrophe"),
    ("backtick_in_string", '{"s":"use `npm i` first"}', "backticks"),
    ("url_in_string", '{"u":"https://example.com//double//slash"}', "// inside a URL"),
    ("smart_quotes_in_string", '{"s":"\\u201cquoted\\u201d"}', "smart quotes as content"),
    ("ellipsis_in_string", '{"s":"to be continued ..."}', "a literal ellipsis"),
    ("html_entity_in_string", '{"s":"5 &lt; 6 &amp;&amp; 7 &gt; 6"}', "HTML entities as content"),
    ("deep_escape_chain", '{"s":"a\\\\\\\\b\\\\\\"c"}', "consecutive backslashes then an escaped quote"),
    ("over_escaped", '{"s":"a\\\\nb"}', "really is backslash-n-b; 'fixing' it corrupts the data"),
    ("empty_containers", '{"a":{},"b":[],"c":"","d":null}', "empty everything"),
    ("numeric_string", '{"id":"007","zip":"01234"}', "leading zeros kept as strings, must not coerce"),
    ("bignum_string", '{"id":"9007199254740993"}', "past 2^53 kept as a string, per RFC 7493"),
]
for name, src, note in TRAPS:
    emit(f"trap/{name}.json", src, "JSON", (), note)

# These two are also traps, but fathom SHOULD report them — reporting an encoded
# value is correct, unwrapping it is the lossy policy choice fathom refuses.
emit("trap/json_in_string.json", '{"payload":"{\\"nested\\":true}"}', "JSON", ["encoded"],
     "double-serialised on purpose; report it, never unwrap it")
emit("trap/double_serialised.json", json.dumps('{"a":[1,2],"b":{"c":3}}'), "JSON", ["encoded"],
     "the whole document is a string containing JSON")
emit("trap/encoded_array_of_objects.json", '{"rows":"[{\\"a\\":1},{\\"a\\":2}]"}',
     "JSON", ["encoded"],
     "an encoded document can be an ARRAY, as long as it holds objects")

# The other side of the same rule, added 2026-08-09 after `11-jupyter-notebook`
# reported 17 encoded documents and every one was a false positive. A string
# that parses as JSON is not a document somebody encoded: Advent of Code day 18
# input IS nested integer lists, and `[376.0, 490.543]` is a Python repr. Both
# parse, both start with a bracket, and nothing upstream encoded anything.
NOT_ENCODED = [
    ("repr_of_float_list", '{"out":"[376.0, 490.543]"}',
     "a Python repr of a list of floats parses as JSON and is not a document"),
    ("puzzle_input_nested_ints", '{"out":"[[[[6,3],7],0],[[7,0],0]]"}',
     "Advent of Code day 18 input; the 17 false positives on corpus file 11"),
    ("bare_scalar_array", '{"out":"[1, 2, 3]"}',
     "an array of scalars is bracketed data, not an encoded document"),
    ("empty_array_string", '{"out":"[]"}',
     "parses, starts with a bracket, holds nothing"),
]
for name, src, note in NOT_ENCODED:
    emit(f"trap/{name}.json", src, "JSON", (), note)

# ── damage that parses cleanly ───────────────────────────────────────────────
emit("damage/negative_zero.json", '{"z": -0, "n": 0}', "JSON", ["negzero"],
     'json.loads("-0") returns int 0 and the sign is gone')
emit("damage/duplicate_keys.json", '{"a":1,"b":{"x":1,"x":2},"a":3}', "JSON", ["dupes"],
     "valid per RFC 8259 SHOULD; last one silently wins")
emit("damage/big_int.json", '{"id": 9007199254740993}', "JSON", ["bigints"],
     "past 2^53; anything JavaScript-derived rounds it")
emit("damage/nonfinite_literal.json", '{"v": [1.0, NaN], "w": Infinity}', "JSON", ["nonfinite"],
     "Python writes these and jsonlite refuses them: a file Python wrote that R cannot read")
emit("damage/overflow_to_inf.json", '{"big": 1e400}', "JSON", ["nonfinite"],
     "no literal Infinity in the text; the parse created one")
emit("damage/lone_surrogate.json", b'{"a": "\xed\xa0\x80"}', "JSON", ["bad_bytes"],
     "CESU-8 lone surrogate; a replace-decode swallows it silently")

# ── encodings that are valid JSON in the wrong clothes ───────────────────────
emit("encoding/utf8_bom.json", b'\xef\xbb\xbf{"a": 1}', "JSON", (), "UTF-8 BOM", bom="utf-8")
emit("encoding/utf16le_bom.json", '{"a": 1}'.encode("utf-16-le") and
     b'\xff\xfe' + '{"a": 1}'.encode("utf-16-le"), "JSON", (), "UTF-16LE", bom="utf-16-le")
emit("encoding/utf16be_bom.json", b'\xfe\xff' + '{"a": 1}'.encode("utf-16-be"),
     "JSON", (), "UTF-16BE", bom="utf-16-be")

# ── formats that are not JSON and are not broken ─────────────────────────────
emit("format/plain.ndjson", '{"i":1}\n{"i":2}\n{"i":3}\n', "NDJSON", (), "three records", records=3)
emit("format/no_trailing_newline.ndjson", '{"i":1}\n{"i":2}', "NDJSON", (), "no final newline", records=2)
emit("format/crlf.ndjson", '{"i":1}\r\n{"i":2}\r\n', "NDJSON", (), "CRLF line endings", records=2)
emit("format/blank_lines.ndjson", '{"i":1}\n\n{"i":2}\n', "NDJSON", (), "blank lines between records", records=2)
emit("format/scalars.ndjson", '1\n"two"\ntrue\nnull\n', "NDJSON", (), "scalar records", records=4)
emit("format/bad_line_middle.ndjson", '{"i":1}\n{bad}\n{"i":3}\n', "NDJSON", (),
     "one broken line: still NDJSON, and it must say which line", records=2, bad_lines=1)
emit("format/jsonc.json", '{\n  // a comment\n  "a": 1,\n  "b": [1,2,],\n}\n', "JSONC", (),
     "comments and trailing commas — every tsconfig.json")

# ── controls: the reader must not manufacture the damage it reports ──────────
# Only U+2028, U+2029 and U+0085 belong here. str.splitlines() also breaks on
# \v and \f, but RFC 8259 s7 requires U+0000-U+001F to be escaped inside a
# string, so those cannot appear raw in a valid document and cannot trigger the
# bug. Two such cases were written before checking and the suite rejected them.
#
# `04-gharchive` reported six unreadable records and had broken them itself, by
# splitting NDJSON with str.splitlines(), which also breaks on U+2028. Only
# counting newlines by hand caught it. **Every damage flag needs a control**: a
# case that is genuinely clean and where the flag must stay silent.
for ch, name in [(" ", "line_separator"), (" ", "paragraph_separator"),
                 ("\x85", "next_line")]:
    emit(f"control/ndjson_with_{name}.ndjson",
         '{"i":1,"text":"before' + ch + 'after"}\n{"i":2}\n', "NDJSON", (),
         f"a record containing U+{ord(ch):04X}; NDJSON splits on \\n alone, "
         f"so this is TWO records and zero bad lines", records=2, bad_lines=0)

emit("control/gzipped.json.gz", __import__("gzip").compress(b'{"a":[1,2],"b":"x"}'),
     "JSON", (), "gzip is how JSON at scale ships; unreadable is not an answer",
     compressed="gzip")

# ── genuinely unreadable ─────────────────────────────────────────────────────
emit("broken/empty.json", "", None, (), "empty, which is not the same as truncated", empty=True)
emit("broken/whitespace.json", "   \n  ", None, (), "whitespace only", empty=True)
emit("broken/not_json.json", "hello, world", None, (), "prose", truncated=False)

# ── the truncation ladder: every byte offset of three documents ──────────────
# Best generated, never collected. A last-character test passes 153 of these and
# fails on the ones that happen to stop after a closing bracket.
LADDER = {
    "nested": '{"a":{"b":[1,2.5e-3,"x\\u00e9y",true,null]},"c":"café"}',
    "escapes": '["\\u0041\\n\\t\\\\","café中文"]',
    "numbers": "[0,-0,1e10,1.5E-300,9007199254740993,-1.797693134862315e308]",
}
for label, doc in LADDER.items():
    raw = doc.encode()
    for i in range(1, len(raw)):
        # Expected flags are DERIVED, not asserted by hand. The first version
        # declared these clean and the suite caught seven wrong labels: a cut
        # landing inside a multi-byte character really does produce invalid
        # UTF-8, and reporting it is right. Deriving the label from the bytes is
        # the same correction the source corpus had to make to its own.
        try:
            raw[:i].decode()
            bad = ()
        except UnicodeDecodeError:
            bad = ["bad_bytes"]
        emit(f"truncate/{label}_{i:04d}.json", raw[:i], None, bad,
             f"{label} cut at {i} of {len(raw)} bytes", truncated=True)
    full = {"numbers": ["negzero", "bigints"]}.get(label, [])
    emit(f"truncate/{label}_full.json", raw, "JSON", full,
         f"{label}, complete — the control")


if __name__ == "__main__":
    (OUT / "manifest.jsonl").parent.mkdir(parents=True, exist_ok=True)
    with open(OUT / "manifest.jsonl", "w") as fh:
        for m in MAN:
            fh.write(json.dumps(m) + "\n")
    n = len(MAN)
    print(f"{n} cases -> {OUT}", file=sys.stderr)
    for pre in ("trap/", "damage/", "encoding/", "format/", "broken/", "truncate/"):
        print(f"  {pre:<12}{sum(1 for m in MAN if m['path'].startswith(pre))}", file=sys.stderr)
