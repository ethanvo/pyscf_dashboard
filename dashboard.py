#!/usr/bin/env python3
"""
Quantum Cruncher // PySCF Terminal Telemetry
Real-time TUI dashboard for monitoring SCF convergence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Static, RichLog
from textual_plotext import PlotextPlot

import parser as log_parser

LOG_FILE = Path("pyscf_run.log")
POLL_INTERVAL = 1.0

# ── Molecule info pane (static) ────────────────────────────────────────────────
_MOLECULE_INFO = """\
[bold cyan]Aspirin[/bold cyan]  [dim]C₉H₈O₄[/dim]
[dim]Acetylsalicylic acid[/dim]
[dim]MW  : 180.16 g/mol[/dim]
[dim]Basis : RHF / 6-31G[/dim]
[dim]Atoms : 21  ·  e⁻ : 112[/dim]

[bold]Cartesian coords (Å)[/bold]
[dim]Atom    X       Y       Z[/dim]
 C₁    0.000   1.405   0.000
 C₂    1.217   0.703   0.000
 C₃    1.217  -0.703   0.000
 C₄    0.000  -1.405   0.000
 C₅   -1.217  -0.703   0.000
 C₆   -1.217   0.703   0.000
 C₇    0.000   2.890   0.000
 O₈    1.057   3.500   0.000
 O₉   -1.178   3.570   0.000
 H₁₀  -1.002   4.515   0.000
 O₁₁   2.381   1.375   0.000
 C₁₂   3.541   0.705   0.000
 O₁₃   4.598   1.315   0.000
 C₁₄   3.541  -0.815   0.000
 H₁₅   2.152  -1.243   0.000
 H₁₆   0.000  -2.485   0.000
 H₁₇  -2.152  -1.243   0.000
 H₁₈  -2.152   1.243   0.000
 H₁₉   4.569  -1.179   0.000
 H₂₀   3.027  -1.179   0.890
 H₂₁   3.027  -1.179  -0.890
"""


# ── Convergence plot widget ────────────────────────────────────────────────────
class ConvergencePlot(PlotextPlot):
    """Live SCF convergence chart (log-scale DIIS error and |ΔE|)."""

    DEFAULT_CSS = """
    ConvergencePlot {
        width: 2fr;
        border: solid $accent;
    }
    """

    def update_data(
        self,
        cycles: list[int],
        log_diis: list[Optional[float]],
        log_delta_e: list[Optional[float]],
    ) -> None:
        plt = self.plt
        plt.clear_data()
        plt.title("The Sweat Index — SCF Convergence")
        plt.xlabel("Cycle")
        plt.ylabel("log₁₀")

        if not cycles:
            self.refresh()
            return

        # |g| gradient (DIIS error)
        pairs_g = [(c, v) for c, v in zip(cycles, log_diis) if v is not None]
        if pairs_g:
            xs, ys = zip(*pairs_g)
            plt.plot(list(xs), list(ys), label="|g| (gradient)", color="red+")

        # |ΔE| — skip cycle 1 whose delta_E equals the raw total energy
        if len(cycles) > 1:
            pairs_de = [
                (c, v)
                for c, v in zip(cycles[1:], log_delta_e[1:])
                if v is not None
            ]
            if pairs_de:
                xs, ys = zip(*pairs_de)
                plt.plot(list(xs), list(ys), label="|ΔE|", color="cyan+")

        self.refresh()


# ── Main application ───────────────────────────────────────────────────────────
class Dashboard(App):
    """Quantum Cruncher — real-time PySCF convergence monitor."""

    CSS = """
    Screen {
        layout: vertical;
        background: #080810;
    }

    /* ── top metric row ── */
    #metrics-row {
        layout: horizontal;
        height: 7;
    }
    .metric-card {
        border: solid $accent;
        padding: 0 2;
        width: 1fr;
        height: 100%;
        content-align: center middle;
        text-align: center;
    }

    /* ── middle: plot + molecule ── */
    #middle-row {
        layout: horizontal;
        height: 1fr;
        min-height: 15;
    }
    #molecule-pane {
        width: 1fr;
        border: solid $accent;
        padding: 1 2;
        overflow-y: auto;
    }

    /* ── bottom log tail ── */
    #log-tail {
        height: 12;
        border: solid $accent;
    }
    """

    TITLE = "Quantum Cruncher // PySCF Terminal Telemetry"
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "quit", "Quit")]

    # ── layout ─────────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="metrics-row"):
            yield Static(
                "[dim]SCF CYCLE[/dim]\n[bold]--[/bold]",
                id="cycle-card",
                classes="metric-card",
            )
            yield Static(
                "[dim]ENERGY (Hartree)[/dim]\n[bold]--[/bold]",
                id="energy-card",
                classes="metric-card",
            )
            yield Static(
                "[dim]DIIS ERROR[/dim]\n[bold]--[/bold]",
                id="diis-card",
                classes="metric-card",
            )

        with Horizontal(id="middle-row"):
            yield ConvergencePlot(id="convergence-plot")
            yield Static(_MOLECULE_INFO, id="molecule-pane", markup=True)

        yield RichLog(id="log-tail", markup=False, auto_scroll=True)
        yield Footer()

    # ── lifecycle ──────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        self._log_offset: int = 0
        self.set_interval(POLL_INTERVAL, self._poll)

    # ── polling ────────────────────────────────────────────────────────────
    async def _poll(self) -> None:
        try:
            await self._update_metrics()
            await self._update_plot()
            self._update_log_tail()
        except Exception:
            pass  # never crash the dashboard during a demo

    async def _update_metrics(self) -> None:
        data   = log_parser.parse_log(LOG_FILE)
        latest = data.get("latest", {})

        cycle_widget  = self.query_one("#cycle-card",  Static)
        energy_widget = self.query_one("#energy-card", Static)
        diis_widget   = self.query_one("#diis-card",   Static)

        if not latest:
            return

        # Cycle card
        if data.get("converged"):
            cycle_widget.update(
                f"[dim]SCF CYCLE[/dim]\n[bold green]{latest['cycle']} ✓ DONE[/bold green]"
            )
        else:
            cycle_widget.update(
                f"[dim]SCF CYCLE[/dim]\n[bold white]{latest['cycle']}[/bold white]"
            )

        # Energy card
        energy_widget.update(
            f"[dim]ENERGY (Hartree)[/dim]\n[bold white]{latest['energy']:.8f}[/bold white]"
        )

        # DIIS error card — colour-coded
        diis = latest["diis_error"]
        if diis < 1e-5:
            colour = "green"
        elif diis < 1e-3:
            colour = "yellow"
        else:
            colour = "red"
        diis_widget.update(
            f"[dim]DIIS ERROR[/dim]\n[bold {colour}]{diis:.2e}[/bold {colour}]"
        )

        # Store data for plot (avoids double parse)
        self._last_data = data

    async def _update_plot(self) -> None:
        data = getattr(self, "_last_data", None) or log_parser.parse_log(LOG_FILE)
        plot = self.query_one("#convergence-plot", ConvergencePlot)
        plot.update_data(data["cycles"], data["log_diis"], data["log_delta_e"])

    def _update_log_tail(self) -> None:
        new_lines, self._log_offset = log_parser.get_new_log_lines(
            LOG_FILE, self._log_offset
        )
        log_tail = self.query_one("#log-tail", RichLog)
        for line in new_lines:
            if line.strip():
                log_tail.write(line)


if __name__ == "__main__":
    Dashboard().run()
