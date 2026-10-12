"""Config v2: the gate must fail on what it claims to, and provenance must
resolve the way config.py's docstring says. Each case was a real defect or
a review finding; none of them is hypothetical.

    python3 -m unittest discover -s skills/brand-factory/tests
"""
import copy, json, pathlib, sys, unittest

SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "assets" / "pipeline"))
import config  # noqa: E402

HOI = SKILL / "examples" / "house-of-ichigo" / "brand.config.json"
STARTER = SKILL / "assets" / "brand.config.json"


def prov(cfg):
    return {p: (s, c, g) for p, v, s, c, g in config.walk(cfg)}


class Provenance(unittest.TestCase):
    def test_override_is_exact_path_only(self):
        p = prov({"$src": "S2", "x": {"$src_px": "S3", "px": 1, "ceiling_px": 2, "px_tablet": 3}})
        self.assertEqual(p["/x/px"][0], "S3")
        self.assertEqual(p["/x/ceiling_px"][0], "S2")
        self.assertEqual(p["/x/px_tablet"][0], "S2")

    def test_override_reaches_through_list_of_dicts(self):
        p = prov({"$src": "S2", "s": {"$src_roles_px_phone": "WO", "roles": [{"px": {"desktop": 1, "phone": 2}}]}})
        self.assertEqual(p["/s/roles/0/px/phone"], ("WO", "default", None))
        self.assertEqual(p["/s/roles/0/px/desktop"][0], "S2")

    def test_explicit_child_source_beats_ancestor_override(self):
        p = prov({"$src": "S2", "a": {"$src_b": "S3", "b": {"$src": "S1", "v": 1}}})
        self.assertEqual(p["/a/b/v"][0], "S1")

    def test_override_keeps_inherited_confidence(self):
        p = prov({"$src": "S2", "$conf": "medium", "a": {"$src_b": "S3", "b": 1}})
        self.assertEqual(p["/a/b"], ("S3", "medium", None))

    def test_fresh_citation_is_judged_on_its_own(self):
        p = prov({"$src": "S3", "$conf": "medium", "a": {"$src": "S2", "b": 1}})
        self.assertEqual(p["/a/b"], ("S2", "high", None))

    def test_named_source_ends_inherited_gap(self):
        p = prov({"$src": "S2", "a": {"$gap": "x", "b": {"$src": "S1", "c": 1}}})
        self.assertEqual(p["/a/b/c"], ("S1", "high", None))

    def test_null_is_never_a_value(self):
        p = prov({"$src": "S2", "a": {"hex": None, "$gap": "x"}, "b": {"hex": None}})
        self.assertEqual(p["/a/hex"][1], "gap")
        self.assertEqual(p["/b/hex"][1], "empty")

    def test_wo_means_default(self):
        self.assertEqual(prov({"$src": "WO", "a": 1})["/a"][1], "default")


class Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hoi = json.loads(HOI.read_text(encoding="utf-8"))

    def errors(self, mutate):
        c = copy.deepcopy(self.hoi)
        mutate(c)
        return "\n".join(config.analyse(c, HOI.parent)["errors"])

    def test_hoi_passes(self):
        self.assertEqual(self.errors(lambda c: None), "")

    def test_starter_passes(self):
        c = json.loads(STARTER.read_text(encoding="utf-8"))
        self.assertEqual(config.analyse(c, STARTER.parent)["errors"], [])

    def test_unknown_source(self):
        self.assertIn("names no source", self.errors(lambda c: c["shape"].__setitem__("$src", "S9:p1")))

    def test_page_out_of_range(self):
        self.assertIn("has 106 pages", self.errors(lambda c: c["shape"].__setitem__("$src", "S2:p999")))

    def test_literal_colour_in_component(self):
        e = self.errors(lambda c: c["components"]["slider"]["thumb"].__setitem__("bg", "#0A0E27"))
        self.assertIn("literal colour at /components/slider/thumb/bg", e)

    def test_prose_in_style_slot(self):
        e = self.errors(lambda c: c["components"]["row"]["rest"].__setitem__("bg", "white at 60%"))
        self.assertIn("not prose", e)

    def test_unresolved_reference(self):
        e = self.errors(lambda c: c["components"]["tabs"].__setitem__("current_rule", "{color.accentx}"))
        self.assertIn("unresolved {color.accentx}", e)

    def test_policy_enum(self):
        self.assertIn("gradient", self.errors(lambda c: c["effects"]["policy"].__setitem__("gradient", "sometimes")))

    def test_unreconciled_guess_in_reproduce_mode(self):
        self.assertIn("guess with no reconcile item", self.errors(lambda c: c["shape"].__setitem__("$conf", "guess")))

    def test_required_role(self):
        self.assertIn("accent_on", self.errors(lambda c: c["color"]["roles"].pop("accent_on")))


class V1View(unittest.TestCase):
    def test_shape_the_v1_scripts_read(self):
        v = config.v1_view(json.loads(HOI.read_text(encoding="utf-8")))
        self.assertEqual(v["color"]["brand"]["hex"], "#1231D6")
        self.assertEqual(set(v["color"]["semantic"]), {"attention", "blocking"})
        self.assertNotIn("#008558", v["color"]["retired"].values(),
                         "the Build pillar must not be retired with the old success role")
        self.assertNotIn("govern", v["color"]["accents"], "an alias of Ink is not a fourth hue")
        self.assertEqual(v["type"]["display"]["weights"], "200 800")
        self.assertEqual(v["type"]["arabic"]["weights"], [400, 500, 600, 700])
        self.assertEqual(v["type"]["tracking"]["sm"], "0")
        self.assertEqual(v["effects"]["policy"]["radius_max_px"], 4)


if __name__ == "__main__":
    unittest.main()
