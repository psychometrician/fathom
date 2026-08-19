//! Is this sound? — the first of the three things the one verb answers.
//!
//! A port of `health()` in `design/probe.py`, and the useful split is **loud
//! against silent, not valid against invalid**. Loud is a truncated download or
//! a model response cut off at `max_tokens`. Silent is the half worth owning:
//! duplicate keys where the last one wins, integers past 2^53, the `NaN` that
//! Python writes and jsonlite refuses, a value that is itself an encoded
//! document.
//!
//! **The policy is report, never repair.** Silently fixing a document destroys
//! the evidence that something upstream is broken.

use crate::json::{Doc, Node, ParseError, SAFE_INT};
use std::io::Read;

/// The sampling contract's cap. See `read()`.
pub const MAX_RECORDS: usize = 20_000;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Format {
    Json,
    Ndjson,
    Jsonc,
}

impl Format {
    pub fn name(self) -> &'static str {
        match self {
            Format::Json => "JSON",
            Format::Ndjson => "NDJSON",
            Format::Jsonc => "JSONC",
        }
    }
}

#[derive(Clone, Debug, Default)]
pub struct Health {
    pub bytes: usize,
    pub compressed: Option<&'static str>,
    pub packed_bytes: Option<usize>,
    pub bom: Option<&'static str>,
    pub bad_bytes: usize,
    pub format: Option<Format>,
    /// Only when nothing could be read. Python's wording, verbatim.
    pub error: Option<String>,
    pub empty: Option<bool>,
    pub truncated: Option<bool>,
    /// NDJSON only.
    pub records: Option<usize>,
    pub lines: Option<usize>,
    pub sampled: Option<bool>,
    pub bad_lines: Vec<(usize, String)>,
    // **The silent half, and it is `Option` on purpose.** These are set only
    // when something was actually parsed. On a file that could not be read, the
    // probe reports no damage counters at all rather than zeroes, because "0
    // duplicate keys" is a claim about a document it never got to look at, and
    // never lying about its own coverage is the contract. `bad_bytes` is not
    // among them: decoding happens before parsing, so it is always known.
    pub dupes: Option<usize>,
    pub negzero: Option<usize>,
    pub nonfinite: Option<usize>,
    pub bigints: Option<usize>,
    pub encoded: Option<usize>,
}

/// A BOM is a document in the wrong clothes, not an unrecognised format.
/// UTF-32's markers are tested before UTF-16's, because `ff fe 00 00` starts
/// with `ff fe`.
const BOMS: [(&[u8], &str); 5] = [
    (&[0x00, 0x00, 0xfe, 0xff], "utf-32-be"),
    (&[0xff, 0xfe, 0x00, 0x00], "utf-32-le"),
    (&[0xef, 0xbb, 0xbf], "utf-8"),
    (&[0xfe, 0xff], "utf-16-be"),
    (&[0xff, 0xfe], "utf-16-le"),
];

pub fn health(path: &std::path::Path) -> std::io::Result<(Health, Option<Doc>)> {
    health_at(path, MAX_RECORDS)
}

/// `health()` with the sampling contract's cap as a parameter.
///
/// **`read()` has always taken the cap and `health()` never did**, so varying it
/// meant going through the byte-slice entry point — which slurps, and therefore
/// could not measure the streaming path at all. Author item 3 asks what it costs
/// to stop sampling, and that question cannot be answered by an instrument that
/// bypasses the reader the answer depends on. `usize::MAX` means no cap.
pub fn health_at(
    path: &std::path::Path,
    max_records: usize,
) -> std::io::Result<(Health, Option<Doc>)> {
    if let Some(got) = stream_ndjson(path, max_records)? {
        return Ok(got);
    }
    let raw = std::fs::read(path)?;
    Ok(read(&raw, max_records))
}

/// How much to pull per `read()` while streaming. Large enough that a 870 MB
/// document is not a million syscalls, small enough to stay off the heap's
/// radar. Nothing depends on this value being any particular size.
const CHUNK: usize = 256 * 1024;

