#!/usr/bin/env python3
"""
Algorithm Comparison Plotter

Features:
1. Finds best mode (2-5) for Dynamic algorithms based on frequency of lowest L2 norm
2. All Dynamic algorithms (Dynamic, Dynamic_BAL, RFDynamic) use the same mode
3. Creates comparison plots for different algorithm groups
4. X-axis: coherence time (frequency), Y-axis: L2 norm or Maximum flow time
5. Solid lines for Dynamic algorithms, SRPT, RMLF; dotted for others
6. High contrast colors for better visibility
7. Output format: PDF
8. Two-algorithm comparisons: Red for our algorithm, Blue for adversary
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import logging
import re

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
BASE_DATA_PATH = "."
ALGORITHM_RESULT_PATH = os.path.join(BASE_DATA_PATH, "algorithm_result")
OUTPUT_PATH = os.path.join(BASE_DATA_PATH, "plots_output", "compare")

os.makedirs(OUTPUT_PATH, exist_ok=True)

# ============================================================================
# ALGORITHM DEFINITIONS
# ============================================================================
DYNAMIC_ALGORITHMS = ['Dynamic', 'Dynamic_BAL', 'RFDynamic']

# Our designed algorithms (use red in two-algorithm comparisons)
OUR_ALGORITHMS = ['Dynamic', 'Dynamic_BAL', 'RFDynamic']

# Clairvoyant includes Dynamic and Dynamic_BAL
CLAIRVOYANT_ALGORITHMS = ['SRPT', 'FCFS', 'SJF', 'RR', 'BAL', 'Dynamic', 'Dynamic_BAL']
NON_CLAIRVOYANT_ALGORITHMS = ['RFDynamic', 'RR', 'RMLF', 'FCFS', 'MLFQ', 'SETF']
ALL_ALGORITHMS = ['SRPT', 'SJF', 'Dynamic', 'BAL', 'Dynamic_BAL', 'RR', 'FCFS',
                  'RMLF', 'MLFQ', 'RFDynamic', 'SETF']

# Algorithms with solid lines
SOLID_LINE_ALGORITHMS = ['Dynamic', 'Dynamic_BAL', 'RFDynamic', 'SRPT', 'RMLF']

# Number of runs to average
NUM_RUNS = 5

# ============================================================================
# HIGH CONTRAST COLOR AND MARKER SCHEMES
# ============================================================================
ALGORITHM_COLORS = {
    'RR': '#0000FF',          # Pure Blue - High contrast
    'SRPT': '#FF0000',        # Pure Red - High contrast
    'SETF': '#00AA00',        # Dark Green - High contrast
    'FCFS': '#FFD700',        # Gold - High contrast
    'BAL': '#8B00FF',         # Violet - High contrast
    'Dynamic': '#FF6600',     # Vibrant Orange - High contrast
    'Dynamic_BAL': '#FF00FF', # Magenta - High contrast
    'RMLF': '#000000',        # Black - High contrast
    'MLFQ': '#808000',        # Olive - High contrast
    'RFDynamic': '#00FFFF',   # Cyan - High contrast
    'SJF': '#8B4513'          # Saddle Brown - High contrast
}

ALGORITHM_MARKERS = {
    'RR': 'o',
    'SRPT': 'D',
    'SETF': '^',
    'FCFS': 's',
    'BAL': 'P',
    'Dynamic': 'v',
    'Dynamic_BAL': 'p',
    'RMLF': '*',
    'MLFQ': 'h',
    'RFDynamic': '<',
    'SJF': 'X'
}

# Global best mode for all Dynamic algorithms
BEST_MODE = None

# ============================================================================
# CASE TYPE DEFINITIONS
# ============================================================================
NON_COMBINATION_CASES = [
    'Bounded_Pareto_random_result',
    'Bounded_Pareto_softrandom_result'
]

COMBINATION_CASES = [
    'Bounded_Pareto_combination_random_result',
    'Bounded_Pareto_combination_softrandom_result',
    'normal_combination_random_result',
    'normal_combination_softrandom_result'
]


def setup_plot_style():
    """Set up matplotlib style with high contrast"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (14, 8),
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'legend.fontsize': 11,
        'lines.linewidth': 3.0,
        'lines.markersize': 12,
        'lines.markeredgewidth': 2.0,
        'axes.grid': True,
        'grid.alpha': 0.4,
        'grid.linewidth': 0.8,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.facecolor': 'white',
        'figure.facecolor': 'white',
    })


