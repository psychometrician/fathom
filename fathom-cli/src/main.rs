//! The one entry point. R and Python invoke this as a subprocess and render
//! what it prints — no FFI, no ABI, a binary and a pipe. `design/implementation.md`.

use fathom_core::escape;
use fathom_core::health::{health, Health};
use fathom_core::json::Doc;
use fathom_core::structure::{classify, containers, fold_recursion};

/// Every byte this binary prints to stdout goes through here, and the reason is
/// a defect rather than tidiness.
///
/// **`println!` PANICS when the far end stops reading**, because Rust ignores
/// SIGPIPE at startup and a closed pipe comes back as a write error the macro
/// unwraps. `head`, `less` and a `jq` that has seen enough all do exactly that,
/// and section 4 of `VERDICT.md` ships `--ndjson` expressly *"for a pipe into
/// `jq`"*.
///
/// **The decision this encodes was already made and already written down** — in
/// the row writers below, as *"a closed pipe is `head`, not a failure"* — and it
/// was applied at two output sites out of thirteen. Defect 37 is that gap, not a
/// missing policy. `design/sigpipe-predictions.md`.
///
/// **Restoring the default SIGPIPE disposition was the alternative and it was
/// rejected**: it kills the process at the write, so the two handlers below
/// would never run and `rows --ndjson | head` would exit 141 where today it
/// exits 0. A repair that makes a committed decision unreachable is not one. It
/// also wants `unsafe` and a raw `extern "C"`, in a workspace whose `Cargo.toml`
/// spends twenty lines justifying its single dependency.
fn emit(s: &str, newline: bool) {
    use std::io::Write;
    let stdout = std::io::stdout();
    let mut w = stdout.lock();
    let ok = w.write_all(s.as_bytes()).is_ok()
        && (!newline || w.write_all(b"\n").is_ok())
        && w.flush().is_ok();
    if !ok {
        // Nothing further can be delivered, so there is nothing to report. The
        // status matches the `return`s in the row writers, which is the whole
        // point of routing every site through one rule.
        std::process::exit(0);
    }
}

/// The string exactly as given. `print!`.
fn out(s: &str) {
    emit(s, false);
}

