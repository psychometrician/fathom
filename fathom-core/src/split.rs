//! The fold reporting that it should not have folded.
//!
//! One `entry` array in `05-fhir-bundle` holds 564 resources of 20 different
//! resourceTypes, and folding them into one shape gives **97 fields, 87% empty,
//! and exactly two fields present in all of them**. Folding within each
//! resourceType instead gives 20 tables, worst 22% empty and eleven of them
//! completely full. **The fold was never wrong. Its scope was.**
//!
//! A discriminator has to earn all five guards below, and every one of them is
//! a false positive that appeared while fitting this:
//!
//!   present in every instance   `status` covers 534 of 564 and is a state.
//!   a scalar value              partitioning on an object means nothing.
//!   few distinct values         `id` is present in all 564 and has 564 values.
//!   the split has to PAY        it must at least halve the key-sets per group.
//!   and it has to pay in HOLES  the worst group must be at most half as empty
//!                               as the fold was. This is the operation's own
//!                               definition rather than a tuned threshold.

use crate::json::{Doc, Node};
use crate::structure::shape;
use std::collections::{BTreeSet, HashMap};

/// Most kinds a split may propose. Every genuine split in the corpus proposes 2
/// to 20; `13-package-lock`'s `funding` proposed 37 on a sponsor URL. **The gap
/// is 20 against 37 and that gap is the whole evidence.**
pub const KIND_MAX: usize = 24;
/// How much disorder there must be to be worth fixing. `04-gharchive` split on
/// `client_id` — six opaque values over 61 records — because any
/// high-cardinality field trivially makes small homogeneous groups. **The gap
/// is 8% against 23%.**
pub const DISORDER_FLOOR: f64 = 0.2;

/// The keys of `o` that actually carry a value.
///
/// A key present with a `null` is a hole. `price()` measures holes with
/// `pandas.isna()`, so a null counts; `emptiness()` measured key presence, so
/// it did not, and on `07-graphql-introspection` the two reported **52% and 0%
/// about the same table** — with the blind one deciding whether to split.
pub fn filled(d: &Doc, o: u32) -> BTreeSet<&str> {
    d.members(o)
        .iter()
        .filter(|m| !d.is_null(m.val))
        .map(|m| d.key(m))
        .collect()
}

/// The distinct shapes a field takes, ignoring differences that mean nothing.
///
/// An empty array says nothing about its nesting depth, so `array` beside
/// `array[1]` is one shape and not two. Without this every optional list reads
/// as polymorphic: the comment thread's `children` is `array[1]` ×165 and
/// `array` ×171, which is 165 parents and 171 leaves.
pub fn varies(shapes: &BTreeSet<String>) -> usize {
    let bare = shapes.contains("array");
    let indexed = shapes.iter().any(|t| t.starts_with("array["));
    shapes.len() - usize::from(bare && indexed)
}

/// What fraction of a folded table's cells would be empty.
pub fn emptiness(d: &Doc, objs: &[u32]) -> f64 {
    // The columns are the ones this group actually FILLS, not the ones it
    // merely carries: a GraphQL SCALAR has all eight introspection keys present
    // and five null in every record, and nobody keeps five all-null columns.
    let mut cols: BTreeSet<&str> = BTreeSet::new();
    let mut hits = 0usize;
    for &o in objs {
        let f = filled(d, o);
        hits += f.len();
        cols.extend(f);
    }
    if cols.is_empty() {
        return 0.0;
    }
    // Every `filled(o)` is a subset of their union, so the intersection Python
    // takes is `filled(o)` itself and the sum above is the same number.
    1.0 - hits as f64 / (objs.len() * cols.len()) as f64
}

/// How much a set of records disagrees about the SHAPE of their values.
///
/// `emptiness()` asks which keys are filled; this asks what the filled ones
/// hold. `10-wikidata` is the document that made the difference matter: every
/// `datavalue` is `{type, value}` with both keys filled, so it is 0% empty and
/// has one key-set, and `value` is `text` on 512 records and `object` on 1,210.
/// **A perfect split existed and the operation was measuring the one thing that
/// document does not suffer from.**
pub fn variation(d: &Doc, objs: &[u32]) -> f64 {
    let mut fields: BTreeSet<&str> = BTreeSet::new();
    for &o in objs {
        fields.extend(filled(d, o));
    }
    if fields.is_empty() {
        return 0.0;
    }
    let mut n = 0usize;
    for f in &fields {
        let mut shapes: BTreeSet<String> = BTreeSet::new();
        for &o in objs {
            if let Some(v) = d.get(o, f) {
                if !d.is_null(v) {
                    shapes.insert(shape(d, v));
                }
            }
        }
        if varies(&shapes) > 1 {
            n += 1;
        }
    }
    n as f64 / fields.len() as f64
}

/// What a split is trying to reduce: holes plus disagreement about shape.
pub fn disorder(d: &Doc, objs: &[u32]) -> f64 {
    emptiness(d, objs).max(variation(d, objs))
}

/// `measure` across groups, weighted by rows. **Reporting only — NOT a guard.**
///
/// Tried as the pricing rule and rejected by measurement: it took
/// `09-stripe-openapi` from 5 splits to 22 and revived two false positives the
/// worst-group rule had correctly killed. It stays because it is the honest
/// number to PRINT — a reader meets the big table — while the decision to split
/// is still made on the worst group.
pub fn weighted(d: &Doc, groups: &[Vec<u32>], measure: fn(&Doc, &[u32]) -> f64) -> f64 {
    let n: usize = groups.iter().map(|g| g.len()).sum();
    if n == 0 {
        return 0.0;
    }
    let mut acc = 0.0;
    for g in groups {
        acc += g.len() as f64 * measure(d, g);
    }
    acc / n as f64
}

