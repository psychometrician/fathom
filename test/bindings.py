"""Do the two bindings return exactly what the binary printed?

    uv run test/bindings.py          # exits non-zero on any mismatch

**This is the only test a thin binding needs, and it is the whole of what the
architecture promises.** `design/implementation.md` chose one Rust core and two
subprocess wrappers over two hand-written implementations, on the grounds that
one core makes the languages agree BY CONSTRUCTION. That guarantee is only real
if the wrappers are transparent, so this asserts transparency directly: for
every corpus document, the bytes R returns and the bytes Python returns are the
bytes the binary wrote.

**It is a different question from `test/parity.py`**, which asks whether the
Rust core reproduces `design/probe.py`. That one guards the port. This one
guards the seam either side of it, and a failure here is a wrapper reformatting,
re-wrapping or re-encoding a page whose column widths are load-bearing.

Shaped like `test/check.py` and `design/parity.py`: a table of cases, one line
per group, non-zero exit on failure.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
BINARY = ROOT / "target" / "release" / "fathom"

# One R session for all documents, and one Python import for all documents.
# Starting R once per file turned a four-second run into forty, and the thing
# being measured has nothing to do with process startup.
R_DRIVER = r"""
# `Rscript -e expr --args a b` leaves the sentinel itself in the vector, which
# put every path one slot from where it was read.
args <- commandArgs(trailingOnly = TRUE)
args <- args[args != "--args"]
.libPaths(c(args[1], .libPaths()))
suppressMessages(library(fathom))
outdir <- args[2]
for (path in args[-c(1, 2)]) {
  text <- as.character(fathom(path))
  con <- file(file.path(outdir, basename(dirname(path))), "wb")
  writeBin(charToRaw(text), con)
  close(con)
}
"""

PY_DRIVER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from fathom import fathom
outdir = Path(sys.argv[2])
for path in sys.argv[3:]:
    (outdir / Path(path).parent.name).write_bytes(
        str(fathom(path)).encode("utf-8"))
"""

# `rows()` cannot be compared as bytes, because the two languages return
# different TYPES on purpose — a data.frame in R, a list of dicts in Python.
# What must agree is the TABLE: the same rows, the same column names, the same
# cells, including which cells are absent. Each driver writes a canonical
# rendering and the two are diffed as text.
#
# The candidate labels are read out of the printed report, so this asks the same
# question `test/candidates.py` asks — does the label the menu printed resolve
# to the table it promised — but across the boundary rather than inside it.
R_ROWS_DRIVER = r"""
args <- commandArgs(trailingOnly = TRUE)
args <- args[args != "--args"]
.libPaths(c(args[1], .libPaths()))
suppressMessages(library(fathom))
outdir <- args[2]
for (spec in args[-c(1, 2)]) {
  parts <- strsplit(spec, "\t", fixed = TRUE)[[1]]
  d <- fathom::rows(parts[1], parts[2])
  # An absent cell is "" on the wire; render it as a marker so the two
  # languages are compared on the ragged edge too rather than around it.
  #
  # `write.table` rather than a loop building a character vector. The first
  # draft did `lines <- c(lines, ...)` per row, which is O(n^2) in R, and it
  # hung on a 8,893 x 17,379 table rather than failing.
  d[is.na(d)] <- "<absent>"
  d[d == ""] <- "<absent>"
  con <- file(file.path(outdir, parts[3]), "wb")
  write.table(d, con, sep = "\t", quote = FALSE, row.names = FALSE,
              col.names = TRUE, fileEncoding = "UTF-8")
  close(con)
}
"""

PY_ROWS_DRIVER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import fathom
outdir = Path(sys.argv[2])
for spec in sys.argv[3:]:
    path, label, name = spec.split("\t")
    rows = fathom.rows(path, label)
    names = []
    for r in rows:
        for k in r:
            if k not in names:
                names.append(k)
    # Python drops an absent key; R keeps the column and empties the cell. The
    # canonical form is the union of names with a marker where a row has none,
    # so the two are the same table written the same way.
    out = ["\t".join(names)]
    for r in rows:
        out.append("\t".join(r.get(n, "<absent>") or "<absent>" for n in names))
    (outdir / name).write_bytes(("\n".join(out) + "\n").encode("utf-8"))