/// The string and a newline, written WITHOUT joining them first, so a 16 MB
/// `structure` dump is not copied to append one byte. `println!`.
fn outln(s: &str) {
    emit(s, true);
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut json = false;
    // `--candidate <label>` asks for a row shape BY THE NAME THE REPORT PRINTED,
    // which is a different question from `rows <file> <path>` and deliberately
    // a different argument. The path language navigates; a candidate label
    // selects from a menu the user has just been shown.
    let mut candidate: Option<String> = None;
    // `--ndjson` turns `rows --candidate` from a SHAPE into the rows. The shape
    // line stays the default because `test/candidates.py` reads it, and because
    // a bare `rows` on a 912 MB document should not print a million lines to a
    // terminal by accident.
    let mut ndjson = false;
    // `--tsv` is the same rows in the format both BINDINGS can read without a
    // dependency: base R has no JSON parser at all. See the writer below.
    let mut tsv = false;
    // Where to stand before doing anything. `into()` in the bindings is this
    // list and nothing else — they accumulate names, the core resolves them.
    let mut at: Vec<String> = Vec::new();
    let mut rest: Vec<&str> = Vec::new();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--json" => json = true,
            "--ndjson" => ndjson = true,
            "--tsv" => tsv = true,
            // One name per flag, repeatable, because a JSON key may contain a
            // dot and a joined path would have to guess where to split it.
            "--at" => {
                i += 1;
                match args.get(i) {
                    Some(name) => at.push(name.clone()),
                    None => {
                        eprintln!("fathom: --at needs a name to go into");
                        std::process::exit(2);
                    }
                }
            }
            "--candidate" => {
                i += 1;
                match args.get(i) {
                    Some(label) => candidate = Some(label.clone()),
                    None => {
                        eprintln!("fathom: --candidate needs the label the report printed");
                        std::process::exit(2);
                    }
                }
            }
            other => rest.push(other),
        }
        i += 1;
    }
    let (verb, path, args) = match rest.as_slice() {
        [v, p, tail @ ..] => (*v, *p, tail),
        [p] => ("health", *p, &[][..]),
        _ => {
            eprintln!("usage: fathom <probe|health|structure|rows|where> <file> [args]");
            std::process::exit(2);
        }
    };
    if !matches!(
        verb,
        "health" | "structure" | "probe" | "rows" | "where" | "whichever"
    ) {
        eprintln!(
            "fathom: unknown verb {verb:?} — probe, health, structure, rows, where, whichever"
        );
        std::process::exit(2);
    }

    let (h, mut doc) = match health(std::path::Path::new(path)) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("fathom: {path}: {e}");
            std::process::exit(1);
        }
    };
    // Stand somewhere else first, and everything after this is unchanged: the
    // walk, the fold, the classifier, the pricing and the report all run on the
    // new root. That is why `into()` needed no new machinery downstream, and why
    // its oracle is `design/probe.py` run on the same subtree.
    let mut resolved = String::new();
    if !at.is_empty() {
        let Some(dd) = doc.as_mut() else {
            eprintln!("fathom: {path}: nothing could be read, so there is nowhere to go");
            std::process::exit(1);
        };
        match fathom_core::extract::at(dd, &at) {
            Ok(p) => resolved = p,
            Err(e) => {
                eprintln!("fathom: {e}");
                std::process::exit(1);
            }
        }
    }
    // `rows` and `where` print the line `design/parity.py`'s R driver prints, so
    // the harness that already diffs Python against R can diff the core against
    // both without learning a third format.
    if verb == "whichever" {
        // `whichever name name …` — path variance, plainly. The names are the
        // trailing arguments, in the order you would try them by hand.
        let Some(dd) = doc else {
            eprintln!("fathom: {path}: nothing could be read");
            std::process::exit(1);
        };
        if args.is_empty() {
            eprintln!("fathom: whichever needs at least one name to try");
            std::process::exit(2);
        }
        let names: Vec<String> = args.iter().map(|s| s.to_string()).collect();
        let got = fathom_core::extract::whichever(&dd, &names);
        if tsv {
            let mut line = String::from("key\tvalue\n");
            for (k, v) in &got {
                escape(k, &mut line);
                line.push('\t');
                match v {
                    // An empty field means NONE of the names was there, which is
                    // the same absent-versus-null rule `rows --tsv` keeps.
                    None => {}
                    Some(id) => fathom_core::write_json(&dd, *id, &mut line),
                }
                line.push('\n');
            }
            out(&line);
        } else {
            let found = got.iter().filter(|(_, v)| v.is_some()).count();
            outln(&format!("{} {}", found, got.len()));
        }
        return;
    }
    if verb == "rows" || verb == "where" {
        let Some(dd) = doc else {
            eprintln!("fathom: {path}: nothing could be read");
            std::process::exit(1);
        };
        // `rows --candidate "an item of versions"` — the row shape the menu
        // named, resolved through the SAME pass that priced it. The sentences
        // run on 2026-08-11 measured what a second engine gets by re-deriving
        // the selection from the name: 37 of 197 wrong, in both directions.
        if let Some(label) = &candidate {
            if verb != "rows" {
                eprintln!("fathom: --candidate is for `rows`, not `{verb}`");
                std::process::exit(2);
            }
            let walk = containers(&dd);
            let fold = fold_recursion(&dd, walk);
            let cands =
                fathom_core::price::candidates_full(&dd, &fold.inst, &fold.arrs, &fold.rec);
            let Some(found) = fathom_core::price::resolve(&cands, label) else {
                eprintln!("fathom: no candidate called {label:?}. The report lists them under");
                eprintln!("        ONE ROW COULD BE; the label is the whole argument.");
                std::process::exit(1);
            };
            let t = fathom_core::price::table(&dd, &found.unit);
            if tsv {
                // The table as a header row and one line per row, EVERY CELL A
                // JSON VALUE. Both bindings read this with no dependency at all:
                // base R's `read.delim` and Python's `csv` module. That is why
                // it exists — R has no JSON parser in base, and a binding that
                // needed one would put a dependency in a package that has none,
                // which is the ground Arrow was rejected on.
                //
                // Encoding every cell as JSON does double duty: no raw tab or
                // newline can appear inside a value, so the delimiter is safe
                // without quoting rules.
                //
                // AN EMPTY FIELD MEANS THE CELL WAS ABSENT. A present-and-null
                // cell is the four characters `null`. This project has spent
                // four defects on that distinction and the wire format keeps it.
                let out = std::io::stdout();
                let mut w = std::io::BufWriter::new(out.lock());
                let mut line = String::new();
                // Column names are written RAW, with the delimiter and the line
                // ending replaced by a space, so the header needs no decoding on
                // either side. A JSON key containing a tab is possible and has
                // never occurred; the substitution is recorded rather than
                // silent.
                for (i, name) in t.names.iter().enumerate() {
                    if i > 0 {
                        line.push('\t');
                    }
                    line.extend(name.chars().map(|c| match c {
                        '\t' | '\n' | '\r' => ' ',
                        c => c,
                    }));
                }
                line.push('\n');
                let _ = std::io::Write::write_all(&mut w, line.as_bytes());
                let mut cells: Vec<Option<&fathom_core::price::Cell>> = Vec::new();
                for row in &t.rows {
                    cells.clear();
                    cells.resize(t.names.len(), None);
                    for (col, cell) in row {
                        cells[*col] = Some(cell);
                    }
                    line.clear();
                    for (i, cell) in cells.iter().enumerate() {
                        if i > 0 {
                            line.push('\t');
                        }
                        match cell {
                            None => {}
                            Some(fathom_core::price::Cell::Node(n)) => {
                                fathom_core::write_json(&dd, *n, &mut line)
                            }
                            Some(fathom_core::price::Cell::Key(s)) => {
                                escape(dd.str_at(*s), &mut line)
                            }
                        }
                    }
                    line.push('\n');
                    if std::io::Write::write_all(&mut w, line.as_bytes()).is_err() {
                        return;
                    }
                }
                let _ = std::io::Write::flush(&mut w);
                return;
            }
            if ndjson {
                // The rows themselves, one JSON object per line. Until
                // 2026-08-13 this table was built and thrown away — the shape
                // was printed and every cell discarded — because how a table
                // crossed the boundary was undecided. `design/implementation.md`
                // records the decision and why Arrow was rejected for it.
                //
                // A cell that is absent is OMITTED rather than written null,
                // because absent and null are different and this project has
                // spent four defects on the difference. A reader gets the same
                // ragged edge the document has.
                let out = std::io::stdout();
                let mut w = std::io::BufWriter::new(out.lock());
                let mut line = String::new();
                for row in &t.rows {
                    line.clear();
                    line.push('{');
                    for (i, (col, cell)) in row.iter().enumerate() {
                        if i > 0 {
                            line.push(',');
                        }
                        escape(&t.names[*col], &mut line);
                        line.push(':');
                        match cell {
                            fathom_core::price::Cell::Node(n) => {
                                fathom_core::write_json(&dd, *n, &mut line)
                            }
                            fathom_core::price::Cell::Key(s) => {
                                escape(dd.str_at(*s), &mut line)
                            }
                        }
                    }
                    line.push('}');
                    line.push('\n');
                    if std::io::Write::write_all(&mut w, line.as_bytes()).is_err() {
                        // A closed pipe is `head`, not a failure. This is
                        // `emit()`'s rule; it stays written out here because the
                        // loop streams row by row and must not build the whole
                        // table as one string to hand over.
                        return;
                    }
                }
                let _ = std::io::Write::flush(&mut w);
                return;
            }
            let (rows, cols) = t.shape();
            outln(&format!("{} {} {}", rows, cols, t.names.join("|")));
            return;
        }
        let arg = args.first().copied().unwrap_or(".");
        if verb == "rows" {
            let r = fathom_core::extract::rows(&dd, arg);
            let keys = match r.found.first() {
                Some((k, _)) if !k.is_empty() => k
                    .iter()
                    .map(|x| x.to_string())
                    .collect::<Vec<_>>()
                    .join("|"),
                _ => "-".to_string(),
            };
            outln(&format!("{} {}", r.found.len(), keys));
        } else if verb == "where" && tsv {
            // Every path that matched, FOLDED, with how many values matched at
            // it. Folding is the point rather than a nicety: the naive answer on
            // `01-npm-registry` is thousands of paths, which is the O(data)
            // failure this project exists to name, committed by fathom's own
            // word. A word that answers a question by printing the data has not
            // answered it.
            let hits = match fathom_core::extract::where_(&dd, arg) {
                Ok(h) => h,
                Err(e) => {
                    eprintln!("fathom: {e}");
                    std::process::exit(2);
                }
            };
            let mut line = String::from("path\tcount\n");
            for (p, &n) in hits.iter() {
                escape(p, &mut line);
                line.push('\t');
                line.push_str(&n.to_string());
                line.push('\n');
            }
            out(&line);
        } else {
            let hits = match fathom_core::extract::where_(&dd, arg) {
                Ok(h) => h,
                Err(e) => {
                    eprintln!("fathom: {e}");
                    std::process::exit(2);
                }
            };
            // A ZERO HERE IS A FINDING, which is why the line above refuses an
            // unknown test instead of arriving at this one. `0 0 -` means the
            // document has none, and until 2026-08-14 it also meant the test
            // was misspelt.
            if hits.is_empty() {
                outln("0 0 -");
            } else {
                // Most matches first, then the path itself. Without the second
                // key a tie is resolved by iteration order and the harness
                // reports a disagreement that is not one.
                let mut best: Option<(&str, usize)> = None;
                for (p, &n) in hits.iter() {
                    let better = match best {
                        None => true,
                        Some((bp, bn)) => n > bn || (n == bn && p < bp),
                    };
                    if better {
                        best = Some((p, n));
                    }
                }
                let (p, n) = best.unwrap();
                outln(&format!("{} {} {}|{}", hits.len(), hits.total(), p, n));
            }
        }
        return;
    }
    if verb == "probe" {
        // The whole report, and the criterion the port is judged against: this
        // must be byte-identical to `uv run design/probe.py <file>`.
        // `main()` prints only the basename, so the CLI passes only that.
        let base = path.rsplit('/').next().unwrap_or(path);
        out(&fathom_core::report::report_at(
            doc.as_ref(),
            &h,
            base,
            &resolved,
        ));
        return;
    }
    if verb == "structure" {
        match doc {
            Some(d) => outln(&structure_json(&d)),
            None => {
                eprintln!("fathom: {path}: nothing could be read");
                std::process::exit(1);
            }
        }
        return;
    }
    if json {
        outln(&as_json(&h));
    } else {
        outln(&oneline(&h));
    }
}

