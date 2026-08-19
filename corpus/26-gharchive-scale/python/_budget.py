"""Shared budget + memory harness for entry 26's attempts.

**Not an attempt file and not a tool.** This entry grades the fourteen on SCALE,
so every attempt needs the same two instruments — a wall clock it cannot exceed
and a peak-memory reading — and repeating them in fourteen files is how they
drift apart. `try-` files are scripts; this is imported, so it deliberately does
NOT carry the `try-` prefix.
"""
import resource
import signal
import time

BUDGET = 600
RECORDS = 286_864          # the whole file, from the entry's own NOTES
RAW_MB = 869.8


class Budget(Exception):
    pass


def _stop(signum, frame):
    raise Budget()


signal.signal(signal.SIGALRM, _stop)


def rss_mb():
    """Peak resident set. macOS reports BYTES here; Linux reports kilobytes."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


class Attempt:
    """Run a thunk under the budget and report finished / seconds / peak RSS."""

    def __init__(self, label, budget=BUDGET, quiet=False):
        self.label, self.budget, self.quiet = label, budget, quiet
        self.why = ''

    def __enter__(self):
        signal.alarm(self.budget)
        self.t0 = time.perf_counter()
        self.finished = True
        return self

    def __exit__(self, exc_type, exc, tb):
        signal.alarm(0)
        self.secs = time.perf_counter() - self.t0
        self.rss = rss_mb()
        if exc_type is Budget:
            self.finished = False
            self.why = f'did not finish in {self.budget}s'
            if self.quiet: return True
            print(f"  {self.label:<38} DID NOT FINISH in {self.budget} s "
                  f"(peak RSS {self.rss:,.0f} MB)")
            return True
        if exc_type is MemoryError:
            self.finished = False
            self.why = 'MemoryError'
            if self.quiet: return True
            print(f"  {self.label:<38} MemoryError after {self.secs:.1f} s "
                  f"(peak RSS {self.rss:,.0f} MB)")
            return True
        if exc_type is not None:
            self.finished = False
            self.why = f'{exc_type.__name__}: {str(exc)[:90]}'
            if self.quiet: return True
            print(f"  {self.label:<38} {exc_type.__name__} after {self.secs:.1f} s: "
                  f"{str(exc)[:90]}")
            return True
        if not self.quiet:
            print(f"  {self.label:<38} {self.secs:>7.1f} s  peak RSS {self.rss:>7,.0f} MB")
        return False


def in_subprocess(script, mode, budget=BUDGET):
    """Run `script` with `mode` as argv[1] and return its reported peak RSS.

    **Necessary rather than tidy, and this entry is where it matters.**
    `ru_maxrss` is a HIGH-WATER MARK for the whole process, so measuring two
    strategies in one run reports the larger of them twice. A first draft of
    `try-pandas.py` did exactly that and made a chunked read that never holds
    the file look more expensive than the whole-file read it followed.
    """
    import subprocess
    import sys
    r = subprocess.run([sys.executable, script, mode], capture_output=True,
                       text=True, timeout=budget + 60)
    lines = [l for l in r.stdout.strip().splitlines() if '\t' in l]
    if lines:
        return lines[-1], r.returncode
    # A subprocess that died before reporting: surface WHY. The exception is
    # the finding in this entry, so "died (rc=1)" is not an acceptable record.
    err = [l for l in r.stderr.strip().splitlines() if l.strip()]
    why = err[-1][:140] if err else "no output"
    return f"!\t{why}", r.returncode
