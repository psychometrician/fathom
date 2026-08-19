//! An insertion-ordered map, because the probe's output depends on one.
//!
//! **This is not a convenience and a `HashMap` would be a silent bug.** Python
//! dicts and `collections.Counter` preserve insertion order, `sorted()` and
//! `list.sort()` are stable, and `design/probe.py` leans on the combination in
//! at least four places where the port would otherwise reorder its output:
//!
//!   `Counter.most_common()`   ties print in first-seen order, so the
//!                             polymorphism report's `text x512, object x1,210`
//!                             is an ordering as well as a count.
//!   `shown.sort(key=…)`       record shapes are sorted by copies, and shapes
//!                             with equal copies fall back to walk order.
//!   `sorted(groups.items(),   a split's kinds are ordered by size, and
//!    key=lambda kv: -len(…))` equal-sized kinds by the order rows arrived.
//!   `sorted(keyset, key=len)` `fold_recursion` canonicalises shortest-first
//!                             and breaks length ties on walk order.
//!
//! None of those would fail a test that checked the FINDINGS. They would move
//! lines around in a report whose byte-for-byte agreement with the probe is the
//! port's entire criterion, and the diff would read as a bug in the fold.
//!
//! `indexmap` does this and is not taken, for the reason in `Cargo.toml`: the
//! crate carries one dependency and the bar for a second is that the standard
//! library cannot express the thing. Sixty lines say it can.

use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct OrderMap<V> {
    keys: Vec<String>,
    vals: Vec<V>,
    index: HashMap<String, usize>,
}

impl<V> Default for OrderMap<V> {
    fn default() -> Self {
        OrderMap {
            keys: Vec::new(),
            vals: Vec::new(),
            index: HashMap::new(),
        }
    }
}

impl<V> OrderMap<V> {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn len(&self) -> usize {
        self.keys.len()
    }

    pub fn is_empty(&self) -> bool {
        self.keys.is_empty()
    }

    pub fn contains_key(&self, k: &str) -> bool {
        self.index.contains_key(k)
    }

    pub fn get(&self, k: &str) -> Option<&V> {
        self.index.get(k).map(|&i| &self.vals[i])
    }

    pub fn get_mut(&mut self, k: &str) -> Option<&mut V> {
        match self.index.get(k) {
            Some(&i) => Some(&mut self.vals[i]),
            None => None,
        }
    }

    pub fn insert(&mut self, k: &str, v: V) {
        match self.index.get(k) {
            Some(&i) => self.vals[i] = v,
            None => {
                self.index.insert(k.to_string(), self.keys.len());
                self.keys.push(k.to_string());
                self.vals.push(v);
            }
        }
    }

    /// `defaultdict`: fetch, creating in place at the end if absent.
    pub fn entry(&mut self, k: &str) -> &mut V
    where
        V: Default,
    {
        let i = match self.index.get(k) {
            Some(&i) => i,
            None => {
                let i = self.keys.len();
                self.index.insert(k.to_string(), i);
                self.keys.push(k.to_string());
                self.vals.push(V::default());
                i
            }
        };
        &mut self.vals[i]
    }

    pub fn iter(&self) -> impl Iterator<Item = (&str, &V)> {
        self.keys.iter().map(|k| k.as_str()).zip(self.vals.iter())
    }

    pub fn keys(&self) -> impl Iterator<Item = &str> {
        self.keys.iter().map(|k| k.as_str())
    }

    pub fn values(&self) -> impl Iterator<Item = &V> {
        self.vals.iter()
    }

    /// Keys in insertion order, which is what a stable sort falls back to.
    pub fn key_vec(&self) -> Vec<&str> {
        self.keys.iter().map(|k| k.as_str()).collect()
    }
}

/// `collections.Counter` over strings, with the same ordering guarantee.
pub type Tally = OrderMap<usize>;

impl OrderMap<usize> {
    pub fn add(&mut self, k: &str, n: usize) {
        *self.entry(k) += n;
    }

    pub fn bump(&mut self, k: &str) {
        *self.entry(k) += 1;
    }

    pub fn total(&self) -> usize {
        self.vals.iter().sum()
    }

    /// `Counter.most_common()` — by count descending, ties in first-seen order,
    /// which a stable sort gives for free.
    pub fn most_common(&self) -> Vec<(&str, usize)> {
        let mut v: Vec<(&str, usize)> = self
            .keys
            .iter()
            .map(|k| k.as_str())
            .zip(self.vals.iter().copied())
            .collect();
        v.sort_by_key(|&(_, n)| std::cmp::Reverse(n));
        v
    }

    /// The largest count alone. `most_common(1)[0][1]`.
    pub fn top(&self) -> usize {
        self.vals.iter().copied().max().unwrap_or(0)
    }
}