"""

# ── the whole vocabulary, both languages, one canonical rendering ────────────
#
# `fathom()` and `rows()` can be compared directly; the other five words return
# a view, a health line or a small table, and R and Python return them as
# DIFFERENT TYPES on purpose. So each driver renders a fixed battery of chain
# sentences into one text blob per document, and the two blobs are diffed.
#
# **Five of the seven words had no cross-language test until 2026-08-13**, which
# is the architecture's central promise going unchecked on most of its surface.
# Two divergences had already been found by accident on the day this was
# written: Python's `csv` refusing a field R read fine, and `back()` printing
# differently in the two languages. Both would have been caught here.
R_CHAIN_DRIVER = r"""
args <- commandArgs(trailingOnly = TRUE)
args <- args[args != "--args"]
.libPaths(c(args[1], .libPaths()))
suppressMessages(library(fathom))
outdir <- args[2]

tab <- function(d) {
  if (!nrow(d)) return("(no rows)")
  d[is.na(d)] <- "<absent>"
  d[d == ""] <- "<absent>"
  paste(c(paste(names(d), collapse = "\t"),
          apply(d, 1, paste, collapse = "\t")), collapse = "\n")
}

for (spec in args[-c(1, 2)]) {
  p <- strsplit(spec, "\t", fixed = TRUE)[[1]]
  src <- p[1]; name <- p[2]
  navs <- Filter(nzchar, strsplit(p[3], ",", fixed = TRUE)[[1]])
  cols <- Filter(nzchar, strsplit(p[4], ",", fixed = TRUE)[[1]])
  labs <- if (length(p) >= 5) strsplit(p[5], "|", fixed = TRUE)[[1]] else character(0)
  out <- character(0)
  v <- read_json(src)
  out <- c(out, "HEALTH", v$health)

  # Every predicate the core knows, not a sample of them.
  for (test in c("url", "email", "date", "empty")) {
    out <- c(out, paste("FIND", test), tab(find(v, test)))
  }

  # Every navigable name the menu offered, and at each one the report, the
  # position, and that back() returns to where it started.
  for (i in seq_along(navs)) {
    nav <- navs[i]
    # `into()` NEVER fails — it is list arithmetic. The refusal comes from the
    # core, when the name does not resolve where you are standing. A MENU LABEL
    # IS NOT A NAVIGABLE NAME: `an entry of dependencies` names a row shape
    # anywhere in the document, while `into("dependencies")` walks one level
    # from here. Both drivers must record that the same way or they differ over
    # an agreement.
    w <- v |> into(nav)
    page <- try(as.character(fathom(w)), silent = TRUE)
    if (inherits(page, "try-error")) {
      out <- c(out, paste("INTO", nav), "(refused)")
      next
    }
    out <- c(out, paste("INTO", nav), paste(w$at, collapse = "."))
    out <- c(out, "BACK", paste((w |> back())$at, collapse = "."))
    out <- c(out, "FATHOM AT", page)
    # The label comes from the SPEC, not from parsing the page. Both drivers
    # then ask for the same table, and neither needs a regex over the report —
    # which is one fewer place the two languages could differ for a reason that
    # has nothing to do with the binding.
    lab <- if (i <= length(labs)) labs[i] else ""
    r <- if (nzchar(lab)) try(tab(rows(w, lab)), silent = TRUE) else "(no candidate)"
    out <- c(out, "ROWS AT",
             if (inherits(r, "try-error")) "(refused)" else r)
    # Two levels deep, where the document allows it: this is where the
    # container-versus-contents question used to live.
    for (nav2 in navs) {
      x <- try(w |> into(nav2), silent = TRUE)
      if (!inherits(x, "try-error")) {
        r <- try(as.character(fathom(x)), silent = TRUE)
        out <- c(out, paste("INTO", nav, nav2),
                 if (inherits(r, "try-error")) "(refused)" else r)
        out <- c(out, "BACK BACK", paste((x |> back() |> back())$at, collapse = "."))
      }
    }
  }

  if (length(cols)) {
    out <- c(out, "WHICHEVER", tab(do.call(whichever, c(list(v), as.list(cols)))))
    # One name alone, so the test can tell a working `whichever` from one that
    # happens to return the same thing either way.
    for (c1 in cols) {
      out <- c(out, paste("WHICHEVER", c1), tab(whichever(v, c1)))
    }
  }
  con <- file(file.path(outdir, name), "wb")
  writeBin(charToRaw(paste0(paste(out, collapse = "\n"), "\n")), con)
  close(con)
}
"""

PY_CHAIN_DRIVER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from fathom import read_json, into, back, find, whichever, fathom
outdir = Path(sys.argv[2])

def tab(rows):
    if not rows:
        return "(no rows)"
    names = []
    for r in rows:
        for k in r:
            if k not in names:
                names.append(k)
    out = ["\t".join(names)]
    for r in rows:
        out.append("\t".join(r.get(n) or "<absent>" for n in names))
    return "\n".join(out)

from fathom import rows

for spec in sys.argv[3:]:
    src, name, navspec, colspec, labspec = spec.split("\t")
    navs = [n for n in navspec.split(",") if n]
    cols = [c for c in colspec.split(",") if c]
    labs = labspec.split("|")
    out = []
    v = read_json(src)
    out += ["HEALTH", v.health]

    # Every predicate the core knows, not a sample of them.
    for test in ("url", "email", "date", "empty"):
        out += [f"FIND {test}", tab(v >> find(test))]

    # Every navigable name the menu offered, and at each one the report, the
    # position, and that back() returns to where it started.
    for i, nav in enumerate(navs):
        # See the R driver: a menu label is not a navigable name, so the core
        # may refuse, and both drivers record the refusal the same way.
        w = v >> into(nav)
        try:
            page = str(fathom(w))
        except Exception:
            out += [f"INTO {nav}", "(refused)"]
            continue
        out += [f"INTO {nav}", ".".join(w.at)]
        out += ["BACK", ".".join((w >> back()).at)]
        out += ["FATHOM AT", page]
        # The label comes from the SPEC, not from parsing the page.
        lab = labs[i] if i < len(labs) else ""
        if not lab:
            out += ["ROWS AT", "(no candidate)"]
        else:
            try:
                out += ["ROWS AT", tab(rows(w, lab))]
            except Exception:
                out += ["ROWS AT", "(refused)"]
        # Two levels deep, where the document allows it.
        for nav2 in navs:
            # `into()` never fails — it is list arithmetic. The refusal comes
            # from the core when the name resolves to nothing, and BOTH drivers
            # must record it the same way or they differ over an agreement.
            x = w >> into(nav2)
            try:
                page2 = str(fathom(x))
            except Exception:
                page2 = "(refused)"
            out += [f"INTO {nav} {nav2}", page2]
            out += ["BACK BACK", ".".join((x >> back() >> back()).at)]

    if cols:
        out += ["WHICHEVER", tab(v >> whichever(*cols))]
        # One name alone, so the test can tell a working `whichever` from one
        # that happens to return the same thing either way.
        for c1 in cols:
            out += [f"WHICHEVER {c1}", tab(v >> whichever(c1))]
    (outdir / name).write_bytes(("\n".join(out) + "\n").encode("utf-8"))
"""

