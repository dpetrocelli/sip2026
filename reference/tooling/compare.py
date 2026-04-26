#!/usr/bin/env python3
"""Comparador alumno vs reference — vara de corrección automática del TP SIP 2026.

Toma el path a un repo de alumno (clonado localmente) y produce un reporte
markdown con análisis estructural, calidad de código y comparación contra el
golden output. NO ejecuta código del alumno (todo es estático).

Uso:
    python compare.py --student /path/al/repo --out reports/<repo>.md

Opciones:
    --reference  /home/.../reference  (default: parent del directorio del script)
    --student    path al repo del alumno (obligatorio)
    --out        path del reporte markdown a generar (default: stdout)

Idioma del reporte: español argentino, formato markdown.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ────────────────────────────────────────────────
# Modelos
# ────────────────────────────────────────────────

REQUIRED_JSON_FIELDS = {
    "titulo": str,
    "precio": (int, float, type(None)),
    "link": (str, type(None)),
    "tienda_oficial": (str, type(None)),
    "envio_gratis": bool,
    "cuotas_sin_interes": (str, type(None)),
}

EXPECTED_PRODUCTS = ["bicicleta_rodado_29", "iphone_16_pro_max", "geforce_5090"]


@dataclass
class StackInfo:
    language: str
    test_framework: str | None
    package_files: list[str]


@dataclass
class HitStatus:
    hit: int
    present: bool
    folder: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class CodeQuality:
    has_explicit_waits: bool
    sleep_count: int
    has_centralized_selectors: bool
    has_logger: bool
    has_browser_factory: bool
    has_dockerfile: bool
    has_ci_workflow: bool
    has_tests: bool
    secrets_at_risk: list[str]


@dataclass
class JsonValidation:
    file: str
    found: bool
    is_array: bool
    count: int
    schema_ok: bool
    schema_errors: list[str]
    fields_complete: dict[str, int]
    sample: dict | None = None


@dataclass
class ComparisonResult:
    student_path: Path
    repo_name: str
    stack: StackInfo
    hits: list[HitStatus]
    quality: CodeQuality
    json_outputs: list[JsonValidation]
    score_per_criterion: dict[str, tuple[int, int]]
    score_total: int


# ────────────────────────────────────────────────
# Detección de stack
# ────────────────────────────────────────────────


def detect_stack(repo: Path) -> StackInfo:
    files = {p.name for p in repo.rglob("*") if p.is_file() and ".git/" not in str(p)}
    package_files = []
    if "requirements.txt" in files or "pyproject.toml" in files or "Pipfile" in files:
        lang = "Python"
        if "pytest.ini" in files or "conftest.py" in files or _grep_in_files(repo, "pytest"):
            tf = "pytest"
        else:
            tf = None
        package_files = [n for n in ["requirements.txt", "pyproject.toml", "Pipfile"] if n in files]
    elif "package.json" in files:
        lang = "Node.js"
        tf = "jest" if _grep_in_files(repo, "jest") else None
        package_files = ["package.json"]
    elif "pom.xml" in files:
        lang = "Java/Maven"
        tf = "junit" if _grep_in_files(repo, "junit") else None
        package_files = ["pom.xml"]
    elif "build.gradle" in files or "build.gradle.kts" in files:
        lang = "Java/Gradle"
        tf = "junit" if _grep_in_files(repo, "junit") else None
        package_files = [n for n in ["build.gradle", "build.gradle.kts"] if n in files]
    else:
        # Fallback: detectar por extensión
        py_count = sum(1 for p in repo.rglob("*.py") if ".git/" not in str(p))
        js_count = sum(
            1 for p in repo.rglob("*.js") if ".git/" not in str(p) and "node_modules/" not in str(p)
        )
        java_count = sum(1 for p in repo.rglob("*.java") if ".git/" not in str(p))
        if py_count > js_count and py_count > java_count:
            lang = "Python (sin requirements.txt)"
        elif js_count > java_count:
            lang = "Node.js (sin package.json)"
        elif java_count:
            lang = "Java (sin pom.xml)"
        else:
            lang = "Desconocido"
        tf = None
    return StackInfo(language=lang, test_framework=tf, package_files=package_files)


def _grep_in_files(repo: Path, term: str) -> bool:
    try:
        out = subprocess.run(
            ["grep", "-r", "-l", term, str(repo)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return bool(out.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ────────────────────────────────────────────────
# Detección de Hits
# ────────────────────────────────────────────────


def detect_hits(repo: Path) -> list[HitStatus]:
    hits = []
    for n in range(1, 9):
        candidates = [
            repo / f"hit{n}",
            repo / f"HIT{n}",
            repo / f"Hit{n}",
            repo / f"hit_{n}",
        ]
        present = any(p.is_dir() and any(p.iterdir()) for p in candidates)
        folder = next((str(p.relative_to(repo)) for p in candidates if p.is_dir()), None)
        notes = []
        if present and folder:
            full = repo / folder
            if not (full / "README.md").exists() and not (full / "readme.md").exists():
                notes.append("sin README")
        hits.append(HitStatus(hit=n, present=present, folder=folder, notes=notes))
    return hits


# ────────────────────────────────────────────────
# Análisis de calidad
# ────────────────────────────────────────────────


def analyze_quality(repo: Path, stack: StackInfo) -> CodeQuality:
    code_files = list(repo.rglob("*.py")) + list(repo.rglob("*.js")) + list(repo.rglob("*.java"))
    code_files = [
        p
        for p in code_files
        if not any(
            x in str(p)
            for x in (".git/", "node_modules/", "target/", "__pycache__/", ".venv/", "/venv/")
        )
    ]

    sleep_count = 0
    has_explicit_waits = False
    for f in code_files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Sleep patterns por lenguaje
        sleep_count += len(re.findall(r"\btime\.sleep\s*\(", txt))
        sleep_count += len(re.findall(r"\bThread\.sleep\s*\(", txt))
        sleep_count += len(re.findall(r"setTimeout\s*\(", txt))
        if re.search(r"WebDriverWait|expected_conditions|ExpectedConditions|until\(", txt):
            has_explicit_waits = True

    selectors_centralized = bool(
        list(repo.rglob("selectors.py"))
        + list(repo.rglob("ml_selectors.py"))
        + list(repo.rglob("Selectors.java"))
        + list(repo.rglob("Locators.java"))
        + list(repo.rglob("selectors.js"))
    )

    has_logger = _has_pattern(code_files, r"logging\.getLogger|winston|slf4j|Logger\s*\.")
    has_browser_factory = _has_pattern(
        code_files, r"browser_factory|BrowserFactory|browser-factory|Driver(Factory|Manager)"
    )

    dockerfiles = list(repo.rglob("Dockerfile")) + list(repo.rglob("dockerfile"))
    has_dockerfile = any(d for d in dockerfiles if ".git/" not in str(d))
    has_ci = (repo / ".github" / "workflows").is_dir() and any(
        (repo / ".github" / "workflows").iterdir()
    )

    test_dirs = (
        list(repo.rglob("test_*.py"))
        + list(repo.rglob("*.test.js"))
        + list(repo.rglob("*Test.java"))
        + list(repo.rglob("conftest.py"))
    )
    has_tests = bool([t for t in test_dirs if ".git/" not in str(t)])

    secrets = _scan_secrets(repo)

    return CodeQuality(
        has_explicit_waits=has_explicit_waits,
        sleep_count=sleep_count,
        has_centralized_selectors=selectors_centralized,
        has_logger=has_logger,
        has_browser_factory=has_browser_factory,
        has_dockerfile=has_dockerfile,
        has_ci_workflow=has_ci,
        has_tests=has_tests,
        secrets_at_risk=secrets,
    )


def _has_pattern(files: list[Path], pattern: str) -> bool:
    rx = re.compile(pattern)
    for f in files:
        try:
            if rx.search(f.read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            continue
    return False


def _scan_secrets(repo: Path) -> list[str]:
    """Heurística simple — busca patrones obvios en archivos commiteados."""
    risky = []
    for f in repo.rglob("*"):
        if not f.is_file() or ".git/" in str(f):
            continue
        if f.name in {".env", ".env.local"} or f.suffix in {".pem", ".key"}:
            risky.append(str(f.relative_to(repo)))
    return risky


# ────────────────────────────────────────────────
# Validación de JSON output
# ────────────────────────────────────────────────


def validate_json_output(repo: Path) -> list[JsonValidation]:
    out = []
    for product in EXPECTED_PRODUCTS:
        # Buscar el archivo en cualquier subfolder llamado output/
        candidates = list(repo.rglob(f"{product}.json"))
        if not candidates:
            out.append(
                JsonValidation(
                    file=f"{product}.json",
                    found=False,
                    is_array=False,
                    count=0,
                    schema_ok=False,
                    schema_errors=["archivo no existe"],
                    fields_complete={},
                )
            )
            continue

        path = candidates[0]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            out.append(
                JsonValidation(
                    file=str(path.relative_to(repo)),
                    found=True,
                    is_array=False,
                    count=0,
                    schema_ok=False,
                    schema_errors=[f"JSON inválido: {exc}"],
                    fields_complete={},
                )
            )
            continue

        is_array = isinstance(data, list)
        count = len(data) if is_array else 0
        errors = []
        fields_complete = dict.fromkeys(REQUIRED_JSON_FIELDS, 0)
        sample = None

        if is_array and data:
            sample = data[0] if isinstance(data[0], dict) else None
            for item in data:
                if not isinstance(item, dict):
                    errors.append("contiene elementos que no son objetos")
                    continue
                for fname, ftype in REQUIRED_JSON_FIELDS.items():
                    if fname in item:
                        if item[fname] is not None and not isinstance(item[fname], ftype):
                            errors.append(
                                f"{fname}: tipo {type(item[fname]).__name__} no es {ftype}"
                            )
                        if item[fname] not in (None, "", False):
                            fields_complete[fname] += 1
                    else:
                        errors.append(f"falta campo '{fname}'")

        schema_ok = is_array and not errors
        # Dedup errors
        errors = list(dict.fromkeys(errors))[:5]

        out.append(
            JsonValidation(
                file=str(path.relative_to(repo)),
                found=True,
                is_array=is_array,
                count=count,
                schema_ok=schema_ok,
                schema_errors=errors,
                fields_complete=fields_complete,
                sample=sample,
            )
        )
    return out


# ────────────────────────────────────────────────
# Scoring (alineado con la rúbrica de Parte 1 + Parte 2)
# ────────────────────────────────────────────────


def compute_score(
    stack: StackInfo,
    hits: list[HitStatus],
    quality: CodeQuality,
    jsons: list[JsonValidation],
) -> tuple[dict[str, tuple[int, int]], int]:
    """Calcula score por criterio. Devuelve (dict[criterio→(ganado, total)], total)."""
    s: dict[str, tuple[int, int]] = {}

    # Hits 1-3 (Parte 1: 60% del peso)
    h1 = hits[0]
    h2 = hits[1]
    h3 = hits[2]

    s["Hit 1 — setup + búsqueda"] = (15 if h1.present else 0, 15)
    s["Hit 2 — Browser Factory"] = (
        25 if h2.present and quality.has_browser_factory else (10 if h2.present else 0),
        25,
    )
    s["Hit 3 — filtros DOM + screenshot"] = (
        30 if h3.present else 0,
        30,
    )

    # Calidad de código (15%)
    quality_score = 0
    if quality.has_explicit_waits:
        quality_score += 5
    if quality.sleep_count == 0:
        quality_score += 5
    elif quality.sleep_count < 3:
        quality_score += 3
    if quality.has_centralized_selectors:
        quality_score += 3
    if quality.has_logger:
        quality_score += 2
    s["Calidad de código"] = (quality_score, 15)

    # README + docs (10%)
    readme_score = 0
    h_with_readme = sum(1 for h in hits[:3] if h.present and "sin README" not in h.notes)
    if h_with_readme >= 3:
        readme_score = 10
    elif h_with_readme >= 2:
        readme_score = 6
    elif h_with_readme >= 1:
        readme_score = 3
    s["README/informe/video"] = (readme_score, 10)

    # Dockerfile (5%)
    s["Dockerfile (deseable)"] = (5 if quality.has_dockerfile else 0, 5)

    total_max = sum(v[1] for v in s.values())
    return s, total_max


# ────────────────────────────────────────────────
# Reporte markdown
# ────────────────────────────────────────────────


def render_report(c: ComparisonResult) -> str:
    lines = []
    lines.append(f"# Evaluación — {c.repo_name}")
    lines.append("")
    lines.append(f"**Path:** `{c.student_path}`")
    lines.append(f"**Stack:** {c.stack.language} (test: {c.stack.test_framework or 'sin tests'})")
    lines.append(f"**Package files:** {', '.join(c.stack.package_files) or 'ninguno'}")
    lines.append("")

    lines.append("## Hits implementados")
    for h in c.hits:
        check = "✅" if h.present else "❌"
        folder = f" (`{h.folder}`)" if h.folder else ""
        notes = f" — {', '.join(h.notes)}" if h.notes else ""
        lines.append(f"- {check} Hit #{h.hit}{folder}{notes}")
    lines.append("")

    lines.append("## Calidad de código")
    q = c.quality
    lines.append("| Check | Resultado |")
    lines.append("|-------|-----------|")
    lines.append(
        f"| Explicit waits (`WebDriverWait`/`expected_conditions`) | {'✅' if q.has_explicit_waits else '❌'} |"
    )
    lines.append(
        f"| Conteo de `sleep` (anti-pattern) | {'✅ 0' if q.sleep_count == 0 else f'⚠️ {q.sleep_count}'} |"
    )
    lines.append(
        f"| Selectores centralizados (módulo aparte) | {'✅' if q.has_centralized_selectors else '❌'} |"
    )
    lines.append(f"| Logger estructurado | {'✅' if q.has_logger else '❌'} |")
    lines.append(f"| Browser Factory | {'✅' if q.has_browser_factory else '❌'} |")
    lines.append(f"| Dockerfile presente | {'✅' if q.has_dockerfile else '❌'} |")
    lines.append(f"| CI workflow (.github/workflows/) | {'✅' if q.has_ci_workflow else '❌'} |")
    lines.append(f"| Tests presentes | {'✅' if q.has_tests else '❌'} |")
    lines.append(
        f"| Archivos `.env` o claves commiteadas | {'⚠️ ' + ', '.join(q.secrets_at_risk) if q.secrets_at_risk else '✅ ninguno'} |"
    )
    lines.append("")

    lines.append("## JSON output (Hit #4 — Parte 2)")
    if not any(j.found for j in c.json_outputs):
        lines.append("❌ Ningún archivo JSON de output encontrado.")
    else:
        lines.append(
            "| Archivo | Found | Array | Count | Schema OK | titulo | precio | link | tienda_oficial | envio_gratis | cuotas |"
        )
        lines.append(
            "|---------|:-----:|:-----:|------:|:---------:|-------:|-------:|-----:|---------------:|-------------:|-------:|"
        )
        for j in c.json_outputs:
            f = j.fields_complete
            lines.append(
                f"| `{j.file}` | {'✅' if j.found else '❌'} | "
                f"{'✅' if j.is_array else '❌'} | {j.count} | "
                f"{'✅' if j.schema_ok else '❌'} | "
                f"{f.get('titulo', 0)} | {f.get('precio', 0)} | {f.get('link', 0)} | "
                f"{f.get('tienda_oficial', 0)} | {f.get('envio_gratis', 0)} | {f.get('cuotas_sin_interes', 0)} |"
            )
        for j in c.json_outputs:
            if j.schema_errors:
                lines.append("")
                lines.append(f"**`{j.file}` — errores de schema:**")
                for e in j.schema_errors:
                    lines.append(f"  - {e}")
    lines.append("")

    lines.append("## Score (rúbrica Parte 1 — Hits 1-3)")
    lines.append("| Criterio | Score | Peso |")
    lines.append("|----------|------:|-----:|")
    won_total = 0
    max_total = 0
    for k, (w, m) in c.score_per_criterion.items():
        won_total += w
        max_total += m
        lines.append(f"| {k} | {w} | {m} |")
    lines.append(f"| **TOTAL** | **{won_total}** | **{max_total}** |")
    lines.append("")
    lines.append(f"**Score normalizado: {(won_total / max_total) * 100:.1f} / 100**")
    lines.append("")
    return "\n".join(lines)


# ────────────────────────────────────────────────
# Entrypoint
# ────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparador alumno vs reference")
    parser.add_argument("--student", required=True, type=Path, help="Path al repo del alumno")
    parser.add_argument(
        "--out", type=Path, default=None, help="Path al markdown de salida (default: stdout)"
    )
    args = parser.parse_args()

    repo = args.student.resolve()
    if not repo.is_dir():
        print(f"ERROR: {repo} no es un directorio", file=sys.stderr)
        return 2

    stack = detect_stack(repo)
    hits = detect_hits(repo)
    quality = analyze_quality(repo, stack)
    jsons = validate_json_output(repo)
    scores, _max = compute_score(stack, hits, quality, jsons)

    won_total = sum(v[0] for v in scores.values())
    result = ComparisonResult(
        student_path=repo,
        repo_name=repo.name,
        stack=stack,
        hits=hits,
        quality=quality,
        json_outputs=jsons,
        score_per_criterion=scores,
        score_total=won_total,
    )

    md = render_report(result)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
        print(f"Reporte: {args.out}")
    else:
        print(md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