/// Enough bytes to hold the first 50 non-empty lines of any real NDJSON. If the
/// prefix runs out before 50 lines, the document is small and gets slurped —
/// there is nothing to save on a file this size, and the proven path is free.
const PREFIX_CAP: usize = 8 * 1024 * 1024;

/// NDJSON without holding the document — the reason `MAX_RECORDS` exists.
///
/// **The sampling contract bounds the PARSE and `std::fs::read` did not bound
/// the READ**, so `26-gharchive-scale` cost 1,073 MB to describe 6.97% of
/// itself: 117.6 MB of gzip and 869.8 MB of inflated text, both live, to look at
/// 20,000 of 286,864 records. `FINDINGS.md` 2026-08-15.
///
/// **This returns `None` whenever equivalence cannot be PROVED, and `health()`
/// slurps instead.** That is the safety property the whole change rests on:
/// every document that does not take this path runs exactly the code it ran
/// before, so it is byte-identical by construction rather than by testing.
///
/// The conditions are all of: no BOM; strict UTF-8 throughout; at least two
/// non-empty lines; **the first non-empty line parses on its own**; and the same
/// 60%-of-the-first-50 rule `other_format()` applies.
///
/// **The first-line condition is what makes skipping the whole-document JSON
/// attempt a proof rather than a guess.** `read()` tries `parse_into(txt)` on
/// the entire text before considering NDJSON. If line 1 is a complete JSON value
/// and a second non-empty line exists, that attempt MUST fail — a JSON document
/// is exactly one value and anything following it is trailing content — so the
/// branch this path skips could not have been taken.
fn stream_ndjson(
    path: &std::path::Path,
    max_records: usize,
) -> std::io::Result<Option<(Health, Option<Doc>)>> {
    let file = std::fs::File::open(path)?;
    let packed = file.metadata().map(|m| m.len() as usize).ok();

    // Two bytes decide gzip, and they have to be put back before anything else
    // reads. `Chain` is exactly that and costs nothing.
    let mut head = [0u8; 2];
    let mut probe_reader = std::io::BufReader::new(file);
    let n = fill(&mut probe_reader, &mut head)?;
    let gz = n == 2 && head[..2] == [0x1f, 0x8b];
    let joined = std::io::Read::chain(std::io::Cursor::new(head[..n].to_vec()), probe_reader);
    let mut src: Box<dyn std::io::Read> = if gz {
        Box::new(flate2::read::GzDecoder::new(joined))
    } else {
        Box::new(joined)
    };

    // ── the prefix, which decides whether this path applies at all ──
    let mut buf: Vec<u8> = Vec::with_capacity(CHUNK);
    let mut chunk = vec![0u8; CHUNK];
    let mut eof = false;
    while buf.len() < PREFIX_CAP && count_lines(&buf) < 51 {
        let got = src.read(&mut chunk)?;
        if got == 0 {
            eof = true;
            break;
        }
        buf.extend_from_slice(&chunk[..got]);
    }
    // A BOM is a document in the wrong clothes and `decode()` owns that; a
    // 16- or 32-bit encoding cannot be split on `\n` bytes at all.
    if BOMS.iter().any(|(b, _)| buf.starts_with(b)) {
        return Ok(None);
    }
    // Small enough to have ended inside the prefix: slurping costs nothing and
    // the proven path is worth more than the saving.
    if eof {
        return Ok(None);
    }
    let Ok(text) = std::str::from_utf8(&buf) else {
        return Ok(None); // ill-formed bytes: `decode()`'s lossy path owns this
    };
    // The last line in the prefix is almost certainly cut in half, so it is not
    // evidence about anything and is dropped before the format test.
    let mut lines: Vec<&str> = text
        .split('\n')
        .map(|l| l.trim_end_matches('\r'))
        .filter(|l| !l.trim().is_empty())
        .collect();
    lines.pop();
    if lines.len() < 2 {
        return Ok(None);
    }
    // `other_format()`'s rule, applied to the same first 50.
    let sample = &lines[..lines.len().min(50)];
    let ok = sample.iter().filter(|l| Doc::parses(l)).count();
    if (ok as f64) < 2.0f64.max(sample.len() as f64 * 0.6) {
        return Ok(None);
    }
    // The proof. Without this the whole-document JSON attempt cannot be skipped.
    if !Doc::parses(lines[0]) {
        return Ok(None);
    }

    // ── committed: stream the rest, holding one line at a time ──
    let mut out = Health {
        compressed: if gz { Some("gzip") } else { None },
        packed_bytes: if gz { packed } else { None },
        ..Default::default()
    };
    let mut doc = Doc::new();
    let mut roots = Vec::new();
    let mut total_lines = 0usize;
    let mut bytes = 0usize;
    // The prefix is part of the stream, not something separate: it becomes the
    // carry's first contents and is never copied again.
    bytes += buf.len();
    let mut carry: Vec<u8> = buf;

    loop {
        let mut start = 0;
        while let Some(nl) = memchr(b'\n', &carry[start..]) {
            let line = &carry[start..start + nl];
            if !take_line(line, &mut doc, &mut roots, &mut total_lines, max_records, &mut out) {
                return Ok(None); // ill-formed UTF-8: hand it to the lossy path
            }
            start += nl + 1;
        }
        // Only the tail of an unfinished line survives a chunk, so this shifts
        // one partial record rather than a buffer.
        carry.drain(..start);
        let got = src.read(&mut chunk)?;
        if got == 0 {
            break;
        }
        bytes += got;
        carry.extend_from_slice(&chunk[..got]);
    }
    // Whatever is left had no trailing newline; it is still a line.
    if !take_line(&carry, &mut doc, &mut roots, &mut total_lines, max_records, &mut out) {
        return Ok(None);
    }

    out.bytes = bytes;
    doc.root_array(&roots);
    out.format = Some(Format::Ndjson);
    out.records = Some(roots.len());
    out.lines = Some(total_lines);
    // `other_format()` writes this as `lines.len() > read_n` where
    // `read_n = lines.len().min(max_records)`. Same statement, said once.
    out.sampled = Some(total_lines > max_records);
    damage(&mut out, &doc);
    Ok(Some((out, Some(doc))))
}

