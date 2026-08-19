//! A JSON document as a flat arena, and a parser that matches Python's `json`.
//!
//! **Two decisions are load-bearing here and both are recorded in
//! `design/implementation.md`.**
//!
//! **The arena.** Values live in one `Vec<Node>` addressed by index, with the
//! children of every container in one contiguous run and every string in one
//! shared buffer. That is `yyjson`'s design, and it is the whole measured case
//! for this port: the prototype needs 968 MB on `04-gharchive` where
//! `jsonlite::stream_in` needs 427 MB, because it builds a Python object per
//! record. **A core that parses fast and then materialises the same graph
//! inherits the entire problem**, so the representation is the thing being
//! ported, not the speed.
//!
//! **The parser is hand-written**, because the health verb measures three
//! things a conforming parser is entitled to hide:
//!
//!   duplicate keys   valid per RFC 8259 SHOULD, last one silently wins. A
//!                    parser that returns a map has already thrown away the
//!                    evidence that anything was lost.
//!   `-0`             `json.loads("-0")` returns int 0 and the sign is gone.
//!                    It survives only in the token text.
//!   `NaN`/`Infinity` Python's `json` writes them and jsonlite refuses them, so
//!                    a file Python wrote is a file R cannot read. Rejecting
//!                    them at the parser makes that finding unreportable.
//!
//! Matching Python matters more than matching the RFC, because the oracle this
//! port is diffed against is `design/probe.py` and a difference in the parser
//! reads downstream as a difference in the fold.

use std::fmt;

/// 2^53. Past this, anything JavaScript-derived rounds the value.
pub const SAFE_INT: i128 = 9_007_199_254_740_992;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Null,
    Bool,
    Number,
    Text,
    Array,
    Object,
}

impl Kind {
    /// The word the probe prints. `JSON_TYPE` in `design/probe.py`.
    pub fn word(self) -> &'static str {
        match self {
            Kind::Null => "null",
            Kind::Bool => "boolean",
            Kind::Number => "number",
            Kind::Text => "text",
            Kind::Array => "array",
            Kind::Object => "object",
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub enum Node {
    Null,
    Bool(bool),
    /// An integer that fits in `i64`.
    Int(i64),
    /// An integer that does not. **Python's `int` is arbitrary precision**, so
    /// `abs(v) > 2**53` is exact for a two-hundred-digit literal; the token is
    /// kept rather than the value so the comparison stays exact too.
    BigInt(u32),
    Float(f64),
    Str(u32),
    Array { start: u32, len: u32 },
    Object { start: u32, len: u32 },
}

#[derive(Clone, Copy, Debug)]
pub struct Member {
    pub key: u32,
    pub val: u32,
}

/// Damage counted while parsing, because it is only visible here.
#[derive(Clone, Copy, Debug, Default)]
pub struct Tally {
    pub dupes: usize,
    pub negzero: usize,
}

#[derive(Clone, Debug)]
pub struct ParseError {
    pub msg: String,
    pub line: usize,
    pub column: usize,
    pub char: usize,
}

impl fmt::Display for ParseError {
    /// Python's wording, because `main()` prints `str(e)` verbatim for a file
    /// it cannot read and the port is scored on what it SAID.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}: line {} column {} (char {})",
            self.msg, self.line, self.column, self.char
        )
    }
}

#[derive(Default)]
pub struct Doc {
    nodes: Vec<Node>,
    elems: Vec<u32>,
    members: Vec<Member>,
    sbuf: String,
    spans: Vec<(u32, u32)>,
    root: u32,
    pub tally: Tally,
}

impl Doc {
    pub fn new() -> Doc {
        Doc::default()
    }

    // ── reading ──────────────────────────────────────────────────────────────

    pub fn root(&self) -> u32 {
        self.root
    }

    pub fn node(&self, id: u32) -> Node {
        self.nodes[id as usize]
    }

