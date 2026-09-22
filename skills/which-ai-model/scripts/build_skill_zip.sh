#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/which-ai-model-skill.XXXXXXXX")"

cleanup() {
  rm -rf -- "${WORK_DIR:?}"
}
trap cleanup EXIT

mkdir -p "${WORK_DIR}/which-ai-model/references" "${ROOT_DIR}/dist"
cp "${ROOT_DIR}/SKILL.md" "${WORK_DIR}/which-ai-model/SKILL.md"
cp "${ROOT_DIR}"/references/*.md "${WORK_DIR}/which-ai-model/references/"

(
  cd "${WORK_DIR}"
  zip -X -qr "${ROOT_DIR}/dist/which-ai-model.zip" which-ai-model
)

echo "Wrote ${ROOT_DIR}/dist/which-ai-model.zip"
