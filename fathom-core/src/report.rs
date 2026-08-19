//! The page a reader actually sees, and `positional()`, which prices uses too.
//!
//! That last clause changed with defect 27's repair. `positional()` was written
//! for the section this module prints and nothing else read it, which is exactly
//! why the row menu could not name an aligned table: the scan and the menu were
//! in different modules and only one of them had run.
//!
//! **This is the last stage of the port and the one the criterion is written
//! against.** Every earlier stage was diffed as structured data, which is the
//! right way to find out WHICH stage is wrong. This one is diffed as bytes,
//! because the probe's product is a rendered page and a report that is correct
//! in substance and different in layout is still a different report.
//!
//! Column widths, thousands separators and the wrap at 92 characters are all
//! load-bearing. `design/coverage.py` reads this report back as a set of claims
//! and tells a shape header (4 spaces) from a `SPLIT ON` (6) from a wrapped
//! continuation (17) by indentation alone.

use crate::json::{Doc, Kind, Node};
use crate::ordermap::{OrderMap, Tally};
use crate::price::{candidates, py_str, py_str_lit};
use crate::split::{discriminator, emptiness, filled, varies, variation, weighted, Split};
use crate::structure::{classify, commas, containers, fold_recursion, shape, Verdict};
use crate::health::{Format, Health};
use std::collections::{BTreeSet, HashMap, HashSet};

/// How many record shapes and keyed sites to print.
pub const SHOW: usize = 40;

/// `f"{x:.0%}"`. Python scales then rounds half-to-even, and so does Rust.
fn pct(x: f64) -> String {
    format!("{:.0}%", x * 100.0)
}

/// Pad right to `w` CHARACTERS, which is what Python's `{:<w}` counts.
fn lpad(s: &str, w: usize) -> String {
    let n = s.chars().count();
    if n >= w {
        s.to_string()
    } else {
        format!("{s}{}", " ".repeat(w - n))
    }
}

/// Pad left to `w` characters — Python's `{:>w}`.
fn rpad(s: &str, w: usize) -> String {
    let n = s.chars().count();
    if n >= w {
        s.to_string()
    } else {
        format!("{}{s}", " ".repeat(w - n))
    }
}

