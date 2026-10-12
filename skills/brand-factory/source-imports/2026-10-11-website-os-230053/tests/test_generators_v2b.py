"""v2 generators, second batch: tailwind.py, icons.py, microcopy.py.

    python3 -m unittest discover -s skills/brand-factory/tests
"""
import copy as stdcopy, json, pathlib, sys, tempfile, unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "assets" / "pipeline"))
import config  # noqa: E402
import tree as tree_mod  # noqa: E402
import tokens_css  # noqa: E402
import tailwind  # noqa: E402
import icons  # noqa: E402
import microcopy  # noqa: E402

HOI = SKILL / "examples" / "house-of-ichigo" / "brand.config.json"
STARTER = SKILL / "assets" / "brand.config.json"


def load(p):
    cfg, _, a = config.load(p)
    return cfg, a


def tokens_for(cfg, a):
    return tokens_css.build(cfg, tree_mod.build_tree(cfg, a))


class Tailwind(unittest.TestCase):
    def build(self, p):
        cfg, a = load(p)
        tcss = tokens_for(cfg, a)
        css, skipped, n, _derived = tailwind.build(cfg, tcss)
        return cfg, tcss, css

    def test_hoi_passes_its_own_gate(self):
        cfg, tcss, css = self.build(HOI)
        self.assertEqual(tailwind.gate(css, tcss), [])
        self.assertIn("--color-accent:", css)
        self.assertIn("--breakpoint-md: initial;", css)
        self.assertIn("--breakpoint-sm: 600px;", css)
        self.assertIn("--shadow-*: initial;", css)
        self.assertIn("--color-*: initial;", css)
        self.assertIn("--text-heading-md--line-height: var(--type-heading-md-lh);", css)
        self.assertIn("--spacing: 4px;", css)
        self.assertNotIn("--animate-", css.replace("--animate-*: initial;", ""))

    def test_starter_passes(self):
        cfg, tcss, css = self.build(STARTER)
        self.assertEqual(tailwind.gate(css, tcss), [])

    def test_gate_catches_planted_self_reference(self):
        cfg, tcss, css = self.build(HOI)
        bad = css.replace("--color-fg: var(--palette-fg);", "--color-fg: var(--color-fg);")
        self.assertNotEqual(bad, css)
        self.assertTrue(any("self-reference" in e for e in tailwind.gate(bad, tcss)))

    def test_gate_catches_unresolved_and_literals(self):
        cfg, tcss, css = self.build(HOI)
        errs = tailwind.gate(css + "\n:root { --x: var(--nope); --color-y: #fff; }", tcss)
        self.assertTrue(any("unresolved var(--nope)" in e for e in errs))
        self.assertTrue(any("colour literal" in e for e in errs))

    def test_gate_catches_cycle(self):
        cfg, tcss, css = self.build(HOI)
        errs = tailwind.gate(css + "\n:root { --a1: var(--a2); --a2: var(--a1); }", tcss)
        self.assertTrue(any("cycle" in e for e in errs))


