"""Sondas de regresión para la configuración de pytest (#80, S2/S3/S4)."""
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _correr(*args):
    """Shell limpio simulado: sin clave ni settings heredados del pytest padre."""
    entorno = {**os.environ}
    for clave in ("DJANGO_SECRET_KEY", "DJANGO_SETTINGS_MODULE"):
        entorno.pop(clave, None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args], cwd=RAIZ, env=entorno,
        capture_output=True, text=True,
    )


def test_cov_documentado_mide_solo_apps(tmp_path):
    """S3: el comando documentado NO debe medir los tests ( blocker del verify)."""
    json_cov = tmp_path / "cov.json"
    r = _correr("--cov=apps", f"--cov-report=json:{json_cov}", "--collect-only", "-q")
    assert r.returncode == 0, r.stdout + r.stderr
    medidos = list(json.loads(json_cov.read_text())["files"])
    fuera = [f for f in medidos if not f.startswith("apps/")]
    assert fuera == [], f"--cov=apps midió fuera de apps/: {fuera[:5]}"


def test_arranca_sin_django_secret_key_y_no_la_filtra():
    r = _correr("--collect-only", "-q")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DJANGO_SECRET_KEY" not in r.stdout + r.stderr


def test_strict_markers_sin_registro_falla():
    r = _correr("--collect-only", "-q", "-o", "markers=")
    assert r.returncode == 3, r.stdout + r.stderr
