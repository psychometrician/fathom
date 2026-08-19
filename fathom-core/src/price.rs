//! What could one row be? — the third of the three things the one verb answers.
//!
//! **Pricing the row shapes is the part nothing else offers.** On the first
//! corpus file, one row per version is 288 rows that are 60% empty and one row
//! per dependency edge is 4,645 rows with the package name repeated 4,645
//! times. The cost of rectangling **changes in kind with the row you pick** —
//! shallow gives you holes, deep gives you duplication — and the document tells
//! you neither.
//!
//! ## This module is a model of pandas, and that is the whole difficulty
//!
//! `design/probe.py` prices a candidate by building the table with
//! `pandas.json_normalize` and reading three things off it: the shape, the
//! `isna()` fraction, and the per-column `nunique()` of `astype(str)`.
//! `design/implementation.md` named this **the largest parity risk in the
//! port**, before any Rust was written, because a percentage that moves by one
//! point is a diff that looks like a bug in the fold.
//!
//! So the behaviour was measured rather than assumed, against **pandas 3.0.5**,
//! and two of the measurements contradicted the obvious guess:
//!
//!   * **`astype(str)` leaves a missing value missing.** It does NOT render
//!     `NaN` as the string `"nan"`, and `nunique()` then drops it. An absent
//!     key, a JSON `null` and a `None` all vanish from the count rather than
//!     collapsing into one shared string.
//!   * **The dtype decides the digits.** A column of integers with no missing
//!     value is `int64` and stringifies as `1`; the same column with one hole
//!     is `float64` and stringifies as `1.0`. Same data, different distinct
//!     count, and nothing in the JSON changed.
//!
//! **Anything here that pandas changes is a parity failure, not a bug in
//! fathom**, and `test/parity.py` is what would catch it.

use crate::json::{Doc, Kind, Member, Node};
use crate::ordermap::OrderMap;
// Defect 27's repair made the row menu depend on the alignment scan, which lives
// beside the section that prints it. The two modules now use each other, which
// is the shape of the finding: the report and the menu are one design, and a
// structure the page announces and the menu cannot name is the defect itself.
use crate::report::positional;
use crate::split::{discriminator, Split};
use crate::structure::classify;
use crate::structure::Verdict;
use std::collections::{HashMap, HashSet};

/// Python's `str(float)`, which is `repr` and is not Rust's.
///
/// The shortest round-trip digits are the same in both languages; the
/// *presentation* is not. CPython switches to exponential when the decimal
/// point sits at or below -4 or above 16, always signs the exponent and pads it
/// to two digits, and always leaves a `.0` on an integral value. Rust switches
/// far earlier and pads nothing, so `1e15` prints as `1e15` where Python writes
/// `1000000000000000.0`.
pub fn py_float(v: f64) -> String {
    if v.is_nan() {
        return "nan".to_string();
    }
    if v.is_infinite() {
        return if v > 0.0 { "inf" } else { "-inf" }.to_string();
    }
    let neg = v.is_sign_negative();
    let a = v.abs();
    if a == 0.0 {
        return if neg { "-0.0" } else { "0.0" }.to_string();
    }
    // `{:e}` gives the shortest round-trip mantissa, which is the same digit
    // string CPython's repr starts from.
    let sci = format!("{a:e}");
    let (mant, exp) = sci.split_once('e').unwrap_or((sci.as_str(), "0"));
    let exp: i32 = exp.parse().unwrap_or(0);
    let digits: String = mant.chars().filter(|c| *c != '.').collect();
    // value = 0.<digits> x 10^decpt
    let decpt = exp + 1;

    let mut out = String::new();
    if neg {
        out.push('-');
    }
    if decpt <= -4 || decpt > 16 {
        out.push_str(&digits[..1]);
        if digits.len() > 1 {
            out.push('.');
            out.push_str(&digits[1..]);
        }
        let e = decpt - 1;
        out.push('e');
        out.push(if e < 0 { '-' } else { '+' });
        out.push_str(&format!("{:02}", e.abs()));
    } else if decpt <= 0 {
        out.push_str("0.");
        for _ in 0..(-decpt) {
            out.push('0');
        }
        out.push_str(&digits);
    } else if decpt as usize >= digits.len() {
        out.push_str(&digits);
        for _ in 0..(decpt as usize - digits.len()) {
            out.push('0');
        }
        out.push_str(".0");
    } else {
        out.push_str(&digits[..decpt as usize]);
        out.push('.');
        out.push_str(&digits[decpt as usize..]);
    }
    out
}

