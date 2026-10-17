//! mdbook preprocessor: links to what the book leaves out point at the
//! repository at the built revision.
//!
//! The book's source is assembled from docs/ by contrib/book.py, with the
//! repository's README as its introduction and docs/index.md as contents.md.
//! Links to pages of docs/ the book does not hold, and to anything outside
//! docs/, become URLs under `preprocessor.relink.blob`; the others become
//! relative to the chapter's place in the book.

use std::collections::HashSet;
use std::ops::Range;
use std::path::Path;

use anyhow::{Context, Result, bail};
use mdbook_markdown::pulldown_cmark::{Event, LinkType, Tag, TagEnd};
use mdbook_markdown::{MarkdownOptions, new_cmark_parser};
use pathdiff::diff_paths;
use percent_encoding::percent_decode_str;

const DOCS: &str = "docs";
const CONTENTS: &str = "contents.md";
const INTRODUCTION: &str = "README.md";

fn main() -> Result<()> {
    match std::env::args().nth(1).as_deref() {
        Some("supports") => return Ok(()),
        Some(arg) => bail!("unknown argument {arg:?}"),
        None => {}
    }
    let (ctx, mut book) = mdbook_preprocessor::parse_input(std::io::stdin())?;
    let blob: String = ctx
        .config
        .get("preprocessor.relink.blob")?
        .context("preprocessor.relink.blob is not set")?;
    let html = ctx.config.html_config().unwrap_or_default();
    let mut options = MarkdownOptions::default();
    options.smart_punctuation = html.smart_punctuation;
    options.definition_lists = html.definition_lists;
    options.admonitions = html.admonitions;
    let chapters: HashSet<String> = book
        .chapters()
        .filter_map(|c| c.source_path.as_deref())
        .map(posix)
        .filter(|p| p != INTRODUCTION && p != CONTENTS)
        .collect();
    let docs = ctx.root.join(DOCS);
    let mut left_out = HashSet::new();
    pages(&docs, &docs, &mut left_out)?;
    left_out.retain(|p| !chapters.contains(p));
    book.for_each_chapter_mut(|chapter| {
        let Some(source) = chapter.source_path.as_deref().map(posix) else {
            return;
        };
        let base = match source.as_str() {
            INTRODUCTION => ".".to_string(),
            CONTENTS => DOCS.to_string(),
            page => posix(
                Path::new(DOCS)
                    .join(page)
                    .parent()
                    .expect("a page path has a directory"),
            ),
        };
        chapter.content = relink(&chapter.content, &options, &base, &blob, &left_out);
    });
    serde_json::to_writer(std::io::stdout(), &book)?;
    Ok(())
}

fn posix(path: &Path) -> String {
    path.to_string_lossy().into_owned()
}

/// The pages under `dir`, as paths relative to `root`.
fn pages(root: &Path, dir: &Path, out: &mut HashSet<String>) -> Result<()> {
    for entry in std::fs::read_dir(dir).with_context(|| format!("reading {}", dir.display()))? {
        let path = entry?.path();
        if path.is_dir() {
            pages(root, &path, out)?;
        } else if path.extension().is_some_and(|e| e == "md") {
            out.insert(posix(path.strip_prefix(root)?));
        }
    }
    Ok(())
}

/// Links of a file in directory `base` of the repository, rewritten for a
/// book whose source is docs/: targets in docs/ but not among `left_out`
/// become relative to the file's place in the book, and every other target
/// a URL under `blob`.
fn relink(
    text: &str,
    options: &MarkdownOptions,
    base: &str,
    blob: &str,
    left_out: &HashSet<String>,
) -> String {
    let here = if base == "." { DOCS } else { base };
    let mut out = String::with_capacity(text.len());
    let mut last = 0;
    for range in destinations(text, options) {
        out.push_str(&text[last..range.start]);
        out.push_str(&retarget(&text[range.clone()], base, here, blob, left_out));
        last = range.end;
    }
    out.push_str(&text[last..]);
    out
}

fn retarget(url: &str, base: &str, here: &str, blob: &str, left_out: &HashSet<String>) -> String {
    if !is_path(url) {
        return url.to_string();
    }
    let (path, frag) = url.split_at(url.find('#').unwrap_or(url.len()));
    let mut target = resolve(base, path);
    if target == format!("{DOCS}/index.md") {
        target = format!("{DOCS}/{CONTENTS}");
    } else if !target.starts_with(&format!("{DOCS}/"))
        || left_out.contains(&decode(&target[DOCS.len() + 1..]))
    {
        return format!("{blob}/{target}{frag}");
    }
    let relative = diff_paths(&target, here).expect("the chapter's directory has no `..`");
    format!("{}{frag}", posix(&relative))
}

