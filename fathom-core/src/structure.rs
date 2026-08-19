//! What is in here? — the second of the three things the one verb answers.
//!
//! A port of the structure half of `design/probe.py`: the walk, the fold that
//! makes output proportional to the STRUCTURE rather than to the data, the
//! classifier that decides whether an object's keys are field names or values,
//! and the recursion fold that describes a comment thread once instead of once
//! per level.
//!
//! **Every threshold here is fitted to a measured gap and none of them is
//! tuneable.** `KEYED_MIN` 20, `KIND_MAX` 24 on a gap of 20-against-37,
//! `VOCAB_GROWTH` 0.02 on a gap of 0.007-against-0.030. The probe's docstrings
//! carry the evidence; this file carries the arithmetic, and changing a constant
//! here without a corpus file that forces it is how a probe stops being an
//! instrument.

use crate::json::{Doc, Kind, Node};
use crate::ordermap::{OrderMap, Tally};
use std::collections::{BTreeSet, HashSet};

/// A fallback threshold, used only where the sibling test cannot run.
pub const KEYED_MIN: f64 = 20.0;
/// Keys per copy below which `classify` declines. Gap: 0.007 vs 0.030.
pub const VOCAB_GROWTH: f64 = 0.02;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Verdict {
    Data,
    Structural,
    Undecided,
    /// The vocabulary would fit in a field list, so the probe declines to call
    /// these keys data. Distinct from `Undecided` because the fold reads this
    /// verdict too, and conflating the two was defect 22.
    Saturated,
    Empty,
}

impl Verdict {
    pub fn word(self) -> &'static str {
        match self {
            Verdict::Data => "data",
            Verdict::Structural => "structural",
            Verdict::Undecided => "undecided",
            Verdict::Saturated => "saturated",
            Verdict::Empty => "empty",
        }
    }
}

/// Thousands separators, because the probe prints `1,210` and not `1210`.
pub fn commas(n: usize) -> String {
    let s = n.to_string();
    let mut out = String::with_capacity(s.len() + s.len() / 3);
    let b = s.as_bytes();
    for (i, c) in b.iter().enumerate() {
        if i > 0 && (b.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(*c as char);
    }
    out
}

/// Python's `type(v).__name__`, which `classify` uses and `shape` does not.
/// The difference is load-bearing: `JSON_TYPE` folds `int` and `float` into one
/// word, and the homogeneity signal must keep them apart.
fn pytype(d: &Doc, id: u32) -> &'static str {
    match d.node(id) {
        Node::Null => "NoneType",
        Node::Bool(_) => "bool",
        Node::Int(_) | Node::BigInt(_) => "int",
        Node::Float(_) => "float",
        Node::Str(_) => "str",
        Node::Array { .. } => "list",
        Node::Object { .. } => "dict",
    }
}

/// The type of a value, and for arrays how deeply they nest AND what they hold.
///
/// Type alone cannot see `03-natural-earth`'s polymorphism, where a Polygon's
/// `coordinates` is `[[[x,y]]]` and a MultiPolygon's is `[[[[x,y]]]]`. Depth
/// alone cannot see `05-fhir-bundle`'s, where `category` is `["environment"]`
/// on 9 resources and `[{"coding": …}]` on 257. Both halves are reported.
///
/// An EMPTY array reports plain `array`: its depth is unknown, and inventing
/// one would manufacture a difference between `[]` and `[1,2]` that nobody
/// means.
pub fn shape(d: &Doc, id: u32) -> String {
    if d.kind(id) != Kind::Array {
        return d.kind(id).word().to_string();
    }
    let (mut n, mut x) = (0usize, id);
    while d.kind(x) == Kind::Array {
        let els = d.elements(x);
        if els.is_empty() {
            return "array".to_string();
        }
        n += 1;
        x = els[0];
    }
    format!("array[{n}] {}", d.kind(x).word())
}

#[derive(Default)]
pub struct Walk {
    /// path -> the object nodes found there
    pub inst: OrderMap<Vec<u32>>,
    /// path -> the array nodes found there
    pub arrs: OrderMap<Vec<u32>>,
    /// path -> how many times each shape occurred
    pub types: OrderMap<Tally>,
}

