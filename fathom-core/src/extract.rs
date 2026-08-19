//! The extract half: `rows`, `first_present`, `take` and `where`.
//!
//! The probe answers *what is in here*. These four take what you asked for, and
//! each earned its place against a rule that is deliberately hard to satisfy: a
//! word belongs only if removing it makes one of the fixed questions
//! unanswerable on at least one corpus file.
//!
//! **The oracles are `design/rows.py`, `first_present.py`, `take.py` and
//! `where.py`**, and `design/parity.py`'s nineteen sentences are the contract.
//! Those nineteen already agree across two independent implementations, Python
//! and a hand-written R; this is the third, and it has to agree with both.
//!
//! ## The path language, and why it is four rules rather than a query syntax
//!
//! ```text
//!   .            the document itself, one row
//!   name         the field called `name`
//!   "1.0.0"      a field whose name needs quoting
//!   *            every child — object values and array elements alike
//!   name**       follow `name` repeatedly: the answer for a recursive document
//!   **           every descendant (a firehose, and rarely what anybody means)
//! ```
//!
//! Each was forced by a corpus file rather than chosen. `*` ignores the
//! object/array distinction because npm's `versions` is keyed and GeoJSON's
//! `features` is an array and a user wants one row per thing in both. The key
//! at every `*` survives into the table because dropping it throws away
//! `1.0.0`, the most important column in the file. Dots inside a key are not
//! separators, because npm's keys ARE version numbers. And recursion is one
//! step taken again, not every step: bare `**` returned 4,690 rows for a
//! 335-comment thread by descending into `author` and `text` as eagerly as into
//! `children`.

use crate::json::{Doc, Kind, Node};
use crate::ordermap::OrderMap;
use crate::structure::fold_set;

/// A captured key. An object contributes its name, an array its position, and
/// `str()` of either is what the parity harness compares.
#[derive(Clone, Debug, PartialEq)]
pub enum Key {
    Name(String),
    Index(usize),
}

impl std::fmt::Display for Key {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Key::Name(s) => f.write_str(s),
            Key::Index(i) => write!(f, "{i}"),
        }
    }
}

/// A path string into segments. `.` alone is the empty path: the document.
///
/// This is `SEGMENT = re.compile(r'"((?:[^"\\]|\\.)*)"|([^.]+)')` written as a
/// scan. The alternation is tried in order at each position, so a `"` only
/// begins a quoted segment when the quote actually closes; otherwise the
/// second branch swallows it as ordinary text. A `.` matches neither branch and
/// is therefore skipped, which is what makes it the separator.
///
/// **The quoted form is not unescaped**, matching Python: the regex captures
/// the raw inner text, backslashes and all.
pub fn parse(path: &str) -> Vec<String> {
    let p = path.trim();
    if p == "." || p.is_empty() {
        return Vec::new();
    }
    let b = p.as_bytes();
    let mut out = Vec::new();
    let mut i = 0usize;
    while i < b.len() {
        if b[i] == b'"' {
            // Try the quoted branch: `(?:[^"\\]|\\.)*` then a closing quote.
            let mut j = i + 1;
            let mut ok = false;
            while j < b.len() {
                if b[j] == b'\\' {
                    j += 2;
                } else if b[j] == b'"' {
                    ok = true;
                    break;
                } else {
                    j += 1;
                }
            }
            if ok && j <= b.len() {
                out.push(p[i + 1..j].to_string());
                i = j + 1;
                continue;
            }
        }
        if b[i] == b'.' {
            i += 1;
            continue;
        }
        let start = i;
        while i < b.len() && b[i] != b'.' {
            i += 1;
        }
        out.push(p[start..i].to_string());
    }
    out
}

/// `(key, value)` for every child — an object's items or an array's positions.
///
/// The unification is the point: a caller asking for one row per version and
/// one row per feature is asking one question, and only the document
/// distinguishes them.
fn children(d: &Doc, node: u32) -> Vec<(Key, u32)> {
    match d.kind(node) {
        Kind::Object => d
            .members(node)
            .iter()
            .map(|m| (Key::Name(d.key(m).to_string()), m.val))
            .collect(),
        Kind::Array => d
            .elements(node)
            .iter()
            .enumerate()
            .map(|(i, &v)| (Key::Index(i), v))
            .collect(),
        _ => Vec::new(),
    }
}