MENU = re.compile(r"^\s{4}(\S.*?)\s{2,}([\d,]+) rows x\s+([\d,]+) cols")
# A label like `an entry of versions` names something `into()` can descend into.
# `an entry of $[]`, `a node at any depth (13 levels)` and anything holding the
# fold's markers do not, so they are skipped and the count is reported.
NAVIGABLE = re.compile(r"^an (?:entry|item) of ([A-Za-z_][A-Za-z0-9_-]*)$")

# A table this wide is not a table either language can hold: R's data.frame and
# Python's dict both degrade badly past a few thousand columns, and the TSV wire
# format costs one field per column per row whether the cell is there or not.
# `29-mdn-browser-compat` names two such candidates — 1,090 x 126,299 and
# 8,893 x 17,379, both **100% empty** — where TSV is 149 MB and 160 MB against
# NDJSON's 16 MB and 13 MB.
#
# Named here and reported rather than silently absent, which is the same rule
# `documents()` follows for the 912 MB file.
WIDE = 2_000


def candidates(src, env):
    """Every label the report prints for one document, with its shape."""
    report = subprocess.run(
        [str(BINARY), "probe", str(src)], capture_output=True, env=env
    ).stdout.decode("utf-8", "replace")
    out = []
    for line in report.splitlines():
        if m := MENU.match(line):
            out.append((m.group(1).strip(),
                        int(m.group(2).replace(",", "")),
                        int(m.group(3).replace(",", ""))))
    return out


