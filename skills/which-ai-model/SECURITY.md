# Security

## Reporting

Please report a suspected vulnerability privately to House of Ichigo before
opening a public issue. Do not include secrets, private client material, or a
working exploit in a public report.

## Build dependency scope

The checked-in skill, infographic and presentation contain no runtime service
and make no network calls. `pptxgenjs` is a development-only dependency used to
regenerate the teaching deck from checked-in text and layout constants.

As of 22 September 2026, npm reports two high-severity denial-of-service
advisories against the transitive `image-size` package used by PptxGenJS:

- GHSA-w3rx-r6r6-pgpr — malformed ICNS input can cause an infinite loop.
- GHSA-5p2g-fcmc-qvqq — malformed JXL or HEIF input can cause an infinite loop.

The deck builder does not read external or user-supplied images, and therefore
does not expose the affected parsers to untrusted input. Do not extend the build
script to accept untrusted images while these advisories remain unresolved.

GitHub's advisory database currently lists no patched `image-size` release. Pin
the present dependency versions, monitor the upstream advisory, and upgrade as
soon as PptxGenJS adopts a patched parser. Re-run `npm audit` after every lockfile
change.