/// One line of the stream, with `other_format()`'s filtering rule exactly.
/// Returns false if the bytes are not valid UTF-8, which abandons the fast path.
fn take_line(
    raw: &[u8],
    doc: &mut Doc,
    roots: &mut Vec<u32>,
    total: &mut usize,
    max_records: usize,
    out: &mut Health,
) -> bool {
    let Ok(s) = std::str::from_utf8(raw) else {
        return false;
    };
    let s = s.trim_end_matches('\r');
    if s.trim().is_empty() {
        return true; // blank lines are not lines, per `other_format()`
    }
    *total += 1;
    if *total <= max_records {
        match doc.parse_into(s) {
            Ok(id) => roots.push(id),
            Err(e) => out.bad_lines.push((*total, e.to_string())),
        }
    }
    true
}

/// Non-empty lines fully contained in `buf`, for sizing the prefix only.
fn count_lines(buf: &[u8]) -> usize {
    buf.split(|&b| b == b'\n')
        .filter(|l| !l.iter().all(|&c| c.is_ascii_whitespace()))
        .count()
}

fn memchr(needle: u8, hay: &[u8]) -> Option<usize> {
    hay.iter().position(|&b| b == needle)
}

/// `read()` until the buffer is full or the source ends, because one `read()`
/// is allowed to return fewer bytes than asked for and a two-byte magic number
/// arriving one byte at a time would otherwise read as "not gzip".
fn fill(r: &mut impl std::io::Read, into: &mut [u8]) -> std::io::Result<usize> {
    let mut n = 0;
    while n < into.len() {
        match r.read(&mut into[n..])? {
            0 => break,
            got => n += got,
        }
    }
    Ok(n)
}

