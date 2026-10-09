#!/usr/bin/env python3
"""How much of this book is still the starter book?

The starter is a chassis: nine pages that prove the pipeline works. Its
prose is placeholder prose. Two brands with nothing in common — opposite
palette temperature, serif against geometric sans, 0 against 18px radius,
portrait against landscape — still came out of it 99% identical in markup
and 94% identical in wording, because only the VALUES diverge. The layouts
and the sentences are shared.

That is the correct behaviour for a chassis and a catastrophe in a
deliverable, and nothing else in the build can tell the difference. Contrast
is measurable, a clipped page is measurable, "this reads like everyone
else's brand book" is not — so this measures the one part of it that is:
how many of the chassis's own sentences are still sitting in your book.

    python3 build/divergence.py

`book.status` in brand.config.json decides whether it is advice or a gate:

    starter   the shipped chassis. Reports only. (default)
    draft     reports, and warns over the threshold.
    final     FAILS over the threshold. Set this before you hand anything
              to a client, and the build will refuse to call a lightly
              recoloured chassis a finished brand book.

It measures shared sentences, not quality. A book that clears it can still
be thin; see docs/05-contents.md for the word counts that matter.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "brand.config.json").read_text(encoding="utf-8"))
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))

THRESHOLD = 25          # % of chassis sentences still present, for draft/final
MIN_WORDS = 6           # shorter strings are labels, not prose


def chassis_sentences():
    """The placeholder prose, read out of the generator that writes it.

    Reading book.py rather than keeping a second copy means this cannot
    drift: a sentence rewritten in the generator stops being counted the
    moment it changes, which is exactly right — a rewritten sentence is no
    longer the chassis's."""
    src = (ROOT / "build" / "book.py").read_text(encoding="utf-8")
    out = set()
    # every single- and double-quoted literal in the generator
    for m in re.finditer(r"'([^'\\\n]{12,})'|\"([^\"\\\n]{12,})\"", src):
        s = (m.group(1) or m.group(2)).strip()
        if s.startswith(("<", "http", "var(", "#", ".", "--")) or ":" in s[:14]:
            continue
        s = re.sub(r"<[^>]+>", "", s)
        for part in re.split(r"(?<=[.!?])\s+", s):
            part = part.strip()
            if len(part.split()) >= MIN_WORDS:
                out.add(normalise(part))
    return {s for s in out if s}


def normalise(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


def book_text():
    p = next((ROOT / "out").glob("*-brand-book-*.html"), None)
    if not p:
        sys.exit("no book in out/ — run build/book.py first")
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return p, normalise(t)


def main():
    status = CFG.get("book", {}).get("status", "starter")
    sents = chassis_sentences()
    path, text = book_text()

    present = sorted(s for s in sents if s in text)
    pct = round(100 * len(present) / len(sents), 1) if sents else 0.0
    words = len(text.split())

    print(f"divergence · {path.name}")
    print(f"  book status            {status}")
    print(f"  chassis sentences      {len(sents)}")
    print(f"  still present          {len(present)}  ({pct}% of the chassis)")
    print(f"  words in the book      {words}")

    if present:
        print("\n  these sentences came from the starter, not from you:")
        for s in present[:6]:
            print(f"    · {s[:88]}…" if len(s) > 88 else f"    · {s}")
        if len(present) > 6:
            print(f"    · … and {len(present) - 6} more")

    if status == "starter":
        print("\n  book.status is 'starter', so this is a report and not a "
              "gate.\n  Set it to 'draft' once you begin writing, and "
              "'final' before handover:\n  at 'final' the build FAILS while "
              f"more than {THRESHOLD}% of the chassis\n  survives, which is "
              "what stops a recoloured starter going out as a\n  brand book.")
        return 0

    if pct <= THRESHOLD:
        print(f"\n  ok — {pct}% is at or under the {THRESHOLD}% threshold. "
              f"The book is yours.")
        return 0

    msg = (f"{pct}% of the starter's own sentences are still in this book "
           f"(threshold {THRESHOLD}%).\n"
           f"  The palette and the type are yours; the words are not. Two "
           f"brands with\n  nothing in common come out of the chassis 94% "
           f"identical in wording, so a\n  reader who has seen another book "
           f"built this way will recognise this one.\n"
           f"  docs/05-contents.md has the page-by-page inventory to write "
           f"against.")
    if status == "final":
        print(f"\nFAILED\n  {msg}")
        return 1
    print(f"\nwarning\n  {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