/// The fold, dumped for `test/parity.py` to diff against `design/probe.py`.
///
/// **This is a scoring surface, not a product.** The probe crosses the process
/// boundary as a rendered report; this exists so the walk, the classifier and
/// the recursion fold can be scored SEPARATELY, before the renderer that would
/// otherwise be the only thing a diff could see. A single big-bang comparison
/// at the end would report one difference for a document and leave which stage
/// produced it to be guessed.
fn structure_json(d: &Doc) -> String {
    let walk = containers(d);
    let mut s = String::from("{\"walk\":{");
    let counts = |m: &fathom_core::ordermap::OrderMap<Vec<u32>>| -> String {
        let mut b = String::from("[");
        for (i, (p, v)) in m.iter().enumerate() {
            if i > 0 {
                b.push(',');
            }
            b.push('[');
            escape(p, &mut b);
            b.push_str(&format!(",{}]", v.len()));
        }
        b.push(']');
        b
    };
    let tallies = |m: &fathom_core::ordermap::OrderMap<fathom_core::ordermap::Tally>| -> String {
        let mut b = String::from("[");
        for (i, (p, t)) in m.iter().enumerate() {
            if i > 0 {
                b.push(',');
            }
            b.push('[');
            escape(p, &mut b);
            b.push_str(",[");
            for (j, (k, n)) in t.iter().enumerate() {
                if j > 0 {
                    b.push(',');
                }
                b.push('[');
                escape(k, &mut b);
                b.push_str(&format!(",{n}]"));
            }
            b.push_str("]]");
        }
        b.push(']');
        b
    };

    s.push_str("\"inst\":");
    s.push_str(&counts(&walk.inst));
    s.push_str(",\"arrs\":");
    s.push_str(&counts(&walk.arrs));
    s.push_str(",\"types\":");
    s.push_str(&tallies(&walk.types));
    s.push_str("},\"fold\":{");

    let fold = fold_recursion(d, walk);
    s.push_str("\"inst\":");
    s.push_str(&counts(&fold.inst));
    s.push_str(",\"arrs\":");
    s.push_str(&counts(&fold.arrs));
    s.push_str(",\"types\":");
    s.push_str(&tallies(&fold.types));
    s.push_str(",\"rec\":[");
    for (i, (p, n)) in fold.rec.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        s.push('[');
        escape(p, &mut s);
        s.push_str(&format!(",{n}]"));
    }
    s.push_str("]},\"classify\":[");
    for (i, (p, objs)) in fold.inst.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        let (v, why) = classify(d, objs);
        s.push('[');
        escape(p, &mut s);
        s.push(',');
        escape(v.word(), &mut s);
        s.push(',');
        escape(&why, &mut s);
        s.push(']');
    }
    s.push_str("],\"measures\":[");
    for (i, (p, objs)) in fold.inst.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        let live: Vec<u32> = objs.iter().copied().filter(|&o| d.len_of(o) > 0).collect();
        s.push('[');
        escape(p, &mut s);
        s.push_str(&format!(
            ",{:?},{:?}]",
            fathom_core::split::emptiness(d, &live),
            fathom_core::split::variation(d, &live)
        ));
    }
    s.push_str("],\"splits\":[");
    for (i, (p, objs)) in fold.inst.iter().enumerate() {
        if i > 0 {
            s.push(',');
        }
        s.push('[');
        escape(p, &mut s);
        match fathom_core::split::discriminator(d, objs) {
            None => s.push_str(",null,null]"),
            Some(sp) => {
                s.push(',');
                escape(&sp.field, &mut s);
                s.push_str(",[");
                for (j, (lab, g)) in sp.groups.iter().enumerate() {
                    if j > 0 {
                        s.push(',');
                    }
                    s.push('[');
                    escape(lab, &mut s);
                    s.push_str(&format!(",{}]", g.len()));
                }
                s.push_str("]]");
            }
        }
    }
    s.push_str("],\"candidates\":[");
    for (i, c) in fathom_core::price::candidates(d, &fold.inst, &fold.arrs, &fold.rec)
        .iter()
        .enumerate()
    {
        if i > 0 {
            s.push(',');
        }
        s.push('[');
        escape(&c.label, &mut s);
        s.push_str(&format!(",{},{},", c.rows, c.cols));
        match c.holes {
            Some(h) => s.push_str(&format!("{h:?}")),
            None => s.push_str("null"),
        }
        s.push(',');
        match &c.dup {
            Some((col, n)) => {
                s.push('[');
                escape(col, &mut s);
                s.push_str(&format!(",{n:?}]"));
            }
            None => s.push_str("null"),
        }
        s.push(',');
        match &c.split {
            Some(sp) => {
                s.push('[');
                escape(&sp.field, &mut s);
                s.push_str(&format!(",{}]", sp.groups.len()));
            }
            None => s.push_str("null"),
        }
        s.push(',');
        match &c.more {
            Some((n, k, w)) => {
                s.push_str(&format!("[{n},{k},"));
                escape(w, &mut s);
                s.push(']');
            }
            None => s.push_str("null"),
        }
        s.push(']');
    }
    s.push_str("]}");
    s
}

