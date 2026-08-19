"""Can `into` enter an unnamed container, and does it narrow when it does?
— 2026-08-14.

**An instrument, like `menu-labels.py` and `find-tests.py`.** It runs the
shipped binary and modifies nothing. Running it is not a freeze event.

`design/vocabulary.md` records that `into` descends by NAME only, so a document
wrapping its records in a bare array *"cannot be entered"*, and leaves open
whether it should be able to. Predictions first, in
`design/into-unnamed-predictions.md`.

## What is measured

**Whether an array root is actually refused.** `extract.rs::at` gathers every
element's named field when standing on an array, so the claim is testable
rather than a reading of the docs.

**Whether the names on offer are DATA keys.** A name that is a movie title or a
package name is a name that does not survive the next file — question 14, not
question 8.

**Whether entering NARROWS.** `into` is documented as the performance mechanism:
scoping the analysis is the only saving available. So the honest test of
"can it enter" is not whether the call succeeds but whether the work drops.
"""
import gzip
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
MAX_RECORDS = 20_000


def documents():
    for d in sorted((ROOT / "corpus").iterdir()):
        if not d.is_dir():
            continue
        for name in ("source.json", "source.json.gz", "source.jsonl"):
            if (d / name).exists():
                yield d.name, d / name
                break


def load(path):
    raw = gzip.open(path, "rb").read() if path.suffix == ".gz" else path.read_bytes()
    text = raw.decode("utf-8", "replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        out = []
        for ln in text.split("\n"):
            if ln.strip():
                out.append(json.loads(ln))
                if len(out) == MAX_RECORDS:
                    break
        return out


def timed_probe(path, at=None):
    """Seconds for `fathom probe`, optionally scoped. None if it refuses."""
    args = [str(BIN), "probe", str(path)]
    if at:
        args += ["--at", at]
    t0 = time.perf_counter()
    r = subprocess.run(args, capture_output=True, text=True)
    s = time.perf_counter() - t0
    return (s, r.stdout) if r.returncode == 0 else (None, r.stderr.strip()[:70])


def root_kind(doc):
    if isinstance(doc, list):
        return "array"
    if isinstance(doc, dict):
        return "object"
    return "scalar"


def names_at_root(doc):
    """Every name `into` would accept from the root, and whether it is a DATA key.

    An object offers its own fields. An array offers the fields of the things
    inside it — that is the gathering branch. A key is called DATA when the
    container holding it has many keys and they are not a fixed vocabulary; the
    threshold is the probe's own `KEYED_MIN`, 20, and it is stated rather than
    tuned here.
    """
    if isinstance(doc, dict):
        offered = list(doc)
        return offered, len(offered) >= 20
    if isinstance(doc, list):
        keys = []
        for el in doc[:200]:
            if isinstance(el, dict):
                keys.extend(el)
        uniq = list(dict.fromkeys(keys))
        # the array's ELEMENTS are what gets entered; their keys are data when
        # a single element carries a great many of them
        big = any(isinstance(el, dict) and len(el) >= 20 for el in doc[:200])
        return uniq, big
    return [], False


def main():
    docs = list(documents())
    print(f"{len(docs)} documents\n")
    print("  entry                        root    names  data?  whole   scoped  saving")
    rows = []
    for entry, path in docs:
        doc = load(path)
        kind = root_kind(doc)
        offered, is_data = names_at_root(doc)
        whole, _ = timed_probe(path)
        best = None
        # try the first few names the root offers; report the biggest saving
        for nm in offered[:5]:
            s, _out = timed_probe(path, nm)
            if s is not None and (best is None or s < best[1]):
                best = (nm, s)
        if whole is None:
            print(f"  {entry:<28} {kind:<7} unreadable")
            continue
        if best is None:
            print(f"  {entry:<28} {kind:<7} {len(offered):>5}  {'yes' if is_data else 'no':<5} "
                  f"{whole:>6.2f}   REFUSED")
            rows.append((entry, kind, len(offered), is_data, whole, None, None))
            continue
        saving = whole / best[1] if best[1] > 0 else float("inf")
        print(f"  {entry:<28} {kind:<7} {len(offered):>5}  {'yes' if is_data else 'no':<5} "
              f"{whole:>6.2f}  {best[1]:>6.2f}  {saving:>5.1f}x  via {best[0][:22]}")
        rows.append((entry, kind, len(offered), is_data, whole, best[1], saving))

    arrays = [r for r in rows if r[1] == "array"]
    objects = [r for r in rows if r[1] == "object"]
    print(f"\n  root is a bare ARRAY in {len(arrays)} of {len(rows)} documents: "
          f"{', '.join(r[0] for r in arrays)}")
    refused = [r for r in rows if r[5] is None]
    print(f"  documents where `into` was REFUSED every name it was offered: {len(refused)}"
          + (f" — {', '.join(r[0] for r in refused)}" if refused else ""))

    def med(v):
        v = sorted(x for x in v if x is not None)
        return v[len(v) // 2] if v else float("nan")

    print(f"\n  median saving, OBJECT roots: {med([r[6] for r in objects]):.1f}x")
    print(f"  median saving, ARRAY  roots: {med([r[6] for r in arrays]):.1f}x")
    dk = [r for r in rows if r[3]]
    print(f"\n  documents whose root offers only DATA keys: {len(dk)} — "
          f"{', '.join(r[0] for r in dk)}")


if __name__ == "__main__":
    main()
