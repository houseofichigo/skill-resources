from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_catalog import archive_member_is_safe, find_sensitive_issues  # noqa: E402


class ReleaseSafetyTests(unittest.TestCase):
    def test_archive_path_traversal_is_rejected(self) -> None:
        self.assertFalse(archive_member_is_safe("../secret.txt"))
        self.assertFalse(archive_member_is_safe("skill/../../secret.txt"))
        self.assertFalse(archive_member_is_safe("/absolute/path"))
        self.assertFalse(archive_member_is_safe("skill\\secret.txt"))
        self.assertTrue(archive_member_is_safe("skill/SKILL.md"))

    def test_company_runtime_coupling_is_rejected(self) -> None:
        issues = find_sensitive_issues(
            "Read workspaces/hoi-" + "company and then use House of " + "Ichigo defaults.",
            "skills/example/SKILL.md",
            False,
        )
        self.assertTrue(any("runtime" in issue for issue in issues))
        self.assertTrue(any("publisher coupling" in issue for issue in issues))

    def test_real_identity_and_email_are_rejected(self) -> None:
        issues = find_sensitive_issues(
            "Contact Sab" + "ri at person@" + "real-company.test for access.",
            "skills/example/SKILL.md",
            False,
        )
        self.assertTrue(any("owner-identifying" in issue for issue in issues))
        self.assertTrue(any("email" in issue for issue in issues))

    def test_fictional_contact_is_allowed(self) -> None:
        self.assertEqual(
            [],
            find_sensitive_issues(
                "Fictional example: Northstar Analytics, person@example.com.",
                "fixtures/fictional.md",
                False,
            ),
        )

    def test_private_key_and_token_are_rejected(self) -> None:
        private_key = "-----BEGIN " + "PRIVATE KEY-----"
        token = "ghp_" + "a" * 32
        issues = find_sensitive_issues(
            f"{private_key}\nTOKEN={token}", "skills/example/fixture.txt", False
        )
        self.assertTrue(any("credential" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