fn as_json(h: &Health) -> String {
    let mut s = String::from("{");
    let mut first = true;
    let mut field = |s: &mut String, k: &str, v: String| {
        if !first {
            s.push(',');
        }
        first = false;
        escape(k, s);
        s.push(':');
        s.push_str(&v);
    };
    let opt_str = |v: Option<&str>| match v {
        Some(x) => {
            let mut b = String::new();
            escape(x, &mut b);
            b
        }
        None => "null".into(),
    };
    let opt_num = |v: Option<usize>| match v {
        Some(x) => x.to_string(),
        None => "null".into(),
    };
    let opt_bool = |v: Option<bool>| match v {
        Some(x) => x.to_string(),
        None => "null".into(),
    };

    field(&mut s, "bytes", h.bytes.to_string());
    field(&mut s, "format", opt_str(h.format.map(|f| f.name())));
    field(&mut s, "compressed", opt_str(h.compressed));
    field(&mut s, "packed_bytes", opt_num(h.packed_bytes));
    field(&mut s, "bom", opt_str(h.bom));
    field(&mut s, "dupes", opt_num(h.dupes));
    field(&mut s, "negzero", opt_num(h.negzero));
    field(&mut s, "nonfinite", opt_num(h.nonfinite));
    field(&mut s, "bigints", opt_num(h.bigints));
    field(&mut s, "encoded", opt_num(h.encoded));
    field(&mut s, "bad_bytes", h.bad_bytes.to_string());
    field(&mut s, "empty", opt_bool(h.empty));
    field(&mut s, "truncated", opt_bool(h.truncated));
    field(&mut s, "records", opt_num(h.records));
    field(&mut s, "lines", opt_num(h.lines));
    field(&mut s, "sampled", opt_bool(h.sampled));
    field(&mut s, "error", opt_str(h.error.as_deref()));
    let lines: Vec<String> = h
        .bad_lines
        .iter()
        .map(|(n, m)| {
            let mut b = String::new();
            escape(m, &mut b);
            format!("[{n},{b}]")
        })
        .collect();
    field(&mut s, "bad_lines", format!("[{}]", lines.join(",")));
    s.push('}');
    s
}

