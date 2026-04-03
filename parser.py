"""
Parser for PySCF SCF log files.

Extracts cycle-by-cycle convergence data from the standard PySCF RHF log format:
    cycle= N E= -XXX  delta_E= XXX  |g|= XXX  |ddm|= XXX

Public API:
    parse_log(path)           -> dict with full history + latest values
    get_new_log_lines(path, offset) -> (new_lines, new_offset)
"""

from __future__ import annotations

import math
import re
from pathlib import Path

# Matches PySCF's logger.info format from pyscf/scf/hf.py:
#   'cycle= %d E= %.15g  delta_E= %4.3g  |g|= %4.3g  |ddm|= %4.3g'
_CYCLE_RE = re.compile(
    r"cycle=\s*(\d+)\s+"
    r"E=\s*([-\d.eE+]+)\s+"
    r"delta_E=\s*([-\d.eE+\-]+)\s+"
    r"\|g\|=\s*([\d.eE+\-]+)\s+"
    r"\|ddm\|=\s*([\d.eE+\-]+)"
)

_CONVERGED_RE = re.compile(r"converged SCF energy\s*=\s*([-\d.eE+]+)")


def _f(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _log10(v: float | None) -> float | None:
    if v is None:
        return None
    try:
        return math.log10(v) if v > 0 else None
    except (ValueError, OverflowError):
        return None


def parse_log(log_path: Path | str) -> dict:
    """
    Parse a PySCF SCF log file.

    Returns a dict:
      cycles      : list[int]
      energies    : list[float]
      delta_e     : list[float]   — signed ΔE per cycle
      diis_error  : list[float]   — |g| gradient norm
      ddm         : list[float]   — |ddm| density-matrix change
      log_diis    : list[float|None]  — log10(|g|) for plotting
      log_delta_e : list[float|None]  — log10(|delta_E|) for plotting
      latest      : dict          — values from most recent cycle, or {}
      converged   : bool
      final_energy: float | None
    """
    log_path = Path(log_path)
    cycles, energies, delta_e, diis_error, ddm = [], [], [], [], []
    converged = False
    final_energy = None

    if not log_path.exists():
        return _build(cycles, energies, delta_e, diis_error, ddm, converged, final_energy)

    try:
        text = log_path.read_text(errors="replace")
    except OSError:
        return _build(cycles, energies, delta_e, diis_error, ddm, converged, final_energy)

    for m in _CYCLE_RE.finditer(text):
        cyc = int(m.group(1))
        e   = _f(m.group(2))
        de  = _f(m.group(3))
        g   = _f(m.group(4))
        d   = _f(m.group(5))
        if None not in (e, de, g, d):
            cycles.append(cyc)
            energies.append(e)
            delta_e.append(de)
            diis_error.append(g)
            ddm.append(d)

    cm = _CONVERGED_RE.search(text)
    if cm:
        converged = True
        final_energy = _f(cm.group(1))

    return _build(cycles, energies, delta_e, diis_error, ddm, converged, final_energy)


def _build(cycles, energies, delta_e, diis_error, ddm, converged, final_energy) -> dict:
    latest: dict = {}
    if cycles:
        latest = {
            "cycle":      cycles[-1],
            "energy":     energies[-1],
            "delta_e":    delta_e[-1],
            "diis_error": diis_error[-1],
            "ddm":        ddm[-1],
        }

    log_diis    = [_log10(v) for v in diis_error]
    log_delta_e = [_log10(abs(v)) if v != 0 else None for v in delta_e]

    return {
        "cycles":       cycles,
        "energies":     energies,
        "delta_e":      delta_e,
        "diis_error":   diis_error,
        "ddm":          ddm,
        "log_diis":     log_diis,
        "log_delta_e":  log_delta_e,
        "latest":       latest,
        "converged":    converged,
        "final_energy": final_energy,
    }


def get_new_log_lines(log_path: Path | str, offset: int) -> tuple[list[str], int]:
    """
    Read any bytes added to *log_path* since *offset*.
    Returns (list_of_new_lines, new_byte_offset).
    """
    log_path = Path(log_path)
    if not log_path.exists():
        return [], offset
    try:
        with open(log_path, "r", errors="replace") as fh:
            fh.seek(offset)
            chunk = fh.read()
            new_offset = fh.tell()
        return chunk.splitlines(), new_offset
    except OSError:
        return [], offset
