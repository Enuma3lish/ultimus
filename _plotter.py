"""
Enhanced Algorithm Comparison Plotter - Modified for User Requirements

Features:
1. Generate average files for each algorithm from 10 trial runs
2. Create group comparison plots (clairvoyant vs non-clairvoyant)
3. Create mode comparison plots for Dynamic algorithms (mode1 vs mode6)
4. Support for avg30/avg60/avg90, random, and softrandom cases
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import logging

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
BASE_DATA_PATH = "/Users/melowu/Desktop/ultimus"
ALGORITHM_RESULT_PATH = os.path.join(BASE_DATA_PATH, "algorithm_result")
OUTPUT_PATH = os.path.join(BASE_DATA_PATH, "plots_output")

# Create output directory
os.makedirs(OUTPUT_PATH, exist_ok=True)

# ============================================================================
# ALGORITHM DEFINITIONS
# ============================================================================
# Clairvoyant algorithms (know job sizes)
CLAIRVOYANT_ALGORITHMS = ['SRPT', 'SJF', 'Dynamic', 'BAL', 'Dynamic_BAL', 'RR', 'FCFS']

# Non-clairvoyant algorithms (don't know job sizes)
NON_CLAIRVOYANT_ALGORITHMS = ['RMLF', 'MLFQ', 'RR', 'FCFS', 'RFDynamic', 'SETF']

# Algorithms with multiple modes
DYNAMIC_ALGORITHMS = ['Dynamic', 'Dynamic_BAL', 'RFDynamic']

# All unique algorithms
ALL_ALGORITHMS = ['SRPT', 'SJF', 'Dynamic', 'BAL', 'Dynamic_BAL', 'RR', 'FCFS',
                  'RMLF', 'MLFQ', 'RFDynamic', 'SETF']

# ============================================================================
# COLOR AND MARKER SCHEMES
# ============================================================================
ALGORITHM_COLORS = {
    'RR': '#1f77b4',      # Blue
    'SRPT': '#ff7f0e',    # Orange
    'SETF': '#2ca02c',    # Green
    'FCFS': '#d62728',    # Red
    'BAL': '#9467bd',     # Purple
    'Dynamic': '#8c564b', # Brown
    'Dynamic_BAL': '#e377c2',  # Pink
    'RMLF': '#404040',    # Dark Gray (changed for better visibility)
    'MLFQ': '#bcbd22',    # Olive
    'RFDynamic': '#17becf', # Cyan
    'SJF': '#a0522d'      # Sienna (added distinct color)
}

ALGORITHM_MARKERS = {
    'RR': 'o',           # Circle
    'SRPT': 's',         # Square
    'SETF': '^',         # Triangle up
    'FCFS': 'v',         # Triangle down
    'BAL': 'D',          # Diamond
    'Dynamic': 'x',      # X
    'Dynamic_BAL': 'P',  # Plus filled
    'RMLF': '*',         # Star
    'MLFQ': 'p',         # Pentagon
    'RFDynamic': 'h'     # Hexagon
}

MODE_COLORS = {
    'mode1': '#e74c3c',      # Red (worst)
    'mode6': '#2ecc71',      # Green (best)
    'benchmark': '#3498db'   # Blue (benchmark - best overall)
}

MODE_MARKERS = {
    'mode1': 's',            # Square
    'mode6': 'o',            # Circle
    'benchmark': 'D'         # Diamond
}

def setup_plot_style():
    """Set up matplotlib style for publication-quality plots"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (12, 7),
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'legend.fontsize': 11,
        'lines.linewidth': 2.5,
        'lines.markersize': 10,
        'lines.markeredgewidth': 1.5,
        'axes.grid': True,
        'grid.alpha': 0.4,
        'grid.linewidth': 0.8,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
    })

# ============================================================================
# BENCHMARK MODE SELECTION
# ============================================================================

# Global cache for RFDynamic benchmark mode
RFDYNAMIC_BENCHMARK_MODE = None