# ============================================================================
# DISCOVER COMBINATION STRUCTURE
# ============================================================================

def discover_combinations(case_type, combo_type):
    """
    Discover all unique combinations in a given case type.

    Args:
        case_type: e.g., 'Bounded_Pareto_combination_random_result'
        combo_type: 'two_result', 'three_result', or 'four_result'

    Returns:
        List of tuples: (prefix_pattern, pair_id, h_values_str)
        e.g., [('two_combination_H64_H512', 'pair_1', 'H64_H512'), ...]
    """
    # Use SRPT as reference algorithm to discover combinations
    ref_algo = 'SRPT'
    ref_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{ref_algo}_result", case_type, combo_type)

    if not os.path.exists(ref_dir):
        return []

    files = os.listdir(ref_dir)

    combinations = set()

    for f in files:
        if combo_type == 'two_result':
            match = re.match(r'(two_combination_[^_]+_[^_]+)_(pair_\d+)_', f)
        elif combo_type == 'three_result':
            match = re.match(r'(three_combination_[^_]+_[^_]+_[^_]+)_(triplet_\d+)_', f)
        elif combo_type == 'four_result':
            match = re.match(r'(four_combination_[^_]+_[^_]+_[^_]+_[^_]+)_(quadruplet_\d+)_', f)
        else:
            continue

        if match:
            prefix = match.group(1)
            pair_id = match.group(2)
            h_values = prefix.replace('two_combination_', '').replace('three_combination_', '').replace('four_combination_', '')
            combinations.add((prefix, pair_id, h_values))

    return sorted(combinations)


# ============================================================================
# BEST MODE SELECTION
# ============================================================================

