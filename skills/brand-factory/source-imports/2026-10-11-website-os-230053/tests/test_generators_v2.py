"""v2 generators: tree.py, dtcg.py, designmd.py.

    python3 -m unittest discover -s skills/brand-factory/tests

Nothing here writes into the skill: DESIGN.md for the lint test goes to a
temporary directory.
"""
import json, pathlib, re, shutil, subprocess, sys, tempfile, unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "assets" / "pipeline"))
import config  # noqa: E402
import tree as tree_mod  # noqa: E402
import dtcg  # noqa: E402
import designmd  # noqa: E402

HOI = SKILL / "examples" / "house-of-ichigo" / "brand.config.json"
STARTER = SKILL / "assets" / "brand.config.json"
EXTRAS = ("color.tint.", "color.retired.", "font.", "breakpoint.")
ALLOWED_TOP = {"version", "name", "description", "omitted",
               "colors", "typography", "rounded", "spacing", "components"}


def load(p):
    cfg, _, a = config.load(p)
    return cfg, a


def front_matter_keys(md):
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    assert m, "no front matter"
    return [l.split(":", 1)[0].strip('"') for l in m.group(1).split("\n")
            if l and not l.startswith(" ")]


class Tree(unittest.TestCase):
    def check_names(self, path):
        cfg, a = load(path)
        t = tree_mod.build_tree(cfg, a)
        targets = config.ref_targets(cfg)
        refnames = {n for n in t["tokens"] if not n.startswith(EXTRAS)} | set(t["components"])
        gapnames = {g["name"] for g in t["_gaps"]}
        # every token in a reference category is a ref target …
        self.assertEqual(refnames - targets, set())
        # … and every ref target is a token, a component, or a listed gap
        self.assertEqual(targets - refnames - gapnames, set())
        # a gap is never also a token
        self.assertEqual({g["name"] for g in t["_gaps"] if "part" not in g} & set(t["tokens"]), set())
        return t, targets

    def test_names_match_ref_targets_hoi(self):
        t, targets = self.check_names(HOI)
        tokens_or_components = {n for n in t["tokens"] if not n.startswith(EXTRAS)} | set(t["components"])
        # HOI: only the two gap roles are ref targets without a token
        self.assertEqual(targets - tokens_or_components, set(), "a gap role must not be a reference target")

    def test_names_match_ref_targets_starter(self):
        self.check_names(STARTER)

    def test_extras_present(self):
        cfg, a = load(HOI)
        t = tree_mod.build_tree(cfg, a)
        names = set(t["tokens"])
        self.assertIn("color.tint.accent.70", names)
        self.assertIn("font.display", names)
        self.assertIn("breakpoint.wide", names)
        self.assertTrue(t["tokens"]["color.retired.terracotta"].get("deprecated"))
        self.assertNotIn("color.retired.success_was", names)   # retired role, not colour

    def test_every_token_has_provenance(self):
        for p in (HOI, STARTER):
            cfg, a = load(p)
            for name, tok in tree_mod.build_tree(cfg, a)["tokens"].items():
                self.assertTrue(tok["provenance"] and tok["provenance"]["src"]
                                and tok["provenance"]["conf"], name)
                self.assertTrue(tok["json_pointer"].startswith("/"), name)

    def test_resolve(self):
        cfg, a = load(HOI)
        t = tree_mod.build_tree(cfg, a)
        self.assertEqual(tree_mod.resolve("{color.accent}", t), "#1231D6")
        self.assertEqual(tree_mod.resolve("{color.pillar.govern}", t), "#0A0E27")
        self.assertIsNone(tree_mod.resolve("{color.nope}", t))
        self.assertEqual(tree_mod.resolve("plain", t), "plain")

    def test_type_composite(self):
        cfg, a = load(HOI)
        t = tree_mod.build_tree(cfg, a)
        d = t["tokens"]["type.display_xl"]
        self.assertEqual(d["value"]["fontFamily"], "{font.display}")
        self.assertEqual(d["value"]["fontSize"], {"value": 88, "unit": "px"})
        self.assertEqual(d["value"]["letterSpacing"], "-.035em")          # band ≥64
        self.assertEqual(d["extensions"]["breakpoints"]["phone"]["letterSpacing"], "-.03em")  # 44px → band ≥43
        self.assertEqual(t["tokens"]["type.eyebrow"]["value"]["letterSpacing"], ".2em")  # role wins
        # weakest part: button size is a default
        self.assertEqual(t["tokens"]["type.button"]["provenance"]["conf"], "default")