fn go(d: &Doc, id: u32, p: &str, big: &HashSet<String>, w: &mut Walk) {
    match d.kind(id) {
        Kind::Object => {
            w.inst.entry(p).push(id);
            let folded = big.contains(p);
            for m in d.members(id) {
                let kp = if folded {
                    format!("{p}.<key>")
                } else {
                    format!("{p}.{}", d.key(m))
                };
                w.types.entry(&kp).bump(&shape(d, m.val));
                go(d, m.val, &kp, big, w);
            }
        }
        Kind::Array => {
            w.arrs.entry(p).push(id);
            let kp = format!("{p}[]");
            for &e in d.elements(id) {
                go(d, e, &kp, big, w);
            }
        }
        _ => {}
    }
}

fn walk(d: &Doc, big: &HashSet<String>) -> Walk {
    let mut w = Walk::default();
    go(d, d.root(), "$", big, &mut w);
    w
}

/// The set of container paths whose keys are data, and the walk that proves it.
///
/// **It is a fixed point, not a single pass.** Data-ness is a property of the
/// aggregate, and the aggregate only becomes visible once the container above
/// it has folded — `peerDependenciesMeta` is one to five keys per copy and
/// about thirty across copies, so a per-instance test never folds it and the
/// output grows with the data. So: walk, fold whatever now looks like data,
/// walk again, until nothing new folds.
///
/// **Split out of `containers()` on 2026-08-18 for DEFECT 36, and the split is
/// the repair.** `where_` was deciding the same question with a strictly weaker
/// test — `classify(d, &[node])`, one container at a time — because this set
/// was locked inside `containers()`, which hands back the walk rather than the
/// set. Mirrors `fold_set()` in `design/probe.py`.
pub fn fold_set(d: &Doc) -> (HashSet<String>, Walk) {
    let mut big: HashSet<String> = HashSet::new();
    for _ in 0..20 {
        let got = walk(d, &big);
        let mut new: Vec<String> = Vec::new();
        for (p, objs) in got.inst.iter() {
            if !big.contains(p) && folds(d, p, objs) {
                new.push(p.to_string());
            }
        }
        if new.is_empty() {
            return (big, got);
        }
        big.extend(new);
    }
    let got = walk(d, &big);
    (big, got)
}

/// Every object, grouped by the path of its container, with data keys folded.
///
/// The fixed point that decides it is `fold_set()` above; this returns only the
/// walk, which is what every caller here wants and was the reason the set had
/// no way out of this function until defect 36 needed it.
pub fn containers(d: &Doc) -> Walk {
    fold_set(d).1
}

/// Should this site's keys collapse to `<key>`? One definition, two callers.
///
/// Keys the probe calls **data** always fold; that is operation 2 and it is
/// unchanged. A **saturated** site — one whose whole vocabulary would fit in a
/// field list, so the probe declines to say — folds only when its members are
/// RECORDS, and that condition was measured rather than chosen.
///
/// **Folding a collection of records still describes them**, under `<key>`.
/// **Folding a collection of scalars erases the only names those leaves will
/// ever have.** `13-package-lock`'s `engines` holds 1,058 strings under five
/// keys, and an earlier draft of this repair folded it and put 6.5% of that
/// document beyond naming; `20-homebrew-formulae`'s `variations` holds 5,295
/// objects and loses nothing.
///
/// **And a site that is ALREADY a collection's member does not fold again.** A
/// `<key>` step means the fold has placed a name here, and what a name
/// addresses is a record. Without this clause `$.paths.<key>` folds `get`,
/// `post` and `delete` on `09-stripe-openapi`, taking that file's keys-as-data
/// 47 → 46. That trade is measured and is not made here.
pub fn folds(d: &Doc, p: &str, objs: &[u32]) -> bool {
    match classify(d, objs).0 {
        Verdict::Data => true,
        Verdict::Saturated if !p.ends_with("<key>") => {
            let vals: Vec<u32> = objs
                .iter()
                .filter(|&&o| d.len_of(o) > 0)
                .flat_map(|&o| d.members(o).iter().map(|m| m.val))
                .collect();
            !vals.is_empty() && vals.iter().all(|&v| d.kind(v) == Kind::Object)
        }
        _ => false,
    }
}

