# Quantum Cruncher // PySCF Terminal Telemetry

A real-time terminal dashboard for monitoring SCF convergence during quantum chemistry calculations. Built with [Textual](https://github.com/Textualize/textual) and [PySCF](https://pyscf.org/).

## Demo

The included mock calculation runs a Restricted Hartree-Fock (RHF/6-31G) calculation on Aspirin (C₉H₈O₄, 21 atoms, 112 electrons) with a 2-second pause per SCF cycle so convergence can be observed live in the dashboard.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the calculation and dashboard in two separate terminals:

```bash
# Terminal 1 — start the SCF calculation
python3 mock_calc.py

# Terminal 2 — launch the dashboard
python3 dashboard.py
```

Press `q` or `Ctrl+C` to quit the dashboard.

## Dashboard Layout

- **Metric cards** — current SCF cycle, total energy (Hartree), and DIIS error
- **Convergence plot** — log₁₀ of |g| (gradient/DIIS error) and |ΔE| vs. cycle number
- **Molecule pane** — Aspirin structure info and Cartesian coordinates
- **Log tail** — live stream of the last lines written to `pyscf_run.log`

The DIIS error card is color-coded: red (> 1e-3), yellow (< 1e-3), green (< 1e-5, near convergence).

## How It Works

`mock_calc.py` runs a real PySCF calculation and writes verbose output to `pyscf_run.log`. `parser.py` uses regex to extract per-cycle metrics from PySCF's standard log format. `dashboard.py` polls the log file every second and updates all widgets in real time.
