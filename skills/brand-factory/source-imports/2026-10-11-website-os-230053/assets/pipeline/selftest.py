#!/usr/bin/env python3
"""Prove the checker fires.

A check you have never seen fail is not a check. This writes one
deliberately bad file that violates every rule check.py enforces, runs the
checker on it, and fails if any gate stayed quiet — then runs it on the
shipped templates and fails if any gate fired.

Both directions matter. A checker that misses a violation lets drift
through; a checker that cries wolf on its own templates teaches people to
skim its output, and then the real failure scrolls past with the noise.

    python3 build/selftest.py
"""
import json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))
CHECK = ROOT / "build" / "check.py"

RETIRED = next(iter(
    {k: v for k, v in T["color"].get("retired", {}).items()
     if not k.startswith("$")}.values()), "#CF5B2B")

# The off-palette probe must be a colour the brand has not classified. v1
# used #3B82F6, which a brand that retires Tailwind blue (HOI 3.3 does)
# reports as RETIRED instead — the checker was right and the test was not.
_RET = {v.upper() for v in T["color"].get("retired", {}).values()
        if isinstance(v, str)}
OFF = next(h for h in ("#3B82F6", "#8A2BE2", "#B45309", "#6D28D9")
           if h not in _RET)

# Policy cases are the brand's. Where the brand forbids an effect, the bad
# file carries it and the checker must fire; where it allows one, a clean
# file carries it and the checker must stay SILENT — otherwise the
# checker is still enforcing someone else's brand.
POLICY = T.get("effects", {}).get("policy", {})
EFFECT_CASES = [  # (policy key, forbidden value, css fragment, finding)
    ("gradient", "none", ".g{background:linear-gradient(#fff,#000)}", "GRADIENT"),
    ("blur", "none", ".h{backdrop-filter:blur(8px)}", "BLUR"),
    ("filter", "none", ".i{filter:grayscale(1)}", "IMAGE FILTER"),
    ("transform_on_press", False, ".j:active{transform:scale(.98)}", "TRANSFORM ON PRESS"),
    ("opacity_hover", False, ".l:hover{opacity:.88}", "OPACITY HOVER"),
    ("scroll_linked_motion", False, ".m{animation-timeline:scroll()}", "SCROLL-LINKED MOTION"),
]
RADIUS_CASE = (f".k{{border-radius:0 0 {(POLICY.get('radius_max_px', 4) + 6) / 16}rem 0}}",
               "BORDER-RADIUS")
FORBIDDEN = [c for c in EFFECT_CASES if POLICY.get(c[0]) == c[1]]
ALLOWED = [c for c in EFFECT_CASES if c[0] in POLICY and POLICY.get(c[0]) != c[1]]
SHADOW = POLICY.get("shadow", "none") == "none"
EXTRA = "\n  ".join([c[2] for c in FORBIDDEN] + [RADIUS_CASE[0]]
                     + ([".d{box-shadow:0 2px 8px rgba(0,0,0,.2)}"] if SHADOW else []))