/// The byte ranges of the destinations, as written, of the inline links,
/// images and link reference definitions mdbook finds in `text`.
fn destinations(text: &str, options: &MarkdownOptions) -> Vec<Range<usize>> {
    let parser = new_cmark_parser(text, options);
    let mut found: Vec<_> = parser
        .reference_definitions()
        .iter()
        .map(|(_, def)| {
            let open = def.span.start
                + text[def.span.start..]
                    .find('[')
                    .expect("a definition opens with its label");
            destination(text, label_end(text, open) + 1)
        })
        .collect();
    // The link or image being read: whether it is inline, and where the
    // last event inside it ends, after which its text closes with `](`.
    let mut open: Vec<(bool, usize)> = Vec::new();
    for (event, range) in parser.into_offset_iter() {
        match event {
            Event::Start(Tag::Link { link_type, .. } | Tag::Image { link_type, .. }) => {
                open.push((link_type == LinkType::Inline, range.start));
                continue;
            }
            Event::End(TagEnd::Link | TagEnd::Image) => {
                let (inline, inner) = open.pop().expect("a link ends after it starts");
                if inline {
                    let close = inner
                        + text[inner..]
                            .find("](")
                            .expect("an inline link's text closes with `](`");
                    found.push(destination(text, close + 2));
                }
            }
            _ => {}
        }
        if let Some((_, inner)) = open.last_mut() {
            *inner = (*inner).max(range.end);
        }
    }
    found.sort_by_key(|r| r.start);
    found
}

/// Where the label opened at `open` closes.
fn label_end(text: &str, open: usize) -> usize {
    let b = text.as_bytes();
    let mut i = open + 1;
    while b[i] != b']' {
        i += if b[i] == b'\\' { 2 } else { 1 };
    }
    i + 1
}

/// The destination after `i`, past spaces and tabs with at most one line
/// ending, after which a block quote repeats its markers.
fn destination(text: &str, mut i: usize) -> Range<usize> {
    let b = text.as_bytes();
    let at = |i: usize| b.get(i).copied().unwrap_or(0);
    while matches!(at(i), b' ' | b'\t') {
        i += 1;
    }
    if at(i) == b'\r' {
        i += 1;
    }
    if at(i) == b'\n' {
        i += 1;
        while matches!(at(i), b' ' | b'\t' | b'>') {
            i += 1;
        }
    }
    if at(i) == b'<' {
        let start = i + 1;
        let mut j = start;
        while !matches!(at(j), b'>' | 0) {
            j += if at(j) == b'\\' { 2 } else { 1 };
        }
        return start..j;
    }
    let start = i;
    let mut depth = 0;
    loop {
        match at(i) {
            b'\\' if at(i + 1).is_ascii_punctuation() => i += 1,
            b'(' => depth += 1,
            b')' if depth == 0 => break,
            b')' => depth -= 1,
            c if c <= b' ' => break,
            _ => {}
        }
        i += 1;
    }
    start..i
}

/// Whether `url` names a path, rather than a fragment, a network path or
/// a URL with a scheme.
fn is_path(url: &str) -> bool {
    if url.is_empty() || url.starts_with('#') || url.starts_with("//") {
        return false;
    }
    let Some((scheme, _)) = url.split_once(':') else {
        return true;
    };
    let mut chars = scheme.chars();
    !(chars.next().is_some_and(|c| c.is_ascii_alphabetic())
        && chars.all(|c| c.is_ascii_alphanumeric() || "+.-".contains(c)))
}

/// The repository path of link target `path` of a file in directory
/// `base`. In docs/, a path from `/` starts at the bundle root.
fn resolve(base: &str, path: &str) -> String {
    let base = match path.strip_prefix('/') {
        Some(_) if base == "." => ".",
        Some(_) => DOCS,
        None => base,
    };
    normpath(&format!("{base}/{}", path.trim_start_matches('/')))
}

/// `path` as the file name it stands for, its escapes and percent-encoding
/// undone.
fn decode(path: &str) -> String {
    let mut unescaped = String::with_capacity(path.len());
    let mut chars = path.chars().peekable();
    while let Some(c) = chars.next() {
        match chars.peek() {
            Some(&next) if c == '\\' && next.is_ascii_punctuation() => {}
            _ => unescaped.push(c),
        }
    }
    percent_decode_str(&unescaped)
        .decode_utf8_lossy()
        .into_owned()
}

