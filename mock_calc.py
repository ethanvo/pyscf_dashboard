#!/usr/bin/env python3
"""
Mock PySCF RHF/6-31G calculation on Aspirin (C9H8O4).
Injects a 2-second sleep per SCF cycle so the dashboard can be observed.
Output is streamed to pyscf_run.log.
"""

import time
from pyscf import gto, scf

# Aspirin (C9H8O4) - 21 atoms
# Benzene ring in xy-plane; carboxylic acid at C1, acetyloxy at C2.
# Distances: C-C(ar)=1.40, C-C(sp2)=1.49, C=O=1.22, C-O=1.34-1.36, O-H=0.96, C-H(ar)=1.08, C-H(sp3)=1.09
ASPIRIN_GEOMETRY = """
 C   0.0000   1.4050   0.0000
 C   1.2165   0.7025   0.0000
 C   1.2165  -0.7025   0.0000
 C   0.0000  -1.4050   0.0000
 C  -1.2165  -0.7025   0.0000
 C  -1.2165   0.7025   0.0000
 C   0.0000   2.8900   0.0000
 O   1.0570   3.5000   0.0000
 O  -1.1780   3.5700   0.0000
 H  -1.0020   4.5150   0.0000
 O   2.3810   1.3750   0.0000
 C   3.5410   0.7050   0.0000
 O   4.5980   1.3150   0.0000
 C   3.5410  -0.8150   0.0000
 H   2.1520  -1.2430   0.0000
 H   0.0000  -2.4850   0.0000
 H  -2.1520  -1.2430   0.0000
 H  -2.1520   1.2430   0.0000
 H   4.5690  -1.1790   0.0000
 H   3.0270  -1.1790   0.8900
 H   3.0270  -1.1790  -0.8900
"""


def run_aspirin_scf():
    mol = gto.Mole()
    mol.atom = ASPIRIN_GEOMETRY
    mol.basis = "6-31g"
    mol.charge = 0
    mol.spin = 0
    mol.output = "pyscf_run.log"
    mol.verbose = 4
    mol.max_memory = 4000
    mol.build()

    # Flush after build so initialization info lands in the log immediately
    mol.stdout.flush()

    mf = scf.RHF(mol)
    mf.max_cycle = 150
    mf.conv_tol = 1e-9

    def slow_callback(envs):
        """Flush log and sleep so the dashboard has time to update."""
        mol.stdout.flush()
        time.sleep(2.0)

    mf.callback = slow_callback

    print("=" * 60)
    print("  Quantum Cruncher — Mock Aspirin RHF/6-31G Calculation")
    print("  Output  : pyscf_run.log")
    print("  Sleep   : 2s per SCF cycle (for dashboard demo)")
    print("=" * 60, flush=True)

    energy = mf.kernel()
    mol.stdout.flush()

    print(f"\nFinal RHF/6-31G Energy: {energy:.10f} Hartree", flush=True)


if __name__ == "__main__":
    run_aspirin_scf()