/// Every match of `segs` against `node`, as `(captured keys, value)`.
///
/// **The traversal order is load-bearing** and is Python's exactly: both
/// repeat forms use a LIFO stack, so a descent takes the LAST child first,
/// while the yields at one level come out in child order. `design/parity.py`
/// compares the FIRST match's captured keys, so an order that merely finds the
/// same set would be reported as a disagreement.
pub fn match_path(d: &Doc, node: u32, segs: &[String]) -> Vec<(Vec<Key>, u32)> {
    let mut out = Vec::new();
    let mut keys = Vec::new();
    go(d, node, segs, &mut keys, &mut out);
    out
}

fn go(d: &Doc, node: u32, segs: &[String], keys: &mut Vec<Key>, out: &mut Vec<(Vec<Key>, u32)>) {
    if segs.is_empty() {
        out.push((keys.clone(), node));
        return;
    }
    let head = &segs[0];
    let rest = &segs[1..];

    if head == "*" {
        for (k, v) in children(d, node) {
            keys.push(k);
            go(d, v, rest, keys, out);
            keys.pop();
        }
        return;
    }

    // `children**` — follow a NAMED step repeatedly. The bare form below is a
    // firehose; this one names the step, which is what a recursive document
    // actually means.
    let named = head.ends_with("**") && head.chars().count() > 2;
    if named {
        let name = &head[..head.len() - 2];
        let mut stack = vec![node];
        while let Some(n) = stack.pop() {
            if d.kind(n) != Kind::Object {
                continue;
            }
            let Some(target) = d.get(n, name) else { continue };
            for (k, v) in children(d, target) {
                keys.push(k);
                go(d, v, rest, keys, out);
                keys.pop();
                stack.push(v);
            }
        }
        return;
    }

    if head == "**" {
        let mut stack = children(d, node);
        while let Some((k, v)) = stack.pop() {
            keys.push(k);
            go(d, v, rest, keys, out);
            keys.pop();
            stack.extend(children(d, v));
        }
        return;
    }

    // A named field. The captured keys do NOT grow: only a `*` contributes a
    // column.
    if d.kind(node) == Kind::Object {
        if let Some(v) = d.get(node, head) {
            go(d, v, rest, keys, out);
        }
    }
    // A segment that does not match yields nothing, which is the honest answer.
}

/// The column names a path's stars contribute, disambiguated on repeat.
///
/// `versions.*.dependencies.*` gives `versions` and `dependencies`, so a
/// dependency edge lands as three columns — which no path-taking tool gives you
/// without extra work.
fn star_columns(segs: &[String]) -> Vec<String> {
    let mut names: Vec<String> = Vec::new();
    for (i, s) in segs.iter().enumerate() {
        let is_star = s == "*" || s.ends_with("**");
        if !is_star {
            continue;
        }
        if s.ends_with("**") {
            let stem = &s[..s.len() - 2];
            names.push(if stem.is_empty() {
                "item".to_string()
            } else {
                stem.to_string()
            });
        } else if i > 0 {
            names.push(segs[i - 1].clone());
        } else {
            names.push("item".to_string());
        }
    }
    let mut seen: OrderMap<usize> = OrderMap::new();
    let mut cols = Vec::with_capacity(names.len());
    for n in names {
        let c = seen.entry(&n);
        *c += 1;
        let k = *c;
        cols.push(if k == 1 { n } else { format!("{n}{k}") });
    }
    cols
}

/// One row per match. Every `*` becomes a column; the value supplies the rest.
pub struct Rows {
    /// The columns the stars contributed, after collision renaming.
    pub key_cols: Vec<String>,
    /// `(captured keys, matched value)`, in match order.
    pub found: Vec<(Vec<Key>, u32)>,
}

pub fn rows(d: &Doc, path: &str) -> Rows {
    let segs = parse(path);
    let mut cols = star_columns(&segs);
    let found = match_path(d, d.root(), &segs);

    // A captured key can collide with a field of the record it came from:
    // `children**` names its key column `children`, and every comment also HAS
    // a `children` field, so the index was silently overwritten by the subtree.
    // Resolved once for the whole table rather than per row, so the columns
    // stay the same shape for every record.
    let mut fields: std::collections::HashSet<&str> = std::collections::HashSet::new();
    for (_, v) in &found {
        if d.kind(*v) == Kind::Object {
            for m in d.members(*v) {
                fields.insert(d.key(m));
            }
        }
    }
    for c in cols.iter_mut() {
        if fields.contains(c.as_str()) {
            *c = format!("{c}_key");
        }
    }
    Rows {
        key_cols: cols,
        found,
    }
}

