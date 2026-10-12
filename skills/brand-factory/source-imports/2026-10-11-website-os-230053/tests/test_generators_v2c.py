"""v2 interface generators: components.py and patterns.py.

    python3 -m unittest discover -s skills/brand-factory/tests

Nothing here writes into the skill: generated CSS goes to a temporary
directory, pages are built in memory. The render gate is not run here (it
needs node and a Chromium); all.py runs it.
"""
import copy, json, pathlib, re, sys, tempfile, unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "assets" / "pipeline"))
import config  # noqa: E402
import uikit  # noqa: E402
import components as C  # noqa: E402
import patterns as P  # noqa: E402

HOI = SKILL / "examples" / "house-of-ichigo" / "brand.config.json"
STARTER = SKILL / "assets" / "brand.config.json"


def ctx_for(path, mutate=None):
    cfg, _, a = config.load(path)
    if mutate:
        cfg = copy.deepcopy(cfg)
        mutate(cfg)
    return uikit.Ctx(cfg, uikit.build_tree(cfg, a))


def components_css(ctx):
    sheet, groups, manifest, unrendered = C.build(ctx)
    return sheet.css(), manifest, unrendered


class LiteralGate(unittest.TestCase):
    def gate(self, css):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "components.css"
            p.write_text(css, encoding="utf-8")
            return uikit.literal_gate([p])

    def test_hoi_components_have_no_literal(self):
        css, _, _ = components_css(ctx_for(HOI))
        self.assertEqual(self.gate(css), [])

    def test_planted_hex_fails(self):
        def plant(cfg):
            cfg["components"]["button"]["variants"]["primary"]["rest"]["bg"] = "#FF0000"
        css, _, _ = components_css(ctx_for(HOI, plant))
        bad = self.gate(css)
        self.assertTrue(any("#FF0000" in b for b in bad), bad)

    def test_planted_rgb_and_family_fail(self):
        css = ".x { color: rgb(1, 2, 3); font-family: 'Comic Sans'; }"
        bad = self.gate(css)
        self.assertTrue(any("rgb()" in b for b in bad))
        self.assertTrue(any("font family" in b for b in bad))

    def test_the_config_gate_refuses_the_same_plant(self):
        # the config gate is the first line; the literal gate is the second
        cfg = json.loads(HOI.read_text(encoding="utf-8"))
        cfg["components"]["button"]["variants"]["primary"]["rest"]["bg"] = "#FF0000"
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "brand.config.json"
            p.write_text(json.dumps(cfg), encoding="utf-8")
            a = config.analyse(cfg, HOI.parent)
            self.assertTrue(any("#FF0000" in e or "literal" in e.lower() for e in a["errors"]), a["errors"][:3])


class Manifest(unittest.TestCase):
    def test_every_config_component_is_in_the_manifest(self):
        ctx = ctx_for(HOI)
        _, manifest, _ = components_css(ctx)
        names = [m["name"] for m in manifest]
        self.assertEqual(sorted(names), sorted(k for k in ctx.cfg["components"] if not k.startswith("$")))
        for m in manifest:
            self.assertIn(m["group"], C.GROUPS, m["name"])
            self.assertTrue(m["states"], m["name"])

    def test_every_component_has_a_renderer(self):
        _, _, unrendered = components_css(ctx_for(HOI))
        self.assertEqual([u for u in unrendered if "no renderer" in u["why"]], [])

    def test_p_ids_are_config_ids(self):
        ctx = ctx_for(HOI)
        _, manifest, _ = components_css(ctx)
        ids = set(ctx.cfg["proposals_3_4"]["ids"])
        used = {p for m in manifest for p in m["p_ids"] + m["p_id_candidates"]}
        self.assertTrue(used, "no component linked to a 3.4 proposal")
        self.assertEqual(used - ids, set())

    def test_starter_has_no_components_and_passes(self):
        css, manifest, unrendered = components_css(ctx_for(STARTER))
        self.assertEqual(manifest, [])
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "components.css"
            p.write_text(css, encoding="utf-8")
            self.assertEqual(uikit.literal_gate([p]), [])

    def test_hover_is_gated_and_no_press_transform(self):
        ctx = ctx_for(HOI)
        css, _, _ = components_css(ctx)
        media = None
        for line in css.split("\n"):
            if line.startswith("@media"):
                media = line
            elif line == "}" and media is not None and not line.startswith("  "):
                pass
            if ":hover" in line and "{" in line:
                self.assertTrue(line.startswith("  ") and media and ctx.hover_q in media,
                                f"a :hover rule outside the hover gate: {line.strip()}")
            if not line.startswith(" ") and not line.startswith("@media") and line.endswith("{"):
                media = None
        for m in re.finditer(r":active[^{]*\{([^}]*)\}", css):
            self.assertNotIn("transform", m.group(1))
        self.assertNotIn("transition: all", css)
        self.assertNotRegex(css, r"box-shadow\s*:\s*(?!none)")