/// A Python string literal, as `repr` writes it. Only reached INSIDE a list or
/// a dict: a bare string cell goes through `str`, which has no quotes, and that
/// asymmetry is why the integer `1` and the string `"1"` collapse to one
/// distinct value in an object column while `[1]` and `["1"]` do not.
pub fn py_str_lit(s: &str, out: &mut String) {
    let q = if s.contains('\'') && !s.contains('"') {
        '"'
    } else {
        '\''
    };
    out.push(q);
    for c in s.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c == q => {
                out.push('\\');
                out.push(c);
            }
            c if (c as u32) < 0x20 || (c as u32) == 0x7f => {
                out.push_str(&format!("\\x{:02x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out.push(q);
}

/// Python's `str` of a JSON value: a bare string keeps no quotes, everything
/// else is its `repr`. The report prints sample values and group labels this
/// way, so the asymmetry is visible output rather than an internal detail.
pub fn py_str(d: &Doc, id: u32) -> String {
    if let Some(s) = d.as_str(id) {
        return s.to_string();
    }
    let mut b = String::new();
    py_repr(d, id, &mut b);
    b
}

/// Python's `repr` of a JSON value.
pub fn py_repr(d: &Doc, id: u32, out: &mut String) {
    match d.node(id) {
        Node::Null => out.push_str("None"),
        Node::Bool(true) => out.push_str("True"),
        Node::Bool(false) => out.push_str("False"),
        Node::Int(i) => out.push_str(&i.to_string()),
        Node::BigInt(s) => out.push_str(d.str_at(s)),
        Node::Float(f) => out.push_str(&py_float(f)),
        Node::Str(s) => py_str_lit(d.str_at(s), out),
        Node::Array { .. } => {
            out.push('[');
            for (i, &e) in d.elements(id).iter().enumerate() {
                if i > 0 {
                    out.push_str(", ");
                }
                py_repr(d, e, out);
            }
            out.push(']');
        }
        Node::Object { .. } => {
            out.push('{');
            for (i, m) in d.members(id).iter().enumerate() {
                if i > 0 {
                    out.push_str(", ");
                }
                py_str_lit(d.key(m), out);
                out.push_str(": ");
                py_repr(d, m.val, out);
            }
            out.push('}');
        }
    }
}

/// The dtype pandas infers for a column, which decides how its values print.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum DType {
    Int64,
    Float64,
    Bool,
    Str,
    Object,
}

#[derive(Default)]
struct ColStats {
    /// Cells that are absent, or present and `null`. Both are `isna`.
    missing: usize,
    has_int: bool,
    has_big: bool,
    has_float: bool,
    has_bool: bool,
    has_str: bool,
    has_container: bool,
}

impl ColStats {
    fn dtype(&self) -> DType {
        // A container or a big integer lands in an object column whatever else
        // is there, and so does any mixture of families.
        if self.has_container || self.has_big {
            return DType::Object;
        }
        let families = usize::from(self.has_int || self.has_float)
            + usize::from(self.has_bool)
            + usize::from(self.has_str);
        if families > 1 {
            return DType::Object;
        }
        if self.has_int || self.has_float {
            // Integers with a hole become floats, and `1` becomes `1.0`. Same
            // data, different distinct count.
            if self.has_float || self.missing > 0 {
                return DType::Float64;
            }
            return DType::Int64;
        }
        if self.has_bool {
            return if self.missing > 0 {
                DType::Object
            } else {
                DType::Bool
            };
        }
        if self.has_str {
            return DType::Str;
        }
        // Nothing but holes.
        DType::Object
    }
}

fn note(d: &Doc, id: u32, s: &mut ColStats) {
    match d.node(id) {
        Node::Null => s.missing += 1,
        Node::Bool(_) => s.has_bool = true,
        Node::Int(_) => s.has_int = true,
        Node::BigInt(_) => s.has_big = true,
        Node::Float(_) => s.has_float = true,
        Node::Str(_) => s.has_str = true,
        Node::Array { .. } | Node::Object { .. } => s.has_container = true,
    }
}

/// What `astype(str)` puts in the cell, or `None` where it leaves a hole.
fn cell_str(d: &Doc, id: u32, dt: DType) -> Option<String> {
    if d.is_null(id) {
        return None;
    }
    Some(match dt {
        DType::Int64 => match d.node(id) {
            Node::Int(i) => i.to_string(),
            _ => String::new(),
        },
        DType::Float64 => match d.node(id) {
            Node::Int(i) => py_float(i as f64),
            Node::Float(f) => py_float(f),
            _ => String::new(),
        },
        DType::Bool => match d.node(id) {
            Node::Bool(true) => "True".to_string(),
            Node::Bool(false) => "False".to_string(),
            _ => String::new(),
        },
        // A bare string goes through `str`, not `repr`: no quotes.
        DType::Str => d.as_str(id).unwrap_or("").to_string(),
        DType::Object => match d.node(id) {
            Node::Str(s) => d.str_at(s).to_string(),
            _ => {
                let mut b = String::new();
                py_repr(d, id, &mut b);
                b
            }
        },
    })
}

/// `nested_to_record`: flatten nested DICTS with a `.`, leave lists alone.
///
/// An empty dict contributes no column at all — the key disappears rather than
/// becoming a hole — which is measured pandas behaviour and not an assumption.
fn flatten(d: &Doc, id: u32, prefix: &str, out: &mut Vec<(String, u32)>) {
    for m in d.members(id) {
        let key = if prefix.is_empty() {
            d.key(m).to_string()
        } else {
            format!("{prefix}.{}", d.key(m))
        };
        if d.kind(m.val) == Kind::Object {
            flatten(d, m.val, &key, out);
        } else {
            out.push((key, m.val));
        }
    }
}

pub struct Priced {
    pub label: String,
    pub rows: usize,
    pub cols: usize,
    pub holes: Option<f64>,
    /// `(column, how many times the most-distinct column still repeats)`
    pub dup: Option<(String, f64)>,
    pub split: Option<Split>,
    /// DEFECT 34: how many items of this NAME live at other paths, how many
    /// such paths, and the first of them in `rows.py`'s language. The printed
    /// count is one path's; this is what it leaves out.
    pub more: Option<(usize, usize, String)>,
}

/// A built table: column names, and per row the cells it actually has.
///
/// **This is the thing `price()` used to build and throw away**, and keeping it
/// is the whole of how `rows()` sits ON the fold rather than beside it. The
/// sentences run on 2026-08-11 measured what happens when a second engine
/// guesses at what a candidate name means: **37 of 197 wrong, in both
/// directions** — `an item of contributors` collected 1,596 where 7 was wanted
/// and `an entry of properties` collected 23 where 6,714 was wanted. A cell is
/// `None` where that row has no value for the column, which is `isna`.
pub struct Table {
    pub names: Vec<String>,
    pub rows: Vec<Vec<(usize, Cell)>>,
}

/// What sits in a cell.
///
/// **A JSON key is not a value and the type has to say so.** Keys live in the
/// string table and values are nodes, so the first version of this held a key's
/// span in a slot meant for a node id and indexed the wrong array — an
/// out-of-bounds panic on the first document with a keys-as-data site whose
/// values are scalars. The two are different things and the distinction is
/// load-bearing here of all places: `an entry of X` exists BECAUSE the keys are
/// data, so its key column is the more interesting of the two.
#[derive(Clone, Copy)]
pub enum Cell {
    /// A value node.
    Node(u32),
    /// An object key, as a span in the string table.
    Key(u32),
}

impl Table {
    pub fn shape(&self) -> (usize, usize) {
        (self.rows.len(), self.names.len())
    }
}

/// Flatten records into columns, exactly as `pandas.json_normalize` would.
fn build(d: &Doc, records: &[u32]) -> Table {
    let mut index: HashMap<String, usize> = HashMap::new();
    let mut names: Vec<String> = Vec::new();
    let mut rows: Vec<Vec<(usize, Cell)>> = Vec::with_capacity(records.len());
    let mut flat: Vec<(String, u32)> = Vec::new();
    for &r in records {
        flat.clear();
        flatten(d, r, "", &mut flat);
        let mut row = Vec::with_capacity(flat.len());
        for (k, v) in &flat {
            let i = match index.get(k) {
                Some(&i) => i,
                None => {
                    let i = names.len();
                    index.insert(k.clone(), i);
                    names.push(k.clone());
                    i
                }
            };
            row.push((i, Cell::Node(*v)));
        }
        rows.push(row);
    }
    Table { names, rows }
}

/// Build the table pandas would build, and read the three numbers off it.
/// `None` where `price()` returns without appending — no records, or a frame
/// with no columns.
fn price(d: &Doc, records: &[u32], label: &str, more: Option<(usize, usize, String)>) -> Option<Priced> {
    if records.is_empty() {
        return None;
    }
    let Table { names, rows } = build(d, records);
    let ncols = names.len();
    if ncols == 0 {
        return None; // `t.empty`
    }
    let nrows = rows.len();

    // Pass one: the dtype needs every value in the column before any of them
    // can be turned into a string.
    let mut stats: Vec<ColStats> = (0..ncols).map(|_| ColStats::default()).collect();
    let mut present = vec![0usize; ncols];
    for row in &rows {
        for &(c, cell) in row {
            let Cell::Node(v) = cell else { continue };
            present[c] += 1;
            note(d, v, &mut stats[c]);
        }
    }
    for c in 0..ncols {
        // An absent key is `isna` exactly as a `null` is.
        stats[c].missing += nrows - present[c];
    }
    let holes: usize = stats.iter().map(|s| s.missing).sum();

    // Pass two: distinct strings per column, holes excluded.
    let dtypes: Vec<DType> = stats.iter().map(|s| s.dtype()).collect();
    let mut distinct: Vec<HashSet<String>> = (0..ncols).map(|_| HashSet::new()).collect();
    for row in &rows {
        for &(c, cell) in row {
            let Cell::Node(v) = cell else { continue };
            if let Some(s) = cell_str(d, v, dtypes[c]) {
                distinct[c].insert(s);
            }
        }
    }

    // `max((nunique or 1, column))` — most distinct wins, and a tie goes to the
    // lexicographically larger column name, because Python is comparing the
    // whole tuple.
    let mut best: Option<(usize, &str)> = None;
    for c in 0..ncols {
        let n = distinct[c].len().max(1);
        let cand = (n, names[c].as_str());
        // `map_or` rather than the newer `is_none_or`: the workspace declares
        // `rust-version = "1.75"` and that one is stable from 1.82. The MSRV is
        // not decoration — it is what a vendored CRAN build has to satisfy.
        #[allow(clippy::unnecessary_map_or)]
        if best.map_or(true, |b| cand > b) {
            best = Some(cand);
        }
    }
    let (worst_n, worst_col) = best.unwrap();
    let dup = nrows as f64 / worst_n as f64;

    Some(Priced {
        label: label.to_string(),
        rows: nrows,
        cols: ncols,
        holes: Some(holes as f64 / (nrows * ncols) as f64),
        dup: if dup > 2.0 {
            Some((worst_col.to_string(), dup))
        } else {
            None
        },
        split: discriminator(d, records),
        more,
    })
}

/// A path ending in the fold's marker, named in the language a reader types.
///
/// DEFECT 28, repaired 2026-08-12. The fold replaces a container's key with
/// `<key>` when its keys are data — `extract.rs` — so a path can END in the
/// marker and the label came out as `an item of <key>`: correct inside the
/// fold, and a name nobody can type.
///
/// **`<key>` is the fold's spelling of `*` and nothing else.** `design/rows.py`
/// defines `*` as *every child, object values and array elements alike*, and
/// requires the key at every `*` to survive into the table as data. So this
/// invents no notation; it writes an internal marker in the external language.
///
/// **The bare name one level up was tried first and it DELETES the line**:
/// `aliases` is itself a keys-as-data site, so `an entry of aliases` already
/// held that name in `seen`. An untypeable candidate traded for a missing one
/// is worse, and the two units differ — an ENTRY of aliases is one row per
/// language, an ITEM of `aliases.*` is one row per alias.
///
/// **The larger half is a COLLISION.** `<key>` is the same string at every
/// keyed site, so `seen` treated four unrelated sites on `10-wikidata` as one
/// name and printed only the first.
fn above_marker(p: &str) -> String {
    let mut segs: Vec<&str> = p
        .split('.')
        .map(|s| s.trim_end_matches(['[', ']']))
        .collect();
    let mut stars = 0;
    while segs.last() == Some(&"<key>") {
        segs.pop();
        stars += 1;
    }
    if stars == 0 {
        // The callers only ask about a path whose last segment IS the marker.
        return "$".to_string();
    }
    // DEFECT 30, repaired 2026-08-12. Markers all the way to the root — a
    // document whose ROOT keys are data. The first version returned `$` here
    // and both callers skip on `$`, so `27-grafana-dashboard` lost a line that
    // had printed before defect 28's repair. **The root case needs no new rule;
    // it is this rule with an empty base**: a name followed by one `.*` per
    // marker becomes, with no name, one `*` per marker. `design/rows.py`
    // already defines a bare `*` as every child of the document.
    match segs.last() {
        None | Some(&"$") => vec!["*"; stars].join("."),
        Some(s) => format!("{}{}", s, ".*".repeat(stars)),
    }
}

/// A probe path as `design/rows.py` would write it, segment by segment.
///
/// The probe writes `types[]` for an array's elements and `<key>` where keys
/// are data. `rows.py` writes one thing for both: `*` is every child, object
/// values and array elements alike.
fn rows_path(p: &str) -> Vec<String> {
    let mut out = Vec::new();
    for seg in p.split('.').skip(1) {
        let star = seg.ends_with("[]");
        let name = if star { &seg[..seg.len() - 2] } else { seg };
        out.push(if name == "<key>" { "*" } else { name }.to_string());
        if star {
            out.push("*".to_string());
        }
    }
    out
}

/// `a node at any depth`, qualified ONLY where the depth alone collides.
///
/// DEFECT 29, repaired 2026-08-12. The label was the depth and nothing else, so
/// `07-graphql-introspection` printed `(4 levels)` three times and
/// `09-stripe-openapi` printed `(2 levels)` six times — **seven candidates that
/// could not be selected**, including stripe's largest table at 2,542 x 393.
///
/// **Naming the shape does not fix it**: graphql's four recursive shapes are all
/// called `type` and three of stripe's are called `items`. The qualifier is the
/// shortest suffix separating a shape from its rivals, and only shapes that
/// collide get one, so 24 of 26 corpus reports are untouched.
fn recursion_labels(paths: &[&str], rec: &OrderMap<usize>) -> HashMap<String, String> {
    let base: Vec<String> = paths
        .iter()
        .map(|p| format!("a node at any depth ({} levels)", rec.get(p).unwrap() + 1))
        .collect();
    let mut clashes: HashMap<&str, usize> = HashMap::new();
    for b in &base {
        *clashes.entry(b.as_str()).or_insert(0) += 1;
    }
    let rendered: Vec<Vec<String>> = paths.iter().map(|p| rows_path(p)).collect();

    let mut out = HashMap::new();
    for (i, p) in paths.iter().enumerate() {
        if clashes[base[i].as_str()] == 1 {
            out.insert(p.to_string(), base[i].clone());
            continue;
        }
        let rivals: Vec<usize> = (0..paths.len()).filter(|&j| base[j] == base[i]).collect();
        let segs = &rendered[i];
        let mut suffix = segs.join(".");
        for k in 1..=segs.len() {
            let here = segs[segs.len() - k..].join(".");
            let hits = rivals
                .iter()
                .filter(|&&j| {
                    let r = &rendered[j];
                    r.len() >= k && r[r.len() - k..].join(".") == here
                })
                .count();
            if hits == 1 {
                suffix = here;
                break;
            }
        }
        out.insert(
            p.to_string(),
            format!(
                "a node at any depth in {} ({} levels)",
                suffix,
                rec.get(p).unwrap() + 1
            ),
        );
    }
    out
}

/// What a candidate is made OF, kept so its table can be rebuilt without
/// re-deriving the selection from its name.
///
/// **A row is not always an object, and pretending it is would be the bug.**
/// Four of the five kinds here are not record-shaped: the document itself, a
/// keyed container whose values are scalars, an array of scalars, and a set of
/// equal-length sibling arrays where a row is a POSITION rather than a node.
pub enum Unit {
    /// Objects flattened into columns — what `price()` measures.
    Records(Vec<u32>),
    /// The document itself: one row, one column per top-level member.
    Document,
    /// Elements that are not all objects: one column, one row each.
    Items(Vec<u32>),
    /// A keyed container whose values are not all objects: key and value.
    Entries(Vec<Member>),
    /// Equal-length sibling arrays under one parent — defect 27's candidate.
    /// One row per position per instance, one column per array.
    Positions {
        names: Vec<String>,
        arrays: Vec<Vec<u32>>,
        n: usize,
    },
}

/// A priced row shape and the thing it was priced FROM.
pub struct Candidate {
    pub priced: Priced,
    pub unit: Unit,
}

/// Row shapes, computed on the FOLD rather than on the data.
///
/// The first version of this recursed into raw values and emitted one candidate
/// per version, producing 1,239 lines on a 786 KB file — reproducing the exact
/// O(data) failure the probe exists to prevent. **The fold is not a display
/// step.**
pub fn candidates(
    d: &Doc,
    inst: &OrderMap<Vec<u32>>,
    arrs: &OrderMap<Vec<u32>>,
    rec: &OrderMap<usize>,
) -> Vec<Priced> {
    candidates_full(d, inst, arrs, rec)
        .into_iter()
        .map(|c| c.priced)
        .collect()
}

/// `candidates()`, keeping what each one was built from.
///
/// **This is the one function, and `candidates()` is a projection of it.** The
/// sentences run proved a second engine cannot re-derive the candidate set from
/// the name — the probe's rule comes from its FOLD, which knows which
/// occurrences a candidate covers — so `rows()` reads the selection off the
/// same pass that printed the menu rather than reconstructing it.
pub fn candidates_full(
    d: &Doc,
    inst: &OrderMap<Vec<u32>>,
    arrs: &OrderMap<Vec<u32>>,
    rec: &OrderMap<usize>,
) -> Vec<Candidate> {
    let mut out: Vec<Candidate> = Vec::new();
    let plain = |label: String, rows: usize, cols: usize| Priced {
        label,
        rows,
        cols,
        holes: None,
        dup: None,
        split: None,
        more: None,
    };

    let root = d.root();
    // A top-level array is the whole point of NDJSON, and the array loop below
    // skips `$`, so it has to be named here or the format with the most obvious
    // row shape in the world would offer none.
    if d.kind(root) == Kind::Array {
        let items = d.elements(root).to_vec();
        if !items.is_empty() && items.iter().all(|&i| d.kind(i) == Kind::Object) {
            if let Some(p) = price(d, &items, "a record", None) {
                out.push(Candidate {
                    priced: p,
                    unit: Unit::Records(items),
                });
            }
        } else {
            out.push(Candidate {
                priced: plain("a record".into(), items.len(), 1),
                unit: Unit::Items(items),
            });
        }
    } else {
        // `len(doc)`, and Python's `len` is not only "how many members".
        //
        // **`trap/double_serialised.json` is the whole document as ONE STRING
        // containing JSON**, so the root is a scalar and `len` counts its
        // CHARACTERS — 23 of them, reported as 23 columns. It is a nonsense
        // number and it is the oracle's nonsense number, so the port makes it
        // too. Found by the diff; a reasonable guess had returned 0.
        //
        // A root that is a bare number or a bare `true` raises `TypeError` in
        // the probe and takes the whole report down. Nothing in the corpus or
        // the suite is one, and crashing is not a behaviour worth reproducing,
        // so this answers 0 and the divergence is recorded here rather than
        // hidden.
        let n = match d.kind(root) {
            Kind::Object | Kind::Array => d.len_of(root),
            Kind::Text => d.as_str(root).map_or(0, |s| s.chars().count()),
            _ => 0,
        };
        out.push(Candidate {
            priced: plain("the whole document".into(), 1, n),
            unit: Unit::Document,
        });
    }

    let mut paths: Vec<&str> = inst.keys().collect();
    paths.sort_unstable();

    // A recursive shape's row count is the whole tree, not the top level.
    let recursive: Vec<&str> = paths
        .iter()
        .copied()
        .filter(|p| rec.get(p).map_or(false, |&l| l > 0))
        .collect();
    let labels = recursion_labels(&recursive, rec);
    for p in &paths {
        if let Some(&levels) = rec.get(p) {
            if levels > 0 {
                let objs = inst.get(p).unwrap();
                if let Some(pr) = price(d, objs, &labels[*p], None) {
                    out.push(Candidate {
                        priced: pr,
                        unit: Unit::Records(objs.clone()),
                    });
                }
            }
        }
    }

    // DEFECT 39, repaired 2026-08-18. **Defect 34's repair went to the ARRAY
    // loop below and this one never got it.** The diagnosis there is this
    // loop's verbatim: `seen` keeps the first path in sorted order for a name
    // and drops the rest silently, so the printed count is ONE path's while the
    // reader reads it as the count of the word.
    //
    // It did not need a second document — it had five. 50 of 161 keyed
    // candidate names hide a second path and 38 drop the BIGGER one; entry 30
    // printed `an entry of priceDimensions — 1,643` where the document holds
    // 4,505. The repair is defect 34's: the count stays, the page says what it
    // left out. `uv run design/candidate-twins.py`.
    //
    // `classify` is asked ONCE per site and carried, because it is the
    // expensive call here and a pre-pass would otherwise double it.
    let mut keyed: Vec<(&str, String, Vec<Member>)> = Vec::new();
    for p in &paths {
        let objs = inst.get(p).unwrap();
        if *p == "$" || classify(d, objs).0 != Verdict::Data {
            continue;
        }
        let mut name = p.rsplit('.').next().unwrap_or(p).to_string();
        if name == "<key>" {
            name = above_marker(p);
        }
        // `$` is checked BEFORE any de-duplication, because the oracle's `or`
        // short circuits and never puts `$` in `seen`.
        if name == "$" {
            continue;
        }
        let members: Vec<Member> = objs
            .iter()
            .flat_map(|&o| d.members(o).iter().copied())
            .collect();
        keyed.push((p, name, members));
    }

    // **A TWIN IS ANY KEYED SITE OF THAT NAME, not only a record-valued one,
    // and the difference is 10 modifiers against 51.** Restricting it to
    // record-valued sites is what the plumbing makes easy — `more` rides
    // through `price()` and the scalar branch below builds its `Priced` by hand
    // — and it is not what the defect is. `20-homebrew-formulae` prints
    // `an entry of uses_from_macos[] — 84` while another keyed site of that
    // name holds 943.
    //
    // **It never compares unlike things**: all 305 twin relationships this
    // widening adds are scalar-to-scalar, and the corpus holds ZERO where a
    // record-valued candidate has a scalar twin. That branch is therefore
    // unreachable here and untested — stated in advance rather than after.
    let mut keyed_by_name: HashMap<String, Vec<(&str, usize)>> = HashMap::new();
    for (q, qname, qmembers) in &keyed {
        if !qmembers.is_empty() {
            keyed_by_name
                .entry(qname.clone())
                .or_default()
                .push((q, qmembers.len()));
        }
    }

    let mut seen: HashSet<String> = HashSet::new();
    for (p, name, members) in &keyed {
        // An empty site still CLAIMS the name, as the oracle does.
        if !seen.insert(name.clone()) {
            continue;
        }
        let vals: Vec<u32> = members.iter().map(|m| m.val).collect();
        if vals.is_empty() {
            continue;
        }
        let twins: Vec<&(&str, usize)> = keyed_by_name
            .get(name)
            .map(|v| v.iter().filter(|(q, _)| q != p).collect())
            .unwrap_or_default();
        let more = if twins.is_empty() {
            None
        } else {
            Some((
                twins.iter().map(|(_, n)| *n).sum(),
                twins.len(),
                rows_path(twins[0].0).join("."),
            ))
        };
        if vals.iter().all(|&v| d.kind(v) == Kind::Object) {
            if let Some(pr) = price(d, &vals, &format!("an entry of {name}"), more) {
                out.push(Candidate {
                    priced: pr,
                    unit: Unit::Records(vals),
                });
            }
        } else {
            out.push(Candidate {
                priced: Priced {
                    more,
                    ..plain(format!("an entry of {name}"), vals.len(), 2)
                },
                unit: Unit::Entries(members.clone()),
            });
        }
    }

    // DEFECT 34, repaired 2026-08-13. `seen` keeps the FIRST path in sorted
    // order for a name and drops the rest silently, so the printed count is one
    // path's while the reader reads it as the count of the word. On
    // `27-grafana-dashboard` the menu said 31 panels where there are 132, and
    // 225 targets where there are 269 — from OPPOSITE levels, by lexicographic
    // accident. Naming both was measured and rejected: 22 extra candidates on
    // stripe, 122 paths for one name on MDN. The count stays and the page SAYS
    // what it left out. 41 lines across the corpus.
    let mut apaths: Vec<&str> = arrs.keys().collect();
    apaths.sort_unstable();
    let mut by_name: HashMap<String, Vec<(&str, usize)>> = HashMap::new();
    for q in &apaths {
        let stem = q.trim_end_matches(['[', ']']);
        let mut nm = stem.rsplit('.').next().unwrap_or(stem).to_string();
        if nm == "<key>" {
            nm = above_marker(stem);
        }
        let items: Vec<u32> = arrs
            .get(q)
            .unwrap()
            .iter()
            .flat_map(|&l| d.elements(l).iter().copied())
            .collect();
        if !items.is_empty() && items.iter().all(|&i| d.kind(i) == Kind::Object) {
            by_name.entry(nm).or_default().push((*q, items.len()));
        }
    }
    // DEFECT 39, SECOND FACET, repaired 2026-08-18. **`seen` used to be shared
    // with the keyed loop above**, which runs first — so an array site whose
    // bare name a keyed site had already claimed was skipped entirely and no
    // candidate was offered for it at all. 16 of them on
    // `29-mdn-browser-compat`, including `chrome` at 120 items.
    //
    // **The two loops emit DIFFERENT labels** — `an entry of X` against
    // `an item of X` — so nothing could ever have collided. The shared set
    // reads as deliberate and is not: this loop was written second and reused
    // the name in scope.
    let mut seen_arrays: HashSet<String> = HashSet::new();
    for p in &apaths {
        let stem = p.trim_end_matches(['[', ']']);
        let mut name = stem.rsplit('.').next().unwrap_or(stem).to_string();
        if name == "<key>" {
            name = above_marker(stem);
        }
        // DEFECT 41, repaired 2026-08-19. **The claim used to sit ABOVE the
        // record test** — it was the `!seen_arrays.insert(..)` in this very
        // condition, which checks and claims in one move — so the first path in
        // sorted order took the name whether or not it produced anything.
        // `12-agent-trace` has `$[].attachment.content`, 66 arrays and every
        // one EMPTY, sorting before `message`: `$[].message.content` at 1,363
        // records over 11 fields was never offered. The claim is still made
        // BEFORE `price()`, which may decline, exactly as the oracle does.
        if name == "$" || seen_arrays.contains(&name) {
            continue;
        }
        let items: Vec<u32> = arrs
            .get(p)
            .unwrap()
            .iter()
            .flat_map(|&l| d.elements(l).iter().copied())
            .collect();
        if items.is_empty() || !items.iter().all(|&i| d.kind(i) == Kind::Object) {
            continue;
        }
        seen_arrays.insert(name.clone());
        let twins: Vec<&(&str, usize)> = by_name
            .get(&name)
            .map(|v| v.iter().filter(|(q, _)| q != p).collect())
            .unwrap_or_default();
        let more = if twins.is_empty() {
            None
        } else {
            Some((
                twins.iter().map(|(_, n)| *n).sum(),
                twins.len(),
                rows_path(twins[0].0.trim_end_matches(['[', ']'])).join("."),
            ))
        };
        if let Some(pr) = price(d, &items, &format!("an item of {name}"), more) {
            out.push(Candidate {
                priced: pr,
                unit: Unit::Records(items),
            });
        }
    }

    // DEFECT 27, repaired 2026-08-11. The probe DETECTED positional alignment,
    // printed it, and then offered no way to ask for it. On `06-espn-qbr` the
    // four arrays under `$.categories[]` are a 10 x 4 table the menu never
    // mentioned — while `an item of glossary`, the alphabetically sorted decoy
    // the section above warns against joining, WAS offered. `08-open-meteo` is
    // the worse case: its entire menu was one line, `the whole document`, and
    // the 336 x 5 table that IS the document was absent.
    //
    // ONE CANDIDATE PER PARENT, not one per length group, because THE PARENT IS
    // THE TABLE is the rule `positional` already enforces. File 06's group of
    // six paths spans two parents holding 1 and 28 instances, so a single 10 x 6
    // candidate would name a table that cannot be built without the very join
    // the section above forbids — same length is not same order.
    //
    // NAMED BY PATH, and the bare name was tried first. Both of file 06's
    // parents end in `categories` and `an item of categories` is already in the
    // menu, so every bare-name scheme either collides or drops the one table the
    // defect names. A candidate a reader cannot type is defect 28.
    //
    // ROWS POOL ACROSS INSTANCES, like every other candidate here, and the
    // instance count is the largest any of the parent's columns has: a column
    // missing from some instances is a hole in the table, not fewer rows.
    //
    // NOT PRICED THROUGH `price`. Emptiness is zero by construction and there
    // are no records to find a discriminator in, so building the table to learn
    // that would contradict the rule this function opens with.
    for (n, ps) in positional(d, arrs) {
        // The instance LISTS are kept now, not just their counts, because
        // `rows()` has to be able to build this table and a count cannot.
        let mut by_parent: OrderMap<Vec<(&str, Vec<u32>)>> = OrderMap::new();
        for (p, _) in &ps {
            let parent = match p.rfind('.') {
                Some(i) => &p[..i],
                None => "",
            };
            let lists = arrs.get(p).cloned().unwrap_or_default();
            by_parent.entry(parent).push((*p, lists));
        }
        let mut parents: Vec<(&str, &Vec<(&str, Vec<u32>)>)> = by_parent.iter().collect();
        parents.sort_by(|a, b| a.0.cmp(b.0));
        for (parent, cols) in parents {
            let instances = cols.iter().map(|(_, l)| l.len()).max().unwrap_or(0);
            out.push(Candidate {
                priced: plain(
                    format!("a position in {parent}"),
                    n * instances,
                    cols.len(),
                ),
                unit: Unit::Positions {
                    names: cols
                        .iter()
                        .map(|(p, _)| {
                            let stem = p.trim_end_matches(['[', ']']);
                            stem.rsplit('.').next().unwrap_or(stem).to_string()
                        })
                        .collect(),
                    arrays: cols.iter().map(|(_, l)| l.clone()).collect(),
                    n,
                },
            });
        }
    }
    out
}

/// The table a candidate names, built on demand.
///
/// **Building it is O(data) and that is correct.** The DESCRIPTION must be
/// proportional to the structure — that is the project's whole claim — but an
/// extraction is asked for by name, once, and its answer is the rows. What
/// would be wrong is pricing the menu this way, which is the failure
/// `candidates()` opens by describing.
pub fn table(d: &Doc, unit: &Unit) -> Table {
    match unit {
        Unit::Records(records) => build(d, records),
        Unit::Document => {
            let root = d.root();
            let mut names = Vec::new();
            let mut row = Vec::new();
            if d.kind(root) == Kind::Object {
                for (i, m) in d.members(root).iter().enumerate() {
                    names.push(d.key(m).to_string());
                    row.push((i, Cell::Node(m.val)));
                }
            }
            Table {
                names,
                rows: vec![row],
            }
        }
        Unit::Items(items) => Table {
            names: vec!["value".to_string()],
            rows: items.iter().map(|&i| vec![(0, Cell::Node(i))]).collect(),
        },
        Unit::Entries(members) => Table {
            names: vec!["key".to_string(), "value".to_string()],
            rows: members
                .iter()
                .map(|m| vec![(0, Cell::Key(m.key)), (1, Cell::Node(m.val))])
                .collect(),
        },
        Unit::Positions { names, arrays, n } => {
            let instances = arrays.iter().map(|l| l.len()).max().unwrap_or(0);
            let mut rows = Vec::with_capacity(n * instances);
            for i in 0..instances {
                for pos in 0..*n {
                    let mut row = Vec::with_capacity(arrays.len());
                    for (c, lists) in arrays.iter().enumerate() {
                        // A column absent from this instance is a HOLE, which
                        // is why the row count is the largest instance count
                        // rather than the smallest.
                        if let Some(&list) = lists.get(i) {
                            if let Some(&v) = d.elements(list).get(pos) {
                                row.push((c, Cell::Node(v)));
                            }
                        }
                    }
                    rows.push(row);
                }
            }
            Table {
                names: names.clone(),
                rows,
            }
        }
    }
}

/// Find the candidate a reader typed, by the exact label the report printed.
///
/// **The label is the whole argument**, which is the 2026-08-11 finding: a bare
/// field name cannot distinguish `an item of children` from `a node at any
/// depth`, and `rows("children")` returned 335 where 25 was wanted.
pub fn resolve<'a>(candidates: &'a [Candidate], label: &str) -> Option<&'a Candidate> {
    candidates.iter().find(|c| c.priced.label == label)
}