/// First `n` characters, not bytes. Python slices strings by code point.
fn cut(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

/// Arrays of scalars whose length never varies, grouped by that length.
///
/// **THE PARENT IS THE TABLE**, and requiring that is what `09-stripe-openapi`
/// forced. The first version asked only for two paths sharing a length of at
/// least three, and on a 7.6 MB document with thousands of small arrays it
/// reported "22 paths hold arrays of exactly 3" — unrelated `required` and
/// `enum` lists scattered across 22 parents.
///
/// **Length 3 across 22 parents is a coincidence. Length 336 across 5 paths in
/// ONE parent is a table.** So a parent qualifies only when it holds at least
/// two constant-length scalar arrays and all of them agree on that length: the
/// parent is wholly a table, or it is not one.
pub fn positional<'a>(d: &Doc, arrs: &'a OrderMap<Vec<u32>>) -> Vec<(usize, Vec<(&'a str, u32)>)> {
    // path -> (length, first array node)
    let mut fixed: Vec<(&str, usize, u32)> = Vec::new();
    for (p, lists) in arrs.iter() {
        let mut lens: BTreeSet<usize> = BTreeSet::new();
        for &l in lists {
            lens.insert(d.len_of(l));
        }
        if lens.len() != 1 {
            continue;
        }
        let n = *lens.iter().next().unwrap();
        if n < 3 {
            continue;
        }
        // Ordinary scalar arrays vary per record and drop out above; a nested
        // one is not a column of a table.
        let scalar = lists.iter().all(|&l| {
            d.elements(l)
                .iter()
                .all(|&v| !matches!(d.kind(v), Kind::Object | Kind::Array))
        });
        if !scalar {
            continue;
        }
        fixed.push((p, n, lists[0]));
    }

    let mut by_parent: OrderMap<Vec<(&str, usize, u32)>> = OrderMap::new();
    for (p, n, first) in fixed {
        let parent = match p.rfind('.') {
            Some(i) => &p[..i],
            None => "",
        };
        by_parent.entry(parent).push((p, n, first));
    }

    let mut groups: OrderMap<Vec<(&str, u32)>> = OrderMap::new();
    for (_, entries) in by_parent.iter() {
        if entries.len() < 2 {
            continue;
        }
        let lens: BTreeSet<usize> = entries.iter().map(|e| e.1).collect();
        if lens.len() != 1 {
            continue;
        }
        let n = *lens.iter().next().unwrap();
        for (p, _, first) in entries {
            groups.entry(&n.to_string()).push((*p, *first));
        }
    }

    let mut out: Vec<(usize, Vec<(&str, u32)>)> = groups
        .iter()
        .filter(|(_, ps)| ps.len() > 1)
        .map(|(k, ps)| {
            let mut v = ps.clone();
            v.sort_by(|a, b| a.0.cmp(b.0));
            (k.parse::<usize>().unwrap_or(0), v)
        })
        .collect();
    out.sort_by_key(|(n, _)| *n);
    out
}

/// One instance, all strings, all distinct, all short. A header row.
///
/// **Necessary and nowhere near sufficient**, and `08-open-meteo` proved it in
/// the worst possible way: a column of 336 ISO timestamps is one instance of
/// distinct strings under forty characters, so the probe marked it as the
/// header and advised zipping the others against it — advice that yields a
/// table rather than an error. The caller must apply `names_are_keys` first.
fn looks_like_names(d: &Doc, lists: &[u32], count: usize) -> bool {
    if count != 1 {
        return false;
    }
    let els = d.elements(lists[0]);
    if els.is_empty() {
        return false;
    }
    let mut seen: HashSet<&str> = HashSet::new();
    for &v in els {
        match d.as_str(v) {
            Some(s) if !s.is_empty() && s.chars().count() <= 40 => {
                seen.insert(s);
            }
            _ => return false,
        }
    }
    seen.len() == els.len()
}

/// Do all the aligned arrays sit under ONE parent? Then the names are keys.
///
/// One parent means safe; more than one means a choice, and a choice is where
/// the decoy lives. `06-espn-qbr`'s `glossary` holds the same ten names in a
/// different order, so the obvious join reports the league's best quarterback
/// at -7.4.
fn names_are_keys(paths: &[&str]) -> bool {
    let parents: HashSet<&str> = paths
        .iter()
        .map(|p| match p.rfind('.') {
            Some(i) => &p[..i],
            None => "",
        })
        .collect();
    parents.len() == 1
}

fn parent_of(p: &str) -> &str {
    match p.rfind('.') {
        Some(i) => &p[..i],
        None => "",
    }
}

fn after_last_dot(p: &str) -> &str {
    match p.rfind('.') {
        Some(i) => &p[i + 1..],
        None => "",
    }
}

/// A record shape's field list, in full, wrapped under its label.
///
/// Wrapping rather than truncating is the whole of defect 20's repair. Output
/// stays proportional to the STRUCTURE — a shape with 97 fields costs 97 names
/// however many million records carry them.
///
/// **The 17-character indent is load-bearing and not cosmetic**: `coverage.py`
/// reads this report as a set of claims, and a continuation line has to be
/// distinguishable from a new shape header (4 spaces) or a `SPLIT ON` (6).
fn fields(out: &mut String, label: &str, items: &[String]) {
    const WIDTH: usize = 92;
    if items.is_empty() {
        out.push_str(&format!("      {}(none)\n", lpad(label, 11)));
        return;
    }
    let mut lines: Vec<String> = Vec::new();
    let mut line = String::new();
    for it in items {
        if !line.is_empty() && line.chars().count() + 1 + it.chars().count() > WIDTH {
            lines.push(std::mem::take(&mut line));
            line = it.clone();
        } else if line.is_empty() {
            line = it.clone();
        } else {
            line = format!("{line} {it}");
        }
    }
    lines.push(line);
    out.push_str(&format!("      {}{}\n", lpad(label, 11), lines[0]));
    for extra in &lines[1..] {
        out.push_str(&format!("      {}{}\n", lpad("", 11), extra));
    }
}

fn depth(d: &Doc, id: u32) -> usize {
    match d.kind(id) {
        Kind::Object if d.len_of(id) > 0 => {
            1 + d.members(id).iter().map(|m| depth(d, m.val)).max().unwrap_or(0)
        }
        Kind::Array if d.len_of(id) > 0 => {
            1 + d.elements(id).iter().map(|&v| depth(d, v)).max().unwrap_or(0)
        }
        _ => 0,
    }
}

fn paths_of(d: &Doc, id: u32, p: &str, acc: &mut HashSet<String>) {
    if !p.is_empty() {
        acc.insert(p.to_string());
    }
    match d.kind(id) {
        Kind::Object => {
            for m in d.members(id) {
                paths_of(d, m.val, &format!("{p}.{}", d.key(m)), acc);
            }
        }
        Kind::Array => {
            let kp = format!("{p}[]");
            for &v in d.elements(id) {
                paths_of(d, v, &kp, acc);
            }
        }
        _ => {}
    }
}

/// The shapes a field takes, as a set, so `varies()` can discount an empty
/// array beside a full one.
fn shapes_of(t: &Tally) -> BTreeSet<String> {
    t.keys().map(|s| s.to_string()).collect()
}

/// The whole report, as the probe prints it.
///
/// `d` is `None` exactly when nothing could be parsed, which is the same
/// condition as `h.format == None` — the report returns after two lines there,
/// so the document is never reached.
pub fn report(d: Option<&Doc>, h: &Health, name: &str) -> String {
    report_at(d, h, name, "")
}

/// The report, with a note saying where it is standing.
///
/// **A scoped report that does not say it is scoped is a report that lies by
/// omission** — the shape below describes a subtree while the health line
/// describes the whole file, and without this line the two read as one claim.
///
/// `at` is the RESOLVED path, not the names the user typed, so the `*` that
/// says *mapped over every value here* is visible. That is the notation being
/// output rather than input, which is what the vocabulary decided it should be.
/// Fields at one record shape that are LISTS PACKED INTO TEXT — defect 26.
///
/// **A field wrapped in the same non-alphanumeric character at both ends, AND
/// at least one SIBLING field wrapped in that same character.** One field alone
/// is never enough: `,nc,` and `04-gharchive`'s `:hash:` are structurally
/// identical and no single value separates them. `design/probe.py::packed` owns
/// the reasoning and the measurement — 3 matched, 3 true, 0 false over all 29
/// documents, where the relaxed rule takes 386 false.
fn packed(d: &Doc, objs: &[u32]) -> (Vec<String>, char) {
    let mut names: Vec<String> = Vec::new();
    for &o in objs {
        for m in d.members(o) {
            let k = d.key(m).to_string();
            if !names.contains(&k) {
                names.push(k);
            }
        }
    }
    names.sort();
    let mut wrap: Vec<(String, char)> = Vec::new();
    for name in names {
        let mut chars: Vec<char> = Vec::new();
        let mut any = false;
        let mut ok = true;
        for &o in objs {
            let Some(v) = d.get(o, &name) else { continue };
            if d.is_null(v) {
                continue;
            }
            any = true;
            let Some(t) = d.as_str(v) else {
                ok = false;
                break;
            };
            let cs: Vec<char> = t.chars().collect();
            if cs.len() < 3 || cs[0] != cs[cs.len() - 1]
                || cs[0].is_alphanumeric() || cs[0].is_whitespace()
            {
                ok = false;
                break;
            }
            if !chars.contains(&cs[0]) {
                chars.push(cs[0]);
            }
        }
        if ok && any && chars.len() == 1 {
            wrap.push((name, chars[0]));
        }
    }
    let hits: Vec<String> = wrap
        .iter()
        .filter(|(_, c)| wrap.iter().filter(|(_, o)| o == c).count() > 1)
        .map(|(n, _)| n.clone())
        .collect();
    let w = hits
        .first()
        .and_then(|h| wrap.iter().find(|(n, _)| n == h).map(|(_, c)| *c))
        .unwrap_or(' ');
    (hits, w)
}

pub fn report_at(d: Option<&Doc>, h: &Health, name: &str, at: &str) -> String {
    let mut o = String::new();
    let mut lit = String::new();
    py_str_lit(name, &mut lit);
    o.push_str(&format!("\n> fathom({lit})\n\n"));
    if !at.is_empty() && at != "$" {
        o.push_str(&format!("  at {at}\n"));
    }

    let b = h.bytes;
    let mut size = if b < 1024 {
        format!("{b} bytes")
    } else if b < 1 << 20 {
        format!("{:.0} KB", b as f64 / 1024.0)
    } else {
        format!("{:.1} MB", b as f64 / (1u64 << 20) as f64)
    };

    let Some(fmt) = h.format else {
        let what = if h.empty == Some(true) {
            "empty"
        } else if h.truncated == Some(true) {
            "chopped off"
        } else {
            "not a format I recognise"
        };
        o.push_str(&format!("  {size} · {what}\n"));
        o.push_str(&format!("  {}\n", h.error.as_deref().unwrap_or("")));
        return o;
    };
    let Some(d) = d else { return o };

    let mut said = match fmt {
        Format::Json => "valid JSON · read whole file".to_string(),
        Format::Ndjson => format!(
            "NDJSON, {} of {} records read · not one JSON document, and not broken",
            commas(h.records.unwrap_or(0)),
            commas(h.lines.unwrap_or(0))
        ),
        Format::Jsonc => {
            "JSONC, comments and trailing commas · not valid JSON, and not broken".to_string()
        }
    };
    if let Some(c) = h.compressed {
        said = format!(
            "{:.1} MB of {c}, unpacked to {size} · {said}",
            h.packed_bytes.unwrap_or(0) as f64 / (1u64 << 20) as f64
        );
        size = format!("{:.1} MB", h.bytes as f64 / (1u64 << 20) as f64);
    }

    let mut flags = vec![
        match h.dupes.unwrap_or(0) {
            0 => "no duplicate keys".to_string(),
            n => format!("{n} duplicate keys"),
        },
        match h.nonfinite.unwrap_or(0) {
            0 => "no NaN or Infinity".to_string(),
            n => format!("{n} NaN/Infinity"),
        },
        match h.bigints.unwrap_or(0) {
            0 => "no ints past 2^53".to_string(),
            n => format!("{n} ints past 2^53"),
        },
    ];
    for (v, msg) in [
        (h.negzero.unwrap_or(0), "negative zeros, sign lost on parse"),
        (h.bad_bytes, "bytes that are not valid UTF-8"),
        (h.encoded.unwrap_or(0), "values that are themselves encoded JSON"),
    ] {
        if v > 0 {
            flags.push(format!("{v} {msg}"));
        }
    }
    let enc = match h.bom {
        Some(bo) => format!(" · {bo} BOM"),
        None => String::new(),
    };
    o.push_str(&format!("  {size} · {said}{enc}\n"));
    o.push_str(&format!("  {}\n", flags.join(" · ")));
    if !h.bad_lines.is_empty() {
        // Coverage honesty: say what could not be read, and where.
        o.push_str(&format!(
            "  {} line{} could not be read, first at line {} — everything below describes the rest\n",
            h.bad_lines.len(),
            if h.bad_lines.len() > 1 { "s" } else { "" },
            h.bad_lines[0].0
        ));
    }
    if h.sampled == Some(true) {
        // The sampling contract. The probe must never let a reader believe a
        // description covers a document it only sampled.
        o.push_str(&format!(
            "  SAMPLE: the first {} of {} records. Everything below describes those and cannot speak for the rest.\n",
            commas(h.records.unwrap_or(0)),
            commas(h.lines.unwrap_or(0))
        ));
    }

    let walk = containers(d);
    let fold = fold_recursion(d, walk);
    let (inst, arrs, rec, types) = (&fold.inst, &fold.arrs, &fold.rec, &fold.types);

    let mut sorted_paths: Vec<&str> = inst.keys().collect();
    sorted_paths.sort_unstable();

    let mut keyed: Vec<(&str, usize, String)> = Vec::new();
    let mut undecided: Vec<&str> = Vec::new();
    let mut saturated: Vec<(&str, usize, String)> = Vec::new();
    for p in &sorted_paths {
        let objs = inst.get(p).unwrap();
        let (v, why) = classify(d, objs);
        if v == Verdict::Data {
            let total: usize = objs.iter().map(|&x| d.len_of(x)).sum();
            keyed.push((p, total / objs.len().max(1), why));
        } else if v == Verdict::Undecided && *p != "$" {
            undecided.push(p);
        } else if v == Verdict::Saturated && *p != "$" {
            // The count classify() reasoned about, not the raw one — it drops
            // empty objects first, so sorting on the raw length ordered the
            // list by a number the line beside it does not print.
            let live = objs.iter().filter(|&&x| d.len_of(x) > 0).count();
            let head = why.split(" — ").next().unwrap_or(&why).to_string();
            saturated.push((p, live, head));
        }
    }

    o.push_str("\n  KEYS THAT ARE DATA\n");
    // Biggest first and capped: 47 sites whose paths run past 180 characters
    // is not a description.
    let mut by_size: Vec<&(&str, usize, String)> = keyed.iter().collect();
    by_size.sort_by_key(|k| std::cmp::Reverse(k.1));
    for (p, n, why) in by_size.iter().take(SHOW) {
        o.push_str(&format!(
            "    {} {{{n} keys}}   {why}\n",
            lpad(&cut(p, 110), 40)
        ));
    }
    if by_size.len() > SHOW {
        o.push_str(&format!(
            "    … and {} more keyed sites, the largest {} keys\n",
            by_size.len() - SHOW,
            by_size[SHOW].1
        ));
    }
    if !undecided.is_empty() {
        // An honest "I cannot tell" has to be summarised or it becomes noise.
        let head: Vec<&str> = undecided.iter().take(8).copied().collect();
        o.push_str(&format!(
            "    could not call {} small single-copy objects, shortest first:\n",
            undecided.len()
        ));
        let mut shortest = head.clone();
        shortest.sort_by_key(|u| u.chars().count());
        for u in &shortest {
            o.push_str(&format!("      {}\n", cut(u, 96)));
        }
        if undecided.len() > head.len() {
            o.push_str(&format!(
                "      … and {} more\n",
                undecided.len() - head.len()
            ));
        }
    }
    if !saturated.is_empty() {
        // DEFECT 23: this used to be folded into the line above, which said
        // "small single-copy objects" about `$[].bottle.stable.files` and its
        // 8,531 copies. A right verdict with a lie attached sends a reader to
        // look at single-copy objects that are not the problem.
        o.push_str(&format!(
            "    could not call {} {} whose whole key vocabulary would fit in \
             a field list, most copies first:\n",
            saturated.len(),
            if saturated.len() == 1 { "site" } else { "sites" }
        ));
        let mut by_copies: Vec<&(&str, usize, String)> = saturated.iter().collect();
        by_copies.sort_by_key(|s| std::cmp::Reverse(s.1));
        for (p, _, why) in by_copies.iter().take(8) {
            o.push_str(&format!("      {} {why}\n", lpad(&cut(p, 60), 60)));
        }
        if saturated.len() > 8 {
            o.push_str(&format!("      … and {} more\n", saturated.len() - 8));
        }
    }

    o.push_str("\n  RECORD SHAPES, FOLDED\n");
    let mut shown: Vec<(&str, Vec<u32>)> = Vec::new();
    for (p, objs) in inst.iter() {
        let live: Vec<u32> = objs.iter().copied().filter(|&x| d.len_of(x) > 0).collect();
        if live.len() >= 2 && classify(d, &live).0 != Verdict::Data {
            shown.push((p, live));
        }
    }
    let splits: Vec<Option<Split>> = shown.iter().map(|(_, o)| discriminator(d, o)).collect();
    // A SHAPE THAT SPLITS IS NEVER DROPPED. Sorting by copies alone cost four
    // of `09-stripe-openapi`'s five splits to the cap, which is a display limit
    // hiding the most important thing the probe has to say.
    let mut order: Vec<usize> = (0..shown.len()).collect();
    order.sort_by_key(|&i| (splits[i].is_none(), std::cmp::Reverse(shown[i].1.len())));

    // ONE SHAPE IS DESCRIBED ONCE — defect 25, found by `23-cratesio-summary`,
    // where a 23-field crate record arrived under four containers and was
    // printed four times. `fold_recursion` already merges identical key-sets
    // when one is REACHABLE from the other, which is defect 1's repair and is
    // not touched here; siblings are not recursion.
    //
    // The test is exact — same `always`, same `sometimes` WITH counts — so the
    // block replaced would have been byte-identical and nothing is lost.
    let mut seen: HashMap<(Vec<String>, Vec<(usize, String)>), String> = HashMap::new();

    for &i in order.iter().take(SHOW) {
        let (p, objs) = &shown[i];
        let mut c: Tally = Tally::new();
        for &x in objs {
            for m in d.members(x) {
                c.bump(d.key(m));
            }
        }
        let mut always: Vec<String> = c
            .iter()
            .filter(|(_, &v)| v == objs.len())
            .map(|(k, _)| k.to_string())
            .collect();
        always.sort();
        let mut some: Vec<(usize, String)> = c
            .iter()
            .filter(|(_, &v)| v < objs.len())
            .map(|(k, &v)| (v, k.to_string()))
            .collect();
        some.sort_by(|a, b| b.cmp(a));
        let mut keysets: HashSet<Vec<&str>> = HashSet::new();
        for &x in objs {
            let mut ks: Vec<&str> = d.members(x).iter().map(|m| d.key(m)).collect();
            ks.sort_unstable();
            keysets.insert(ks);
        }
        let shapes = keysets.len();
        let deep = match rec.get(p) {
            Some(&n) if n > 0 => format!(" · RECURSIVE, {} levels", n + 1),
            _ => String::new(),
        };
        o.push_str(&format!(
            "    {p}   {} copies · {} fields · {shapes} distinct key-set{}{deep}\n",
            objs.len(),
            c.len(),
            if shapes > 1 { "s" } else { "" }
        ));
        let mut block = String::new();
        fields(&mut block, "always", &always);
        // `sometimes (none)` is noise: the header's `1 distinct key-set` has
        // already said it.
        if !some.is_empty() {
            let items: Vec<String> = some.iter().map(|(v, k)| format!("{k}({v})")).collect();
            fields(&mut block, "sometimes", &items);
        }
        // SAY IT ONCE, UNLESS SAYING WHERE COSTS MORE THAN SAYING IT AGAIN.
        // Measured: collapsing unconditionally made six of eleven affected files
        // LARGER, because a three-field list is cheaper than a reference to a
        // fifty-character path. The two criteria agree — a reader cannot eyeball
        // two 23-field lists as identical, and that is the same length at which
        // the reference starts paying.
        let sig = (always.clone(), some.clone());
        let back = seen
            .get(&sig)
            .map(|r| format!("      same shape as {}\n", cut(r, 96)));
        match back {
            Some(b) if b.chars().count() < block.chars().count() => o.push_str(&b),
            _ => {
                seen.entry(sig).or_insert_with(|| p.to_string());
                o.push_str(&block);
            }
        }

        // Defect 26 — lists packed into text. Printed where a reader meets
        // the fields rather than as its own section. `design/probe.py::packed`
        // owns the rule and the reasoning; this reproduces it.
        let (packs, wrapper) = packed(d, objs);
        if !packs.is_empty() {
            o.push_str(&format!(
                "      └─ {} {} packed into text — '{}' wraps every value and {} fields here share it\n",
                packs.join(", "),
                if packs.len() > 1 { "are lists" } else { "is a list" },
                wrapper,
                packs.len()
            ));
        }

        if let Some(sp) = &splits[i] {
            let gs: Vec<Vec<u32>> = sp.groups.iter().map(|(_, g)| g.clone()).collect();
            // Say which disorder the split removes. `10-wikidata`'s is 0% empty
            // and entirely disagreement about the shape of a value.
            let what = if variation(d, objs) > emptiness(d, objs) {
                format!(
                    "{} of fields disagree on shape, {} after",
                    pct(variation(d, objs)),
                    pct(weighted(d, &gs, variation))
                )
            } else {
                format!(
                    "{} empty folded, {} after",
                    pct(emptiness(d, objs)),
                    pct(weighted(d, &gs, emptiness))
                )
            };
            o.push_str(&format!(
                "      SPLIT ON   {} — {} kinds, not one shape. {what}\n",
                sp.field,
                sp.groups.len()
            ));
            let mut top: Vec<&(String, Vec<u32>)> = sp.groups.iter().collect();
            top.sort_by_key(|(_, g)| std::cmp::Reverse(g.len()));
            for (v, g) in top.iter().take(6) {
                let mut cols: BTreeSet<&str> = BTreeSet::new();
                for &x in g.iter() {
                    cols.extend(filled(d, x));
                }
                o.push_str(&format!(
                    "        {} {} x {} cols   {} empty\n",
                    lpad(&cut(v, 28), 30),
                    rpad(&g.len().to_string(), 5),
                    rpad(&cols.len().to_string(), 3),
                    pct(emptiness(d, g))
                ));
            }
            if sp.groups.len() > 6 {
                let mut by_len: Vec<usize> = sp.groups.iter().map(|(_, g)| g.len()).collect();
                by_len.sort_unstable();
                let rest: usize = by_len[..by_len.len() - 6].iter().sum();
                o.push_str(&format!(
                    "        … {} more, {rest} instances\n",
                    sp.groups.len() - 6
                ));
            }
        }
    }
    if order.len() > SHOW {
        o.push_str(&format!(
            "    … and {} more record shapes, the largest {} copies. Ordered by copies, so what is above is the biggest of them.\n",
            order.len() - SHOW,
            shown[order[SHOW]].1.len()
        ));
    }

    // A null is not a type. The probe once printed `execution_count number
    // x131, null x1` under FIELDS THAT CHANGE TYPE for one unexecuted cell in
    // 272, while `axes.py` graded the same file polymorphic 0.
    let mut poly: Vec<(&str, &Tally)> = Vec::new();
    for (p, c) in types.iter() {
        let s = shapes_of(c);
        let live: BTreeSet<&String> = s.iter().filter(|t| *t != "null").collect();
        let n = {
            let bare = live.iter().any(|t| t.as_str() == "array");
            let indexed = live.iter().any(|t| t.starts_with("array["));
            live.len() - usize::from(bare && indexed)
        };
        if n > 1 {
            poly.push((p, c));
        }
    }
    if !poly.is_empty() {
        poly.sort_by_key(|(_, c)| std::cmp::Reverse(c.total()));
        o.push_str("\n  FIELDS THAT CHANGE TYPE\n");
        // DEFECT 33, repaired 2026-08-12. The only one of the four sections
        // without a cap: `29-mdn-browser-compat` has 1,336 fields that change
        // type and printed 1,444 lines of a 1,962-line report. The argument is
        // already written above the keyed-site cap — an unordered list of 47 is
        // not a description, and 1,336 is not one either. Most values first,
        // and what is dropped is SAID.
        for (p, c) in poly.iter().take(SHOW) {
            let spread: Vec<String> = c
                .most_common()
                .iter()
                .map(|(t, n)| format!("{t} x{}", commas(*n)))
                .collect();
            o.push_str(&format!("    {} {}\n", lpad(p, 44), spread.join(", ")));

            let holder = parent_of(p);
            let field = after_last_dot(p);
            let holder_objs = inst.get(holder).cloned().unwrap_or_default();
            let found = discriminator(d, &holder_objs);
            // A field can look polymorphic only because the fold merged records
            // of different kinds.
            if let Some(sp) = &found {
                let uniform = sp.groups.iter().all(|(_, g)| {
                    let mut s: BTreeSet<String> = BTreeSet::new();
                    for &x in g {
                        if let Some(v) = d.get(x, field) {
                            s.insert(shape(d, v));
                        }
                    }
                    varies(&s) <= 1
                });
                if uniform {
                    o.push_str(&format!(
                        "    {} └─ not really: one type within each {}. An artifact of folding {} kinds.\n",
                        lpad("", 44),
                        sp.field,
                        sp.groups.len()
                    ));
                    continue;
                }
            }

            // MISSINGNESS WEARING A VALUE. A field that is a NUMBER on some
            // records and one of very FEW strings on others. Across all corpus
            // files exactly two fields match and both are that bug.
            let mut nums = false;
            let mut txts: BTreeSet<&str> = BTreeSet::new();
            for &x in &holder_objs {
                if let Some(v) = d.get(x, field) {
                    match d.node(v) {
                        Node::Int(_) | Node::Float(_) | Node::BigInt(_) => nums = true,
                        Node::Str(s) => {
                            txts.insert(d.str_at(s));
                        }
                        _ => {}
                    }
                }
            }
            if nums && !txts.is_empty() && txts.len() <= 3 {
                let listed: Vec<String> = txts
                    .iter()
                    .map(|t| {
                        let mut b = String::new();
                        py_str_lit(t, &mut b);
                        b
                    })
                    .collect();
                o.push_str(&format!(
                    "    {} └─ {} where a number was expected — missing, written as a value. Not counted as empty.\n",
                    lpad("", 44),
                    listed.join(", ")
                ));
            }
        }
        if poly.len() > SHOW {
            let rest = &poly[SHOW..];
            o.push_str(&format!(
                "    … and {} more fields that change type, the largest {} values\n",
                commas(rest.len()),
                commas(rest[0].1.total())
            ));
        }
    }

    let aligned = positional(d, arrs);
    if !aligned.is_empty() {
        o.push_str("\n  ALIGNED BY POSITION, NOT BY NESTING\n");
        for (n, ps) in &aligned {
            let plist: Vec<&str> = ps.iter().map(|(p, _)| *p).collect();
            let one_parent = names_are_keys(&plist);
            let names: Vec<&str> = if one_parent {
                Vec::new()
            } else {
                ps.iter()
                    .filter(|(p, first)| {
                        looks_like_names(d, &[*first], arrs.get(p).map_or(0, |v| v.len()))
                    })
                    .map(|(p, _)| *p)
                    .collect()
            };
            o.push_str(&format!(
                "    {} paths hold arrays of exactly {n} — same length everywhere, so probably one table stored in columns\n",
                ps.len()
            ));
            for (p, first) in ps {
                let tag = if names.contains(p) { "   <- the names" } else { "" };
                let sample: Vec<String> = d
                    .elements(*first)
                    .iter()
                    .take(4)
                    .map(|&v| py_str(d, v))
                    .collect();
                // The space between the padded path and the sample is part of
                // the format string in the probe, not part of the padding.
                o.push_str(&format!(
                    "      {} {}{tag}\n",
                    lpad(p, 46),
                    cut(&sample.join(", "), 38)
                ));
            }
            if !names.is_empty() {
                // All candidates are listed rather than one being chosen. File
                // 06 offers three spellings of the same header, so picking one
                // would be arbitrary dressed as an answer.
                let tails: Vec<&str> = names.iter().map(|p| after_last_dot(p)).collect();
                o.push_str(&format!(
                    "      to name the others, zip them in order against {}\n",
                    tails.join(" or ")
                ));
                o.push_str(&format!(
                    "      NOT against another array of {n} found elsewhere: same length is not same order\n"
                ));
            } else if one_parent {
                // Said explicitly, because "no header row" and "the names are
                // right here" are different facts.
                o.push_str(&format!(
                    "      the names are the keys of {} — nothing to join and nothing to mis-join\n",
                    parent_of(ps[0].0)
                ));
            }
        }
    }

    let mut all_paths: HashSet<String> = HashSet::new();
    paths_of(d, d.root(), "", &mut all_paths);
    o.push_str(&format!(
        "\n  {} levels deep · {} distinct paths\n",
        depth(d, d.root()),
        commas(all_paths.len())
    ));

    // The menu says what it is FOR — see `design/probe.py`, which owns the
    // reasoning. A label is a name for `rows()` and not always one `into()` can
    // take, and 75% of named candidates are in that second group.
    o.push_str("\n  ONE ROW COULD BE — give any of these to rows()\n");
    for c in candidates(d, inst, arrs, rec) {
        let mut bits = format!("{} rows", rpad(&commas(c.rows), 7));
        if c.cols > 0 {
            bits.push_str(&format!(" x {} cols", rpad(&c.cols.to_string(), 4)));
        }
        if let Some(hl) = c.holes {
            if hl > 0.1 {
                bits.push_str(&format!("   {} empty", pct(hl)));
            }
        }
        if let Some((col, n)) = &c.dup {
            bits.push_str(&format!("   {col} repeated {:.0}x", n));
        }
        o.push_str(&format!("    {}{bits}\n", lpad(&c.label, 34)));
        // The join. A candidate whose records carry a discriminator is not one
        // table, and the probe knew that before it printed the line above.
        if let Some(sp) = &c.split {
            let mut top: Vec<&(String, Vec<u32>)> = sp.groups.iter().collect();
            top.sort_by_key(|(_, g)| std::cmp::Reverse(g.len()));
            let named: Vec<String> = top
                .iter()
                .take(4)
                .map(|(v, g)| format!("{} {}", cut(v, 18), commas(g.len())))
                .collect();
            let more = if top.len() > 4 {
                format!(", +{} more", top.len() - 4)
            } else {
                String::new()
            };
            let gs: Vec<Vec<u32>> = sp.groups.iter().map(|(_, g)| g.clone()).collect();
            o.push_str(&format!(
                "      └─ or {} tables, split on {} — {} empty: {}{more}\n",
                sp.groups.len(),
                sp.field,
                pct(weighted(d, &gs, emptiness)),
                named.join(", ")
            ));
        }
        // DEFECT 34. The count above is one path's; say what it leaves out.
        if let Some((n, k, where_)) = &c.more {
            let at = if *k == 1 {
                where_.clone()
            } else {
                format!("{k} other paths")
            };
            o.push_str(&format!(
                "      └─ {} more at {at} — not counted above\n",
                commas(*n)
            ));
        }
    }
    o.push('\n');
    o
}