/// Are this container's keys data, or field names?
///
/// Two signals, and NEITHER works alone. Sibling overlap alone calls ragged
/// records data; type homogeneity alone calls `author{name, email}` data.
/// Conjoined they got 11 of 12 hand-labelled cases right, and the one miss
/// names the real boundary: a closed, stable vocabulary like
/// `data{text/html, text/plain}` is structurally a record and no structural
/// signal can see it. Those are reported undecided.
pub fn classify(d: &Doc, objs: &[u32]) -> (Verdict, String) {
    let objs: Vec<u32> = objs.iter().copied().filter(|&o| d.len_of(o) > 0).collect();
    if objs.is_empty() {
        return (Verdict::Empty, String::new());
    }
    let count = objs.len() as f64;
    let n = objs.iter().map(|&o| d.len_of(o)).sum::<usize>() as f64 / count;
    let hom = objs
        .iter()
        .map(|&o| {
            let mut c = Tally::new();
            for m in d.members(o) {
                c.bump(pytype(d, m.val));
            }
            c.top() as f64 / d.len_of(o) as f64
        })
        .sum::<f64>()
        / count;

    // A COLLECTION KEYED BY NAME. The sibling test assumes a data vocabulary
    // CHANGES between copies, and a stable one breaks it: nineteen snapshots of
    // the same tracked files share their paths, so overlap measured 0.66 where
    // data is supposed to be below 0.5. What it missed is not subtle — 563
    // values, every one an object, and exactly ONE key-set among them. That is
    // a table addressed by name. Deliberately strict: ONE key-set, not "few".
    let vals: Vec<u32> = objs
        .iter()
        .flat_map(|&o| d.members(o).iter().map(|m| m.val))
        .collect();
    if n >= KEYED_MIN && !vals.is_empty() && vals.iter().all(|&v| d.kind(v) == Kind::Object) {
        let mut sets: HashSet<Vec<&str>> = HashSet::new();
        for &v in &vals {
            let mut ks: Vec<&str> = d.members(v).iter().map(|m| d.key(m)).collect();
            ks.sort_unstable();
            sets.insert(ks);
            if sets.len() > 1 {
                break;
            }
        }
        if sets.len() == 1 {
            return (
                Verdict::Data,
                format!(
                    "{} values, all one shape, {} keys per copy — a collection, not a record",
                    commas(vals.len()),
                    n as usize
                ),
            );
        }
    }

    if objs.len() > 1 {
        let mut allk = Tally::new();
        for &o in &objs {
            for m in d.members(o) {
                allk.bump(d.key(m));
            }
        }
        let ov = allk.total() as f64 / (allk.len() as f64 * count);
        if ov < 0.5 && hom >= 0.9 {
            // DECLINE TO CLAIM when the vocabulary is saturated. This does NOT
            // detect closed vocabularies — no structural signal can. What it
            // does is stop over-claiming: with one copy the probe admits it
            // cannot tell, and with a thousand it was stating the wrong answer.
            // The measure is whether the vocabulary GROWS as copies accumulate.
            //
            // **THE VERDICT IS A REPORTING DECISION AND WAS ALSO A STRUCTURAL
            // ONE, which is defect 22.** `containers` folds whatever this
            // returns as data, so `Undecided` here did not only stop the probe
            // naming these keys — it stopped their siblings folding. On
            // `20-homebrew-formulae` that turned `$[].variations` into THIRTEEN
            // unfolded platform sites, each with too few copies for this very
            // guard to fire on, and each then reported as data.
            if allk.len() as f64 / count < VOCAB_GROWTH {
                return (
                    Verdict::Saturated,
                    format!(
                        "{} keys over {} copies — too few to tell data from a field list",
                        allk.len(),
                        objs.len()
                    ),
                );
            }
            return (
                Verdict::Data,
                format!(
                    "{} copies share few keys ({:.2}), values one type",
                    objs.len(),
                    ov
                ),
            );
        }
        if ov < 0.5 {
            return (
                Verdict::Structural,
                format!(
                    "{} ragged copies ({:.2}), values differ ({:.2})",
                    objs.len(),
                    ov,
                    hom
                ),
            );
        }
        return (
            Verdict::Structural,
            format!("{} copies share their keys ({:.2})", objs.len(), ov),
        );
    }
    // DEFECT 31, repaired 2026-08-12, and it is a CONSISTENCY fix rather than a
    // new rule. The two signals are sibling overlap and type homogeneity, and
    // neither works alone. The multi-copy branch demands both — `ov < 0.5 &&
    // hom >= 0.9`. This branch has no siblings to measure overlap against, and
    // it was demanding neither: enough keys was the whole test.
    //
    // `27-grafana-dashboard`'s ROOT is a fixed schema — annotations, editable,
    // panels, templating, title, uid, version — called data on the strength of
    // there being 25 of them. `hom` is already computed above for every object,
    // single copies included; the repair applies the existing test at the
    // existing threshold to a number already in hand.
    //
    // Eleven corpus sites reach this branch: TEN score exactly 1.0000 and the
    // eleventh scores 0.2400. That gap is not a threshold anybody chose.
    // DEFECT 32, repaired 2026-08-12, replacing defect 31's `hom >= 0.9`, which
    // was too strict: `28-home-assistant-i18n` was held out to test it and it
    // refused five message groups a reader would call keyed collections.
    //
    // `hom` is the wrong measure here. Over 47 single-copy sites in 28 entries,
    // the ones that must be ACCEPTED run 0.6364 to 1.0000 continuously and the
    // one that must be REFUSED sits at 0.2400 — no natural cut. It averages a
    // modal fraction, which is a statistic over many copies and noise over one.
    //
    // The COUNT of distinct value types separates categorically: forty-six of
    // the 47 have ONE or TWO, and `27-grafana-dashboard`'s root — a real schema
    // — has SIX. The rule it states: **a keyed collection's values are one kind
    // of thing, or a leaf and a group.** A record is what has numbers and
    // booleans and arrays and strings at once.
    //
    // Nulls are excluded because a null is not a type. No corpus site has one
    // here, so it costs nothing measured.
    if n > KEYED_MIN {
        // `pytype` is the oracle's `type(v).__name__`, which already tells an
        // `int` from a `float` where `Kind` collapses both to Number.
        let kinds: BTreeSet<&'static str> = d
            .members(objs[0])
            .iter()
            .map(|m| pytype(d, m.val))
            .filter(|t| *t != "NoneType")
            .collect();
        if kinds.len() <= 2 {
            return (
                Verdict::Data,
                format!("one copy, {} keys — not a field list", n as usize),
            );
        }
        return (
            Verdict::Structural,
            format!(
                "one copy, {} keys, {} value types — a field list",
                n as usize,
                kinds.len()
            ),
        );
    }
    (
        Verdict::Undecided,
        format!(
            "one copy, {} keys — nothing separates it from a record",
            n as usize
        ),
    )
}

