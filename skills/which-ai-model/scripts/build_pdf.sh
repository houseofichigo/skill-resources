#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_PPTX="${ROOT_DIR}/presentation/which-ai-model-explained.pptx"
TARGET_PDF="${ROOT_DIR}/presentation/which-ai-model-explained.pdf"
SOFFICE_BIN="${SOFFICE_BIN:-soffice}"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/which-ai-model-pdf.XXXXXXXX")"

cleanup() {
  rm -rf -- "${WORK_DIR:?}"
}
trap cleanup EXIT

for command in unzip zip perl; do
  command -v "${command}" >/dev/null || {
    echo "Missing required command: ${command}" >&2
    exit 1
  }
done

[[ -f "${SOURCE_PPTX}" ]] || {
  echo "Build the PPTX before exporting the PDF." >&2
  exit 1
}

mkdir -p "${WORK_DIR}/pptx"
unzip -q "${SOURCE_PPTX}" -d "${WORK_DIR}/pptx"

# The editable deck keeps the supplied Manrope, Inter Tight and JetBrains Mono
# typefaces. LibreOffice does not consume the WOFF2 files embedded for the web
# artifact, so its PDF export uses metrically compatible bundled fallbacks.
find "${WORK_DIR}/pptx" -type f \( -name '*.xml' -o -name '*.rels' \) \
  -exec perl -pi -e \
  's/Manrope/Rubik/g; s/Inter Tight/Noto Sans/g; s/JetBrains Mono/DejaVu Sans Mono/g' \
  {} +

(
  cd "${WORK_DIR}/pptx"
  zip -X -qr "${WORK_DIR}/which-ai-model-pdf-source.pptx" .
)

"${SOFFICE_BIN}" --headless --convert-to pdf --outdir "${WORK_DIR}" \
  "${WORK_DIR}/which-ai-model-pdf-source.pptx"

cp "${WORK_DIR}/which-ai-model-pdf-source.pdf" "${TARGET_PDF}"
echo "Wrote ${TARGET_PDF}"