# One file, every violation. Each fragment is annotated with the gate it
# is there to trip, so a gate that stops firing is traceable to a line.
BAD = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../references/tokens.css">
<style>
  .a{{color:{RETIRED}}}                        /* retired colour     */
  .b{{color:{OFF}}}                           /* off-palette        */
  .c{{font-family:"Comic Sans MS"}}             /* unapproved font    */
  {EXTRA}                                       /* the brand's effects.policy */
  @media (max-width:800px){{.a{{color:#000}}}}   /* bare media query   */
</style></head><body>
<h1 style="font-family:var(--display);font-style:italic">x</h1>
<p>We leverage seamless synergy to unlock your journey.</p>
</body></html>
"""

# substring → what it proves. Substrings, not exact strings, so wording can
# improve without breaking the test.
MUST_FIRE = {
    "RETIRED COLOUR": "old material leaking into new work",
    "OFF-PALETTE": "a colour from outside the system",
    "UNAPPROVED FONT": "a font nobody licensed",
    "bare @media": "a breakpoint that fires during PDF export",
    "SYNTHESISED ITALIC": "a fake italic in an inline style attribute",
    "banned word": "the voice list",
    RADIUS_CASE[1]: "a corner rounder than effects.policy.radius_max_px",
}
if SHADOW:
    MUST_FIRE["BOX-SHADOW"] = "elevation by shadow, where the brand forbids it"
for _k, _v, _css, _finding in FORBIDDEN:
    MUST_FIRE[_finding] = f"effects.policy.{_k} is {_v!r}"


# The originality metric, pinned to nine cases with known right answers.
# Seven are real: they come from two brands' actual palettes, including one
# collision an earlier version of this metric was blind to and one false
# positive it used to report. A metric with no fixture drifts.
#   FLAG   = compared, and under the threshold
#   clear  = compared, and far enough away
#   exempt = not worth comparing at all
COLOUR_CASES = [
    ("navy-black vs neutral near-black", "#0A0E27", "#191919", "exempt"),
    ("cool grey vs warm paper", "#F2F5F8", "#F0EEE6", "exempt"),
    ("warm paper vs warm paper", "#FAF8F2", "#F0EEE6", "FLAG"),
    ("teal vs framework cyan-600", "#0089A8", "#0891B2", "FLAG"),
    ("green vs framework emerald-700", "#008558", "#047857", "FLAG"),
    ("blue vs framework blue-700", "#1231D6", "#1D4ED8", "FLAG"),
    ("magenta vs framework pink-600", "#E2006D", "#DB2777", "clear"),
    ("hairline vs framework hairline", "#E3E8EF", "#E5E7EB", "exempt"),
    ("pure white vs warm paper", "#FFFFFF", "#F0EEE6", "exempt"),
]


def colour_metric():
    """Import the metric out of tokens.py without running the build."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_tok", ROOT / "build" / "tokens.py")
    mod = importlib.util.module_from_spec(spec)
    # tokens.py measures at import; run it in a namespace where main() is
    # never called, which is what module_from_spec + exec_module gives us.
    spec.loader.exec_module(mod)
    return mod.comparable, mod.distance


def run(*paths):
    r = subprocess.run([sys.executable, str(CHECK), *map(str, paths)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    if not (ROOT / "out" / "tokens.json").exists():
        sys.exit("run build/all.py first — selftest reads out/tokens.json")

    bad = pathlib.Path(tempfile.mkdtemp()) / "bad.html"
    bad.write_text(BAD, encoding="utf-8")

    fails = []

    code, out = run(bad)
    print("negative · every gate must fire on a deliberately bad file")
    for needle, what in MUST_FIRE.items():
        ok = needle in out
        print(f"  {'fires ' if ok else 'SILENT'}  {needle:20} {what}")
        if not ok:
            fails.append(f"{needle} did not fire — {what} is unguarded")
    if code == 0:
        fails.append("checker exited 0 on a file full of errors")

    # The other direction for policy: what the brand ALLOWS must not fire.
    if ALLOWED:
        ok_file = bad.parent / "allowed.html"
        ok_file.write_text(
            '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<link rel="stylesheet" href="../references/tokens.css"><style>'
            + "".join(c[2] for c in ALLOWED) + "</style></head><body>"
            "<p>x</p></body></html>", encoding="utf-8")
        _, out = run(ok_file)
        print("\npolicy · what effects.policy allows must stay silent")
        for k, v, _css, finding in ALLOWED:
            quiet = finding not in out
            print(f"  {'silent' if quiet else 'FIRES '}  {finding:20} "
                  f"effects.policy.{k} is {POLICY.get(k)!r}")
            if not quiet:
                fails.append(f"{finding} fired although the brand allows it "
                             f"— the checker is enforcing another brand")

    templates = sorted((ROOT / "skill-template" / "templates").glob("*.html"))
    code, out = run(*templates)
    noisy = [ln.strip() for ln in out.splitlines()
             if "ERROR" in ln or "warning" in ln]
    print(f"\npositive · the {len(templates)} shipped templates must be silent")
    if noisy:
        for ln in noisy:
            print("  NOISE   ", ln)
        fails.append(f"{len(noisy)} finding(s) on shipped templates — a "
                     f"checker that cries wolf on its own output gets "
                     f"ignored, and then the real failure scrolls past")
    else:
        print("  clean")

    comparable, distance = colour_metric()
    thr = json.loads((ROOT / "brand.config.json").read_text(
        encoding="utf-8")).get("avoid_palettes", {}).get("threshold", 40)
    print(f"\nmetric · originality, {len(COLOUR_CASES)} pinned cases "
          f"(threshold {thr})")
    for label, a, b, want in COLOUR_CASES:
        d = distance(a, b)
        got = ("FLAG" if d < thr else "clear") if comparable(a, b) else "exempt"
        ok = got == want
        print(f"  {'ok    ' if ok else 'WRONG '} {label:34} "
              f"{got:7} {d:>6}   want {want}")
        if not ok:
            fails.append(f"originality metric: {label} gives {got}, "
                         f"should be {want}")

    if fails:
        print("\nFAILED")
        for f in fails:
            print("  ·", f)
        sys.exit(1)
    print(f"\nselftest ok · {len(MUST_FIRE)} gates fire, "
          f"{len(templates)} templates clean, "
          f"{len(COLOUR_CASES)} metric cases correct")


if __name__ == "__main__":
    main()
