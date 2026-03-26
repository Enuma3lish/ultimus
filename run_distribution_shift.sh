#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo " Distribution Shift Experiment (4.6)"
echo "  N=10000  B=100  k=8  rho=1.00"
echo "  First 5000: BP-H64 | Last 5000: BP-H262144"
echo "============================================================"
echo ""

# --- Step 1: Generate job data ---
echo ">>> Step 1: Generating distribution shift workload..."
if [[ -d ".venv" ]]; then
    source .venv/bin/activate
fi
python Job_init.py --mode generate --num-jobs 10000
echo "    Done."
echo ""

# --- Step 2: Build the C++ experiment ---
echo ">>> Step 2: Building C++ experiment..."
EXP_DIR="Cpp_Optimization/experiments/distribution_shift"
mkdir -p "${EXP_DIR}/build"
cd "${EXP_DIR}/build"
cmake .. && make -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
cd "$SCRIPT_DIR"
echo "    Done."
echo ""

# --- Step 3: Run the experiment ---
echo ">>> Step 3: Running all algorithms on shift workload..."
"./${EXP_DIR}/build/DistributionShift"
echo ""

# --- Step 4: Generate plots ---
echo ">>> Step 4: Generating distribution shift plots..."
python compare_plotter.py --distribution-shift
echo ""

echo "============================================================"
echo " COMPLETE"
echo " Results: algorithm_result/distribution_shift_result/"
echo " Figures: figures/sec4_distribution_shift/"
echo "============================================================"