    pub fn kind(&self, id: u32) -> Kind {
        match self.nodes[id as usize] {
            Node::Null => Kind::Null,
            Node::Bool(_) => Kind::Bool,
            Node::Int(_) | Node::BigInt(_) | Node::Float(_) => Kind::Number,
            Node::Str(_) => Kind::Text,
            Node::Array { .. } => Kind::Array,
            Node::Object { .. } => Kind::Object,
        }
    }

    pub fn is_null(&self, id: u32) -> bool {
        matches!(self.nodes[id as usize], Node::Null)
    }

    pub fn str_at(&self, s: u32) -> &str {
        let (a, b) = self.spans[s as usize];
        &self.sbuf[a as usize..b as usize]
    }

    pub fn as_str(&self, id: u32) -> Option<&str> {
        match self.nodes[id as usize] {
            Node::Str(s) => Some(self.str_at(s)),
            _ => None,
        }
    }

    pub fn elements(&self, id: u32) -> &[u32] {
        match self.nodes[id as usize] {
            Node::Array { start, len } => &self.elems[start as usize..(start + len) as usize],
            _ => &[],
        }
    }

    pub fn members(&self, id: u32) -> &[Member] {
        match self.nodes[id as usize] {
            Node::Object { start, len } => &self.members[start as usize..(start + len) as usize],
            _ => &[],
        }
    }

    pub fn key(&self, m: &Member) -> &str {
        self.str_at(m.key)
    }

    /// The value of `field`, or `None` if the key is absent. Absent and present
    /// with a `null` are DIFFERENT and the probe depends on the difference.
    pub fn get(&self, id: u32, field: &str) -> Option<u32> {
        self.members(id)
            .iter()
            .find(|m| self.key(m) == field)
            .map(|m| m.val)
    }

    pub fn len_of(&self, id: u32) -> usize {
        match self.nodes[id as usize] {
            Node::Array { len, .. } | Node::Object { len, .. } => len as usize,
            _ => 0,
        }
    }

    /// Every scalar under `id`, in document order. `_scalars()` in the probe:
    /// object VALUES only, never keys.
    pub fn scalars(&self, id: u32, f: &mut impl FnMut(Node)) {
        match self.nodes[id as usize] {
            Node::Object { start, len } => {
                for i in start..start + len {
                    let v = self.members[i as usize].val;
                    self.scalars(v, f);
                }
            }
            Node::Array { start, len } => {
                for i in start..start + len {
                    let v = self.elems[i as usize];
                    self.scalars(v, f);
                }
            }
            n => f(n),
        }
    }

    // ── writing ──────────────────────────────────────────────────────────────

    fn intern(&mut self, s: &str) -> u32 {
        let a = self.sbuf.len() as u32;
        self.sbuf.push_str(s);
        self.spans.push((a, self.sbuf.len() as u32));
        (self.spans.len() - 1) as u32
    }

    fn push(&mut self, n: Node) -> u32 {
        self.nodes.push(n);
        (self.nodes.len() - 1) as u32
    }

    /// Wrap already-parsed values in one array and make it the root. NDJSON is
    /// a list of records to everything downstream, exactly as it is in Python.
    pub fn root_array(&mut self, ids: &[u32]) {
        let start = self.elems.len() as u32;
        self.elems.extend_from_slice(ids);
        self.root = self.push(Node::Array {
            start,
            len: ids.len() as u32,
        });
    }

    pub fn set_root(&mut self, id: u32) {
        self.root = id;
    }

    /// Parse `text` as one complete JSON value, trailing whitespace allowed.
    pub fn parse_into(&mut self, text: &str) -> Result<u32, ParseError> {
        let mut p = Parser {
            b: text.as_bytes(),
            i: 0,
            depth: 0,
            scratch: Vec::new(),
            keys: Vec::new(),
            keep: Vec::new(),
        };
        let id = p.value(self)?;
        p.ws();
        if p.i < p.b.len() {
            return Err(p.err_at("Extra data", p.i));
        }
        Ok(id)
    }

