#!/usr/bin/env bash
# ============================================================================
# validate-site.sh
# ----------------------------------------------------------------------------
# Validates the rendered HTML pages of the SIP 2026 docs site before commit.
#
# Usage:
#   cd /path/to/html-pages
#   ./scripts/validate-site.sh
#
# Requirements:
#   - bash 4+
#   - python3 (stdlib only: html.parser)
#   - find, grep, awk
#
# Exit codes:
#   0  All checks passed (no errors, no warnings)
#   1  At least one error was found
#   2  No errors but at least one warning
#
# Checks:
#   1. Broken internal anchors  (<a href="#x"> without matching id="x")
#   2. Broken site-internal links (<a href="other.html"> not on disk)
#   3. Broken assets (img src / link href / script src under assets/)
#   4. Banner / branding consistency on practica-*.html
#        - exactly one <header class="unlu-header">
#        - exactly one .banner-pill matching "TP N" or "TP N · PARTE M"
#        - a breadcrumb (.page-breadcrumb)
#   5. Forgotten placeholders (TODO / FIXME / XXX / [pegar invite acá] ...)
#   6. Quick CSS sanity check on assets/style.css (balanced braces, no ":;")
# ============================================================================

set -euo pipefail

# ---------- colors ----------
if [[ -t 1 ]]; then
  RED=$'\033[0;31m'
  YELLOW=$'\033[0;33m'
  GREEN=$'\033[0;32m'
  BLUE=$'\033[0;34m'
  BOLD=$'\033[1m'
  NC=$'\033[0m'
else
  RED=""; YELLOW=""; GREEN=""; BLUE=""; BOLD=""; NC=""
fi

ERRORS=0
WARNINGS=0

err()  { printf '%s\n' "${RED}❌ ERROR:${NC}  $*"; ERRORS=$((ERRORS + 1)); }
warn() { printf '%s\n' "${YELLOW}⚠️  WARN:${NC}  $*"; WARNINGS=$((WARNINGS + 1)); }
ok()   { printf '%s\n' "${GREEN}✅ OK:${NC}    $*"; }
info() { printf '%s\n' "${BLUE}ℹ️  INFO:${NC}  $*"; }
hdr()  { printf '\n%s\n' "${BOLD}== $* ==${NC}"; }

# ---------- locate site root ----------
# Resolve script dir, then assume site root is the parent (scripts/..).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SITE_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${SITE_ROOT}"

info "Site root: ${SITE_ROOT}"

# ---------- collect rendered HTMLs ----------
shopt -s nullglob
HTML_FILES=( index.html practica-*.html )
shopt -u nullglob