class DTCG(unittest.TestCase):
    def test_oklch_round_trip(self):
        L, C, H = dtcg.hex_to_oklch("#1231D6")
        r, g, b = dtcg.oklch_to_rgb(L, C, H)
        for got, want in zip((r, g, b), (0x12, 0x31, 0xD6)):
            self.assertLessEqual(abs(got * 255 - want), 1.0)
        self.assertEqual(dtcg.oklch_to_hex(L, C, H)[0], "#1231D6")

    def test_ramp_anchors_brand_hex(self):
        steps = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
        r, anchor = dtcg.ramp("#1231D6", steps)
        self.assertEqual(r[str(anchor)]["hex"], "#1231D6")
        Ls = [r[str(s)]["oklch"][0] for s in steps]
        self.assertEqual(Ls, sorted(Ls, reverse=True))      # monotonic light → dark
        for s in steps:                                     # all in gamut
            self.assertRegex(r[str(s)]["hex"], r"^#[0-9A-F]{6}$")

    def test_every_token_has_provenance(self):
        for p in (HOI, STARTER):
            cfg, a = load(p)
            doc, _, errors, _ = dtcg.build(cfg, a)
            self.assertEqual(errors, [])
            toks = list(dtcg.walk_tokens(doc))
            self.assertTrue(toks)
            for name, t in toks:
                e = t["$extensions"]["brand-factory"]
                self.assertTrue(e["provenance"]["src"] and e["provenance"]["conf"], name)
                self.assertTrue(e["pointer"].startswith("/"), name)

    def test_shapes(self):
        cfg, a = load(HOI)
        doc, _, _, ramps = dtcg.build(cfg, a)
        acc = doc["color"]["accent"]
        self.assertEqual(acc["$value"]["colorSpace"], "srgb")
        self.assertEqual(acc["$value"]["hex"], "#1231D6")
        self.assertEqual(acc["$extensions"]["brand-factory"]["ramp"]["surface_use"], "forbidden")
        self.assertEqual(acc["$extensions"]["brand-factory"]["ramp"]["provenance"]["conf"], "derived")
        self.assertEqual(doc["color"]["pillar"]["govern"]["$value"], "{color.fg}")
        # retired colours are a denylist in $extensions, never tokens
        self.assertNotIn("retired", doc["color"])
        ret = {c["name"]: c for c in doc["$extensions"]["brand-factory"]["retired"]["colors"]}
        self.assertEqual(ret["terracotta"]["hex"], "#CF5B2B")
        self.assertNotIn("$type", ret["terracotta"])
        # letterSpacing: px for DTCG, the brand's em kept beside it
        self.assertEqual(doc["type"]["display_xl"]["$extensions"]["brand-factory"]["letterSpacing_css"], "-.035em")
        self.assertEqual(doc["color"]["muted_on_dark"]["$value"]["alpha"], 0.6)
        self.assertEqual(doc["type"]["display_xl"]["$value"]["letterSpacing"],
                         {"value": -3.08, "unit": "px"})
        self.assertEqual(set(ramps), {"color.accent", "color.pillar.learn",
                                      "color.pillar.build", "color.pillar.lead"})


class DesignMD(unittest.TestCase):
    def test_front_matter_only_allowed_groups(self):
        for p in (HOI, STARTER):
            cfg, a = load(p)
            md, _, _ = designmd.build(cfg, a)
            keys = front_matter_keys(md)
            self.assertTrue(set(keys) <= ALLOWED_TOP, set(keys) - ALLOWED_TOP)
            self.assertIn("colors", keys)

    def test_body_sections_in_spec_order(self):
        cfg, a = load(HOI)
        md, _, _ = designmd.build(cfg, a)
        heads = re.findall(r"^## (.+)$", md, re.M)
        self.assertEqual(heads, ["Overview", "Colors", "Typography", "Layout", "Elevation & Depth",
                                 "Shapes", "Components", "Do's and Don'ts", "Responsive",
                                 "Known Gaps", "Provenance"])

    def test_idempotent(self):
        for p in (HOI, STARTER):
            cfg, a = load(p)
            md1, ext1, _ = designmd.build(cfg, a)
            cfg, a = load(p)
            md2, ext2, _ = designmd.build(cfg, a)
            self.assertEqual(md1, md2)
            self.assertEqual(ext1, ext2)
            doc1 = json.dumps(dtcg.build(cfg, a)[0], indent=2, ensure_ascii=False)
            doc2 = json.dumps(dtcg.build(*load(p))[0], indent=2, ensure_ascii=False)
            self.assertEqual(doc1, doc2)

    def test_lint_passes(self):
        if not shutil.which("npx"):
            self.skipTest("npx is not on PATH — the @google/design.md linter cannot run")
        for p in (HOI, STARTER):
            cfg, a = load(p)
            md, _, _ = designmd.build(cfg, a)
            with tempfile.TemporaryDirectory() as d:
                f = pathlib.Path(d) / "DESIGN.md"
                f.write_text(md, encoding="utf-8")
                res, err = designmd.lint(f, d)
            if res is None:
                self.skipTest(f"linter unavailable: {err}")
            errs = [x for x in res["findings"] if x["severity"] == "error"]
            self.assertEqual(errs, [], p.name)


if __name__ == "__main__":
    unittest.main()