class Icons(unittest.TestCase):
    def setUp(self):
        try:
            self.lucide = icons.find_lucide()
        except FileNotFoundError:
            self.skipTest("Lucide not available")

    def test_hoi_names_all_resolve(self):
        cfg, _ = load(HOI)
        items = icons.wanted(cfg)
        self.assertGreaterEqual(len(items), 60)
        missing = [l for _, l, *_ in items if not (self.lucide / f"{l}.svg").exists()]
        self.assertEqual(missing, [])
        self.assertIn(("learn", "graduation-cap", None, False, "brand"), items)

    def test_render_normalises(self):
        src = (self.lucide / "chevron-right.svg").read_text()
        svg, sym = icons.render(src, 1.6, False)
        for need in ('viewBox="0 0 24 24"', 'stroke="currentColor"', 'stroke-width="1.6"',
                     'fill="none"', 'aria-hidden="true"', 'stroke-linecap="round"'):
            self.assertIn(need, svg)
        for gone in ("width=", "height=", "class=", "vector-effect"):
            self.assertNotIn(gone, svg.replace('stroke-width=', ''))
        self.assertEqual(icons.gate_svg("x", svg), [])
        self.assertIn("vector-effect", icons.render(src, 1.6, True)[0])

    def test_dot_fill_dropped_only_when_covered_by_stroke(self):
        src = ('<svg viewBox="0 0 24 24"><circle cx="1" cy="1" r=".5" fill="currentColor"/>'
               '<circle cx="5" cy="5" r="4" fill="currentColor"/></svg>')
        svg, _ = icons.render(src, 1.6, False)
        self.assertEqual(svg.count('fill="currentColor"'), 1)       # the big one stays …
        self.assertTrue(icons.gate_svg("x", svg))                   # … and the gate fails it

    def test_missing_lucide_is_a_clear_error(self):
        import os
        old = os.environ.get("LUCIDE_DIR")
        try:
            os.environ["LUCIDE_DIR"] = "/nonexistent/lucide"
            with tempfile.TemporaryDirectory() as d:
                orig = icons.FALLBACK
                icons.FALLBACK = "/nonexistent/fallback"
                try:
                    with self.assertRaises(FileNotFoundError) as cm:
                        icons.find_lucide(pathlib.Path(d))
                finally:
                    icons.FALLBACK = orig
            self.assertIn("LUCIDE_DIR", str(cm.exception))
        finally:
            if old is None:
                os.environ.pop("LUCIDE_DIR", None)
            else:
                os.environ["LUCIDE_DIR"] = old

    def test_starter_has_no_icons(self):
        cfg, _ = load(STARTER)
        self.assertEqual(icons.wanted(cfg) if cfg.get("icons") else [], [])


class Microcopy(unittest.TestCase):
    def setUp(self):
        self.cfg, _ = load(HOI)
        self.copy = {l: microcopy.clean(self.cfg["copy"].get(l)) if self.cfg["copy"].get(l) else None
                     for l in self.cfg["locales"]["list"]}

    def run_check(self, mutate=None):
        cp = stdcopy.deepcopy(self.copy)
        if mutate:
            mutate(cp)
        return microcopy.check(self.cfg, cp)[0]

    def test_ar_is_a_gap_not_a_failure(self):
        self.assertIsNone(self.copy["ar"])
        self.assertFalse([e for e in self.run_check() if e.startswith("ar")])

    def test_hoi_has_no_banned_word_or_typography_error(self):
        errs = [e for e in self.run_check() if "key(s)" not in e]
        self.assertEqual(errs, [])

    def test_planted_banned_word(self):
        errs = self.run_check(lambda c: c["en"]["cta"].__setitem__("read", "Unlock the library"))
        self.assertTrue(any("en.cta.read" in e and "banned word 'Unlock'" in e for e in errs))

    def test_banned_is_whole_word(self):
        errs = self.run_check(lambda c: c["en"]["cta"].__setitem__("read", "Unlocked, enabled, journeys"))
        self.assertFalse([e for e in errs if "banned" in e])

    def test_planted_missing_fr_key(self):
        errs = self.run_check(lambda c: c["fr"]["cta"].pop("send"))
        self.assertTrue(any(e.startswith("fr:") and "cta.send" in e for e in errs))

    def test_fr_typography(self):
        def bad(c):
            c["fr"]["cta"]["send"] = 'Dites "oui" : vraiment ?'
            c["fr"]["cta"]["read"] = "«Lire»"
        errs = "\n".join(self.run_check(bad))
        self.assertIn('fr.cta.send: ASCII "', errs)
        self.assertIn("':' not preceded", errs)
        self.assertIn("'?' not preceded", errs)
        self.assertIn("« not followed", errs)
        self.assertIn("» not preceded", errs)
        ok = lambda c: c["fr"]["cta"].__setitem__("send", "Rien : « ok » à 10:30 sur https://x.fr/a?b=1")
        self.assertFalse([e for e in self.run_check(ok) if "cta.send" in e])

    def test_exclamation(self):
        errs = self.run_check(lambda c: c["en"]["cta"].__setitem__("read", "Read now!"))
        self.assertTrue(any("exclamation" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