/// The value at the first of `paths` that is there. `None` if none are.
///
/// **Both halves of the name carry something people get wrong.** `first` says
/// the arguments are a priority order rather than a set; `present` says the
/// only value skipped is a missing one, **so a zero comes back**.
pub fn first_present(d: &Doc, node: u32, paths: &[String]) -> Option<u32> {
    for p in paths {
        for (_k, v) in match_path(d, node, &parse(p)) {
            if !d.is_null(v) {
                return Some(v);
            }
        }
    }
    None
}

/// One row per record, one column per path. **Nothing else is built** — that is
/// the whole of it, and the measured claim is that it skips 97.9% of the cells
/// a general-purpose flattener would materialise.
pub fn take(d: &Doc, records: &[u32], paths: &[String]) -> (Vec<String>, Vec<Vec<Option<u32>>>) {
    let mut seen: OrderMap<usize> = OrderMap::new();
    let mut names = Vec::with_capacity(paths.len());
    for p in paths {
        let segs = parse(p);
        let last = segs.last().cloned().unwrap_or_default();
        let c = seen.entry(&last);
        *c += 1;
        let k = *c;
        names.push(if k == 1 { last } else { format!("{last}{k}") });
    }
    let out = records
        .iter()
        .map(|&r| {
            paths
                .iter()
                .map(|p| match_path(d, r, &parse(p)).first().map(|(_, v)| *v))
                .collect()
        })
        .collect();
    (names, out)
}

// ── where ────────────────────────────────────────────────────────────────────

/// Python's `\s` for the purposes of the email predicate.
fn is_space(c: char) -> bool {
    c.is_whitespace()
}

/// `^[^@\s]+@[^@\s]+\.[^@\s]+$`
fn is_email(s: &str) -> bool {
    let mut parts = s.split('@');
    let (Some(local), Some(domain), None) = (parts.next(), parts.next(), parts.next()) else {
        return false;
    };
    if local.is_empty() || domain.is_empty() {
        return false;
    }
    if local.chars().any(is_space) || domain.chars().any(is_space) {
        return false;
    }
    // The greedy `[^@\s]+` before `\.` means the domain needs a dot that is
    // neither first nor last.
    match domain.rfind('.') {
        Some(i) => i > 0 && i + 1 < domain.len(),
        None => false,
    }
}

/// `^(https?|git\+https?|ftp)://`, case-insensitive.
fn is_url(s: &str) -> bool {
    let head: String = s.chars().take(14).flat_map(|c| c.to_lowercase()).collect();
    ["http://", "https://", "git+http://", "git+https://", "ftp://"]
        .iter()
        .any(|p| head.starts_with(p))
}

/// `^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2})?`
///
/// The trailing group is optional and nothing is anchored at the end, so the
/// predicate is exactly "starts with a `YYYY-MM-DD`".
///
/// **One known divergence, written down rather than hidden**: Python's `\d`
/// matches any Unicode decimal digit and this matches ASCII. No corpus document
/// dates anything in Devanagari.
fn is_iso_date(s: &str) -> bool {
    let b = s.as_bytes();
    if b.len() < 10 {
        return false;
    }
    let d = |i: usize| b[i].is_ascii_digit();
    d(0) && d(1) && d(2) && d(3) && b[4] == b'-' && d(5) && d(6) && b[7] == b'-' && d(8) && d(9)
}

fn is_empty_value(d: &Doc, id: u32) -> bool {
    match d.node(id) {
        Node::Null => true,
        Node::Str(s) => d.str_at(s).is_empty(),
        Node::Array { len, .. } | Node::Object { len, .. } => len == 0,
        _ => false,
    }
}

/// The four tests `find()` accepts, in the order both bindings list them.
///
/// **This array is the one owner.** Each binding names the four in the message
/// it raises for a non-string argument, and NEITHER checks a string against
/// them — an unknown name is the core's to refuse, because a binding that knew
/// the set would be a second place to edit when there is a fifth.
pub const TESTS: [&str; 4] = ["url", "email", "date", "empty"];

#[derive(Clone, Copy)]
enum Test {
    Url,
    Email,
    Date,
    Empty,
}