if [[ ${#HTML_FILES[@]} -eq 0 ]]; then
  err "No rendered HTML files (index.html / practica-*.html) found in ${SITE_ROOT}"
  exit 1
fi

info "HTMLs to validate: ${#HTML_FILES[@]} (${HTML_FILES[*]})"

# ---------- python parser helper ----------
# Reads HTML files passed as args and emits one record per line:
#   FILE\tKIND\tVALUE\tLINE
# KIND ∈ {ID, ANCHOR, LINK, IMG, CSS, SCRIPT}
read -r -d '' PY_PARSER <<'PYEOF' || true
import sys
from html.parser import HTMLParser

class Collector(HTMLParser):
    def __init__(self, fname):
        super().__init__(convert_charrefs=True)
        self.fname = fname
        self.records = []

    def _emit(self, kind, value):
        line, _col = self.getpos()
        # Tab-separated; strip tabs/newlines from value defensively.
        value = (value or "").replace("\t", " ").replace("\n", " ")
        self.records.append(f"{self.fname}\t{kind}\t{value}\t{line}")

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        # Any element with id="..."
        if "id" in d and d["id"]:
            self._emit("ID", d["id"])

        if tag == "a":
            href = d.get("href")
            if href:
                if href.startswith("#"):
                    self._emit("ANCHOR", href[1:])
                elif "://" not in href and not href.startswith(("mailto:", "tel:", "javascript:", "data:")):
                    self._emit("LINK", href)
        elif tag == "img":
            src = d.get("src")
            if src and "://" not in src and not src.startswith("data:"):
                self._emit("IMG", src)
        elif tag == "link":
            href = d.get("href")
            if href and "://" not in href and not href.startswith("data:"):
                self._emit("CSS", href)
        elif tag == "script":
            src = d.get("src")
            if src and "://" not in src and not src.startswith("data:"):
                self._emit("SCRIPT", src)

for path in sys.argv[1:]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
    except Exception as e:
        sys.stderr.write(f"PARSE-FAIL\t{path}\t{e}\n")
        continue
    p = Collector(path)
    try:
        p.feed(data)
        p.close()
    except Exception as e:
        sys.stderr.write(f"PARSE-FAIL\t{path}\t{e}\n")
        continue
    for rec in p.records:
        print(rec)
PYEOF

# Run parser once for all files; capture to a temp file.
PARSE_OUT="$(mktemp)"
trap 'rm -f "${PARSE_OUT}"' EXIT

if ! python3 -c "${PY_PARSER}" "${HTML_FILES[@]}" >"${PARSE_OUT}"; then
  err "HTML parser failed; aborting."
  exit 1
fi

# ---------- 1) broken internal anchors ----------
hdr "1) Internal anchors"

# Build per-file id sets, then verify every anchor.
# We do it in a single awk pass for speed.
BROKEN_ANCHORS="$(
  awk -F'\t' '
    {
      file=$1; kind=$2; val=$3; line=$4;
      if (kind == "ID")     ids[file SUBSEP val] = 1;
      if (kind == "ANCHOR") { anc_file[NR]=file; anc_val[NR]=val; anc_line[NR]=line; anc_n=NR; }
    }
    END {
      for (i=1; i<=anc_n; i++) {
        if (anc_file[i] == "") continue;
        v = anc_val[i];
        # Empty fragment (#) is harmless ("scroll to top"); skip.
        if (v == "") continue;
        if (!((anc_file[i] SUBSEP v) in ids)) {
          printf "%s:%s\t#%s\n", anc_file[i], anc_line[i], v;
        }
      }
    }
  ' "${PARSE_OUT}"
)"

if [[ -n "${BROKEN_ANCHORS}" ]]; then
  while IFS=$'\t' read -r where target; do
    err "Broken anchor ${target} at ${where}"
  done <<< "${BROKEN_ANCHORS}"
else
  ok "All internal anchors resolve."
fi

# ---------- 2) broken site-internal links ----------
hdr "2) Site-internal links"

LINK_BROKEN=0
while IFS=$'\t' read -r file kind value line; do
  [[ "${kind}" == "LINK" ]] || continue

  # Strip query/fragment for filesystem check.
  path="${value%%#*}"
  path="${path%%\?*}"

  # Skip empty (was pure fragment, handled in step 1).
  [[ -z "${path}" ]] && continue

  # Skip absolute paths (none should appear, but defensive).
  [[ "${path}" == /* ]] && continue

  if [[ ! -e "${path}" && ! -d "${path}" ]]; then
    err "Broken site link '${value}' in ${file}:${line}"
    LINK_BROKEN=$((LINK_BROKEN + 1))
  fi
done < "${PARSE_OUT}"

if [[ ${LINK_BROKEN} -eq 0 ]]; then
  ok "All site-internal links resolve."
fi

# ---------- 3) broken assets (img / link / script) ----------
hdr "3) Assets (img / link / script)"

ASSET_BROKEN=0
while IFS=$'\t' read -r file kind value line; do
  case "${kind}" in
    IMG|CSS|SCRIPT) ;;
    *) continue ;;
  esac

  # We only enforce assets/* (other relative paths handled in step 2).
  path="${value%%#*}"
  path="${path%%\?*}"

  [[ -z "${path}" ]] && continue
  [[ "${path}" == /* ]] && continue

  if [[ "${path}" == assets/* || "${path}" == ./assets/* ]]; then
    if [[ ! -f "${path#./}" ]]; then
      err "Missing asset '${value}' referenced from ${file}:${line}"
      ASSET_BROKEN=$((ASSET_BROKEN + 1))
    fi
  else
    # Non-assets relative file (e.g. favicon.ico): warn if missing.
    if [[ ! -e "${path#./}" ]]; then
      warn "Missing file '${value}' referenced from ${file}:${line}"
    fi
  fi
done < "${PARSE_OUT}"

if [[ ${ASSET_BROKEN} -eq 0 ]]; then
  ok "All assets present."
fi

# ---------- 4) banner / branding consistency ----------
hdr "4) Banner / branding (practica-*.html)"

BANNER_RE='^TP[[:space:]]+[0-9]+([[:space:]]+·[[:space:]]+PARTE[[:space:]]+[0-9]+)?$'
shopt -s nullglob
PRACTICAS=( practica-*.html )
shopt -u nullglob

if [[ ${#PRACTICAS[@]} -eq 0 ]]; then
  warn "No practica-*.html files found; skipping branding check."
else
  for f in "${PRACTICAS[@]}"; do
    # Count <header class="unlu-header"> occurrences.
    n_header=$(grep -cE '<header[^>]*class="[^"]*unlu-header[^"]*"' "${f}" || true)
    if [[ "${n_header}" -ne 1 ]]; then
      err "${f}: expected exactly 1 <header class=\"unlu-header\">, found ${n_header}"
    fi

    # Count .banner-pill spans and validate text.
    pill_lines=$(grep -nE 'class="[^"]*banner-pill[^"]*"' "${f}" || true)
    n_pill=$(printf '%s\n' "${pill_lines}" | grep -c . || true)
    if [[ "${n_pill}" -ne 1 ]]; then
      err "${f}: expected exactly 1 .banner-pill, found ${n_pill}"
    else
      pill_text=$(printf '%s' "${pill_lines}" \
        | sed -E 's/.*<span[^>]*class="[^"]*banner-pill[^"]*"[^>]*>([^<]*)<\/span>.*/\1/' \
        | head -n1 \
        | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
      if [[ ! "${pill_text}" =~ ${BANNER_RE} ]]; then
        err "${f}: .banner-pill text '${pill_text}' does not match 'TP N' or 'TP N · PARTE M'"
      fi
    fi

    # Breadcrumb presence.
    if ! grep -qE 'class="page-breadcrumb"' "${f}"; then
      err "${f}: missing breadcrumb (<nav class=\"page-breadcrumb\">)"
    else
      # Breadcrumb should contain a .current span with the page name (non-empty).
      if ! grep -qE '<span class="current">[^<]+</span>' "${f}"; then
        warn "${f}: breadcrumb has no <span class=\"current\">PageName</span>"
      fi
    fi
  done
  ok "Branding check completed for ${#PRACTICAS[@]} practica file(s)."
fi

# ---------- 5) forgotten placeholders ----------
hdr "5) Forgotten placeholders"

# Patterns that should never ship.
PLACEHOLDER_PATTERNS=(
  '\[pegar[^]]*\]'
  '\[TODO[^]]*\]'
  '\[FIXME[^]]*\]'
  '\bTODO\b'
  '\bFIXME\b'
  '\bXXX\b'
  'lorem ipsum'
)

PLACE_FOUND=0
for pat in "${PLACEHOLDER_PATTERNS[@]}"; do
  # -I = skip binary, -n = line numbers, -E = ERE, -i = case-insensitive (covers TODO/Todo/todo).
  matches=$(grep -InE "${pat}" -- *.html 2>/dev/null || true)
  if [[ -n "${matches}" ]]; then
    while IFS= read -r line; do
      err "Placeholder '${pat}' -> ${line}"
      PLACE_FOUND=$((PLACE_FOUND + 1))
    done <<< "${matches}"
  fi
done

if [[ ${PLACE_FOUND} -eq 0 ]]; then
  ok "No forgotten placeholders found."
fi

# ---------- 6) quick CSS sanity ----------
hdr "6) CSS sanity (assets/style.css)"

CSS=assets/style.css
if [[ ! -f "${CSS}" ]]; then
  warn "${CSS} not found; skipping CSS check."
else
  # Strip /* ... */ comments before brace counting (works across lines).
  stripped=$(python3 - "${CSS}" <<'PY'
import re, sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    src = f.read()
src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
sys.stdout.write(src)
PY
)
  open_braces=$(printf '%s' "${stripped}" | tr -cd '{' | wc -c)
  close_braces=$(printf '%s' "${stripped}" | tr -cd '}' | wc -c)
  if [[ "${open_braces}" -ne "${close_braces}" ]]; then
    err "${CSS}: unbalanced braces ({=${open_braces}, }=${close_braces})"
  else
    ok "${CSS}: braces balanced ({=${open_braces}, }=${close_braces})."
  fi

  # Detect ":;"  (declaration with empty value), ignoring strings is a stretch
  # for grep; this is a best-effort warning.
  empty_decl=$(grep -nE ':[[:space:]]*;' "${CSS}" || true)
  if [[ -n "${empty_decl}" ]]; then
    while IFS= read -r line; do
      warn "${CSS}: empty declaration -> ${line}"
    done <<< "${empty_decl}"
  fi
fi

# ---------- summary ----------
hdr "Summary"

n_html=${#HTML_FILES[@]}
if [[ ${ERRORS} -gt 0 ]]; then
  printf '%s\n' "${RED}${BOLD}❌ ${ERRORS} error(s), ${WARNINGS} warning(s) across ${n_html} HTML file(s).${NC}"
  exit 1
elif [[ ${WARNINGS} -gt 0 ]]; then
  printf '%s\n' "${YELLOW}${BOLD}⚠️  0 errors, ${WARNINGS} warning(s) across ${n_html} HTML file(s).${NC}"
  exit 2
else
  printf '%s\n' "${GREEN}${BOLD}✅ ${n_html} HTML file(s) validated, 0 errors, 0 warnings.${NC}"
  exit 0
fi
