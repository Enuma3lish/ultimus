#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP_DIR="Cpp_Optimization/experiments/distribution_shift"
cd "$SCRIPT_DIR"

# ============================================================
# §4.6 Distribution Shift Experiment
#   N=10000  B=100  k=16  rho=1.00  seeds=1..10
#   First 5000: BP-H64 | Last 5000: BP-H262144
# ============================================================

BINARY="./${EXP_DIR}/build/DistributionShift"
BASE_OUT="./algorithm_result/distribution_shift_result"
SEEDS=(1 2 3 4 5 6 7 8 9 10)
B=100

echo "============================================================"
echo " Distribution Shift Experiment (§4.6)"
echo "  Seeds: ${SEEDS[*]}"
echo "  B=${B}  k=16  eval_window=100"
echo "============================================================"
echo ""

# --- Step 0: Generate seed 10 data if missing ---
if [ ! -f "./data/distribution_shift_10/shift_H64_H262144.csv" ]; then
    echo ">>> Step 0: Generating seed 10 data..."
    python -c "
import sys; sys.path.insert(0, '.')
from Job_init import distribution_shift_job_init
import Write_csv, os
os.makedirs('data/distribution_shift_10', exist_ok=True)
samples = distribution_shift_job_init(num_jobs=10000, avg_inter_arrival_time=30)
Write_csv.Write_raw('data/distribution_shift_10/shift_H64_H262144.csv', samples)
print('  Generated distribution_shift_10 data')
"
    echo ""
fi

# --- Step 1: Build ---
echo ">>> Step 1: Building DistributionShift..."
cd "${EXP_DIR}"
mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -1
make -j"$(nproc)" 2>&1 | tail -1
cd "$SCRIPT_DIR"
echo "  Build complete."
echo ""

# --- Step 2: Run baselines (once per seed) ---
echo ">>> Step 2: Running baselines for all ${#SEEDS[@]} seeds..."
pids=()
for seed in "${SEEDS[@]}"; do
    DATA="./data/distribution_shift_${seed}/shift_H64_H262144.csv"
    OUT_DIR="${BASE_OUT}/seed_${seed}/baselines"
    mkdir -p "$OUT_DIR"
    "$BINARY" "$DATA" "$B" baselines "$OUT_DIR" > "${OUT_DIR}/run.log" 2>&1 &
    pids+=($!)
done
for pid in "${pids[@]}"; do
    wait "$pid" || { echo "ERROR: baseline process $pid failed"; exit 1; }
done
echo "  Baselines complete for all seeds."
echo ""

# --- Step 3: Run framework algorithms (per seed, B=100) ---
echo ">>> Step 3: Running framework algorithms (${#SEEDS[@]} seeds × B=${B})..."
pids=()
for seed in "${SEEDS[@]}"; do
    DATA="./data/distribution_shift_${seed}/shift_H64_H262144.csv"
    OUT_DIR="${BASE_OUT}/seed_${seed}/B_${B}"
    mkdir -p "$OUT_DIR"
    "$BINARY" "$DATA" "$B" framework "$OUT_DIR" > "${OUT_DIR}/run.log" 2>&1 &
    pids+=($!)
done
for pid in "${pids[@]}"; do
    wait "$pid" || { echo "ERROR: framework process $pid failed"; exit 1; }
done
echo "  Framework runs complete."
echo ""

# --- Step 4: Generate plots ---
echo ">>> Step 4: Generating distribution shift plots..."
python compare_plotter.py --distribution-shift
echo ""

echo "============================================================"
echo " COMPLETE"
echo " Results: ${BASE_OUT}/"
echo " Figures: figures/sec4_timevarying/"
echo "============================================================"