impl Test {
    /// **The parse is the gate, and it exists because there was none.** Until
    /// 2026-08-14 `matches()` ended in `_ => false`, so `where(doc, "urls")`
    /// walked the whole document, matched nothing, printed `0 0 -` and exited
    /// 0 — the same bytes and the same status a document with no URLs gives.
    ///
    /// **A zero here is not rare, it is EVIDENCE**, which is what made the
    /// silence expensive rather than untidy. `test/parity.py` asserts a zero on
    /// purpose for `16-movie-ratings`/`empty`, because that file writes its
    /// missingness as the string `unknown` — defect 18 restated by a second
    /// instrument. A typo produced that same answer, so the reader had no way
    /// to tell a finding from a fat finger. `CLAUDE.md` puts a flag that fails
    /// to fire on exactly the footing of one that fires wrongly.
    ///
    /// **`design/where.py` never had the hole**: the oracle takes a callable,
    /// so an unknown name reached `test(value)` and raised. The string dispatch
    /// is the PORT's, added with the CLI and never argued — and `parity.py`
    /// could not have caught it, because it only ever passed the four valid
    /// names. A harness over inputs that cannot reach a branch says nothing
    /// about that branch, which is defect 30's lesson arriving somewhere new.
    ///
    /// Parsing to a type rather than guarding the string DELETES the
    /// fallthrough instead of checking around it, so a fifth test cannot
    /// reintroduce the silence by being added here and forgotten there.
    fn parse(name: &str) -> Option<Test> {
        match name {
            "url" => Some(Test::Url),
            "email" => Some(Test::Email),
            "date" => Some(Test::Date),
            "empty" => Some(Test::Empty),
            _ => None,
        }
    }
}

fn matches(d: &Doc, id: u32, pred: Test) -> bool {
    match pred {
        Test::Empty => is_empty_value(d, id),
        Test::Url => d.as_str(id).map(is_url).unwrap_or(false),
        Test::Email => d.as_str(id).map(is_email).unwrap_or(false),
        Test::Date => d.as_str(id).map(is_iso_date).unwrap_or(false),
    }
}

/// `{folded path: count}` for every path whose value matches.
///
/// The fold replaces a container's key with `<key>` when its keys are data,
/// which is the probe's own idea reused: a path that differs only by which
/// version it named is one path, not 288. Without it npm's URL report goes from
/// **7 path shapes to 659**, which is the O(data) failure this word exists to
/// avoid.
///
/// **A CONTAINER IS TESTED TOO**, and until 2026-08-10 it was not — the test
/// was the `else` of the descent, so two of `empty`'s four clauses were
/// unreachable code that read as working. That was found by writing the word in
/// R, which is what the parity harness is for.
///
/// **Refuses an unknown test rather than finding nothing in it.** See
/// `Test::parse`; the error is the caller's to print.
pub fn where_(d: &Doc, pred: &str) -> Result<OrderMap<usize>, String> {
    let Some(test) = Test::parse(pred) else {
        return Err(format!(
            "no test called {pred:?} — the tests are {}",
            TESTS.join(", ")
        ));
    };
    let mut hits: OrderMap<usize> = OrderMap::new();
    let mut parts: Vec<String> = Vec::new();
    let big = fold_set(d).0;
    let mut ip = String::from("$");
    walk(d, d.root(), &mut parts, &mut ip, &big, test, &mut hits);
    Ok(hits)
}

#[allow(clippy::too_many_arguments)]
fn walk(
    d: &Doc,
    node: u32,
    parts: &mut Vec<String>,
    ip: &mut String,
    big: &std::collections::HashSet<String>,
    pred: Test,
    hits: &mut OrderMap<usize>,
) {
    if matches(d, node, pred) {
        let p = if parts.is_empty() {
            ".".to_string()
        } else {
            parts.join(".")
        };
        *hits.entry(&p) += 1;
    }
    match d.kind(node) {
        Kind::Object => {
            // **DEFECT 36, repaired 2026-08-18: ask the FOLD, not `classify`.**
            // This used to call `classify(d, &[node])` — ONE container, which
            // always takes the single-copy branch and so decides on `KEYED_MIN`
            // alone. That is a strictly weaker test than the one `containers()`
            // already runs, and on `29-mdn-browser-compat` it under-folds badly:
            // the 1,090 `api` interfaces hold a median of FIVE method names, so
            // none reach twenty and `where url` named 11,320 paths for 35,392
            // values. `containers()` folds that same site correctly and always
            // did. Two walks were answering *are these keys data* two ways.
            //
            // The old comment here was right that handing `classify` the node's
            // VALUES as siblings breaks npm, and that is not what this does.
            // `fold_set` pools a container's own COPIES by folded path — a third
            // question, and the one `containers()` has always asked.
            //
            // Its companion claim, that this over-folded npm, was measured FALSE
            // on 2026-08-18: a version object has 17 keys and four value types,
            // so the single-copy branch returned Undecided and never folded it.
            // `where url` on npm is byte-identical before and after.
            let many = big.contains(ip.as_str());
            for i in 0..d.len_of(node) {
                let m = d.members(node)[i];
                let seg = if many {
                    "<key>".to_string()
                } else {
                    d.key(&m).to_string()
                };
                let keep = ip.len();
                ip.push('.');
                ip.push_str(&seg);
                parts.push(seg);
                walk(d, m.val, parts, ip, big, pred, hits);
                parts.pop();
                ip.truncate(keep);
            }
        }
        Kind::Array => {
            for i in 0..d.len_of(node) {
                let v = d.elements(node)[i];
                let keep = ip.len();
                ip.push_str("[]");
                parts.push("[]".to_string());
                walk(d, v, parts, ip, big, pred, hits);
                parts.pop();
                ip.truncate(keep);
            }
        }
        _ => {}
    }
}