def find_rfdynamic_benchmark_from_random():
    """
    Find RFDynamic's benchmark mode based on random case results.
    The benchmark is the mode (excluding mode6) that has the lowest L2 norm
    flow time most frequently across all coherence times.

    Returns:
        int: The benchmark mode number (1-5)
    """
    global RFDYNAMIC_BENCHMARK_MODE

    if RFDYNAMIC_BENCHMARK_MODE is not None:
        return RFDYNAMIC_BENCHMARK_MODE

    algorithm = 'RFDynamic'
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")
    data_file = os.path.join(algorithm_dir, f"{algorithm}_final_random_result.csv")

    if not os.path.exists(data_file):
        logger.warning(f"RFDynamic random result file not found: {data_file}")
        logger.warning(f"Defaulting to mode5 for RFDynamic")
        RFDYNAMIC_BENCHMARK_MODE = 5
        return 5

    try:
        df = pd.read_csv(data_file)

        # Count how many times each mode (1-5) has the lowest L2 norm
        mode_win_counts = {i: 0 for i in range(1, 6)}

        for _, row in df.iterrows():
            # Get L2 norm values for modes 1-5
            mode_values = {}
            for i in range(1, 6):
                col_name = f'mode{i}_L2_norm_flow_time'
                if col_name in df.columns and pd.notna(row[col_name]):
                    mode_values[i] = row[col_name]

            # Find which mode has the lowest value
            if mode_values:
                best_mode = min(mode_values.items(), key=lambda x: x[1])[0]
                mode_win_counts[best_mode] += 1

        # Find the mode with the most wins
        benchmark_mode = max(mode_win_counts.items(), key=lambda x: x[1])[0]

        logger.info(f"\n{'='*60}")
        logger.info(f"RFDynamic Benchmark Mode Selection (from random case):")
        logger.info(f"  Mode win counts (lowest L2 norm frequency):")
        for mode, count in sorted(mode_win_counts.items()):
            logger.info(f"    Mode {mode}: {count} times")
        logger.info(f"  Selected benchmark: mode{benchmark_mode}")
        logger.info(f"{'='*60}\n")

        RFDYNAMIC_BENCHMARK_MODE = benchmark_mode
        return benchmark_mode

    except Exception as e:
        logger.warning(f"Error finding RFDynamic benchmark mode: {e}")
        logger.warning(f"Defaulting to mode5 for RFDynamic")
        RFDYNAMIC_BENCHMARK_MODE = 5
        return 5

def find_benchmark_mode(df, algorithm):
    """
    Find the benchmark mode for a Dynamic algorithm.

    For RFDynamic: Uses the mode that has lowest L2 norm most frequently in random case
    For other Dynamic algorithms: Uses the mode closest to mode 6 (excluding mode 6)

    Args:
        df: DataFrame with mode columns
        algorithm: Algorithm name

    Returns:
        Tuple of (benchmark_mode_number, benchmark_column_name)
    """
    # Special handling for RFDynamic
    if algorithm == 'RFDynamic':
        benchmark_mode = find_rfdynamic_benchmark_from_random()
        return benchmark_mode, f'mode{benchmark_mode}_L2_norm_flow_time'

    # For other Dynamic algorithms, use the original logic
    mode_columns = [col for col in df.columns if 'mode' in col and 'L2_norm_flow_time' in col]

    if not mode_columns or 'mode6_L2_norm_flow_time' not in df.columns:
        logger.warning(f"No mode columns or mode6 not found for {algorithm}")
        return 5, 'mode5_L2_norm_flow_time'  # Default to mode5

    # Calculate distance from each mode to mode 6
    mode6_values = df['mode6_L2_norm_flow_time'].values
    mode_distances = {}

    for i in range(1, 6):  # modes 1-5 (excluding mode 6)
        col_name = f'mode{i}_L2_norm_flow_time'
        if col_name in df.columns:
            mode_values = df[col_name].values
            # Calculate mean absolute difference
            distance = np.mean(np.abs(mode_values - mode6_values))
            mode_distances[i] = distance

    if not mode_distances:
        logger.warning(f"Could not calculate distances for {algorithm}")
        return 5, 'mode5_L2_norm_flow_time'

    # Find the mode with smallest distance to mode 6
    benchmark_mode = min(mode_distances.items(), key=lambda x: x[1])[0]

    logger.info(f"  Benchmark mode for {algorithm}: mode{benchmark_mode} (closest to mode6)")
    logger.info(f"    Distances to mode6: {mode_distances}")

    return benchmark_mode, f'mode{benchmark_mode}_L2_norm_flow_time'

# ============================================================================
# STEP 1: GENERATE AVERAGE FILES
# ============================================================================