    /// Parse a whole document. The common case.
    pub fn parse(text: &str) -> Result<Doc, ParseError> {
        let mut d = Doc::new();
        let id = d.parse_into(text)?;
        d.set_root(id);
        Ok(d)
    }

    /// Does `text` parse at all? `_parses()` in the probe — used to decide
    /// whether a file is NDJSON, where the values are thrown away.
    pub fn parses(text: &str) -> bool {
        let mut d = Doc::new();
        d.parse_into(text).is_ok()
    }
}

struct Parser<'a> {
    b: &'a [u8],
    i: usize,
    depth: u32,
    scratch: Vec<u32>,
    keys: Vec<u32>,
    keep: Vec<Member>,
}

/// Nesting past this is refused rather than allowed to overflow the stack.
/// Python raises `RecursionError` at a comparable point; no corpus document is
/// within two orders of magnitude of it.
const MAX_DEPTH: u32 = 2000;

impl<'a> Parser<'a> {
    fn ws(&mut self) {
        // Python's json treats exactly these four as whitespace.
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\t' | b'\n' | b'\r') {
            self.i += 1;
        }
    }

    fn err_at(&self, msg: &str, at: usize) -> ParseError {
        let mut line = 1usize;
        let mut col = 1usize;
        let mut chars = 0usize;
        let text = std::str::from_utf8(&self.b[..at.min(self.b.len())]).unwrap_or("");
        for c in text.chars() {
            chars += 1;
            if c == '\n' {
                line += 1;
                col = 1;
            } else {
                col += 1;
            }
        }
        ParseError {
            msg: msg.to_string(),
            line,
            column: col,
            char: chars,
        }
    }

    fn value(&mut self, d: &mut Doc) -> Result<u32, ParseError> {
        self.ws();
        if self.i >= self.b.len() {
            return Err(self.err_at("Expecting value", self.i));
        }
        let start = self.i;
        let rest = &self.b[self.i..];
        match self.b[self.i] {
            b'{' => self.object(d),
            b'[' => self.array(d),
            b'"' => {
                let s = self.string(d)?;
                Ok(d.push(Node::Str(s)))
            }
            b't' if rest.starts_with(b"true") => {
                self.i += 4;
                Ok(d.push(Node::Bool(true)))
            }
            b'f' if rest.starts_with(b"false") => {
                self.i += 5;
                Ok(d.push(Node::Bool(false)))
            }
            b'n' if rest.starts_with(b"null") => {
                self.i += 4;
                Ok(d.push(Node::Null))
            }
            // **Python's `json` accepts these three bare and that is the point.**
            // `json.dumps` emits them, jsonlite refuses them, and the health
            // verb exists to say so.
            b'N' if rest.starts_with(b"NaN") => {
                self.i += 3;
                Ok(d.push(Node::Float(f64::NAN)))
            }
            b'I' if rest.starts_with(b"Infinity") => {
                self.i += 8;
                Ok(d.push(Node::Float(f64::INFINITY)))
            }
            b'-' if rest.starts_with(b"-Infinity") => {
                self.i += 9;
                Ok(d.push(Node::Float(f64::NEG_INFINITY)))
            }
            b'-' | b'0'..=b'9' => self.number(d),
            _ => Err(self.err_at("Expecting value", start)),
        }
    }

    fn number(&mut self, d: &mut Doc) -> Result<u32, ParseError> {
        let start = self.i;
        if self.i < self.b.len() && self.b[self.i] == b'-' {
            self.i += 1;
        }
        // Python's NUMBER_RE: no leading zeros, so `01` is `0` then a syntax
        // error at `1`, never the integer one.
        let int_start = self.i;
        if self.i < self.b.len() && self.b[self.i] == b'0' {
            self.i += 1;
        } else {
            while self.i < self.b.len() && self.b[self.i].is_ascii_digit() {
                self.i += 1;
            }
        }
        if self.i == int_start {
            return Err(self.err_at("Expecting value", start));
        }
        let mut is_float = false;
        // A `.` with no digit after it is NOT part of the number. Python's
        // regex leaves it, so `[1.]` fails on the delimiter rather than here.
        if self.i + 1 < self.b.len() && self.b[self.i] == b'.' && self.b[self.i + 1].is_ascii_digit()
        {
            is_float = true;
            self.i += 1;
            while self.i < self.b.len() && self.b[self.i].is_ascii_digit() {
                self.i += 1;
            }
        }
        if self.i < self.b.len() && (self.b[self.i] | 0x20) == b'e' {
            let save = self.i;
            let mut j = self.i + 1;
            if j < self.b.len() && (self.b[j] == b'+' || self.b[j] == b'-') {
                j += 1;
            }
            if j < self.b.len() && self.b[j].is_ascii_digit() {
                while j < self.b.len() && self.b[j].is_ascii_digit() {
                    j += 1;
                }
                self.i = j;
                is_float = true;
            } else {
                self.i = save;
            }
        }
        let tok = std::str::from_utf8(&self.b[start..self.i]).unwrap();

        // NEGATIVE ZERO. `json.loads("-0")` returns int 0 and the sign is gone,
        // so the probe hooks the token text. The test is on the PARSED value
        // being zero and the TOKEN starting with a minus, which is why
        // `-1e-400` — a float that underflows to -0.0 — is flagged too.
        let node = if is_float {
            let v: f64 = tok.parse().unwrap_or(f64::NAN);
            if v == 0.0 {
                d.tally.negzero += tok.starts_with('-') as usize;
            }
            Node::Float(v)
        } else {
            match tok.parse::<i64>() {
                Ok(v) => {
                    if v == 0 {
                        d.tally.negzero += tok.starts_with('-') as usize;
                    }
                    Node::Int(v)
                }
                // Past i64 is past 2^53 by three orders of magnitude, so the
                // token is kept and the comparison stays exact.
                Err(_) => {
                    let s = d.intern(tok);
                    Node::BigInt(s)
                }
            }
        };
        Ok(d.push(node))
    }

    fn string(&mut self, d: &mut Doc) -> Result<u32, ParseError> {
        let open = self.i;
        self.i += 1;
        let from = self.i;
        // Fast path: no escape and no control character means the bytes are
        // already the value, so nothing is copied twice.
        while self.i < self.b.len() {
            match self.b[self.i] {
                b'"' => {
                    let raw = std::str::from_utf8(&self.b[from..self.i]).unwrap();
                    self.i += 1;
                    return Ok(d.intern(raw));
                }
                b'\\' => break,
                c if c < 0x20 => {
                    return Err(self.err_at("Invalid control character at", self.i));
                }
                _ => self.i += 1,
            }
        }
        if self.i >= self.b.len() {
            return Err(self.err_at("Unterminated string starting at", open));
        }
        let mut out = String::from(std::str::from_utf8(&self.b[from..self.i]).unwrap());
        while self.i < self.b.len() {
            match self.b[self.i] {
                b'"' => {
                    self.i += 1;
                    return Ok(d.intern(&out));
                }
                c if c < 0x20 => {
                    return Err(self.err_at("Invalid control character at", self.i));
                }
                b'\\' => {
                    self.i += 1;
                    if self.i >= self.b.len() {
                        return Err(self.err_at("Unterminated string starting at", open));
                    }
                    let e = self.b[self.i];
                    self.i += 1;
                    match e {
                        b'"' => out.push('"'),
                        b'\\' => out.push('\\'),
                        b'/' => out.push('/'),
                        b'b' => out.push('\u{8}'),
                        b'f' => out.push('\u{c}'),
                        b'n' => out.push('\n'),
                        b'r' => out.push('\r'),
                        b't' => out.push('\t'),
                        b'u' => {
                            // **CPython's rule, measured rather than read off
                            // its source, and the two disagree.** It wants
                            // FIVE characters after the `u`, not four, so a
                            // document that stops exactly after the four hex
                            // digits says `Invalid \uXXXX escape` where the
                            // obvious reading says `Unterminated string`. Five
                            // of the truncation ladder's cases land on exactly
                            // that byte. The oracle is CPython, so this is
                            // CPython's rule and not the defensible one.
                            let upos = self.i - 1;
                            if self.i + 4 >= self.b.len() {
                                return Err(self.err_at("Invalid \\uXXXX escape", upos));
                            }
                            let hi = self.hex4(upos)?;
                            let ch = if (0xD800..0xDC00).contains(&hi) {
                                // A surrogate PAIR is one character.
                                if self.b[self.i..].starts_with(b"\\u") {
                                    let save = self.i;
                                    self.i += 2;
                                    let lo = self.hex4(save + 1)?;
                                    if (0xDC00..0xE000).contains(&lo) {
                                        let c = 0x10000
                                            + ((hi - 0xD800) << 10)
                                            + (lo - 0xDC00);
                                        char::from_u32(c).unwrap_or('\u{fffd}')
                                    } else {
                                        // Not a low surrogate: rewind and let
                                        // the next escape be read normally.
                                        self.i = save;
                                        '\u{fffd}'
                                    }
                                } else {
                                    '\u{fffd}'
                                }
                            } else {
                                // **A lone surrogate is the one place this
                                // cannot match Python.** Python strings hold
                                // one; Rust's cannot, so it becomes U+FFFD.
                                // Recorded as a known divergence rather than
                                // hidden: it changes string CONTENT only, and
                                // no health flag reads string content except
                                // `encoded`, which needs a leading brace.
                                char::from_u32(hi).unwrap_or('\u{fffd}')
                            };
                            out.push(ch);
                        }
                        _ => {
                            return Err(self.err_at("Invalid \\escape", self.i - 2));
                        }
                    }
                }
                _ => {
                    let s = self.i;
                    while self.i < self.b.len()
                        && self.b[self.i] != b'"'
                        && self.b[self.i] != b'\\'
                        && self.b[self.i] >= 0x20
                    {
                        self.i += 1;
                    }
                    out.push_str(std::str::from_utf8(&self.b[s..self.i]).unwrap());
                }
            }
        }
        Err(self.err_at("Unterminated string starting at", open))
    }

    /// `at` is where the failure is REPORTED — the `u`, not the digits, which
    /// is where CPython points.
    fn hex4(&mut self, at: usize) -> Result<u32, ParseError> {
        if self.i + 4 > self.b.len() {
            return Err(self.err_at("Invalid \\uXXXX escape", at));
        }
        let s = std::str::from_utf8(&self.b[self.i..self.i + 4])
            .map_err(|_| self.err_at("Invalid \\uXXXX escape", at))?;
        let v = u32::from_str_radix(s, 16)
            .map_err(|_| self.err_at("Invalid \\uXXXX escape", at))?;
        self.i += 4;
        Ok(v)
    }

    fn array(&mut self, d: &mut Doc) -> Result<u32, ParseError> {
        self.depth += 1;
        if self.depth > MAX_DEPTH {
            return Err(self.err_at("Nesting too deep", self.i));
        }
        self.i += 1;
        let mark = self.scratch.len();
        self.ws();
        if self.i < self.b.len() && self.b[self.i] == b']' {
            self.i += 1;
            self.depth -= 1;
            let start = d.elems.len() as u32;
            return Ok(d.push(Node::Array { start, len: 0 }));
        }
        loop {
            let v = self.value(d)?;
            self.scratch.push(v);
            self.ws();
            if self.i >= self.b.len() {
                return Err(self.err_at("Expecting ',' delimiter", self.i));
            }
            match self.b[self.i] {
                b',' => {
                    self.i += 1;
                }
                b']' => {
                    self.i += 1;
                    break;
                }
                _ => return Err(self.err_at("Expecting ',' delimiter", self.i)),
            }
        }
        // `self` and `d` are distinct, so the children move straight across
        // with no intermediate allocation.
        let start = d.elems.len() as u32;
        let len = (self.scratch.len() - mark) as u32;
        d.elems.extend_from_slice(&self.scratch[mark..]);
        self.scratch.truncate(mark);
        self.depth -= 1;
        Ok(d.push(Node::Array { start, len }))
    }

    fn object(&mut self, d: &mut Doc) -> Result<u32, ParseError> {
        self.depth += 1;
        if self.depth > MAX_DEPTH {
            return Err(self.err_at("Nesting too deep", self.i));
        }
        self.i += 1;
        let mark = self.scratch.len();
        let kmark = self.keys.len();
        self.ws();
        if self.i < self.b.len() && self.b[self.i] == b'}' {
            self.i += 1;
            self.depth -= 1;
            let start = d.members.len() as u32;
            return Ok(d.push(Node::Object { start, len: 0 }));
        }
        loop {
            self.ws();
            if self.i >= self.b.len() || self.b[self.i] != b'"' {
                return Err(self.err_at("Expecting property name enclosed in double quotes", self.i));
            }
            let k = self.string(d)?;
            self.ws();
            if self.i >= self.b.len() || self.b[self.i] != b':' {
                return Err(self.err_at("Expecting ':' delimiter", self.i));
            }
            self.i += 1;
            let v = self.value(d)?;
            self.keys.push(k);
            self.scratch.push(v);
            self.ws();
            if self.i >= self.b.len() {
                return Err(self.err_at("Expecting ',' delimiter", self.i));
            }
            match self.b[self.i] {
                b',' => {
                    self.i += 1;
                }
                b'}' => {
                    self.i += 1;
                    break;
                }
                _ => return Err(self.err_at("Expecting ',' delimiter", self.i)),
            }
        }

        // **`dict(pairs)`, exactly.** A repeated key keeps its FIRST position
        // and its LAST value — that is what Python builds, and key order is
        // load-bearing downstream, so getting it merely nearly right would show
        // up as a reordered fold rather than as a parser bug. One duplicate is
        // counted per repeat OCCURRENCE, which is what the probe's hook appends.
        //
        // Decided in one immutable pass so `d` is free to be written after it.
        // The linear scan is not laziness: almost every object is small, and a
        // hash per object would cost more than it saves. `13-package-lock`
        // keys 1,657 packages by path in a single object, which is what the
        // second branch is for.
        let n = self.scratch.len() - mark;
        self.keep.clear();
        let mut dupes = 0usize;
        if n <= 12 {
            'pair: for a in 0..n {
                let key = self.keys[kmark + a];
                let name = d.str_at(key);
                for k in self.keep.iter_mut() {
                    if d.str_at(k.key) == name {
                        k.val = self.scratch[mark + a];
                        dupes += 1;
                        continue 'pair;
                    }
                }
                self.keep.push(Member {
                    key,
                    val: self.scratch[mark + a],
                });
            }
        } else {
            let mut seen: std::collections::HashMap<&str, usize> =
                std::collections::HashMap::with_capacity(n);
            for a in 0..n {
                let key = self.keys[kmark + a];
                let name = d.str_at(key);
                match seen.entry(name) {
                    std::collections::hash_map::Entry::Occupied(e) => {
                        self.keep[*e.get()].val = self.scratch[mark + a];
                        dupes += 1;
                    }
                    std::collections::hash_map::Entry::Vacant(e) => {
                        e.insert(self.keep.len());
                        self.keep.push(Member {
                            key,
                            val: self.scratch[mark + a],
                        });
                    }
                }
            }
        }

        d.tally.dupes += dupes;
        let start = d.members.len() as u32;
        let len = self.keep.len() as u32;
        d.members.extend_from_slice(&self.keep);
        self.scratch.truncate(mark);
        self.keys.truncate(kmark);
        self.depth -= 1;
        Ok(d.push(Node::Object { start, len }))
    }
}