pub fn read(raw: &[u8], max_records: usize) -> (Health, Option<Doc>) {
    let mut out = Health {
        bytes: raw.len(),
        ..Default::default()
    };

    // Gzip is not a curiosity, it is how JSON at scale actually ships: GH
    // Archive, warehouse exports, log rotation, anything off S3.
    let owned;
    let mut raw = raw;
    if raw.starts_with(&[0x1f, 0x8b]) {
        let mut buf = Vec::new();
        if flate2::read::GzDecoder::new(raw).read_to_end(&mut buf).is_ok() {
            out.compressed = Some("gzip");
            out.packed_bytes = Some(raw.len());
            owned = buf;
            raw = &owned;
            out.bytes = raw.len();
        }
    }

    let bom = BOMS.iter().find(|(b, _)| raw.starts_with(b));
    out.bom = bom.map(|(_, e)| *e);
    // **A `Cow`, and it is worth 56 MB on `14-nyc-311`.** The first version
    // copied the decoded text once to own it and again to strip the BOM, so a
    // 28 MB document cost 84 MB of buffers before a single value was parsed —
    // and the port measured WORSE than the prototype it exists to beat. The
    // clean-UTF-8 path is the overwhelming common case and it now borrows.
    let decoded = decode(raw, out.bom);
    out.bad_bytes = decoded.1;
    // The BOM survives the decode as U+FEFF and is sliced off here, exactly as
    // Python's `.lstrip("﻿")` does, but without a third copy.
    let txt: &str = decoded.0.trim_start_matches('\u{feff}');

    let mut doc = Doc::new();
    match doc.parse_into(txt) {
        Ok(id) => {
            doc.set_root(id);
            out.format = Some(Format::Json);
            damage(&mut out, &doc);
            (out, Some(doc))
        }
        Err(e) => other_format(out, txt, e, max_records),
    }
}

fn other_format(
    mut out: Health,
    txt: &str,
    e: ParseError,
    max_records: usize,
) -> (Health, Option<Doc>) {
    // Split on \n and NOTHING ELSE. `str.splitlines()` also breaks on U+2028,
    // U+2029, \v, \f and NEL, and three GitHub payloads in `04-gharchive` carry
    // a literal U+2028 in user-written text — so three valid records became six
    // fragments and the probe reported six unreadable lines that it had created.
    // A diagnostic that accurately reports damage it caused itself is worse
    // than one that says nothing.
    let lines: Vec<&str> = txt
        .split('\n')
        .map(|l| l.trim_end_matches('\r'))
        .filter(|l| !l.trim().is_empty())
        .collect();

    // MOST of a sample, not all of it. Requiring every one of the first 50 to
    // parse meant a three-line file with one bad line was not NDJSON at all, so
    // the format was lost over a single broken record — which is the very case
    // the format most needs reporting for.
    let sample = &lines[..lines.len().min(50)];
    let ok = sample.iter().filter(|l| Doc::parses(l)).count();
    if lines.len() > 1 && ok as f64 >= 2.0f64.max(sample.len() as f64 * 0.6) {
        // NDJSON, and it stays NDJSON even if a later line is broken. The first
        // version detected it, hit a bad line, and forgot — reporting
        // "unrecognised" for a file whose format it had already identified.
        let read_n = lines.len().min(max_records);
        let mut doc = Doc::new();
        let mut roots = Vec::with_capacity(read_n);
        for (i, l) in lines[..read_n].iter().enumerate() {
            match doc.parse_into(l) {
                Ok(id) => roots.push(id),
                Err(le) => out.bad_lines.push((i + 1, le.to_string())),
            }
        }
        doc.root_array(&roots);
        out.format = Some(Format::Ndjson);
        out.records = Some(roots.len());
        out.lines = Some(lines.len());
        out.sampled = Some(lines.len() > read_n);
        damage(&mut out, &doc);
        return (out, Some(doc));
    }

    let stripped = strip_jsonc(txt);
    if stripped != txt {
        let mut doc = Doc::new();
        if let Ok(id) = doc.parse_into(&stripped) {
            doc.set_root(id);
            out.format = Some(Format::Jsonc);
            damage(&mut out, &doc);
            return (out, Some(doc));
        }
    }

    out.format = None;
    out.error = Some(e.to_string());
    let (empty, truncated) = why_unreadable(txt);
    out.empty = Some(empty);
    out.truncated = Some(truncated);
    (out, None)
}

