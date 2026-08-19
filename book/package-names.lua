-- A package name is set in code font, in every chapter and every part.
--
-- The source writes these names as plain words. The rule about *spelling* — the
-- name is the name, in one case — is separate from this one, which is about
-- *type*. Nothing in a `.qmd` changes, so a writer keeps typing `purrr` and the
-- filter decides how it is set.
--
-- **Why a filter, and not backticks everywhere.** Marking them by hand puts the
-- convention in the hands of whoever writes the next sentence, which is how
-- every convention drifts: by chapter, because a writer holds one file in their
-- head for an afternoon. A filter cannot drift, a part introduction cannot be
-- missed, and a chapter written a year from now is covered without anyone
-- remembering that this rule exists.
--
-- `Code` is the one form both formats already agree about: `<code>` in HTML and
-- `\texttt{}` in a PDF. This book renders HTML only today; the filter is
-- written so that adding PDF later needs no second definition of the rule.
--
-- Adapted from gog's `package-names.lua`, unchanged in mechanism. **The one
-- thing that is genuinely different is `fathom` itself, and it is a
-- consequence of the name being good** — see the exemptions at the foot.

-- Libraries, not applications. Quarto, RStudio and Excel are programs a reader
-- runs, and setting `Quarto` in code font would read as something to type. The
-- line this list draws is one question: could a sentence hand it to
-- `library()`, `import`, `Cargo.toml` or `#include`? Then it is code.
--
-- The thirteen tools in the comparison, the three siblings, and the libraries
-- the architecture chapter weighs. Longest first, so a name can never match
-- inside a longer one — which is what keeps `jq` out of `jqr` and `god` out of
-- nothing at all, since no name here contains another except those two.
local NAMES = {
  "miniz_oxide", "serde_json", "simd-json", "jmespath", "nbformat",
  "tidyjson", "jsonlite", "rrapply", "msgspec", "DuckDB", "fathom",
  "polars", "pandas", "pydash", "orjson", "yyjson", "genson", "flate2",
  "purrr", "tidyr", "ijson", "knitr", "ujson", "glom", "jqr", "gog",
  "god", "jq",
}

-- What the boundary test is protecting, all of it real text in this book:
-- `fathom-core` and `fathom-cli`, which are crate names; `design/fathom.R`,
-- which is a path; `FATHOM`, which would survive on case alone; and the `/god`
-- that ends a repository path. A name may still be followed by ordinary
-- punctuation, so `purrr.` at the end of a sentence and `pandas's` both match,
-- while `fathom.R` does not.
--
-- The classes are written out as ASCII ranges rather than as `%w`, and that is
-- not style. Lua matches bytes, and pandoc has already turned `'` into a curly
-- quote by the time a filter sees it, so `pandas's` ends in the first byte of a
-- three-byte character. Under `%w` that byte reads as a letter and the name
-- goes unmarked, which is the sort of thing that shows up as one plain word in
-- a chapter nobody rereads.
local function boundary_ok(s, i, j)
  local before = i > 1 and s:sub(i - 1, i - 1) or ""
  local after = s:sub(j + 1, j + 1)
  if before ~= "" and before:match("[A-Za-z0-9_/%-%.]") then return false end
  if after ~= "" and after:match("[A-Za-z0-9_/%-]") then return false end
  if after == "." and s:sub(j + 2, j + 2):match("[A-Za-z0-9]") then return false end
  return true
end

-- Pandoc splits text on whitespace, so one `Str` is `purrr,` or `(polars)` or
-- `pandas's`. Each one is walked character by character and rebuilt as a run of
-- inlines, which is the only way to reach a name with punctuation stuck to it.
local function split(s)
  local out, buf, i, hit_any = {}, {}, 1, false
  while i <= #s do
    local hit = nil
    for _, name in ipairs(NAMES) do
      local j = i + #name - 1
      if s:sub(i, j) == name and boundary_ok(s, i, j) then
        hit = name
        break
      end
    end
    if hit then
      if #buf > 0 then
        out[#out + 1] = pandoc.Str(table.concat(buf))
        buf = {}
      end
      out[#out + 1] = pandoc.Code(hit)
      hit_any = true
      i = i + #hit
    else
      buf[#buf + 1] = s:sub(i, i)
      i = i + 1
    end
  end
  if #buf > 0 then out[#out + 1] = pandoc.Str(table.concat(buf)) end
  if not hit_any then return nil end
  return out
end

local inner = {
    -- Top-down, because the exemptions have to be refused *before* their
    -- children are reached. Bottom-up would rewrite the text first and hand
    -- back an element that had already lost.
    traverse = "topdown",

    -- **`fathom` is an ordinary English verb, and that is the whole problem.**
    --
    -- gog could put `gog` in the list unguarded because it is a nonsense
    -- syllable; god could put `god` in because the deity is capitalised and
    -- this filter matches bytes. Neither escape is open here. *To fathom*
    -- something is to measure how deep it goes, and `README.md` says the name
    -- was chosen for precisely that: "it is plain everyday English, and the
    -- understanding sense is a dead metaphor rather than a live one."
    --
    -- **So the property that made the name good is the property that stops a
    -- filter from marking it**, and the exception cannot be automated: no rule
    -- available here separates the verb from the package.
    --
    -- Measured rather than assumed before taking this route: of 24 lowercase
    -- occurrences across the book, **exactly one** is the verb. So the burden
    -- on a writer is one span in one sentence, which is the same size as gog's
    -- `agog`, and marking the rare inverse case by hand is what a filter is
    -- for — it removes the common case, not every case.
    --
    -- Write it `[fathom]{.word}` when you mean the English verb.
    Span = function(el)
      if el.classes:includes("word") then return el, false end
    end,

    -- The motto is copy, not a package reference. It survives on case today —
    -- "Fathom first. Then parse." — and is exempted anyway, so that rewording
    -- it in lower case later cannot quietly set half a slogan in code font.
    Div = function(el)
      if el.classes:includes("fathom-slogan") then return el, false end
    end,

    -- Already code. A chunk's source and its output never reach a `Str` filter
    -- at all, so this is only for inline spans a writer marked by hand.
    Code = function(el) return el, false end,

    Str = function(el)
      local out = split(el.text)
      if out == nil then return nil end
      -- `false` stops the walk from re-entering what was just built.
      return out, false
    end,
}

-- **The body only, and metadata deliberately left alone.**
--
-- A Lua filter walks the whole `Pandoc` document, and that includes `meta`. The
-- first version of this file did, and set the book's own title as
-- `fathom`: Probing JSON in the landing page's `<h1>` — in code font in the
-- heading, and in plain type three inches away in the sidebar, which renders
-- the same string from a different template slot. **A title is the name of a
-- work, not a symbol you type.**
--
-- Walking `doc.blocks` rather than `doc` is the whole fix, and it covers each
-- chapter's front-matter `title:` for the same reason.
--
-- An earlier draft also exempted `Header`, on the guess that chapter titles
-- carried names. Measured: **no heading in the book contains one**, and the
-- titles that do are metadata, which this now excludes anyway. The rule was
-- fitted to nothing and is gone — a guard that never fires is a guard nobody
-- can tell is broken.
return {
  {
    Pandoc = function(doc)
      doc.blocks = doc.blocks:walk(inner)
      return doc
    end,
  },
}
