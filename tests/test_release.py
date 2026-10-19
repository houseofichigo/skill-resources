from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_catalog import APPROVED_IDS, safe_member, sensitive  # noqa: E402


class ReleaseSafetyTests(unittest.TestCase):
    def test_exact_public_allowlist(self) -> None:
        catalogue = json.loads((ROOT / "catalog.json").read_text())
        ids = [record["id"] for record in catalogue["skills"]]
        self.assertEqual(35, len(ids))
        self.assertEqual(APPROVED_IDS, set(ids))
        self.assertEqual(APPROVED_IDS, {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()})

    def test_archive_path_traversal_is_rejected(self) -> None:
        self.assertFalse(safe_member("../secret.txt"))
        self.assertFalse(safe_member("skill/../../secret.txt"))
        self.assertFalse(safe_member("/absolute/path"))
        self.assertFalse(safe_member("skill\\secret.txt"))
        self.assertTrue(safe_member("skill/SKILL.md"))

    def test_company_runtime_coupling_is_rejected(self) -> None:
        issues = sensitive(
            "Read workspaces/hoi-" + "company and then use House of " + "Ichigo defaults.",
            "skills/example/SKILL.md",
            False,
        )
        self.assertTrue(any("runtime" in issue for issue in issues))
        self.assertTrue(any("publisher coupling" in issue for issue in issues))

    def test_real_identity_and_email_are_rejected(self) -> None:
        issues = sensitive(
            "Contact Sab" + "ri at person@" + "real-company.test for access.",
            "skills/example/SKILL.md",
            False,
        )
        self.assertTrue(any("owner-identifying" in issue for issue in issues))
        self.assertTrue(any("email" in issue for issue in issues))

    def test_fictional_contact_is_allowed(self) -> None:
        self.assertEqual(
            [],
            sensitive("Fictional contact: person@example.com.", "fixtures/example.md", False),
        )

    def test_private_key_and_token_are_rejected(self) -> None:
        issues = sensitive(
            "-----BEGIN " + "PRIVATE KEY-----\nTOKEN=ghp_" + "a" * 32,
            "skills/example/fixture.txt",
            False,
        )
        self.assertTrue(any("credential" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