/// Empty, chopped off, or genuinely not JSON — three different answers.
///
/// The first version tested only the last character, so a document truncated
/// just after a `]` was reported as unrecognisable rather than chopped off.
/// Depth at end-of-input is the honest test: something is still open.
fn why_unreadable(txt: &str) -> (bool, bool) {
    if txt.trim().is_empty() {
        return (true, false);
    }
    let (mut depth, mut instr, mut esc) = (0i64, false, false);
    for ch in txt.chars() {
        if esc {
            esc = false;
        } else if instr {
            match ch {
                '\\' => esc = true,
                '"' => instr = false,
                _ => {}
            }
        } else {
            match ch {
                '"' => instr = true,
                '[' | '{' => depth += 1,
                ']' | '}' => depth -= 1,
                _ => {}
            }
        }
    }
    (false, depth > 0 || instr)
}

/// Strings are matched first so a `//` inside one survives; anything else that
/// looks like a comment is removed, then trailing commas. This is
/// `design/probe.py`'s two regexes, written as one forward scan so the
/// left-to-right non-overlapping behaviour is the same.
fn strip_jsonc(txt: &str) -> String {
    let b = txt.as_bytes();
    let mut out = String::with_capacity(txt.len());
    let mut i = 0usize;
    while i < b.len() {
        match b[i] {
            b'"' => {
                let start = i;
                i += 1;
                while i < b.len() {
                    if b[i] == b'\\' {
                        i += 2;
                    } else if b[i] == b'"' {
                        i += 1;
                        break;
                    } else {
                        i += 1;
                    }
                }
                let end = i.min(b.len());
                out.push_str(&txt[start..end]);
            }
            b'/' if b.get(i + 1) == Some(&b'/') => {
                while i < b.len() && b[i] != b'\n' {
                    i += 1;
                }
            }
            b'/' if b.get(i + 1) == Some(&b'*') => {
                // An unterminated block comment is not a match, so it stays —
                // which is what the non-greedy regex does.
                match txt[i + 2..].find("*/") {
                    Some(off) => i = i + 2 + off + 2,
                    None => {
                        out.push('/');
                        i += 1;
                    }
                }
            }
            _ => {
                let start = i;
                while i < b.len() && b[i] != b'"' && b[i] != b'/' {
                    i += 1;
                }
                out.push_str(&txt[start..i]);
            }
        }
    }

    // `,(\s*[}\]])` -> `\1`
    let mut fin = String::with_capacity(out.len());
    let ob = out.as_bytes();
    let mut i = 0usize;
    while i < ob.len() {
        if ob[i] == b',' {
            let mut j = i + 1;
            while j < ob.len() && (ob[j] as char).is_ascii_whitespace() {
                j += 1;
            }
            if j < ob.len() && (ob[j] == b'}' || ob[j] == b']') {
                i += 1; // drop the comma, keep the whitespace and the bracket
                continue;
            }
        }
        let start = i;
        i += 1;
        while i < ob.len() && !out.is_char_boundary(i) {
            i += 1;
        }
        fin.push_str(&out[start..i]);
    }
    fin
}

/// The silent half: it parsed, and something was lost anyway.
fn damage(out: &mut Health, doc: &Doc) {
    out.dupes = Some(doc.tally.dupes);
    out.negzero = Some(doc.tally.negzero);
    let (mut nonfinite, mut bigints, mut encoded) = (0usize, 0usize, 0usize);
    let mut strings: Vec<u32> = Vec::new();
    doc.scalars(doc.root(), &mut |n| match n {
        // Counted on PARSED values. The first version regexed the raw text and
        // fired ten times on a notebook by matching the string "NaN" inside
        // legitimate R output. A health check that cries wolf is worse than none.
        Node::Float(v) if v.is_nan() || v.is_infinite() => nonfinite += 1,
        Node::Int(v) if (v as i128).abs() > SAFE_INT => bigints += 1,
        Node::BigInt(_) => bigints += 1,
        Node::Str(s) => strings.push(s),
        _ => {}
    });
    for s in strings {
        if encoded_doc(doc.str_at(s)) {
            encoded += 1;
        }
    }
    out.nonfinite = Some(nonfinite);
    out.bigints = Some(bigints);
    out.encoded = Some(encoded);
}

