#!/bin/bash
set -e

PROJECT_ROOT="/home/melowu/Work/ultimus"
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

echo ""
echo "=========================================="
echo "Build process complete"
echo "=========================================="