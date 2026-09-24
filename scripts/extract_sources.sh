#!/usr/bin/env bash
# Extracts source PDF text into sources/text/ (gitignored) via pdftotext -layout.
# -layout preserves table structure; without it the scenario/target tables come out
# as unreadable mush. Re-run any time; output is regenerated, not diffed.
set -euo pipefail

SOURCE_DIR="${LEXO_SOURCE_DIR:-$HOME/Downloads/Shared-Public-20260923T050713Z-1-001/Shared-Public/Reports}"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/sources/text"

mkdir -p "$OUT_DIR"

extract() {
  local pdf="$1" name="$2"
  if [[ ! -f "$pdf" ]]; then
    echo "missing: $pdf" >&2
    exit 1
  fi
  pdftotext -layout "$pdf" "$OUT_DIR/$name.txt"
  echo "extracted $name.txt"
}

extract "$SOURCE_DIR/NVDA/NVDA-memo.pdf"                          nvda-memo
extract "$SOURCE_DIR/NVDA/NVDA-factor-report.pdf"                 nvda-factor
extract "$SOURCE_DIR/NVDA/NVDA-theme-report.pdf"                  nvda-theme
extract "$SOURCE_DIR/AMZN/amazon-memo.pdf"                        amzn-memo
extract "$SOURCE_DIR/AMZN/amazon-Factor_Research_Base_Case.pdf"   amzn-factor
extract "$SOURCE_DIR/AMZN/amazon-theme-report.pdf"                amzn-theme