class Cadence(unittest.TestCase):
    def test_hoi_web_patterns_pass(self):
        ctx = ctx_for(HOI)
        pages = ctx.cfg["patterns"]["web"]["pages"]
        checked = 0
        for ptype in (k for k in pages if not k.startswith("$")):
            pillar = C.pillars(ctx)[0] if ptype == "pillar" else None
            pg, html = P.web_page(ctx, ptype, pages[ptype], ptype, pillar)
            names, inks, cad = P.cadence(P.finish(ctx, pg, html, ptype))
            self.assertTrue(cad["pass"], f"{ptype}: {cad['errors']}")
            planned = pg.planned   # after the cadence repair (plan_cadence)
            self.assertEqual(len(names), len(planned), f"{ptype}: {names} vs {planned}")
            if any(l.startswith("cta_band") for l in planned):
                self.assertEqual(names[-1], "cta_band", ptype)
            checked += 1
        self.assertGreaterEqual(checked, 10)

    def test_cadence_catches_adjacent_ink(self):
        html = ('<section class="c-section" data-section="a" data-surface="white"></section>'
                '<section class="c-conv" data-surface="ink" data-section="conviction_band"></section>'
                '<section class="c-cta" data-surface="ink" data-section="cta_band"></section>')
        _, _, cad = P.cadence(html)
        self.assertFalse(cad["pass"])

    def test_a_cadence_warning_fails(self):
        html = ('<section class="c-section" data-section="a" data-surface="white"></section>'
                '<section class="c-conv" data-surface="ink" data-section="conviction_band"></section>'
                '<section class="c-section" data-section="b" data-surface="white"></section>'
                '<section class="c-cta" data-surface="ink" data-section="cta_band"></section>')
        _, _, cad = P.cadence(html)
        self.assertFalse(cad["pass"])

    def test_cadence_repair_moves_or_drops(self):
        items, note = P.plan_cadence(P.parse_seq(["hero w", "a w", "conviction_band i", "b w", "cta_band i"]))
        self.assertIsNotNone(note)
        names = [l for l, _ in items]
        self.assertEqual(names[-1], "cta_band")


class PageTruth(unittest.TestCase):
    def setUp(self):
        self.ctx = ctx_for(HOI)
        C._LANG["ctx"] = self.ctx

    def test_no_config_note_in_page_text(self):
        pages = self.ctx.cfg["patterns"]["web"]["pages"]
        docs = []
        for ptype in (k for k in pages if not k.startswith("$")):
            pg, html = P.web_page(self.ctx, ptype, pages[ptype], ptype, C.pillars(self.ctx)[0] if ptype == "pillar" else None)
            docs.append((ptype, P.finish(self.ctx, pg, html, ptype)))
        self.assertEqual(P.notes_gate(self.ctx.cfg, docs), [])

    def test_notes_gate_fires(self):
        note = P.config_notes(self.ctx.cfg)[0]
        self.assertTrue(P.notes_gate(self.ctx.cfg, [("x", f"<p>{note}</p>")]))

    def test_offer_is_rendered(self):
        pl = C.pillars(self.ctx)[0]
        h = C.programme_html(self.ctx, pl)
        self.assertNotIn("c-slot", h)
        self.assertIn(self.ctx.cfg["copy"]["en"]["offer"]["pillars"][pl["key"]]["programmes"]["core"]["title"], h)

    def test_select_has_no_preselected_answer(self):
        h = C.contact_html(self.ctx)
        self.assertIn('<option value="" disabled selected>', h)
        self.assertIn(" required", h)
        self.assertIn('maxlength="2000"', h)

    def test_french_page_strings(self):
        self.ctx.lang = "fr"
        try:
            pg, html = P.web_page(self.ctx, "contact", ["page head w", "contact_form w"], "contact")
        finally:
            self.ctx.lang = "en"
        self.assertIn(self.ctx.cfg["copy"]["fr"]["contact"]["title"].rstrip("."), html)
        self.assertIn(self.ctx.cfg["copy"]["fr"]["contact"]["topics"][0], html)

    def test_drawer_on_every_page(self):
        pg, html = P.web_page(self.ctx, "home", self.ctx.cfg["patterns"]["web"]["pages"]["home"], "home")
        self.assertIn('id="mnav"', html)
        self.assertIn('aria-controls="mnav"', html)

    def test_parity_gate(self):
        r = [{"kind": "web", "lang": "en", "type": "home", "file": "a", "sections": ["hero"]},
             {"kind": "web", "lang": "fr", "type": "home", "file": "b", "sections": []}]
        self.assertTrue(P.parity_gate(r))

    def test_no_lorem_no_price(self):
        ctx = ctx_for(HOI)
        pages = ctx.cfg["patterns"]["web"]["pages"]
        for ptype in (k for k in pages if not k.startswith("$")):
            pg, html = P.web_page(ctx, ptype, pages[ptype], ptype, C.pillars(ctx)[0] if ptype == "pillar" else None)
            self.assertNotRegex(html.lower(), r"lorem|ipsum")
            self.assertNotRegex(html, r"[€$£]\s?\d|\d\s?(?:€|EUR)\b|\b\d+\s?(?:days?|jours?)\b|half-day")


if __name__ == "__main__":
    unittest.main()
