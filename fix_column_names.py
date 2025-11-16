#!/usr/bin/env python3
"""
Script to fix column names from 'arrival_rate' to 'Mean_inter_arrival_time'
across all relevant files
"""

import re
import os

def fix_cpp_files():
    """Fix C++ header files"""
    cpp_file = "/Users/melowu/Desktop/ultimus/Cpp_Optimization/function_tools/process_avg_folders.h"

    print(f"Fixing {cpp_file}...")

    with open(cpp_file, 'r') as f:
        content = f.read()

    # Replace all occurrences of "arrival_rate" in CSV header output
    content = content.replace(
        'out << "arrival_rate,bp_parameter_L,bp_parameter_H"',
        'out << "Mean_inter_arrival_time,bp_parameter_L,bp_parameter_H"'
    )

    with open(cpp_file, 'w') as f:
        f.write(content)

    print(f"  ✓ Fixed {cpp_file}")

def fix_plotter_files():
    """Fix Python plotter files"""
    files_to_fix = [
        "/Users/melowu/Desktop/ultimus/_plotter.py",
        "/Users/melowu/Desktop/ultimus/distribution_based_plotter.py"
    ]

    for filepath in files_to_fix:
        if not os.path.exists(filepath):
            print(f"  ⚠ Skipping {filepath} (not found)")
            continue

        print(f"Fixing {filepath}...")

        with open(filepath, 'r') as f:
            content = f.read()

        # Replace arrival_rate with Mean_inter_arrival_time
        content = content.replace("'arrival_rate'", "'Mean_inter_arrival_time'")
        content = content.replace('"arrival_rate"', '"Mean_inter_arrival_time"')
        content = content.replace('["arrival_rate"]', '["Mean_inter_arrival_time"]')
        content = content.replace("['arrival_rate']", "['Mean_inter_arrival_time']")
        content = content.replace('df.arrival_rate', 'df.Mean_inter_arrival_time')

        with open(filepath, 'w') as f:
            f.write(content)

        print(f"  ✓ Fixed {filepath}")

def main():
    print("="*80)
    print("FIXING COLUMN NAMES: arrival_rate → Mean_inter_arrival_time")
    print("="*80)

    fix_cpp_files()
    fix_plotter_files()

    print("\n" + "="*80)
    print("ALL FIXES APPLIED!")
    print("="*80)
    print("\nNext steps:")
    print("1. Rebuild C++ algorithms to regenerate result files with new column names")
    print("2. Run the new plotter.py")

if __name__ == "__main__":
    main()
