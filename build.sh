#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
ALGO_DIR="${PROJECT_ROOT}/Cpp_Optimization/algorithms"

ALGORITHMS=(BAL SRPT Dynamic Dynamic_BAL FCFS RR SETF SJF MLFQ RMLF RFDynamic ) 

echo "Building all algorithms..."

for algo in "${ALGORITHMS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Building $algo"
    echo "=========================================="
    
    cd "${ALGO_DIR}/${algo}"
    
    # Create build directory if it doesn't exist
    mkdir -p build
    cd build
    
    # Build
    if cmake .. && make -j4; then
        echo "✓ $algo built successfully"
        
        # Make executable
        chmod +x "$algo"
        ls -l "$algo"
    else
        echo "✗ $algo build failed"
    fi
done

# Build experiments
EXPERIMENT_DIR="${PROJECT_ROOT}/Cpp_Optimization/experiments"

echo ""
echo "=========================================="
echo "Building experiment: distribution_shift"
echo "=========================================="

cd "${EXPERIMENT_DIR}/distribution_shift"
mkdir -p build
cd build

if cmake .. && make -j4; then
    echo "✓ distribution_shift built successfully"
    chmod +x DistributionShift
    ls -l DistributionShift
else
    echo "✗ distribution_shift build failed"
fi

echo ""
echo "=========================================="
echo "Build process complete"
echo "=========================================="