fn normpath(path: &str) -> String {
    let mut parts: Vec<&str> = Vec::new();
    for part in path.split('/') {
        match part {
            "" | "." => {}
            ".." if parts.last().is_some_and(|p| *p != "..") => {
                parts.pop();
            }
            part => parts.push(part),
        }
    }
    if parts.is_empty() {
        ".".to_string()
    } else {
        parts.join("/")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const BLOB: &str = "https://example.org/blob/abc";
    const LEFT_OUT: [&str; 7] = [
        "README.md",
        "log.md",
        "sub/index.md",
        "draft_(old).md",
        "a_((b)).md",
        "a).md",
        "a>b.md",
    ];

    fn relinked(text: &str, base: &str) -> String {
        let left_out = LEFT_OUT.iter().map(|s| s.to_string()).collect();
        relink(text, &MarkdownOptions::default(), base, BLOB, &left_out)
    }

    fn blob(text: &str) -> String {
        text.replace("../README.md", &format!("{BLOB}/README.md"))
    }

    #[test]
    fn links_leave_the_book_only_for_the_repository() {
        for (base, link, expected) in [
            (".", "docs/one.md#a", "one.md#a"),
            (".", "docs/index.md", "contents.md"),
            (".", "flake.nix", &format!("{BLOB}/flake.nix")),
            ("docs", "sub/two.md", "sub/two.md"),
            ("docs", "../README.md", &format!("{BLOB}/README.md")),
            ("docs/sub", "../one.md", "../one.md"),
            ("docs/sub", "../index.md", "../contents.md"),
            (
                "docs/sub",
                "../../nix/site.nix",
                &format!("{BLOB}/nix/site.nix"),
            ),
            (".", "/docs/one.md", "one.md"),
            (".", "/flake.nix", &format!("{BLOB}/flake.nix")),
            ("docs", "/one.md", "one.md"),
            ("docs/sub", "/one.md#a", "../one.md#a"),
            ("docs/sub", "/index.md", "../contents.md"),
            ("docs", "https://example.org/x", "https://example.org/x"),
            ("docs", "#section", "#section"),
            ("docs", "//example.org/spec", "//example.org/spec"),
            (".", "//example.org/spec", "//example.org/spec"),
            ("docs", "log.md", &format!("{BLOB}/docs/log.md")),
            ("docs", "gone.md", "gone.md"),
            ("docs/sub", "index.md", &format!("{BLOB}/docs/sub/index.md")),
            ("docs", "README.md", &format!("{BLOB}/docs/README.md")),
            (".", "docs/README.md", &format!("{BLOB}/docs/README.md")),
            ("docs/sub", "fig.png", "fig.png"),
        ] {
            assert_eq!(
                relinked(&format!("[text]({link})"), base),
                format!("[text]({expected})")
            );
        }
    }

    #[test]
    fn titled_and_reference_links_are_relinked() {
        for text in [
            r#"[t](../README.md "guide")"#,
            "[g]: ../README.md",
            r"[g\]]: ../README.md",
            r"[g\\]: ../README.md",
            "[^]: ../README.md",
            "[^ ]: ../README.md",
            "> [g]: ../README.md",
            "- [g]: ../README.md",
            "[t]( ../README.md )",
            "[t](\n../README.md)",
            "[t](../README.md (t))",
            "[g]:\n../README.md",
            "[g]:\n  ../README.md \"t\"",
            "- a\n\n  [g]:\n  ../README.md",
            "> [g]:\n> ../README.md",
            "> [t](\n> ../README.md)",
            "[a]: x \"`\"\n[g]: ../README.md \"`\"",
            "![fig](../README.md) [![fig](../README.md)](../README.md)",
            "[a `](` b](../README.md)",
        ] {
            assert_eq!(relinked(text, "docs"), blob(text), "{text:?}");
        }
        for (text, expected) in [
            (r#"[t](sub/two.md#a "two")"#, r#"[t](sub/two.md#a "two")"#),
            (
                r#"   [g]: /index.md "contents""#,
                r#"   [g]: contents.md "contents""#,
            ),
        ] {
            assert_eq!(relinked(text, "docs"), expected);
        }
    }

    #[test]
    fn destinations_follow_commonmark() {
        let parens = "(".repeat(32) + &")".repeat(32);
        for (base, link, expected) in [
            (
                "docs",
                "draft_(old).md",
                format!("{BLOB}/docs/draft_(old).md"),
            ),
            ("docs", "fig_(1).png#a", "fig_(1).png#a".into()),
            (".", "<flake.nix>", format!("<{BLOB}/flake.nix>")),
            ("docs", "<../x y.md#a>", format!("<{BLOB}/x y.md#a>")),
            ("docs/sub", "</one.md>", "<../one.md>".into()),
            (
                "docs",
                "<https://example.org/x>",
                "<https://example.org/x>".into(),
            ),
            ("docs", "a_((b)).md", format!("{BLOB}/docs/a_((b)).md")),
            ("docs", r"a\).md", format!(r"{BLOB}/docs/a\).md")),
            ("docs", r"<a\>b.md>", format!(r"<{BLOB}/docs/a\>b.md>")),
            ("docs", r"one\.md", r"one\.md".into()),
            ("docs", "on%65.md", "on%65.md".into()),
            (
                "docs",
                &format!("../a{parens}"),
                format!("{BLOB}/a{parens}"),
            ),
        ] {
            assert_eq!(
                relinked(&format!("[text]({link})"), base),
                format!("[text]({expected})")
            );
        }
    }

    #[test]
    fn what_mdbook_does_not_link_is_left_as_written() {
        for text in [
            &format!("[t](../a{}{})", "(".repeat(34), ")".repeat(34)),
            "[t](../a(b",
            r"\[x](../README.md)",
            "[t](<../a<b>)",
            "[t](../README.md extra)",
            "[t](<../README.md> extra)",
            "[t](../README.md 't' b)",
            "[g]: ../README.md extra",
            "[g]: ../README.md \"t\" b",
            "Text\n[g]: ../README.md",
            "[ ]: ../README.md",
            "[^g]: ../README.md",
            "[^ g]: ../README.md",
            r"[^\]]: ../README.md",
            "[text](<a<b.md>)",
            "[text]((../README.md)",
        ] {
            assert_eq!(relinked(text, "docs"), text);
        }
    }

    #[test]
    fn code_and_raw_html_are_not_relinked() {
        for text in [
            "```markdown\n* [x](../README.md)\n```\n",
            "~~~~\n[g]: ../README.md\n~~~~~\n",
            "Write `[x](../README.md)` or ``[x](`a`.md)``.\n",
            "Write `[x](\n../README.md)`.\n",
            "> Write `[x]\n> (../README.md)`.\n",
            "```\n[x](../README.md)\n",
            "- item\n\n    ```\n    [x](../README.md)\n    ```\n",
            "1. ```\n   [x](../README.md)\n   ```\n",
            "> ```\n> [x](../README.md)\n> ```\n",
            "Text.\n\n    [x](../README.md)\n",
            "    ```\n    [x](../README.md)\n",
            "<div>\n[x](../README.md)\n</div>\n",
            "<!--\n[x](../README.md)\n-->\n",
        ] {
            assert_eq!(relinked(text, "docs"), text);
        }
    }

    #[test]
    fn markdown_options_decide_what_is_a_link() {
        let text = "Term\n: definition\n\n    [x](../README.md)\n";
        let mut options = MarkdownOptions::default();
        options.definition_lists = false;
        assert_eq!(relink(text, &options, "docs", BLOB, &HashSet::new()), text);
    }

    #[test]
    fn links_outside_code_are_relinked() {
        for text in [
            "```\n[x](../README.md)\n```\n\n`a` [y](../README.md)\n",
            "<details>\n\n[x](../README.md)\n\n</details>\n",
            "``a [x](../README.md) `\n",
            "``a``` [x](../README.md) `\n",
            "A `tick.\n\n[x](../README.md) and `a`.\n",
            "    ```\n[x](../README.md)\n",
            "- item\n\n    [x](../README.md)\n",
            "Text.\n    [x](../README.md)\n",
            "Term\n: definition\n\n    [x](../README.md)\n",
            "para\nTerm\n: definition\n\n    [x](../README.md)\n",
            "Note[^1].\n\n[^1]: note\n\n    [x](../README.md)\n",
        ] {
            let expected = match text.split_once("```\n\n") {
                Some((code, rest)) => format!("{code}```\n\n{}", blob(rest)),
                None => blob(text),
            };
            assert_eq!(relinked(text, "docs"), expected, "{text:?}");
        }
    }
}