def find_best_mode():
    """
    Find the best mode (2-5) for Dynamic algorithms.
    Uses Bounded_Pareto_random data to determine which mode most frequently
    has the lowest L2 norm flow time.

    Returns:
        int: Best mode number (2, 3, 4, or 5)
    """
    global BEST_MODE

    if BEST_MODE is not None:
        return BEST_MODE

    logger.info("Finding best mode for Dynamic algorithms (modes 2-5 only)...")

    algorithm = 'Dynamic'
    case_type = 'Bounded_Pareto_random_result'

    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", case_type)

    if not os.path.exists(algorithm_dir):
        logger.warning(f"Directory not found: {algorithm_dir}, defaulting to mode 5")
        BEST_MODE = 5
        return BEST_MODE

    pattern = os.path.join(algorithm_dir, f"{case_type}_{algorithm}_njobs100_*.csv")
    files = sorted(glob.glob(pattern))[:NUM_RUNS]

    if not files:
        logger.warning(f"No files found for {algorithm}, defaulting to mode 5")
        BEST_MODE = 5
        return BEST_MODE

    all_dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_dfs.append(df)
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue

    if not all_dfs:
        BEST_MODE = 5
        return BEST_MODE

    combined_df = pd.concat(all_dfs, ignore_index=True)

    mode_cols = [f'{algorithm}_njobs100_mode{i}_L2_norm_flow_time' for i in range(2, 6)]
    existing_cols = [col for col in mode_cols if col in combined_df.columns]

    if not existing_cols:
        logger.warning("No mode columns found, defaulting to mode 5")
        BEST_MODE = 5
        return BEST_MODE

    grouped = combined_df.groupby('frequency')[existing_cols].mean().reset_index()

    mode_win_counts = {i: 0 for i in range(2, 6)}

    for _, row in grouped.iterrows():
        mode_values = {}
        for i in range(2, 6):
            col_name = f'{algorithm}_njobs100_mode{i}_L2_norm_flow_time'
            if col_name in grouped.columns and pd.notna(row[col_name]):
                mode_values[i] = row[col_name]

        if mode_values:
            best_mode = min(mode_values.items(), key=lambda x: x[1])[0]
            mode_win_counts[best_mode] += 1

    BEST_MODE = max(mode_win_counts.items(), key=lambda x: x[1])[0]

    logger.info(f"Best mode for all Dynamic algorithms: mode{BEST_MODE}")
    logger.info(f"Mode win counts: {mode_win_counts}")

    return BEST_MODE


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_non_combination_data(algorithm, case_type):
    """
    Load non-combination data for an algorithm and average over runs.
    """
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", case_type)

    if not os.path.exists(algorithm_dir):
        return None

    if algorithm in DYNAMIC_ALGORITHMS:
        pattern = os.path.join(algorithm_dir, f"{case_type}_{algorithm}_njobs100_*.csv")
    else:
        pattern = os.path.join(algorithm_dir, f"{case_type}_{algorithm}_*.csv")

    files = sorted(glob.glob(pattern))[:NUM_RUNS]

    if not files:
        return None

    all_dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_dfs.append(df)
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue

    if not all_dfs:
        return None

    combined_df = pd.concat(all_dfs, ignore_index=True)

    if algorithm in DYNAMIC_ALGORITHMS:
        best_mode = find_best_mode()
        l2_col = f'{algorithm}_njobs100_mode{best_mode}_L2_norm_flow_time'
        max_col = f'{algorithm}_njobs100_mode{best_mode}_maximum_flow_time'

        agg_cols = {}
        if l2_col in combined_df.columns:
            agg_cols[l2_col] = 'mean'
        if max_col in combined_df.columns:
            agg_cols[max_col] = 'mean'

        if not agg_cols:
            return None

        grouped = combined_df.groupby('frequency').agg(agg_cols).reset_index()

        if l2_col in grouped.columns:
            grouped[f'{algorithm}_L2_norm_flow_time'] = grouped[l2_col]
        if max_col in grouped.columns:
            grouped[f'{algorithm}_maximum_flow_time'] = grouped[max_col]
    else:
        l2_col = f'{algorithm}_L2_norm_flow_time'
        max_col = f'{algorithm}_maximum_flow_time'

        agg_cols = {}
        if l2_col in combined_df.columns:
            agg_cols[l2_col] = 'mean'
        if max_col in combined_df.columns:
            agg_cols[max_col] = 'mean'

        if not agg_cols:
            return None

        grouped = combined_df.groupby('frequency').agg(agg_cols).reset_index()

    return grouped


def load_combination_data(algorithm, case_type, combo_type, prefix, pair_id):
    """
    Load combination data for a specific pair and average over runs.
    """
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", case_type, combo_type)

    if not os.path.exists(algorithm_dir):
        return None

    if algorithm in DYNAMIC_ALGORITHMS:
        pattern = os.path.join(algorithm_dir, f"{prefix}_{pair_id}_{algorithm}_njobs100_*.csv")
    else:
        pattern = os.path.join(algorithm_dir, f"{prefix}_{pair_id}_{algorithm}_*_result.csv")

    files = sorted(glob.glob(pattern))[:NUM_RUNS]

    if not files:
        return None

    all_dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_dfs.append(df)
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue

    if not all_dfs:
        return None

    combined_df = pd.concat(all_dfs, ignore_index=True)

    if algorithm in DYNAMIC_ALGORITHMS:
        best_mode = find_best_mode()
        l2_col = f'{algorithm}_njobs100_mode{best_mode}_L2_norm_flow_time'
        max_col = f'{algorithm}_njobs100_mode{best_mode}_maximum_flow_time'

        agg_cols = {}
        if l2_col in combined_df.columns:
            agg_cols[l2_col] = 'mean'
        if max_col in combined_df.columns:
            agg_cols[max_col] = 'mean'

        if not agg_cols:
            return None

        grouped = combined_df.groupby('frequency').agg(agg_cols).reset_index()

        if l2_col in grouped.columns:
            grouped[f'{algorithm}_L2_norm_flow_time'] = grouped[l2_col]
        if max_col in grouped.columns:
            grouped[f'{algorithm}_maximum_flow_time'] = grouped[max_col]
    else:
        l2_col = f'{algorithm}_L2_norm_flow_time'
        max_col = f'{algorithm}_maximum_flow_time'

        agg_cols = {}
        if l2_col in combined_df.columns:
            agg_cols[l2_col] = 'mean'
        if max_col in combined_df.columns:
            agg_cols[max_col] = 'mean'

        if not agg_cols:
            return None

        grouped = combined_df.groupby('frequency').agg(agg_cols).reset_index()

    return grouped


# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_comparison(data_dict, algorithms, metric, title, output_file, metric_label=None):
    """
    Create a comparison plot for given algorithms with high contrast colors.

    For two-algorithm comparisons:
    - If one is ours and one is adversary: Our algorithm = Red, Adversary = Blue
    - If both are ours: First = Red solid line with filled marker, Second = Blue dotted line with hollow marker
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    plotted_any = False

    # Check if this is a two-algorithm comparison
    valid_algorithms = [a for a in algorithms if a in data_dict and data_dict[a] is not None]
    is_two_algo_comparison = len(valid_algorithms) == 2

    # Check if both algorithms in two-algo comparison are ours
    both_ours = is_two_algo_comparison and all(a in OUR_ALGORITHMS for a in valid_algorithms)

    algo_index = 0  # Track position for both-ours case

    for algorithm in algorithms:
        if algorithm not in data_dict or data_dict[algorithm] is None:
            continue

        df = data_dict[algorithm]
        col_name = f'{algorithm}_{metric}'

        if col_name not in df.columns:
            logger.warning(f"Column {col_name} not found in {algorithm} data. Available: {df.columns.tolist()}")
            continue

        df = df.sort_values('frequency')

        # Determine styling based on comparison type
        if is_two_algo_comparison:
            if both_ours:
                # Both algorithms are ours
                if algo_index == 0:
                    # First algorithm: Red solid line, filled marker
                    color = '#FF0000'
                    linestyle = '-'
                    linewidth = 3.5
                    markersize = 14
                    fillstyle = 'full'
                    markeredgecolor = 'white'
                else:
                    # Second algorithm: Blue dotted line, hollow marker
                    color = '#0000FF'
                    linestyle = '--'
                    linewidth = 3.0
                    markersize = 12
                    fillstyle = 'none'
                    markeredgecolor = color
                zorder = 10 - algo_index
            else:
                # One ours, one adversary
                if algorithm in OUR_ALGORITHMS:
                    color = '#FF0000'  # Red for our algorithm
                    linestyle = '-'
                    linewidth = 3.5
                    markersize = 14
                    fillstyle = 'full'
                    markeredgecolor = 'white'
                    zorder = 10
                else:
                    color = '#0000FF'  # Blue for adversary
                    linestyle = '--'
                    linewidth = 3.0
                    markersize = 12
                    fillstyle = 'none'
                    markeredgecolor = color
                    zorder = 5
        else:
            # Multi-algorithm comparison - use standard colors
            color = ALGORITHM_COLORS.get(algorithm, 'black')
            if algorithm in SOLID_LINE_ALGORITHMS:
                linestyle = '-'
                linewidth = 3.5
                markersize = 14
                zorder = 10
            else:
                linestyle = '--'
                linewidth = 2.5
                markersize = 10
                zorder = 5
            fillstyle = 'full'
            markeredgecolor = 'white'

        # Label - NO mode suffix for Dynamic algorithms
        label = algorithm

        ax.plot(df['frequency'], df[col_name],
               marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
               color=color,
               linewidth=linewidth,
               markersize=markersize,
               linestyle=linestyle,
               markeredgewidth=2.0,
               markeredgecolor=markeredgecolor,
               fillstyle=fillstyle,
               label=label,
               zorder=zorder)
        plotted_any = True
        algo_index += 1

    if not plotted_any:
        plt.close()
        return False

    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)

    if metric_label:
        ax.set_ylabel(metric_label, fontweight='bold', fontsize=14)
    elif metric == 'L2_norm_flow_time':
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold', fontsize=14)
    else:
        ax.set_ylabel('Maximum Flow Time', fontweight='bold', fontsize=14)

    ax.set_xscale('log', base=2)
    ax.set_yscale('log')

    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    ax.set_xlim(left=2)

    ax.set_title(title, fontweight='bold', fontsize=14, pad=15)
    ax.legend(loc='best', framealpha=0.95, fontsize=11, ncol=2)
    ax.grid(True, alpha=0.3, which='both', linestyle='-', linewidth=0.5)

    plt.tight_layout()

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")
    return True


# ============================================================================
# PLOT GROUP FUNCTIONS
# ============================================================================

def create_plots_for_case(data_dict, output_dir, case_name, has_max_flow_time=True):
    """
    Create all comparison plots for a given case.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Group A: Dynamic_BAL vs BAL (two-algo: Dynamic_BAL=red, BAL=blue)
    plot_comparison(
        data_dict,
        ['Dynamic_BAL', 'BAL'],
        'L2_norm_flow_time',
        f'Dynamic_BAL vs BAL - L2 Norm Flow Time\n{case_name}',
        os.path.join(output_dir, 'Dynamic_BAL_vs_BAL_L2.pdf')
    )

    # Check if max flow time data exists for Dynamic_BAL or BAL
    dynamic_bal_has_max = ('Dynamic_BAL' in data_dict and data_dict['Dynamic_BAL'] is not None and
                           'Dynamic_BAL_maximum_flow_time' in data_dict['Dynamic_BAL'].columns)
    bal_has_max = ('BAL' in data_dict and data_dict['BAL'] is not None and
                   'BAL_maximum_flow_time' in data_dict['BAL'].columns)
    if has_max_flow_time and (dynamic_bal_has_max or bal_has_max):
        plot_comparison(
            data_dict,
            ['Dynamic_BAL', 'BAL'],
            'maximum_flow_time',
            f'Dynamic_BAL vs BAL - Maximum Flow Time\n{case_name}',
            os.path.join(output_dir, 'Dynamic_BAL_vs_BAL_max.pdf')
        )

    # Group B: Dynamic vs SRPT (two-algo: Dynamic=red, SRPT=blue)
    plot_comparison(
        data_dict,
        ['Dynamic', 'SRPT'],
        'L2_norm_flow_time',
        f'Dynamic vs SRPT - L2 Norm Flow Time\n{case_name}',
        os.path.join(output_dir, 'Dynamic_vs_SRPT_L2.pdf')
    )

    # Group C: Dynamic vs Dynamic_BAL (both are ours - use standard colors)
    plot_comparison(
        data_dict,
        ['Dynamic', 'Dynamic_BAL'],
        'L2_norm_flow_time',
        f'Dynamic vs Dynamic_BAL - L2 Norm Flow Time\n{case_name}',
        os.path.join(output_dir, 'Dynamic_vs_Dynamic_BAL_L2.pdf')
    )

    # Group D: Clairvoyant Algorithms (includes Dynamic and Dynamic_BAL)
    plot_comparison(
        data_dict,
        CLAIRVOYANT_ALGORITHMS,
        'L2_norm_flow_time',
        f'Clairvoyant Algorithms - L2 Norm Flow Time\n{case_name}',
        os.path.join(output_dir, 'Clairvoyant_comparison_L2.pdf')
    )

    # Group E: RFDynamic vs RMLF (two-algo: RFDynamic=red, RMLF=blue)
    plot_comparison(
        data_dict,
        ['RFDynamic', 'RMLF'],
        'L2_norm_flow_time',
        f'RFDynamic vs RMLF - L2 Norm Flow Time\n{case_name}',
        os.path.join(output_dir, 'RFDynamic_vs_RMLF_L2.pdf')
    )

    # Check if max flow time data exists for RFDynamic or RMLF
    rfdynamic_has_max = ('RFDynamic' in data_dict and data_dict['RFDynamic'] is not None and
                         'RFDynamic_maximum_flow_time' in data_dict['RFDynamic'].columns)
    rmlf_has_max = ('RMLF' in data_dict and data_dict['RMLF'] is not None and
                    'RMLF_maximum_flow_time' in data_dict['RMLF'].columns)
    if has_max_flow_time and (rfdynamic_has_max or rmlf_has_max):
        plot_comparison(
            data_dict,
            ['RFDynamic', 'RMLF'],
            'maximum_flow_time',
            f'RFDynamic vs RMLF - Maximum Flow Time\n{case_name}',
            os.path.join(output_dir, 'RFDynamic_vs_RMLF_max.pdf')
        )

    # Group F: Non-Clairvoyant Algorithms
    plot_comparison(
        data_dict,
        NON_CLAIRVOYANT_ALGORITHMS,
        'L2_norm_flow_time',
        f'Non-Clairvoyant Algorithms - L2 Norm Flow Time\n{case_name}',
        os.path.join(output_dir, 'NonClairvoyant_comparison_L2.pdf')
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def process_non_combination_cases():
    """Process non-combination cases (Bounded_Pareto_random, softrandom)"""
    logger.info("\n" + "=" * 80)
    logger.info("Processing Non-Combination Cases")
    logger.info("=" * 80)

    for case_type in NON_COMBINATION_CASES:
        logger.info(f"\nProcessing {case_type}...")

        data_dict = {}
        for algorithm in ALL_ALGORITHMS:
            df = load_non_combination_data(algorithm, case_type)
            if df is not None:
                data_dict[algorithm] = df
                # Debug: Check what columns are available
                logger.info(f"  {algorithm} columns: {[c for c in df.columns if 'maximum' in c.lower() or 'L2' in c]}")

        if not data_dict:
            logger.warning(f"No data found for {case_type}")
            continue

        logger.info(f"Loaded algorithms: {list(data_dict.keys())}")

        case_name = case_type.replace('_result', '')
        output_dir = os.path.join(OUTPUT_PATH, case_name)

        create_plots_for_case(data_dict, output_dir, case_name, has_max_flow_time=True)


def process_combination_cases():
    """Process combination cases with new file naming pattern"""
    logger.info("\n" + "=" * 80)
    logger.info("Processing Combination Cases")
    logger.info("=" * 80)

    combo_types = ['two_result', 'three_result', 'four_result']

    for case_type in COMBINATION_CASES:
        logger.info(f"\nProcessing {case_type}...")

        for combo_type in combo_types:
            logger.info(f"  Processing {combo_type}...")

            combinations = discover_combinations(case_type, combo_type)

            if not combinations:
                logger.warning(f"    No combinations found in {case_type}/{combo_type}")
                continue

            logger.info(f"    Found {len(combinations)} combinations")

            for prefix, pair_id, h_values in combinations:
                logger.info(f"      Processing {prefix} ({pair_id})...")

                data_dict = {}
                for algorithm in ALL_ALGORITHMS:
                    df = load_combination_data(algorithm, case_type, combo_type, prefix, pair_id)
                    if df is not None:
                        data_dict[algorithm] = df

                if not data_dict:
                    logger.warning(f"        No data found for {prefix}/{pair_id}")
                    continue

                case_name = case_type.replace('_result', '')
                output_dir = os.path.join(OUTPUT_PATH, case_name, combo_type, f"{prefix}_{pair_id}")

                # Check if max_flow_time is available
                has_max = any(f'{algo}_maximum_flow_time' in df.columns
                             for algo, df in data_dict.items() if df is not None)

                create_plots_for_case(
                    data_dict,
                    output_dir,
                    f"{case_name}\n{h_values} / {pair_id}",
                    has_max_flow_time=has_max
                )


def main():
    """Main execution function"""
    logger.info("\n" + "=" * 80)
    logger.info("ALGORITHM COMPARISON PLOTTER - STARTING")
    logger.info("=" * 80)

    best_mode = find_best_mode()
    logger.info(f"Using mode{best_mode} for all Dynamic algorithms")

    process_non_combination_cases()
    process_combination_cases()

    logger.info("\n" + "=" * 80)
    logger.info("ALL TASKS COMPLETED SUCCESSFULLY!")
    logger.info(f"Output directory: {OUTPUT_PATH}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
