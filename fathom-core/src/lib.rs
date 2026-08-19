//! fathom's core: one command, always the same, that leaves you oriented.
//!
//! **This crate is the port of `design/probe.py`, and the probe stays.** It is
//! the oracle: the port is finished when the diff between the two is empty, on
//! `test/`'s health cases and on every corpus file. `design/implementation.md`
//! records why the port was made, what it was predicted to cost, and the rule
//! that it reproduces the prototype's DEFECTS as faithfully as its findings —
//! a port that improves what it copies cannot be verified against it.

pub mod extract;
pub mod health;
pub mod json;
pub mod ordermap;
pub mod price;
pub mod report;
pub mod split;
pub mod structure;

/// Escape a string as a JSON string body. The probe's summary crosses the
/// process boundary as JSON, per `design/implementation.md`, so the core has to
/// write a little of it.
pub fn escape(s: &str, out: &mut String) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

/// Write a node as JSON. The extract half's wire format, per
/// `design/implementation.md` — one of these per cell, in an NDJSON row.
///
/// **A nested value is written nested, and that is the flattening decision.**
/// 17 of 19 corpus extracts carry a list-column; NDJSON carries an array or an
/// object in a cell without asking anybody to flatten it, so `rows()` may return
/// a table with nested cells. `README.md` already says what that means — the
/// rectangular ones flow onward into god, the rest are terminal.
///
/// **A non-finite number is written as a STRING, and the reason is the whole
/// architecture.** Bare `NaN` and `Infinity` are not JSON: Python's `json.loads`
/// accepts them by default and R's `jsonlite` refuses, so a bare token would
/// make the two bindings disagree on a document the health verb exists to warn
/// about. Emitting `null` instead would be silent loss of the very thing that
/// was detected. A string is the only form both languages read identically.
pub fn write_json(d: &json::Doc, id: u32, out: &mut String) {
    match d.node(id) {
        json::Node::Null => out.push_str("null"),
        json::Node::Bool(b) => out.push_str(if b { "true" } else { "false" }),
        json::Node::Int(i) => out.push_str(&i.to_string()),
        // The token rather than the value, exactly as it was written. Both
        // languages will lose precision parsing it back and that is their
        // arithmetic, not our transport.
        json::Node::BigInt(s) => out.push_str(d.str_at(s)),
        json::Node::Float(f) => {
            if f.is_nan() {
                out.push_str("\"NaN\"");
            } else if f.is_infinite() {
                out.push_str(if f > 0.0 { "\"Infinity\"" } else { "\"-Infinity\"" });
            } else {
                // `py_float` is the probe's own formatting and keeps the sign on
                // `-0.0`, which survives only in the text.
                out.push_str(&price::py_float(f));
            }
        }
        json::Node::Str(s) => escape(d.str_at(s), out),
        json::Node::Array { .. } => {
            out.push('[');
            for (i, &e) in d.elements(id).iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_json(d, e, out);
            }
            out.push(']');
        }
        json::Node::Object { .. } => {
            out.push('{');
            for (i, m) in d.members(id).iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                escape(d.key(m), out);
                out.push(':');
                write_json(d, m.val, out);
            }
            out.push('}');
        }
    }
}
