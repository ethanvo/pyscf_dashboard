# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time terminal dashboard (TUI) for monitoring SCF convergence during quantum chemistry calculations with PySCF. Displays live metrics as a Hartree-Fock/RHF calculation runs on an Aspirin molecule (C₉H₈O₄, 6-31G basis).

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Terminal 1: Run mock RHF calculation (writes to pyscf_run.log, 2s delay per cycle)
python3 mock_calc.py

# Terminal 2: Launch the live dashboard
python3 dashboard.py
```

## Architecture

Three-module pipeline:

```
mock_calc.py → pyscf_run.log → parser.py → dashboard.py
```

- **`mock_calc.py`**: Runs a real PySCF RHF calculation on Aspirin with a 2-second sleep per SCF cycle so the dashboard can observe convergence in real time. Streams verbose output to `pyscf_run.log`.
- **`parser.py`**: Regex-based parser for PySCF's standard `cycle= N E= ... delta_E= ... |g|= ... |ddm|= ...` log format. Key functions: `parse_log(path)` for full analysis and `get_new_log_lines(path, offset)` for incremental reads using byte offsets.
- **`dashboard.py`**: Textual TUI app. Polls `pyscf_run.log` every 1 second via `set_interval`. Renders convergence plots (log-scale |g| and |ΔE|), metric cards, molecule info, and a scrolling log tail.

## Key Details

- The dashboard polls on a 1.0s interval (`POLL_INTERVAL`) and swallows exceptions to avoid crashes during live updates.
- DIIS error (`|g|`) color-codes convergence: red > 1e-3, yellow < 1e-3, green < 1e-5.
- `pandas` and `watchdog` are listed in requirements.txt but not used in the current code.
- No test suite exists yet.
