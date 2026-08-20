#!/usr/bin/env python3
"""The manifests agree: three version declarations, and one description.

    uv run test/versions.py

**Why a check rather than a single source.** The version is written by hand in
three manifests, and CI never assigns it — that is the household's rule, and the
sibling states it plainly: *"Version numbers are never assigned by CI. One number
is written down by hand in several manifests, and the only automation is checks
that they agree."*

Deriving all three from one file would be the obvious alternative and it is worse
in this ecosystem. `DESCRIPTION` must carry a literal for `R CMD check`,
`pyproject.toml` must carry one for a build backend that runs without executing
project code, and Cargo wants one in the manifest. Every scheme that computes
them adds a build step to all three languages so that a human never types a
number — which is a lot of machinery to avoid the failure this file catches in
50 milliseconds.

**So the rule this project already has applies unchanged**: a number may live in
several places if something makes them argue loudly. This is that something.

WHAT IS NOT CHECKED, and it is the interesting gap
--------------------------------------------------
This compares the DECLARATIONS in the repository. It says nothing about what a
user has installed — an engine built last week reports the version it was built
at, and agrees with a manifest that has since moved. `fathom-test/versions.py`
asks the installed packages and their engines instead, which is the other half
and cannot be done from here.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Each declaration, and the pattern that reads it. Anchored, because a version
# appears in more than one form in these files — `rust-version`, a dependency
# pin, a URL — and a loose pattern would compare the wrong number and pass.
DECLARATIONS = {
    "Cargo.toml": (
        # The workspace version; the two crates say `version.workspace = true`.
        r'^\[workspace\.package\][^\[]*?^version\s*=\s*"([^"]+)"',
        re.M | re.S,
    ),
    "r-pkg/fathom/DESCRIPTION": (r"^Version:\s*(\S+)", re.M),
    "py-pkg/fathom/pyproject.toml": (
        r'^\[project\][^\[]*?^version\s*=\s*"([^"]+)"',
        re.M | re.S,
    ),
}


def declared(rel, pattern, flags):
    path = ROOT / rel
    if not path.exists():
        return None, f"{rel} does not exist"
    m = re.search(pattern, path.read_text(), flags)
    if not m:
        return None, f"{rel} has no version this pattern can read"
    return m.group(1), None


def main():
    found, problems = {}, []
    for rel, (pattern, flags) in DECLARATIONS.items():
        value, why = declared(rel, pattern, flags)
        if why:
            problems.append(why)
        else:
            found[rel] = value

    width = max(len(r) for r in DECLARATIONS)
    print(f"VERSIONS: {len(DECLARATIONS)} declarations, written by hand\n")
    for rel in DECLARATIONS:
        print(f"  {rel:<{width}}  {found.get(rel, '(unreadable)')}")
    print()

    for why in problems:
        print(f"  {why}")

    distinct = set(found.values())
    if len(distinct) > 1:
        print(f"  THEY DISAGREE: {', '.join(sorted(distinct))}")
        print()
        print("  A release cut from this tree would ship an R package and a wheel")
        print("  claiming different things about the same engine. Pick one number")
        print("  and write it into all three; nothing here will do it for you, on")
        print("  purpose.")
        return 1

    if problems:
        return 1

    # **The description is the second thing written in two places.** R's
    # `Description:` and Python's `description` are read by different registries
    # and by different people, and there is no mechanism that keeps them equal —
    # they simply drifted, and the R one still said "One verb" after the
    # vocabulary reached seven words.
    #
    # The rule is the sibling's: Python's one-liner IS R's opening sentence, so
    # the longer text may say more but cannot say something else. Compared with
    # whitespace folded, because DESCRIPTION wraps at 80 and a TOML string does
    # not, and a line break is not a disagreement.
    import re as _re
    desc_r = (ROOT / "r-pkg/fathom/DESCRIPTION").read_text()
    m = _re.search(r"^Description:(.*?)(?=^\S+:)", desc_r, _re.M | _re.S)
    r_open = " ".join(m.group(1).split()).split(".")[0].strip() if m else ""
    desc_py = (ROOT / "py-pkg/fathom/pyproject.toml").read_text()
    m2 = _re.search(r'^description\s*=\s*"([^"]+)"', desc_py, _re.M)
    py_desc = " ".join(m2.group(1).split()).rstrip(".") if m2 else ""

    if r_open != py_desc:
        print("  THE DESCRIPTIONS DISAGREE")
        print(f"    R opens with : {r_open}")
        print(f"    Python says  : {py_desc}")
        print()
        print("  Python's description must be R's opening sentence. The R text")
        print("  may go on to say more; it may not say something else.")
        return 1
    print(f"  and both describe it the same way, in {len(py_desc)} characters")

    # **`0.0.x` is not a mistake, and this says so rather than nagging.** While
    # the series stays here every release is a breaking change, because that is
    # what `0.0.x` means to every resolver that reads it. The sibling records the
    # decision to leave it as open and deliberately unmade; fathom inherits the
    # same question and should not answer it by drift.
    version = distinct.pop()
    print(f"  all {len(found)} agree at {version}")
    if version.startswith("0.0."):
        print("  (0.0.x, so every release reads as breaking — deliberate, "
              "and not this check's business)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