def generate_average_files():
    """
    Generate average files for each algorithm from 10 trial runs.
    Creates files: {algorithm_name}_final_result_{avg_type}.csv
                  {algorithm_name}_final_random_result.csv
                  {algorithm_name}_final_softrandom.csv
    """
    logger.info("=" * 80)
    logger.info("Starting to generate average files for all algorithms")
    logger.info("=" * 80)

    for algorithm in ALL_ALGORITHMS:
        algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")

        if not os.path.exists(algorithm_dir):
            logger.warning(f"Directory not found: {algorithm_dir}")
            continue

        logger.info(f"\nProcessing algorithm: {algorithm}")

        # Process avg30, avg60, avg90
        for avg_type in ['avg30', 'avg60', 'avg90']:
            process_avg_type(algorithm, algorithm_dir, avg_type)

        # Process random
        process_random_type(algorithm, algorithm_dir, 'random')

        # Process softrandom
        process_random_type(algorithm, algorithm_dir, 'softrandom')

    logger.info("\n" + "=" * 80)
    logger.info("Average file generation completed!")
    logger.info("=" * 80)

def process_avg_type(algorithm, algorithm_dir, avg_type):
    """Process avg30/avg60/avg90 type results"""
    result_dir = os.path.join(algorithm_dir, f"{avg_type}_result")

    if not os.path.exists(result_dir):
        logger.warning(f"  Directory not found: {result_dir}")
        return

    # Get all CSV files
    pattern = os.path.join(result_dir, "*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        logger.warning(f"  No CSV files found in {result_dir}")
        return

    logger.info(f"  Processing {avg_type}: found {len(files)} files")

    # Group files by arrival_rate (mean-inter-arrival-time)
    arrival_rate_groups = {}

    for file_path in files:
        filename = os.path.basename(file_path)
        # Extract arrival rate from filename (e.g., "20_Dynamic_result_1.csv" -> "20")
        parts = filename.split('_')
        arrival_rate = parts[0]

        if arrival_rate not in arrival_rate_groups:
            arrival_rate_groups[arrival_rate] = []
        arrival_rate_groups[arrival_rate].append(file_path)

    # Process each arrival rate group
    averaged_data = []

    for arrival_rate in sorted(arrival_rate_groups.keys()):
        files_for_rate = arrival_rate_groups[arrival_rate]

        if algorithm in DYNAMIC_ALGORITHMS:
            avg_row = average_dynamic_files(files_for_rate, arrival_rate, algorithm)
        else:
            avg_row = average_regular_files(files_for_rate, arrival_rate, algorithm)

        if avg_row is not None:
            averaged_data.append(avg_row)

    # Create DataFrame and save
    if averaged_data:
        df = pd.DataFrame(averaged_data)
        output_file = os.path.join(algorithm_dir, f"{algorithm}_final_result_{avg_type}.csv")
        df.to_csv(output_file, index=False)
        logger.info(f"  Saved: {output_file}")

def average_regular_files(files, arrival_rate, algorithm):
    """Average files for regular algorithms (no modes)"""
    l2_norm_values = []

    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            # Column name: {Algorithm}_L2_norm_flow_time
            col_name = f"{algorithm}_L2_norm_flow_time"

            if col_name in df.columns:
                # Average all values in this file
                avg_val = df[col_name].mean()
                l2_norm_values.append(avg_val)
        except Exception as e:
            logger.warning(f"    Error reading {file_path}: {e}")
            continue

    if l2_norm_values:
        return {
            'mean_inter_arrival_time': float(arrival_rate),
            'L2_norm_flow_time': np.mean(l2_norm_values)
        }
    return None

def average_dynamic_files(files, arrival_rate, algorithm):
    """Average files for Dynamic algorithms (with modes)"""
    mode_values = {f'mode{i}': [] for i in range(1, 7)}

    for file_path in files:
        try:
            df = pd.read_csv(file_path)

            # Column names: {Algorithm}_njobs100_mode{i}_L2_norm_flow_time
            for mode_num in range(1, 7):
                col_name = f"{algorithm}_njobs100_mode{mode_num}_L2_norm_flow_time"

                if col_name in df.columns:
                    avg_val = df[col_name].mean()
                    mode_values[f'mode{mode_num}'].append(avg_val)
        except Exception as e:
            logger.warning(f"    Error reading {file_path}: {e}")
            continue

    # Create row with all mode averages
    row = {'mean_inter_arrival_time': float(arrival_rate)}

    for mode_num in range(1, 7):
        mode_key = f'mode{mode_num}'
        if mode_values[mode_key]:
            row[f'{mode_key}_L2_norm_flow_time'] = np.mean(mode_values[mode_key])

    return row if len(row) > 1 else None

def process_random_type(algorithm, algorithm_dir, random_type):
    """Process random or softrandom type results"""
    result_dir = os.path.join(algorithm_dir, f"{random_type}_result")

    if not os.path.exists(result_dir):
        logger.warning(f"  Directory not found: {result_dir}")
        return

    # Get all CSV files
    pattern = os.path.join(result_dir, "*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        logger.warning(f"  No CSV files found in {result_dir}")
        return

    logger.info(f"  Processing {random_type}: found {len(files)} files")

    if algorithm in DYNAMIC_ALGORITHMS:
        df_avg = average_random_dynamic_files(files, algorithm)
    else:
        df_avg = average_random_regular_files(files, algorithm)

    if df_avg is not None:
        output_name = f"{algorithm}_final_random_result.csv" if random_type == "random" else f"{algorithm}_final_softrandom.csv"
        output_file = os.path.join(algorithm_dir, output_name)
        df_avg.to_csv(output_file, index=False)
        logger.info(f"  Saved: {output_file}")

def average_random_regular_files(files, algorithm):
    """Average random/softrandom files for regular algorithms"""
    all_data = []

    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
        except Exception as e:
            logger.warning(f"    Error reading {file_path}: {e}")
            continue

    if not all_data:
        return None

    # Concatenate all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)

    # Group by frequency (coherence time) and average
    col_name = f"{algorithm}_L2_norm_flow_time"

    if 'frequency' in combined_df.columns and col_name in combined_df.columns:
        result = combined_df.groupby('frequency')[col_name].mean().reset_index()
        result.columns = ['coherence_time', 'L2_norm_flow_time']
        return result

    return None

def average_random_dynamic_files(files, algorithm):
    """Average random/softrandom files for Dynamic algorithms"""
    all_data = []

    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
        except Exception as e:
            logger.warning(f"    Error reading {file_path}: {e}")
            continue

    if not all_data:
        return None

    # Concatenate all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)

    # Group by frequency and average all mode columns
    mode_cols = [f"{algorithm}_njobs100_mode{i}_L2_norm_flow_time" for i in range(1, 7)]

    if 'frequency' not in combined_df.columns:
        return None

    # Filter existing mode columns
    existing_mode_cols = [col for col in mode_cols if col in combined_df.columns]

    if not existing_mode_cols:
        return None

    result = combined_df.groupby('frequency')[existing_mode_cols].mean().reset_index()

    # Rename columns
    rename_dict = {'frequency': 'coherence_time'}
    for i in range(1, 7):
        old_col = f"{algorithm}_njobs100_mode{i}_L2_norm_flow_time"
        new_col = f"mode{i}_L2_norm_flow_time"
        if old_col in result.columns:
            rename_dict[old_col] = new_col

    result.rename(columns=rename_dict, inplace=True)

    return result

# ============================================================================
# STEP 2: CREATE GROUP COMPARISON PLOTS
# ============================================================================

def create_group_comparison_plots():
    """Create comparison plots for clairvoyant and non-clairvoyant algorithm groups"""
    logger.info("\n" + "=" * 80)
    logger.info("Creating group comparison plots")
    logger.info("=" * 80)

    # Process avg types
    for avg_type in ['avg30', 'avg60', 'avg90']:
        logger.info(f"\nProcessing {avg_type} results...")
        plot_algorithm_group(CLAIRVOYANT_ALGORITHMS, avg_type, "clairvoyant")
        plot_algorithm_group(NON_CLAIRVOYANT_ALGORITHMS, avg_type, "non_clairvoyant")

    # Process random and softrandom
    for result_type in ['random', 'softrandom']:
        logger.info(f"\nProcessing {result_type} results...")
        plot_algorithm_group_random(CLAIRVOYANT_ALGORITHMS, result_type, "clairvoyant")
        plot_algorithm_group_random(NON_CLAIRVOYANT_ALGORITHMS, result_type, "non_clairvoyant")

    logger.info("\n" + "=" * 80)
    logger.info("Group comparison plots completed!")
    logger.info("=" * 80)

def plot_algorithm_group(algorithms, avg_type, group_name):
    """Plot comparison for a group of algorithms (avg type)"""
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 7))

    for algorithm in algorithms:
        algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")
        data_file = os.path.join(algorithm_dir, f"{algorithm}_final_result_{avg_type}.csv")

        if not os.path.exists(data_file):
            logger.warning(f"  File not found: {data_file}")
            continue

        try:
            df = pd.read_csv(data_file)

            if algorithm in DYNAMIC_ALGORITHMS:
                # Find benchmark mode (mode closest to mode 6, excluding mode 6)
                benchmark_mode_num, benchmark_col = find_benchmark_mode(df, algorithm)

                # Plot only benchmark mode
                if benchmark_col in df.columns:
                    ax.plot(df['mean_inter_arrival_time'], df[benchmark_col],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linestyle='-',
                           linewidth=2.5,
                           markersize=10,
                           markeredgewidth=1.5,
                           markeredgecolor='white',
                           markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                           label=f"{algorithm} (mode{benchmark_mode_num})")
            else:
                # Plot regular algorithm
                if 'L2_norm_flow_time' in df.columns:
                    ax.plot(df['mean_inter_arrival_time'], df['L2_norm_flow_time'],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linestyle='-',
                           linewidth=2.5,
                           markersize=10,
                           markeredgewidth=1.5,
                           markeredgecolor='white',
                           markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                           label=algorithm)

        except Exception as e:
            logger.warning(f"  Error plotting {algorithm}: {e}")
            continue

    ax.set_xlabel('Mean Inter-Arrival Time')
    ax.set_ylabel('L2-Norm Flow Time')
    ax.set_title(f'{group_name.replace("_", " ").title()} Algorithms Comparison ({avg_type})')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Set x-axis to show proper increments of 2
    if len(ax.get_lines()) > 0:
        x_data = []
        for line in ax.get_lines():
            x_data.extend(line.get_xdata())
        if x_data:
            x_min, x_max = min(x_data), max(x_data)
            ax.set_xticks(np.arange(int(x_min), int(x_max) + 1, 2))

    # Save plot
    output_file = os.path.join(OUTPUT_PATH, f"{group_name}_{avg_type}_comparison.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"  Saved: {output_file}")

def plot_algorithm_group_random(algorithms, result_type, group_name):
    """Plot comparison for a group of algorithms (random/softrandom type)"""
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 7))

    for algorithm in algorithms:
        algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")

        if result_type == "random":
            data_file = os.path.join(algorithm_dir, f"{algorithm}_final_random_result.csv")
        else:
            data_file = os.path.join(algorithm_dir, f"{algorithm}_final_softrandom.csv")

        if not os.path.exists(data_file):
            logger.warning(f"  File not found: {data_file}")
            continue

        try:
            df = pd.read_csv(data_file)

            if algorithm in DYNAMIC_ALGORITHMS:
                # Find benchmark mode (mode closest to mode 6, excluding mode 6)
                benchmark_mode_num, benchmark_col = find_benchmark_mode(df, algorithm)

                # Plot only benchmark mode
                if benchmark_col in df.columns:
                    ax.plot(df['coherence_time'], df[benchmark_col],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linestyle='-',
                           linewidth=2.5,
                           markersize=10,
                           markeredgewidth=1.5,
                           markeredgecolor='white',
                           markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                           label=f"{algorithm} (mode{benchmark_mode_num})")
            else:
                # Plot regular algorithm
                if 'L2_norm_flow_time' in df.columns:
                    ax.plot(df['coherence_time'], df['L2_norm_flow_time'],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linestyle='-',
                           linewidth=2.5,
                           markersize=10,
                           markeredgewidth=1.5,
                           markeredgecolor='white',
                           markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                           label=algorithm)

        except Exception as e:
            logger.warning(f"  Error plotting {algorithm}: {e}")
            continue

    ax.set_xlabel('Coherence Time')
    ax.set_ylabel('L2-Norm Flow Time')
    ax.set_title(f'{group_name.replace("_", " ").title()} Algorithms Comparison ({result_type})')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)  # Log scale for coherence time

    # Set x-axis to start from 2 (2^1) and show powers of 2
    # Coherence times are [2, 4, 8, 16, 32, 64, ..., 65536] = [2^1, 2^2, ..., 2^16]
    ax.set_xlim(left=2)
    # Set x-ticks to powers of 2
    x_ticks = [2**i for i in range(1, 17)]  # [2, 4, 8, 16, ..., 65536]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])

    # Save plot
    output_file = os.path.join(OUTPUT_PATH, f"{group_name}_{result_type}_comparison.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"  Saved: {output_file}")

# ============================================================================
# STEP 3: CREATE MODE COMPARISON PLOTS FOR DYNAMIC ALGORITHMS
# ============================================================================

def create_dynamic_mode_comparison_plots():
    """Create mode1 vs mode6 comparison plots for Dynamic algorithms"""
    logger.info("\n" + "=" * 80)
    logger.info("Creating Dynamic algorithm mode comparison plots")
    logger.info("=" * 80)

    for algorithm in DYNAMIC_ALGORITHMS:
        logger.info(f"\nProcessing {algorithm}...")

        # Process avg types
        for avg_type in ['avg30', 'avg60', 'avg90']:
            plot_mode_comparison(algorithm, avg_type)

        # Process random and softrandom
        for result_type in ['random', 'softrandom']:
            plot_mode_comparison_random(algorithm, result_type)

    logger.info("\n" + "=" * 80)
    logger.info("Dynamic mode comparison plots completed!")
    logger.info("=" * 80)

def plot_mode_comparison(algorithm, avg_type):
    """Plot mode1 vs mode6 vs benchmark comparison for a Dynamic algorithm (avg type)"""
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")
    data_file = os.path.join(algorithm_dir, f"{algorithm}_final_result_{avg_type}.csv")

    if not os.path.exists(data_file):
        logger.warning(f"  File not found: {data_file}")
        return

    try:
        df = pd.read_csv(data_file)

        if 'mode1_L2_norm_flow_time' not in df.columns or 'mode6_L2_norm_flow_time' not in df.columns:
            logger.warning(f"  Missing mode columns in {data_file}")
            return

        # Find benchmark mode (closest to mode6, excluding mode6)
        benchmark_mode_num, benchmark_col = find_benchmark_mode(df, algorithm)

        setup_plot_style()
        fig, ax = plt.subplots(figsize=(12, 7))

        # Plot mode1 (worst case)
        ax.plot(df['mean_inter_arrival_time'], df['mode1_L2_norm_flow_time'],
               marker=MODE_MARKERS['mode1'],
               color=MODE_COLORS['mode1'],
               linestyle='-',
               linewidth=2.5,
               markersize=10,
               markeredgewidth=1.5,
               markeredgecolor='white',
               markerfacecolor=MODE_COLORS['mode1'],
               label='Mode 1 (Worst Case)')

        # Plot mode6 (best case)
        ax.plot(df['mean_inter_arrival_time'], df['mode6_L2_norm_flow_time'],
               marker=MODE_MARKERS['mode6'],
               color=MODE_COLORS['mode6'],
               linestyle='-',
               linewidth=2.5,
               markersize=10,
               markeredgewidth=1.5,
               markeredgecolor='white',
               markerfacecolor=MODE_COLORS['mode6'],
               label='Mode 6 (Best Case)')

        # Plot benchmark mode (closest to mode6)
        if benchmark_col in df.columns:
            ax.plot(df['mean_inter_arrival_time'], df[benchmark_col],
                   marker=MODE_MARKERS['benchmark'],
                   color=MODE_COLORS['benchmark'],
                   linestyle='-',
                   linewidth=2.5,
                   markersize=10,
                   markeredgewidth=1.5,
                   markeredgecolor='white',
                   markerfacecolor=MODE_COLORS['benchmark'],
                   label=f'Mode {benchmark_mode_num} (Benchmark - Closest to Mode6)')

        ax.set_xlabel('Mean Inter-Arrival Time')
        ax.set_ylabel('L2-Norm Flow Time')
        ax.set_title(f'{algorithm} Mode Comparison ({avg_type})')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        # Set x-axis to show proper increments of 2
        if len(ax.get_lines()) > 0:
            x_data = []
            for line in ax.get_lines():
                x_data.extend(line.get_xdata())
            if x_data:
                x_min, x_max = min(x_data), max(x_data)
                ax.set_xticks(np.arange(int(x_min), int(x_max) + 1, 2))

        # Save plot
        output_file = os.path.join(OUTPUT_PATH, f"{algorithm}_mode_comparison_{avg_type}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

    except Exception as e:
        logger.warning(f"  Error creating mode comparison plot: {e}")

def plot_mode_comparison_random(algorithm, result_type):
    """Plot benchmark vs mode1 vs mode6 comparison for a Dynamic algorithm (random/softrandom type)"""
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")

    if result_type == "random":
        data_file = os.path.join(algorithm_dir, f"{algorithm}_final_random_result.csv")
    else:
        data_file = os.path.join(algorithm_dir, f"{algorithm}_final_softrandom.csv")

    if not os.path.exists(data_file):
        logger.warning(f"  File not found: {data_file}")
        return

    try:
        df = pd.read_csv(data_file)

        if 'mode1_L2_norm_flow_time' not in df.columns or 'mode6_L2_norm_flow_time' not in df.columns:
            logger.warning(f"  Missing mode columns in {data_file}")
            return

        # Find benchmark mode (closest to mode6, excluding mode6)
        benchmark_mode_num, benchmark_col = find_benchmark_mode(df, algorithm)

        setup_plot_style()
        fig, ax = plt.subplots(figsize=(12, 7))

        # Plot mode1 (worst case)
        ax.plot(df['coherence_time'], df['mode1_L2_norm_flow_time'],
               marker=MODE_MARKERS['mode1'],
               color=MODE_COLORS['mode1'],
               linestyle='-',
               linewidth=2.5,
               markersize=10,
               markeredgewidth=1.5,
               markeredgecolor='white',
               markerfacecolor=MODE_COLORS['mode1'],
               label='Mode 1 (Worst Case)')

        # Plot mode6 (best case)
        ax.plot(df['coherence_time'], df['mode6_L2_norm_flow_time'],
               marker=MODE_MARKERS['mode6'],
               color=MODE_COLORS['mode6'],
               linestyle='-',
               linewidth=2.5,
               markersize=10,
               markeredgewidth=1.5,
               markeredgecolor='white',
               markerfacecolor=MODE_COLORS['mode6'],
               label='Mode 6 (Best Case)')

        # Plot benchmark mode (closest to mode6)
        if benchmark_col in df.columns:
            ax.plot(df['coherence_time'], df[benchmark_col],
                   marker=MODE_MARKERS['benchmark'],
                   color=MODE_COLORS['benchmark'],
                   linestyle='-',
                   linewidth=2.5,
                   markersize=10,
                   markeredgewidth=1.5,
                   markeredgecolor='white',
                   markerfacecolor=MODE_COLORS['benchmark'],
                   label=f'Mode {benchmark_mode_num} (Benchmark - Closest to Mode6)')

        ax.set_xlabel('Coherence Time')
        ax.set_ylabel('L2-Norm Flow Time')
        ax.set_title(f'{algorithm} Mode Comparison ({result_type})')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log', base=2)  # Log scale for coherence time

        # Set x-axis to start from 2 (2^1) and show powers of 2
        # Coherence times are [2, 4, 8, 16, 32, 64, ..., 65536] = [2^1, 2^2, ..., 2^16]
        ax.set_xlim(left=2)
        # Set x-ticks to powers of 2
        x_ticks = [2**i for i in range(1, 17)]  # [2, 4, 8, 16, ..., 65536]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])

        # Save plot
        output_file = os.path.join(OUTPUT_PATH, f"{algorithm}_mode_comparison_{result_type}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

    except Exception as e:
        logger.warning(f"  Error creating mode comparison plot: {e}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    logger.info("\n" + "=" * 80)
    logger.info("ALGORITHM COMPARISON PLOTTER - STARTING")
    logger.info("=" * 80)

    # Step 1: Generate average files
    generate_average_files()

    # Step 2: Create group comparison plots
    create_group_comparison_plots()

    # Step 3: Create Dynamic algorithm mode comparison plots
    create_dynamic_mode_comparison_plots()

    logger.info("\n" + "=" * 80)
    logger.info("ALL TASKS COMPLETED SUCCESSFULLY!")
    logger.info(f"Output directory: {OUTPUT_PATH}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