fn distinct_filled(d: &Doc, objs: &[u32]) -> usize {
    let mut seen: BTreeSet<Vec<&str>> = BTreeSet::new();
    for &o in objs {
        seen.insert(filled(d, o).into_iter().collect());
    }
    seen.len()
}

/// A value used to partition on. **`Num` swallows booleans because Python's
/// does**: `True == 1` and `hash(True) == hash(1)`, so `{True, 1}` is one
/// distinct value and one group. Reproducing that matters less for being
/// unlikely than for being invisible when it happens.
#[derive(Clone, PartialEq, Eq, Hash, Debug)]
enum GroupKey {
    Num(i64),
    Big(String),
    Str(String),
}

fn group_key(d: &Doc, v: u32) -> Option<GroupKey> {
    match d.node(v) {
        Node::Bool(b) => Some(GroupKey::Num(i64::from(b))),
        Node::Int(i) => Some(GroupKey::Num(i)),
        Node::BigInt(s) => Some(GroupKey::Big(d.str_at(s).to_string())),
        Node::Str(s) => Some(GroupKey::Str(d.str_at(s).to_string())),
        // A float is refused, and so is null, an array and an object.
        _ => None,
    }
}

/// Python's `str(v)`, which is what the report prints as a group label —
/// a bare string with no quotes, and `True`/`False` capitalised.
pub fn label(d: &Doc, v: u32) -> String {
    match d.node(v) {
        Node::Bool(true) => "True".to_string(),
        Node::Bool(false) => "False".to_string(),
        Node::Int(i) => i.to_string(),
        Node::BigInt(s) => d.str_at(s).to_string(),
        Node::Str(s) => d.str_at(s).to_string(),
        _ => String::new(),
    }
}

pub struct Split {
    pub field: String,
    /// `(label, members)` in first-seen order, which is what `dict(groups)` is.
    pub groups: Vec<Group>,
}

/// A kind, and the records of that kind.
pub type Group = (String, Vec<u32>);

/// `(mean key-sets per group, worst group's disorder, kinds)` — the tuple
/// Python compares with `<`, least raggedness left behind winning.
type Score = (f64, f64, usize);

/// A field whose value says which KIND of record this is.
pub fn discriminator(d: &Doc, objs: &[u32]) -> Option<Split> {
    let objs: Vec<u32> = objs.iter().copied().filter(|&o| d.len_of(o) > 0).collect();
    if objs.len() < 10 {
        return None;
    }
    // THERE HAS TO BE SOMETHING WORTH FIXING.
    let dis_all = disorder(d, &objs);
    if dis_all < DISORDER_FLOOR {
        return None;
    }
    let shapes = distinct_filled(d, &objs);
    let var_all = variation(d, &objs);
    // More than one key-set, OR any disagreement about value shape. One key-set
    // with no shape disagreement means the records genuinely are uniform and
    // there is nothing to partition.
    if shapes < 2 && var_all == 0.0 {
        return None;
    }

    let mut everywhere: BTreeSet<&str> = d.members(objs[0]).iter().map(|m| d.key(m)).collect();
    for &o in &objs[1..] {
        let ks: BTreeSet<&str> = d.members(o).iter().map(|m| d.key(m)).collect();
        everywhere = everywhere.intersection(&ks).copied().collect();
    }

    let ceiling = KIND_MAX.min((objs.len() / 5).max(2));
    let mut best: Option<(Score, String, Vec<Group>)> = None;

    for f in &everywhere {
        let vals: Vec<u32> = objs.iter().map(|&o| d.get(o, f).unwrap()).collect();
        let mut keys: Vec<GroupKey> = Vec::with_capacity(vals.len());
        let mut ok = true;
        for &v in &vals {
            match group_key(d, v) {
                Some(k) => keys.push(k),
                None => {
                    ok = false;
                    break;
                }
            }
        }
        if !ok {
            continue;
        }
        let mut at: HashMap<GroupKey, usize> = HashMap::new();
        let mut groups: Vec<Group> = Vec::new();
        for (i, k) in keys.iter().enumerate() {
            match at.get(k) {
                Some(&j) => groups[j].1.push(objs[i]),
                None => {
                    at.insert(k.clone(), groups.len());
                    groups.push((label(d, vals[i]), vec![objs[i]]));
                }
            }
            if groups.len() > ceiling {
                break;
            }
        }
        let distinct = at.len();
        if !(2..=ceiling).contains(&distinct) {
            continue;
        }
        let mean_shapes = groups
            .iter()
            .map(|(_, g)| distinct_filled(d, g) as f64)
            .sum::<f64>()
            / groups.len() as f64;
        // The split has to PAY, or this is slicing a regular table and calling
        // it an insight.
        if mean_shapes > shapes as f64 / 2.0 && var_all == 0.0 {
            continue;
        }
        // WORST GROUP, not a row-weighted mean. A big clean group must not buy
        // a small filthy one.
        let worst = groups
            .iter()
            .map(|(_, g)| disorder(d, g))
            .fold(f64::NEG_INFINITY, f64::max);
        if worst > dis_all / 2.0 {
            continue;
        }
        // Prefer the field that leaves the least raggedness behind, not the one
        // that makes the most groups — otherwise a near-identifier always wins
        // by cutting every group down to one instance.
        let score = (mean_shapes, worst, distinct);
        let better = match &best {
            None => true,
            Some((b, _, _)) => {
                (score.0, score.1, score.2) < (b.0, b.1, b.2)
            }
        };
        if better {
            best = Some((score, f.to_string(), groups));
        }
    }
    best.map(|(_, field, groups)| Split { field, groups })
}
