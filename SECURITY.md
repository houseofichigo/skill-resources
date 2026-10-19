# Security

Report suspected vulnerabilities privately to House of Ichigo before opening a public
issue. Do not include secrets, private client material or a working exploit in a public
report.

Dependency-specific security constraints belong in the relevant `SKILL.md` or a
linked file under its `references/` directory, so the public package stays complete
without repository wrappers inside the skill folder.

Before reporting, remove credentials and unnecessary personal data from logs and
screenshots. If a real credential appears in any commit, rotate it immediately;
deleting the current file or rewriting Git history is not sufficient by itself.

Public release controls and their limits are documented in
[`RELEASE-SAFETY.md`](RELEASE-SAFETY.md).