/// The one line the text report opens with, so the port can be eyeballed
/// before the rest of the renderer exists.
fn oneline(h: &Health) -> String {
    let b = h.bytes;
    let size = if b < 1024 {
        format!("{b} bytes")
    } else if b < 1 << 20 {
        format!("{:.0} KB", b as f64 / 1024.0)
    } else {
        format!("{:.1} MB", b as f64 / (1 << 20) as f64)
    };
    let said = match h.format {
        Some(f) => f.name().to_string(),
        None => {
            if h.empty == Some(true) {
                "empty".into()
            } else if h.truncated == Some(true) {
                "chopped off".into()
            } else {
                "not a format I recognise".into()
            }
        }
    };
    let flags = [
        ("duplicate keys", h.dupes.unwrap_or(0)),
        ("NaN/Infinity", h.nonfinite.unwrap_or(0)),
        ("ints past 2^53", h.bigints.unwrap_or(0)),
        ("negative zeros", h.negzero.unwrap_or(0)),
        ("bytes that are not valid UTF-8", h.bad_bytes),
        ("values that are themselves encoded JSON", h.encoded.unwrap_or(0)),
    ]
    .iter()
    .filter(|(_, n)| *n > 0)
    .map(|(w, n)| format!("{n} {w}"))
    .collect::<Vec<_>>();
    let tail = if flags.is_empty() {
        String::new()
    } else {
        format!(" · {}", flags.join(" · "))
    };
    format!("  {size} · {said}{tail}")
}