/// True if `s` holds an encoded JSON DOCUMENT, not merely parseable text.
///
/// **A document is an object, or an array containing one.** A bare array of
/// scalars is data that happens to be bracketed. Advent of Code day 18 input IS
/// nested integer lists and `[376.0, 490.543]` is a Python `repr`; all 17 of
/// `11-jupyter-notebook`'s reported encodings were that, and nothing upstream
/// had encoded anything.
pub fn encoded_doc(s: &str) -> bool {
    let s = s.trim();
    if !(s.starts_with('{') || s.starts_with('[')) {
        return false;
    }
    let mut d = Doc::new();
    let Ok(id) = d.parse_into(s) else {
        return false;
    };
    match d.kind(id) {
        crate::json::Kind::Object => true,
        crate::json::Kind::Array => d
            .elements(id)
            .iter()
            .any(|&e| d.kind(e) == crate::json::Kind::Object),
        _ => false,
    }
}

// ── decoding ─────────────────────────────────────────────────────────────────

/// Returns the text and the number of replacement characters it took to get it.
/// Strict first, so ill-formed bytes are reported instead of being silently
/// replaced by U+FFFD. A lone surrogate used to pass as clean.
fn decode<'a>(raw: &'a [u8], bom: Option<&str>) -> (std::borrow::Cow<'a, str>, usize) {
    use std::borrow::Cow;
    let wide = |(s, n): (String, usize)| (Cow::Owned(s), n);
    match bom {
        Some("utf-16-le") => wide(decode16(raw, false)),
        Some("utf-16-be") => wide(decode16(raw, true)),
        Some("utf-32-le") => wide(decode32(raw, false)),
        Some("utf-32-be") => wide(decode32(raw, true)),
        _ => match std::str::from_utf8(raw) {
            Ok(s) => (Cow::Borrowed(s), 0),
            Err(_) => {
                let s = String::from_utf8_lossy(raw).into_owned();
                let n = s.matches('\u{fffd}').count();
                (Cow::Owned(s), n)
            }
        },
    }
}

fn decode16(raw: &[u8], big: bool) -> (String, usize) {
    let units: Vec<u16> = raw
        .chunks_exact(2)
        .map(|c| {
            if big {
                u16::from_be_bytes([c[0], c[1]])
            } else {
                u16::from_le_bytes([c[0], c[1]])
            }
        })
        .collect();
    let mut s = String::with_capacity(units.len());
    let mut bad = 0usize;
    for r in char::decode_utf16(units) {
        match r {
            Ok(c) => s.push(c),
            Err(_) => {
                s.push('\u{fffd}');
                bad += 1;
            }
        }
    }
    if raw.len() % 2 != 0 {
        s.push('\u{fffd}');
        bad += 1;
    }
    (s, bad)
}

fn decode32(raw: &[u8], big: bool) -> (String, usize) {
    let mut s = String::new();
    let mut bad = 0usize;
    for c in raw.chunks_exact(4) {
        let v = if big {
            u32::from_be_bytes([c[0], c[1], c[2], c[3]])
        } else {
            u32::from_le_bytes([c[0], c[1], c[2], c[3]])
        };
        match char::from_u32(v) {
            Some(ch) => s.push(ch),
            None => {
                s.push('\u{fffd}');
                bad += 1;
            }
        }
    }
    if raw.len() % 4 != 0 {
        s.push('\u{fffd}');
        bad += 1;
    }
    (s, bad)
}