pub struct Fold {
    pub inst: OrderMap<Vec<u32>>,
    pub arrs: OrderMap<Vec<u32>>,
    /// path -> how many extra levels folded into it
    pub rec: OrderMap<usize>,
    pub types: OrderMap<Tally>,
}

/// The first FIELD name of a descent, ignoring any `[]` hops.
fn first_step(suffix: &str) -> &str {
    let mut s = suffix;
    while let Some(r) = s.strip_prefix("[]") {
        s = r;
    }
    s = s.strip_prefix('.').unwrap_or(s);
    let head = s.split('.').next().unwrap_or("");
    head.strip_suffix("[]").unwrap_or(head)
}

/// Fold self-similar nesting into one entry.
///
/// A comment thread has ONE record shape that contains itself, and describing
/// it once per level is O(depth) for a structure whose entire point is that it
/// repeats.
///
/// **Key-set equality is not identity, and `05-fhir-bundle` proved it twice.**
/// FHIR builds everything out of reusable element types, so `Claim.total` is
/// `{value, currency}` and `total[].amount` is `{value, currency}`, and a
/// document containing no recursion at all was reported as `RECURSIVE, 2
/// levels`. **The missing condition is reachability: you have to be able to GET
/// there by following a field the ancestor actually has.** A comment has a
/// `children`; a total does not contain a `total`.
pub fn fold_recursion(d: &Doc, w: Walk) -> Fold {
    let Walk { inst, arrs, types } = w;

    let mut keyset: OrderMap<BTreeSet<String>> = OrderMap::new();
    for (p, objs) in inst.iter() {
        if objs.iter().any(|&o| d.len_of(o) > 0) {
            let mut s = BTreeSet::new();
            for &o in objs {
                for m in d.members(o) {
                    s.insert(d.key(m).to_string());
                }
            }
            keyset.insert(p, s);
        }
    }

    let descends = |p: &str, a: &str, ks: &OrderMap<BTreeSet<String>>| -> bool {
        if p == a || !p.starts_with(a) {
            return false;
        }
        let suffix = &p[a.len()..];
        if !suffix.contains('.') {
            return false;
        }
        match ks.get(a) {
            Some(set) => set.contains(first_step(suffix)),
            None => false,
        }
    };

    // Shortest first, ties on walk order — Rust's sort_by_key is stable and so
    // is Python's `sorted(keyset, key=len)`.
    let mut order: Vec<String> = keyset.keys().map(|s| s.to_string()).collect();
    order.sort_by_key(|p| p.len());

    let mut canon: OrderMap<String> = OrderMap::new();
    // The distinct canonical paths assigned so far, in first-seen order. Python
    // reads these out of a `set`, whose order is unspecified; every corpus file
    // was checked to produce identical output under randomised hash seeds, so
    // no length tie among candidates actually decides anything today.
    let mut distinct: Vec<String> = Vec::new();
    for p in &order {
        let mut cands: Vec<&String> = distinct.iter().collect();
        cands.sort_by_key(|a| a.len());
        let hit = cands.into_iter().find(|a| {
            descends(p, a, &keyset) && keyset.get(a) == keyset.get(p)
        });
        let c = hit.cloned().unwrap_or_else(|| p.clone());
        if !distinct.iter().any(|x| x == &c) {
            distinct.push(c.clone());
        }
        canon.insert(p, c);
    }

    let mut merged: OrderMap<Vec<u32>> = OrderMap::new();
    let mut levels: OrderMap<usize> = OrderMap::new();
    for (p, objs) in inst.iter() {
        let c = canon.get(p).map(|s| s.as_str()).unwrap_or(p);
        merged.entry(c).extend(objs.iter().copied());
        if c != p {
            *levels.entry(c) += 1;
        }
    }

    let mut marrs: OrderMap<Vec<u32>> = OrderMap::new();
    for (p, lists) in arrs.iter() {
        // Only rewrite when the canonical really is an array path. A thread
        // whose root shares its comments' shape canonicalises to "$", and
        // "$"[:-2] is the empty string, which produced a row candidate called
        // "an item of ".
        let probe_key = format!("{p}[]");
        let target = match canon.get(&probe_key) {
            Some(c) if c.ends_with("[]") => c[..c.len() - 2].to_string(),
            _ => p.to_string(),
        };
        marrs.entry(&target).extend(lists.iter().copied());
    }

    // Types have to fold too, or polymorphism inside a recursive structure is
    // invisible: `points` is a number on the story and null on all 335
    // comments, but no single unfolded path ever sees both.
    let mut mtypes: OrderMap<Tally> = OrderMap::new();
    for (tp, c) in types.iter() {
        let (holder, field) = match tp.rfind('.') {
            Some(i) => (&tp[..i], &tp[i + 1..]),
            None => ("", tp),
        };
        let h = canon.get(holder).map(|s| s.as_str()).unwrap_or(holder);
        let key = format!("{h}.{field}");
        let slot = mtypes.entry(&key);
        for (k, n) in c.iter() {
            slot.add(k, *n);
        }
    }

    Fold {
        inst: merged,
        arrs: marrs,
        rec: levels,
        types: mtypes,
    }
}