/// Go into a part of the document, and re-root it there.
///
/// **This is `into()`, and it is the whole of what the bindings' navigation
/// does.** They accumulate names; the core resolves them. Everything downstream
/// — the walk, the fold, the classifier, the pricing, the report — then runs
/// unchanged on the new root, which is why navigation needed no new machinery
/// anywhere else and why the oracle for it is `design/probe.py` run on the
/// subtree.
///
/// **It is also the performance mechanism rather than a convenience.** Parsing
/// is 1% of the cost of describing a document, so narrowing the SCOPE of the
/// analysis is the only saving available. Measured on `29-mdn-browser-compat`:
/// describing the whole document is 4.73s, and a twentieth of one subtree is
/// 0.06s.
///
/// Three ways a name resolves, which is `design/chain.py`'s rule:
///
/// | standing on | `into("x")` means |
/// |---|---|
/// | an object with an `x` | that value — the plain case |
/// | an array | every item's `x`, gathered |
/// | an object WITHOUT an `x` | every value's `x`, gathered — a keyed collection |
///
/// The last two are a map, and the ambiguity they used to carry is gone
/// because `rows()` names its unit off the menu rather than inferring depth
/// from the path. **What the user types is a name; what gets recorded is the
/// resolved path**, so the notation is output and never input.
pub fn at(d: &mut Doc, names: &[String]) -> Result<String, String> {
    let mut resolved = String::from("$");
    for name in names {
        let node = d.root();
        match d.kind(node) {
            Kind::Object => {
                if let Some(v) = d.get(node, name) {
                    d.set_root(v);
                    resolved.push('.');
                    resolved.push_str(name);
                    continue;
                }
                // A keyed collection: the name is not a field here, so descend
                // into every value that has it.
                let got: Vec<u32> = d
                    .members(node)
                    .iter()
                    .filter_map(|m| d.get(m.val, name))
                    .collect();
                if got.is_empty() {
                    return Err(format!("no `{name}` at {resolved}"));
                }
                d.root_array(&got);
                resolved.push_str(".*.");
                resolved.push_str(name);
            }
            Kind::Array => {
                let got: Vec<u32> = d
                    .elements(node)
                    .to_vec()
                    .iter()
                    .filter_map(|&e| d.get(e, name))
                    .collect();
                if got.is_empty() {
                    return Err(format!("no `{name}` at {resolved}"));
                }
                d.root_array(&got);
                resolved.push_str("[].");
                resolved.push_str(name);
            }
            _ => return Err(format!("{resolved} holds no fields, so it has no `{name}`")),
        }
    }
    Ok(resolved)
}

/// `whichever`: the first of these names that is actually there, per child.
///
/// **Path variance, plainly.** A corpus document spells the same field
/// `Rating` in some records and `rating` in others; asking for both and taking
/// whichever arrived is the whole of what this word does. Measured on
/// `16-movie-ratings`, `whichever("Rating", "rating")` finds 38 of 38 where
/// either name alone finds a fraction.
///
/// **A null counts as absent**, which is the same rule `first_present` uses:
/// a field that is present and null has not told you anything, so the next
/// name gets its turn.
///
/// Returns one entry per child of where you are standing — its key (or its
/// index, as text) and the value that answered, if any.
pub fn whichever(d: &Doc, names: &[String]) -> Vec<(String, Option<u32>)> {
    let root = d.root();
    let children: Vec<(String, u32)> = match d.kind(root) {
        Kind::Object => d
            .members(root)
            .iter()
            .map(|m| (d.key(m).to_string(), m.val))
            .collect(),
        Kind::Array => d
            .elements(root)
            .iter()
            .enumerate()
            .map(|(i, &e)| (i.to_string(), e))
            .collect(),
        _ => Vec::new(),
    };
    children
        .into_iter()
        .map(|(k, child)| {
            let got = names.iter().find_map(|n| match d.get(child, n) {
                Some(v) if !d.is_null(v) => Some(v),
                _ => None,
            });
            (k, got)
        })
        .collect()
}