def documents():
    """Every corpus document, largest excluded and SAID rather than dropped."""
    out, skipped = [], []
    for entry in sorted((ROOT / "corpus").iterdir()):
        if not entry.is_dir():
            continue
        for name in ("source.json", "source.jsonl"):
            src = entry / name
            if src.exists():
                # `26-gharchive-scale` is 912 MB and the wrapper's transparency
                # does not depend on the size of the document — the report is a
                # few KB whatever the input weighs, which is the project's whole
                # claim. Named here rather than silently absent.
                if src.stat().st_size > 200 * 2**20:
                    skipped.append((entry.name, src.stat().st_size))
                else:
                    out.append(src)
                break
    return out, skipped


def main():
    if not BINARY.exists():
        print(f"  no binary at {BINARY} — run `cargo build --release`")
        return 1

    docs, skipped = documents()
    if not docs:
        print("  no corpus documents found")
        return 1

    # The binary under test is named explicitly, so a result can never be
    # attributed to some other `fathom` that happened to be on PATH. This also
    # exercises the override branch both bindings implement.
    env = dict(os.environ, FATHOM_BIN=str(BINARY))

    failures = []
    too_wide = []
    no_nav = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lib, r_out, py_out = tmp / "lib", tmp / "r", tmp / "py"
        for d in (lib, r_out, py_out):
            d.mkdir()

        # The R half is INSTALLED rather than sourced, because sourcing tests
        # the code and installing tests the package — NAMESPACE, exports and
        # the S3 method registration included.
        install = subprocess.run(
            ["R", "CMD", "INSTALL", f"--library={lib}", str(ROOT / "r-pkg" / "fathom")],
            capture_output=True, text=True, env=env)
        if install.returncode != 0:
            print("  R CMD INSTALL failed:")
            print("   ", install.stderr.strip().replace("\n", "\n    "))
            return 1

        subprocess.run(
            ["Rscript", "-e", R_DRIVER, "--args", str(lib), str(r_out),
             *[str(d) for d in docs]],
            check=True, capture_output=True, env=env)
        subprocess.run(
            [sys.executable, "-c", PY_DRIVER, str(ROOT / "py-pkg" / "fathom"), str(py_out),
             *[str(d) for d in docs]],
            check=True, capture_output=True, env=env)

        print(f"\nBINDINGS: {len(docs)} documents, R and Python against the binary")
        for src in docs:
            entry = src.parent.name
            want = subprocess.run(
                [str(BINARY), "probe", str(src)],
                capture_output=True, env=env).stdout
            for lang, path in (("R", r_out / entry), ("Python", py_out / entry)):
                got = path.read_bytes() if path.exists() else b""
                if got != want:
                    failures.append((entry, lang, len(want), len(got)))

        # ── rows(): the same TABLE in both languages, for every candidate the
        # report names. `fathom()` is compared as bytes because both languages
        # return the page; `rows()` returns a data.frame in R and a list of
        # dicts in Python, so the comparison is of a canonical rendering.
        r_rows, py_rows = tmp / "r_rows", tmp / "py_rows"
        for d in (r_rows, py_rows):
            d.mkdir()
        specs, n_cand = [], 0
        for src in docs:
            for i, (label, n_rows, n_cols) in enumerate(candidates(src, env)):
                if n_cols > WIDE:
                    too_wide.append((src.parent.name, label, n_rows, n_cols))
                    continue
                specs.append(f"{src}\t{label}\t{src.parent.name}#{i}")
                n_cand += 1

        if specs:
            for driver, out, runner in (
                (R_ROWS_DRIVER, r_rows,
                 ["Rscript", "-e", R_ROWS_DRIVER, "--args", str(lib), str(r_rows)]),
                (PY_ROWS_DRIVER, py_rows,
                 [sys.executable, "-c", PY_ROWS_DRIVER, str(ROOT / "py-pkg" / "fathom"), str(py_rows)]),
            ):
                done = subprocess.run(runner + specs, capture_output=True, env=env)
                if done.returncode != 0:
                    print("  a rows() driver failed:")
                    print("   ", done.stderr.decode("utf-8", "replace").strip()
                          .replace("\n", "\n    ")[:900])
                    return 1

            print(f"\nROWS: {n_cand} candidates across {len(docs)} documents, R against Python")
            for spec in specs:
                _, label, name = spec.split("\t")
                a = (r_rows / name).read_bytes() if (r_rows / name).exists() else b""
                b = (py_rows / name).read_bytes() if (py_rows / name).exists() else b""
                if a != b:
                    failures.append((f"{name.split('#')[0]} {label[:30]}",
                                     "R vs Python", len(a), len(b)))

        # ── the whole vocabulary: read_json, into, back, find, whichever ────
        r_ch, py_ch = tmp / "r_ch", tmp / "py_ch"
        for d in (r_ch, py_ch):
            d.mkdir()
        chain_specs = []
        for src in docs:
            cands = candidates(src, env)
            # EVERY navigable name the menu offers, not the first one. A name
            # tested is a name whose resolution rule was exercised, and the
            # three rules — plain field, over a list, over a keyed collection —
            # are chosen by what the name lands on.
            navs = [m.group(1) for label, _r, _c in cands
                    if (m := NAVIGABLE.match(label))]
            if not navs:
                no_nav.append(src.parent.name)
            # Field names to try `whichever` with, taken from the widest
            # candidate the report names, so the test is derived from the
            # document rather than hard-coded per entry.
            cols: list[str] = []
            if cands:
                widest = max(cands, key=lambda c: c[2])[0]
                head = subprocess.run(
                    [str(BINARY), "rows", str(src), "--candidate", widest, "--tsv"],
                    capture_output=True, env=env
                ).stdout.decode("utf-8", "replace").split("\n", 1)[0]
                cols = [n for n in head.split("\t") if n and "," not in n][:3]
            # The first candidate the menu names AT each navigable position,
            # computed once here so both drivers ask for the same table.
            labs = []
            for nav in navs:
                at_menu = subprocess.run(
                    [str(BINARY), "probe", str(src), "--at", nav],
                    capture_output=True, env=env
                ).stdout.decode("utf-8", "replace")
                got = ""
                for line in at_menu.splitlines():
                    if m := MENU.match(line):
                        if int(m.group(3).replace(",", "")) <= WIDE:
                            got = m.group(1).strip()
                            break
                labs.append(got)
            chain_specs.append(
                f"{src}\t{src.parent.name}\t{','.join(navs)}\t{','.join(cols)}"
                f"\t{'|'.join(labs)}")

        for runner in (
            ["Rscript", "-e", R_CHAIN_DRIVER, "--args", str(lib), str(r_ch)],
            [sys.executable, "-c", PY_CHAIN_DRIVER, str(ROOT / "py-pkg" / "fathom"), str(py_ch)],
        ):
            done = subprocess.run(runner + chain_specs, capture_output=True, env=env)
            if done.returncode != 0:
                print("  a vocabulary driver failed:")
                print("   ", done.stderr.decode("utf-8", "replace").strip()
                      .replace("\n", "\n    ")[:900])
                return 1

        n_nav = sum(1 for s in chain_specs if s.split("\t")[2])
        n_names = sum(len([x for x in s.split("\t")[2].split(",") if x]) for s in chain_specs)
        print(f"\nVOCABULARY: {len(docs)} documents — read_json, all four find tests,\n            whichever, and into/back over {n_names} names on {n_nav} documents,\n            R against Python")
        for src in docs:
            entry = src.parent.name
            a = (r_ch / entry).read_bytes() if (r_ch / entry).exists() else b""
            b = (py_ch / entry).read_bytes() if (py_ch / entry).exists() else b""
            if a != b:
                failures.append((entry, "R vs Python", len(a), len(b)))

    if failures:
        for entry, lang, want, got in failures:
            print(f"  {entry:<40} {lang:<12} {want:,} vs {got:,} bytes")
        print(f"\n  {len(failures)} DIFFERENCES")
        return 1

    print("  no differences")
    for entry, size in skipped:
        print(f"  not run: {entry} at {size / 2**20:.0f} MB — "
              f"transparency does not depend on document size")
    for entry in no_nav:
        print(f"  not navigated: {entry} — no candidate label names something "
              f"`into()` can descend into")
    for entry, label, r, c in too_wide:
        print(f"  not run: {entry} {label!r} at {r:,} x {c:,} — wider than "
              f"{WIDE:,} columns is not a table either language can hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
