//! What does it cost fathom to stop sampling? — author item 3's missing number.
//!
//!     cargo run --release --example sampling_cost -- <file> <max_records>
//!     /usr/bin/time -l cargo run … 2>&1 | grep "maximum resident"
//!
//! **An instrument, not a product.** It touches nothing shipped:
//! `health::read` is already `pub` and already takes the cap as a parameter, so
//! the sampling contract can be varied without editing `MAX_RECORDS`, the CLI,
//! or the oracle. `design/coverage.py`, `axes.py` and `growth.py` are the same
//! shape on the Python side — they import the probe and do not modify it.
//!
//! It prints the whole report so that two caps can be DIFFED, which is the
//! fidelity half of the question: `FINDINGS.md` 2026-08-14 records that the
//! 20,000-record sample missed a keys-as-data site the document actually has,
//! and a cost number alone cannot see that.
//!
//! `max_records` of 0 means no cap — `usize::MAX`, every record parsed.

use fathom_core::health::health_at;
use fathom_core::report::report_at;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let (path, cap) = match args.as_slice() {
        [p, c] => (p.clone(), c.parse::<usize>().unwrap_or(0)),
        [p] => (p.clone(), 0),
        _ => {
            eprintln!("usage: sampling_cost <file> [max_records; 0 = uncapped]");
            std::process::exit(2);
        }
    };
    let cap = if cap == 0 { usize::MAX } else { cap };

    // **This went through `health::read(&bytes, cap)` until 2026-08-15, which
    // slurps.** That measured the cost of not sampling on the OLD reader and
    // could not see the streaming one, so the figures it produced are a dated
    // record of a path the product no longer takes for NDJSON.
    let (h, doc) = match health_at(std::path::Path::new(&path), cap) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("sampling_cost: {path}: {e}");
            std::process::exit(1);
        }
    };
    let base = path.rsplit('/').next().unwrap_or(&path);
    print!("{}", report_at(doc.as_ref(), &h, base, ""));
}
