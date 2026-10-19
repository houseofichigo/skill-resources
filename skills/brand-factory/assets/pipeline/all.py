#!/usr/bin/env python3
"""Rebuild everything, twice, then render and check.

    python3 build/all.py

Twice, because a generator that appends rather than replaces looks fine on
the first run and grows on the second. Then rendered, because the failures
that matter in a brand system are silent: a clipped page, a fallback font,
a synthesised italic. Reading the source will not find any of them.
"""
import hashlib, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STEPS = [
    ("fonts",    "build/fonts.py"),
    ("tokens",   "build/tokens.py"),
    ("css",      "build/css.py"),
    ("BRAND.md", "build/brandmd.py"),
    ("book",     "build/book.py"),
]
WATCH = ["out/tokens.json", "out/tokens.css", "out/BRAND.md"]


def digest():
    out = {}
    for f in WATCH:
        p = ROOT / f
        if p.exists():
            out[f] = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    for p in (ROOT / "out").glob("*-brand-book-*.html"):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    return out


def run(label_width=10):
    for label, script in STEPS:
        r = subprocess.run([sys.executable, script], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode:
            print(f"\n{label} FAILED\n{r.stdout}{r.stderr}")
            sys.exit(1)
        tail = [l for l in r.stdout.strip().split("\n") if l.strip()]
        print(f"  {label:{label_width}} {tail[-1] if tail else 'ok'}")


if __name__ == "__main__":
    print("pass 1")
    run()
    a = digest()
    print("pass 2 · idempotence")
    run()
    b = digest()
    drift = [f for f in a if a[f] != b.get(f)]
    if drift:
        print(f"\nNOT IDEMPOTENT — these changed between identical runs: "
              f"{drift}\nA generator is appending where it should replace.")
        sys.exit(1)
    print("  idempotent")
    print("verify")
    r = subprocess.run(["node", "build/verify.js"], cwd=ROOT,
                       capture_output=True, text=True)
    print("  " + r.stdout.strip().replace("\n", "\n  "))
    if r.returncode:
        print(r.stderr.strip())
        sys.exit(1)

    # A check nobody has seen fail is not a check. selftest.py trips every
    # gate in check.py on a deliberately bad file, and requires the shipped
    # templates to stay silent.
    print("selftest")
    r = subprocess.run([sys.executable, "build/selftest.py"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stdout.strip() + r.stderr.strip())
        sys.exit(1)
    print("  " + r.stdout.strip().split("\n")[-1])

    # Everything above measures whether the book is CORRECT. This measures
    # whether it is YOURS: two unrelated brands come out of the chassis 94%
    # identical in wording, and no other gate can see that.
    print("divergence")
    r = subprocess.run([sys.executable, "build/divergence.py"], cwd=ROOT,
                       capture_output=True, text=True)
    lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
    for l in lines:
        if l.startswith(("  still present", "  ok", "FAILED", "warning",
                         "  book status")):
            print("  " + l.strip())
    if r.returncode:
        print(r.stdout.strip().split("FAILED")[-1].strip())
        sys.exit(1)
