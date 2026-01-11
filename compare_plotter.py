#!/usr/bin/env python3
"""
Algorithm Comparison Plotter - Chapter 4 Comprehensive Figures

Features:
1. Finds best mode (2-5) for Dynamic algorithms based on frequency of lowest L2 norm
2. All Dynamic algorithms (Dynamic, Dynamic_BAL, RFDynamic) use the same mode
3. Creates comparison plots for different algorithm groups
4. Strategy selection percentage plots (SRPT/BAL/RMLF vs FCFS)
5. Coherence time effect analysis
6. Distribution characteristic analysis
7. Longest consecutive H duration ratio plots
8. X-axis: coherence time (frequency), Y-axis: various metrics
9. Solid lines for Dynamic algorithms, SRPT, RMLF; dotted for others
10. High contrast colors for better visibility
11. Output format: PDF
12. Two-algorithm comparisons: Red for our algorithm, Blue for adversary
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
ANALYSIS_PATH = os.path.join(BASE_DATA_PATH, "Analysis")  # For Dynamic_analysis, etc.
LONGEST_H_ANALYSIS_PATH = os.path.join(BASE_DATA_PATH, "analysis")  # For longest_h data (lowercase)
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
# STRATEGY SELECTION DATA LOADING
# ============================================================================

def load_strategy_selection_data(algorithm, analysis_type='avg_30'):
    """
    Load strategy selection percentage data from Analysis directory.

    Args:
        algorithm: 'Dynamic', 'Dynamic_BAL', or 'RFDynamic'
        analysis_type: 'avg_30' or 'Random'

    Returns:
        dict: {mode: DataFrame with bp_L, bp_H, FCFS_percentage, strategy_percentage}
    """
    base_dir = os.path.join(ANALYSIS_PATH, f"{algorithm}_analysis", analysis_type)

    if not os.path.exists(base_dir):
        return None

    # Map algorithm to strategy column name
    strategy_map = {
        'Dynamic': 'SRPT_percentage',
        'Dynamic_BAL': 'BAL_percentage',
        'RFDynamic': 'RMLF_percentage'
    }

    strategy_col = strategy_map.get(algorithm)
    if not strategy_col:
        return None

    mode_data = {}

    for mode in range(1, 7):
        mode_dir = os.path.join(base_dir, f"mode_{mode}")
        if not os.path.exists(mode_dir):
            continue

        pattern = os.path.join(mode_dir, f"{algorithm}_{analysis_type}_nJobsPerRound_100_mode_{mode}_round_*.csv")
        files = sorted(glob.glob(pattern))[:NUM_RUNS]

        if not files:
            continue

        all_dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                all_dfs.append(df)
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                continue

        if not all_dfs:
            continue

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Average by bp_L and bp_H
        group_cols = ['bp_L', 'bp_H']
        agg_cols = {
            'FCFS_percentage': 'mean',
            strategy_col: 'mean',
            'total_rounds': 'mean'
        }

        # Filter to only include columns that exist
        agg_cols = {k: v for k, v in agg_cols.items() if k in combined_df.columns}

        if agg_cols:
            grouped = combined_df.groupby(group_cols).agg(agg_cols).reset_index()
            grouped['strategy_percentage'] = grouped.get(strategy_col, 0)
            mode_data[mode] = grouped

    return mode_data


def load_longest_h_data(case_type):
    """
    Load longest consecutive H duration ratio data from analysis directory (lowercase).

    Args:
        case_type: e.g., 'Bounded_Pareto_random', 'Bounded_Pareto_combination_random'

    Returns:
        DataFrame with frequency and longest_H_percentage columns
    """
    analysis_dir = os.path.join(LONGEST_H_ANALYSIS_PATH, case_type)

    if not os.path.exists(analysis_dir):
        return None

    data = []

    # Check for frequency directories
    for item in os.listdir(analysis_dir):
        if item.startswith('freq_'):
            freq = int(item.replace('freq_', ''))
            analysis_file = os.path.join(analysis_dir, item, 'analysis.csv')

            if os.path.exists(analysis_file):
                try:
                    df = pd.read_csv(analysis_file, encoding='utf-8-sig')
                    if len(df) > 0:
                        # Get the percentage value (second column)
                        pct = df.iloc[0, 1] if len(df.columns) > 1 else 0
                        data.append({'frequency': freq, 'longest_H_percentage': pct})
                except Exception as e:
                    logger.warning(f"Error reading {analysis_file}: {e}")

    if not data:
        return None

    return pd.DataFrame(data).sort_values('frequency')


def load_combination_longest_h_data(case_type, combo_name):
    """
    Load longest consecutive H duration ratio data for combination cases.

    Args:
        case_type: e.g., 'Bounded_Pareto_combination_random'
        combo_name: e.g., 'two_combination_H64_H512'

    Returns:
        DataFrame with frequency and longest_H_percentage columns
    """
    analysis_dir = os.path.join(LONGEST_H_ANALYSIS_PATH, case_type, combo_name)

    if not os.path.exists(analysis_dir):
        return None

    data = []

    for item in os.listdir(analysis_dir):
        if item.startswith('freq_'):
            freq = int(item.replace('freq_', ''))
            analysis_file = os.path.join(analysis_dir, item, 'analysis.csv')

            if os.path.exists(analysis_file):
                try:
                    df = pd.read_csv(analysis_file, encoding='utf-8-sig')
                    if len(df) > 0:
                        pct = df.iloc[0, 1] if len(df.columns) > 1 else 0
                        data.append({'frequency': freq, 'longest_H_percentage': pct})
                except Exception as e:
                    logger.warning(f"Error reading {analysis_file}: {e}")

    if not data:
        return None

    return pd.DataFrame(data).sort_values('frequency')


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


def plot_strategy_selection(algorithm, mode_data, output_dir, analysis_type='avg_30'):
    """
    Create strategy selection percentage plots.
    Shows how often SRPT/BAL/RMLF vs FCFS is selected under different conditions.

    Creates separate plots for:
    - Bounded Pareto (bp_L < bp_H): heavy-tail distribution
    - Normal distribution (bp_L >= bp_H): L=30, H=std values like 6,9,12,15,18
    """
    setup_plot_style()

    strategy_name_map = {
        'Dynamic': 'SRPT',
        'Dynamic_BAL': 'BAL',
        'RFDynamic': 'RMLF'
    }

    strategy_name = strategy_name_map.get(algorithm, 'Strategy')

    best_mode = find_best_mode()
    if best_mode not in mode_data:
        logger.warning(f"Best mode {best_mode} not found for {algorithm}")
        return

    df = mode_data[best_mode]

    # Separate into Bounded Pareto (L < H) and Normal (L >= H)
    bounded_pareto = df[df['bp_L'] < df['bp_H']].copy()
    normal_dist = df[df['bp_L'] >= df['bp_H']].copy()

    # Plot 1: Bounded Pareto - Strategy selection by H value
    if len(bounded_pareto) > 0:
        fig, ax = plt.subplots(figsize=(14, 8))

        # Group by bp_H and get average strategy percentage
        grouped = bounded_pareto.groupby('bp_H')['strategy_percentage'].mean().reset_index()
        grouped = grouped.sort_values('bp_H')

        ax.bar(range(len(grouped)), grouped['strategy_percentage'],
               color='#FF0000', alpha=0.8, label=f'{strategy_name} Selection %')

        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels([f'{int(h)}' for h in grouped['bp_H']], rotation=45)
        ax.set_xlabel('Upper Bound (H)', fontweight='bold', fontsize=14)
        ax.set_ylabel('Strategy Selection Percentage (%)', fontweight='bold', fontsize=14)
        ax.set_title(f'{algorithm}: {strategy_name} vs FCFS Selection Rate\n(Bounded Pareto Distribution, Mode {best_mode})',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 105)

        plt.tight_layout()
        output_file = os.path.join(output_dir, f'{algorithm}_strategy_selection_bounded_pareto.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {output_file}")

    # Plot 2: Normal Distribution - Strategy selection by std (bp_H)
    # Show stacked bars with FCFS and Strategy percentages
    if len(normal_dist) > 0:
        fig, ax = plt.subplots(figsize=(14, 8))

        # Get both FCFS and strategy percentages
        agg_dict = {'strategy_percentage': 'mean'}
        if 'FCFS_percentage' in normal_dist.columns:
            agg_dict['FCFS_percentage'] = 'mean'
        grouped = normal_dist.groupby('bp_H').agg(agg_dict).reset_index()
        grouped = grouped.sort_values('bp_H')

        x = range(len(grouped))
        width = 0.35

        # Plot FCFS bars (bottom) and Strategy bars (stacked on top)
        if 'FCFS_percentage' in grouped.columns:
            ax.bar(x, grouped['FCFS_percentage'], width,
                   color='#808080', alpha=0.8, label='FCFS Selection %')
            ax.bar([i + width for i in x], grouped['strategy_percentage'], width,
                   color='#FF0000', alpha=0.8, label=f'{strategy_name} Selection %')
        else:
            ax.bar(x, grouped['strategy_percentage'], width,
                   color='#FF0000', alpha=0.8, label=f'{strategy_name} Selection %')

        ax.set_xticks([i + width/2 for i in x])
        ax.set_xticklabels([f'{int(h)}' for h in grouped['bp_H']], rotation=45)
        ax.set_xlabel('Standard Deviation (σ)', fontweight='bold', fontsize=14)
        ax.set_ylabel('Strategy Selection Percentage (%)', fontweight='bold', fontsize=14)
        ax.set_title(f'{algorithm}: {strategy_name} vs FCFS Selection Rate\n(Normal Distribution, Mode {best_mode})',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 105)

        plt.tight_layout()
        output_file = os.path.join(output_dir, f'{algorithm}_strategy_selection_normal.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {output_file}")

    # Plot 3: Heatmap - Strategy selection by bp_L and bp_H (Bounded Pareto only)
    if len(bounded_pareto) > 0:
        fig, ax = plt.subplots(figsize=(14, 10))

        pivot = bounded_pareto.pivot_table(
            values='strategy_percentage',
            index='bp_L',
            columns='bp_H',
            aggfunc='mean'
        )

        im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([f'{int(h)}' for h in pivot.columns], rotation=45)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([f'{l:.2f}' for l in pivot.index])

        ax.set_xlabel('Upper Bound (H)', fontweight='bold', fontsize=14)
        ax.set_ylabel('Lower Bound (L)', fontweight='bold', fontsize=14)
        ax.set_title(f'{algorithm}: {strategy_name} Selection Percentage Heatmap\n(Bounded Pareto, Mode {best_mode})',
                     fontweight='bold', fontsize=14)

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(f'{strategy_name} Selection %', fontweight='bold')

        plt.tight_layout()
        output_file = os.path.join(output_dir, f'{algorithm}_strategy_selection_heatmap.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {output_file}")


def plot_ratio_comparison(data_dict, our_algo, baseline_algo, metric, title, output_file, metric_label=None):
    """
    Create a ratio plot: our_algo / baseline_algo for the given metric.
    Shows how much better (ratio < 1) or worse (ratio > 1) our algorithm performs.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    if our_algo not in data_dict or baseline_algo not in data_dict:
        plt.close()
        return False

    our_df = data_dict[our_algo]
    baseline_df = data_dict[baseline_algo]

    if our_df is None or baseline_df is None:
        plt.close()
        return False

    our_col = f'{our_algo}_{metric}'
    baseline_col = f'{baseline_algo}_{metric}'

    if our_col not in our_df.columns or baseline_col not in baseline_df.columns:
        plt.close()
        return False

    # Merge on frequency
    merged = pd.merge(
        our_df[['frequency', our_col]],
        baseline_df[['frequency', baseline_col]],
        on='frequency'
    )

    if len(merged) == 0:
        plt.close()
        return False

    # Calculate ratio
    merged['ratio'] = merged[our_col] / merged[baseline_col]
    merged = merged.sort_values('frequency')

    # Plot ratio
    ax.plot(merged['frequency'], merged['ratio'],
           marker='o', color='#FF0000', linewidth=3.0, markersize=10,
           label=f'{our_algo} / {baseline_algo}')

    # Add reference line at ratio = 1
    ax.axhline(y=1.0, color='#0000FF', linestyle='--', linewidth=2.0, alpha=0.7, label='Ratio = 1')

    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)

    if metric_label:
        ax.set_ylabel(metric_label, fontweight='bold', fontsize=14)
    else:
        ax.set_ylabel(f'{metric} Ratio', fontweight='bold', fontsize=14)

    ax.set_xscale('log', base=2)

    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    ax.set_xlim(left=2)

    ax.set_title(title, fontweight='bold', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_file}")
    return True


def plot_strategy_comparison(algo1, algo2, mode_data1, mode_data2, output_dir):
    """
    Create strategy selection comparison between two Dynamic algorithms.
    Shows side-by-side comparison of strategy selection percentages.
    """
    setup_plot_style()

    strategy_name_map = {
        'Dynamic': 'SRPT',
        'Dynamic_BAL': 'BAL',
        'RFDynamic': 'RMLF'
    }

    best_mode = find_best_mode()

    if best_mode not in mode_data1 or best_mode not in mode_data2:
        logger.warning(f"Best mode {best_mode} not found for strategy comparison")
        return

    df1 = mode_data1[best_mode]
    df2 = mode_data2[best_mode]

    # Bounded Pareto comparison
    bp1 = df1[df1['bp_L'] < df1['bp_H']].copy()
    bp2 = df2[df2['bp_L'] < df2['bp_H']].copy()

    if len(bp1) > 0 and len(bp2) > 0:
        fig, ax = plt.subplots(figsize=(14, 8))

        grouped1 = bp1.groupby('bp_H')['strategy_percentage'].mean().reset_index()
        grouped2 = bp2.groupby('bp_H')['strategy_percentage'].mean().reset_index()

        # Merge on bp_H
        merged = pd.merge(grouped1, grouped2, on='bp_H', suffixes=('_1', '_2'))
        merged = merged.sort_values('bp_H')

        x = np.arange(len(merged))
        width = 0.35

        ax.bar(x - width/2, merged['strategy_percentage_1'], width,
               color='#FF0000', alpha=0.8, label=f'{algo1} ({strategy_name_map.get(algo1, "Strategy")})')
        ax.bar(x + width/2, merged['strategy_percentage_2'], width,
               color='#0000FF', alpha=0.8, label=f'{algo2} ({strategy_name_map.get(algo2, "Strategy")})')

        ax.set_xticks(x)
        ax.set_xticklabels([f'{int(h)}' for h in merged['bp_H']], rotation=45)
        ax.set_xlabel('Upper Bound (H)', fontweight='bold', fontsize=14)
        ax.set_ylabel('Strategy Selection Percentage (%)', fontweight='bold', fontsize=14)
        ax.set_title(f'{algo1} vs {algo2}: Strategy Selection Comparison\n(Bounded Pareto, Mode {best_mode})',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 105)

        plt.tight_layout()
        output_file = os.path.join(output_dir, f'{algo1}_vs_{algo2}_strategy_comparison.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {output_file}")


def plot_h_value_performance(output_dir):
    """
    Create performance comparison across different H values (Figure 4.11).
    Shows how algorithm performance changes with different upper bounds.
    """
    setup_plot_style()

    # Use combination data to compare different H values
    case_type = 'Bounded_Pareto_combination_random_result'
    combo_type = 'two_result'

    combinations = discover_combinations(case_type, combo_type)
    if not combinations:
        logger.warning("No combinations found for H value comparison")
        return

    # Collect data for each H combination
    h_performance = {}

    for prefix, pair_id, h_values in combinations:
        # Load Dynamic_BAL and BAL data
        dynamic_bal_df = load_combination_data('Dynamic_BAL', case_type, combo_type, prefix, pair_id)
        bal_df = load_combination_data('BAL', case_type, combo_type, prefix, pair_id)

        if dynamic_bal_df is None or bal_df is None:
            continue

        # Calculate average L2 norm across all frequencies
        if 'Dynamic_BAL_L2_norm_flow_time' in dynamic_bal_df.columns and 'BAL_L2_norm_flow_time' in bal_df.columns:
            avg_ratio = (dynamic_bal_df['Dynamic_BAL_L2_norm_flow_time'].mean() /
                        bal_df['BAL_L2_norm_flow_time'].mean())
            h_performance[h_values] = avg_ratio

    if not h_performance:
        logger.warning("No data for H value performance comparison")
        return

    fig, ax = plt.subplots(figsize=(14, 8))

    h_labels = list(h_performance.keys())
    ratios = list(h_performance.values())

    ax.bar(range(len(h_labels)), ratios, color='#FF0000', alpha=0.8)
    ax.axhline(y=1.0, color='#0000FF', linestyle='--', linewidth=2.0, alpha=0.7, label='Ratio = 1')

    ax.set_xticks(range(len(h_labels)))
    ax.set_xticklabels(h_labels, rotation=45, ha='right')
    ax.set_xlabel('H Value Combinations', fontweight='bold', fontsize=14)
    ax.set_ylabel('Dynamic_BAL / BAL L2-Norm Ratio', fontweight='bold', fontsize=14)
    ax.set_title('Performance Comparison Across Different H Values', fontweight='bold', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'h_value_performance_comparison.pdf')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_file}")


def plot_job_size_distribution(output_dir):
    """
    Create Job Size Distribution PDF comparison plots (Figure 4.2).
    Shows the probability density function of job sizes for different distributions.
    """
    setup_plot_style()

    # Data path for job size data
    data_path = os.path.join(BASE_DATA_PATH, "data")

    # Plot 1: Bounded Pareto distribution comparison (different H values)
    fig, ax = plt.subplots(figsize=(14, 8))

    # Collect job sizes from different H value combinations
    h_values_to_plot = ['H64_H512', 'H512_H4096', 'H4096_H32768', 'H32768_H262144']
    colors = ['#FF0000', '#0000FF', '#00AA00', '#FF00FF']

    plotted_any = False
    for idx, h_combo in enumerate(h_values_to_plot):
        # Try to find data for this H combination
        combo_dir = os.path.join(data_path, "Bounded_Pareto_combination_random_1", f"two_combination_{h_combo}")
        if not os.path.exists(combo_dir):
            continue

        # Find a frequency directory
        freq_dirs = [d for d in os.listdir(combo_dir) if d.startswith('freq_')]
        if not freq_dirs:
            continue

        # Use middle frequency for representative distribution
        freq_dir = sorted(freq_dirs)[len(freq_dirs)//2]

        # Find CSV file with job data
        csv_files = glob.glob(os.path.join(combo_dir, freq_dir, "*.csv"))
        job_csv = [f for f in csv_files if 'longest_H' not in f]

        if not job_csv:
            continue

        try:
            df = pd.read_csv(job_csv[0])
            if 'job_size' in df.columns:
                job_sizes = df['job_size'].values

                # Create histogram as PDF
                hist, bin_edges = np.histogram(job_sizes, bins=50, density=True)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                ax.plot(bin_centers, hist, color=colors[idx], linewidth=2.5,
                       label=h_combo.replace('_', ' / '), alpha=0.8)
                plotted_any = True
        except Exception as e:
            logger.warning(f"Error reading {job_csv[0]}: {e}")
            continue

    if plotted_any:
        ax.set_xlabel('Job Size', fontweight='bold', fontsize=14)
        ax.set_ylabel('Probability Density', fontweight='bold', fontsize=14)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_title('Job Size Distribution (Bounded Pareto)\nDifferent H Value Combinations',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best', title='H Values')
        ax.grid(True, alpha=0.3, which='both')

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'job_size_distribution_bounded_pareto.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        logger.info(f"Saved: {output_file}")
    plt.close()

    # Plot 2: Bounded Pareto vs Normal distribution comparison
    fig, ax = plt.subplots(figsize=(14, 8))

    plotted_any = False

    # Bounded Pareto (random)
    bp_random_dir = os.path.join(data_path, "Bounded_Pareto_random_1")
    if os.path.exists(bp_random_dir):
        freq_dirs = [d for d in os.listdir(bp_random_dir) if d.startswith('freq_')]
        if freq_dirs:
            freq_dir = sorted(freq_dirs)[len(freq_dirs)//2]
            csv_files = glob.glob(os.path.join(bp_random_dir, freq_dir, "*.csv"))
            job_csv = [f for f in csv_files if 'longest_H' not in f]

            if job_csv:
                try:
                    df = pd.read_csv(job_csv[0])
                    if 'job_size' in df.columns:
                        job_sizes = df['job_size'].values
                        hist, bin_edges = np.histogram(job_sizes, bins=50, density=True)
                        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                        ax.plot(bin_centers, hist, color='#FF0000', linewidth=2.5,
                               label='Bounded Pareto', alpha=0.8)
                        plotted_any = True
                except Exception as e:
                    logger.warning(f"Error: {e}")

    # Normal distribution (avg_30)
    normal_dir = os.path.join(data_path, "avg_30_1")
    if os.path.exists(normal_dir):
        # Find subdirectories
        subdirs = [d for d in os.listdir(normal_dir) if os.path.isdir(os.path.join(normal_dir, d))]
        if subdirs:
            subdir = subdirs[0]
            csv_files = glob.glob(os.path.join(normal_dir, subdir, "*.csv"))
            job_csv = [f for f in csv_files if 'longest_H' not in f]

            if job_csv:
                try:
                    df = pd.read_csv(job_csv[0])
                    if 'job_size' in df.columns:
                        job_sizes = df['job_size'].values
                        hist, bin_edges = np.histogram(job_sizes, bins=50, density=True)
                        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                        ax.plot(bin_centers, hist, color='#0000FF', linewidth=2.5,
                               label='Normal Distribution', alpha=0.8)
                        plotted_any = True
                except Exception as e:
                    logger.warning(f"Error: {e}")

    if plotted_any:
        ax.set_xlabel('Job Size', fontweight='bold', fontsize=14)
        ax.set_ylabel('Probability Density', fontweight='bold', fontsize=14)
        ax.set_title('Job Size Distribution Comparison\nBounded Pareto vs Normal',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, which='both')

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'job_size_distribution_comparison.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        logger.info(f"Saved: {output_file}")
    plt.close()

    # Plot 3: Heavy-tail demonstration (log-log plot showing power law)
    fig, ax = plt.subplots(figsize=(14, 8))

    plotted_any = False

    # Use Bounded Pareto random data
    if os.path.exists(bp_random_dir):
        freq_dirs = [d for d in os.listdir(bp_random_dir) if d.startswith('freq_')]
        if freq_dirs:
            freq_dir = sorted(freq_dirs)[len(freq_dirs)//2]
            csv_files = glob.glob(os.path.join(bp_random_dir, freq_dir, "*.csv"))
            job_csv = [f for f in csv_files if 'longest_H' not in f]

            if job_csv:
                try:
                    df = pd.read_csv(job_csv[0])
                    if 'job_size' in df.columns:
                        job_sizes = df['job_size'].values

                        # CCDF (Complementary Cumulative Distribution Function)
                        sorted_sizes = np.sort(job_sizes)
                        ccdf = 1 - np.arange(1, len(sorted_sizes) + 1) / len(sorted_sizes)

                        ax.plot(sorted_sizes, ccdf, color='#FF0000', linewidth=2.5,
                               label='Bounded Pareto CCDF', alpha=0.8)
                        plotted_any = True
                except Exception as e:
                    logger.warning(f"Error: {e}")

    if plotted_any:
        ax.set_xlabel('Job Size', fontweight='bold', fontsize=14)
        ax.set_ylabel('P(X > x)', fontweight='bold', fontsize=14)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_title('Job Size CCDF (Heavy-Tail Demonstration)\nBounded Pareto Distribution',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, which='both')

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'job_size_ccdf_heavy_tail.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        logger.info(f"Saved: {output_file}")
    plt.close()


def plot_load_performance(output_dir):
    """
    Create performance comparison under different loads (Figure 4.12).
    Shows how algorithm performance varies with arrival rate.
    """
    setup_plot_style()

    # Load strategy selection data which contains arrival_rate
    best_mode = find_best_mode()

    # Plot 1: Performance vs Arrival Rate for Dynamic_BAL
    fig, ax = plt.subplots(figsize=(14, 8))

    plotted_any = False

    for algorithm in ['Dynamic', 'Dynamic_BAL']:
        strategy_col = 'SRPT_percentage' if algorithm == 'Dynamic' else 'BAL_percentage'

        base_dir = os.path.join(ANALYSIS_PATH, f"{algorithm}_analysis", "avg_30")
        mode_dir = os.path.join(base_dir, f"mode_{best_mode}")

        if not os.path.exists(mode_dir):
            continue

        pattern = os.path.join(mode_dir, f"{algorithm}_avg_30_nJobsPerRound_100_mode_{best_mode}_round_*.csv")
        files = sorted(glob.glob(pattern))[:NUM_RUNS]

        if not files:
            continue

        all_dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                all_dfs.append(df)
            except:
                continue

        if not all_dfs:
            continue

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Filter for Bounded Pareto (bp_L < bp_H)
        bp_data = combined_df[combined_df['bp_L'] < combined_df['bp_H']].copy()

        if len(bp_data) > 0 and 'arrival_rate' in bp_data.columns and strategy_col in bp_data.columns:
            # Group by arrival rate
            grouped = bp_data.groupby('arrival_rate')[strategy_col].mean().reset_index()
            grouped = grouped.sort_values('arrival_rate')

            color = '#FF0000' if algorithm == 'Dynamic' else '#0000FF'
            marker = 'o' if algorithm == 'Dynamic' else 's'

            ax.plot(grouped['arrival_rate'], grouped[strategy_col],
                   marker=marker, color=color, linewidth=2.5, markersize=8,
                   label=f'{algorithm} Strategy Selection %')
            plotted_any = True

    if plotted_any:
        ax.set_xlabel('Arrival Rate', fontweight='bold', fontsize=14)
        ax.set_ylabel('Strategy Selection Percentage (%)', fontweight='bold', fontsize=14)
        ax.set_title(f'Strategy Selection vs Arrival Rate\n(Bounded Pareto, Mode {best_mode})',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 105)

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'strategy_vs_arrival_rate.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        logger.info(f"Saved: {output_file}")
    plt.close()

    # Plot 2: Heatmap of strategy selection by arrival_rate and bp_H
    for algorithm in ['Dynamic_BAL', 'RFDynamic']:
        strategy_col = 'BAL_percentage' if algorithm == 'Dynamic_BAL' else 'RMLF_percentage'
        strategy_name = 'BAL' if algorithm == 'Dynamic_BAL' else 'RMLF'

        base_dir = os.path.join(ANALYSIS_PATH, f"{algorithm}_analysis", "avg_30")
        mode_dir = os.path.join(base_dir, f"mode_{best_mode}")

        if not os.path.exists(mode_dir):
            continue

        pattern = os.path.join(mode_dir, f"{algorithm}_avg_30_nJobsPerRound_100_mode_{best_mode}_round_*.csv")
        files = sorted(glob.glob(pattern))[:NUM_RUNS]

        if not files:
            continue

        all_dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                all_dfs.append(df)
            except:
                continue

        if not all_dfs:
            continue

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Filter for Bounded Pareto
        bp_data = combined_df[combined_df['bp_L'] < combined_df['bp_H']].copy()

        if len(bp_data) > 0 and 'arrival_rate' in bp_data.columns and strategy_col in bp_data.columns:
            fig, ax = plt.subplots(figsize=(14, 10))

            try:
                pivot = bp_data.pivot_table(
                    values=strategy_col,
                    index='arrival_rate',
                    columns='bp_H',
                    aggfunc='mean'
                )

                im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

                ax.set_xticks(range(len(pivot.columns)))
                ax.set_xticklabels([f'{int(h)}' for h in pivot.columns], rotation=45)
                ax.set_yticks(range(len(pivot.index)))
                ax.set_yticklabels([f'{r:.0f}' for r in pivot.index])

                ax.set_xlabel('Upper Bound (H)', fontweight='bold', fontsize=14)
                ax.set_ylabel('Arrival Rate', fontweight='bold', fontsize=14)
                ax.set_title(f'{algorithm}: {strategy_name} Selection % by Load and H Value\n(Mode {best_mode})',
                             fontweight='bold', fontsize=14)

                cbar = plt.colorbar(im, ax=ax)
                cbar.set_label(f'{strategy_name} Selection %', fontweight='bold')

                plt.tight_layout()
                output_file = os.path.join(output_dir, f'{algorithm}_load_h_heatmap.pdf')
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                plt.savefig(output_file, format='pdf', bbox_inches='tight')
                logger.info(f"Saved: {output_file}")
            except Exception as e:
                logger.warning(f"Error creating heatmap for {algorithm}: {e}")

            plt.close()

    # Plot 3: Performance comparison across different arrival rates (line plot)
    fig, ax = plt.subplots(figsize=(14, 8))

    plotted_any = False
    colors = {'Dynamic_BAL': '#FF0000', 'RFDynamic': '#0000FF'}
    markers = {'Dynamic_BAL': 'o', 'RFDynamic': 's'}

    for algorithm in ['Dynamic_BAL', 'RFDynamic']:
        strategy_col = 'BAL_percentage' if algorithm == 'Dynamic_BAL' else 'RMLF_percentage'

        base_dir = os.path.join(ANALYSIS_PATH, f"{algorithm}_analysis", "avg_30")
        mode_dir = os.path.join(base_dir, f"mode_{best_mode}")

        if not os.path.exists(mode_dir):
            continue

        pattern = os.path.join(mode_dir, f"{algorithm}_avg_30_nJobsPerRound_100_mode_{best_mode}_round_*.csv")
        files = sorted(glob.glob(pattern))[:NUM_RUNS]

        if not files:
            continue

        all_dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                all_dfs.append(df)
            except:
                continue

        if not all_dfs:
            continue

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Filter for Bounded Pareto
        bp_data = combined_df[combined_df['bp_L'] < combined_df['bp_H']].copy()

        if len(bp_data) > 0 and 'arrival_rate' in bp_data.columns and strategy_col in bp_data.columns:
            grouped = bp_data.groupby('arrival_rate')[strategy_col].mean().reset_index()
            grouped = grouped.sort_values('arrival_rate')

            ax.plot(grouped['arrival_rate'], grouped[strategy_col],
                   marker=markers[algorithm], color=colors[algorithm],
                   linewidth=2.5, markersize=8, label=algorithm)
            plotted_any = True

    if plotted_any:
        ax.set_xlabel('Arrival Rate', fontweight='bold', fontsize=14)
        ax.set_ylabel('Strategy Selection Percentage (%)', fontweight='bold', fontsize=14)
        ax.set_title(f'Algorithm Performance vs Load\n(Bounded Pareto, Mode {best_mode})',
                     fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 105)

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'all_algorithms_load_comparison.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        logger.info(f"Saved: {output_file}")
    plt.close()


def plot_random_vs_softrandom(output_dir):
    """
    Create Random vs Softrandom comparison plots (Figure 4.16).
    Shows side-by-side comparison of performance under different workload patterns.
    """
    setup_plot_style()

    # Load data for both random and softrandom
    random_data = {}
    softrandom_data = {}

    for algorithm in ['Dynamic_BAL', 'BAL', 'RFDynamic', 'RMLF']:
        random_df = load_non_combination_data(algorithm, 'Bounded_Pareto_random_result')
        softrandom_df = load_non_combination_data(algorithm, 'Bounded_Pareto_softrandom_result')

        if random_df is not None:
            random_data[algorithm] = random_df
        if softrandom_df is not None:
            softrandom_data[algorithm] = softrandom_df

    if not random_data or not softrandom_data:
        logger.warning("Missing data for Random vs Softrandom comparison")
        return

    # Plot 1: Dynamic_BAL comparison
    if 'Dynamic_BAL' in random_data and 'Dynamic_BAL' in softrandom_data:
        fig, ax = plt.subplots(figsize=(14, 8))

        random_df = random_data['Dynamic_BAL'].sort_values('frequency')
        softrandom_df = softrandom_data['Dynamic_BAL'].sort_values('frequency')

        if 'Dynamic_BAL_L2_norm_flow_time' in random_df.columns:
            ax.plot(random_df['frequency'], random_df['Dynamic_BAL_L2_norm_flow_time'],
                   marker='o', color='#FF0000', linewidth=3.0, markersize=10,
                   linestyle='-', label='Dynamic_BAL (Random)')

        if 'Dynamic_BAL_L2_norm_flow_time' in softrandom_df.columns:
            ax.plot(softrandom_df['frequency'], softrandom_df['Dynamic_BAL_L2_norm_flow_time'],
                   marker='s', color='#0000FF', linewidth=3.0, markersize=10,
                   linestyle='--', label='Dynamic_BAL (Softrandom)')

        ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold', fontsize=14)
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')

        x_ticks = [2**i for i in range(1, 17)]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
        ax.set_xlim(left=2)

        ax.set_title('Dynamic_BAL: Random vs Softrandom', fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, which='both')

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'Dynamic_BAL_random_vs_softrandom.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {output_file}")

    # Plot 2: RFDynamic comparison
    if 'RFDynamic' in random_data and 'RFDynamic' in softrandom_data:
        fig, ax = plt.subplots(figsize=(14, 8))

        random_df = random_data['RFDynamic'].sort_values('frequency')
        softrandom_df = softrandom_data['RFDynamic'].sort_values('frequency')

        if 'RFDynamic_L2_norm_flow_time' in random_df.columns:
            ax.plot(random_df['frequency'], random_df['RFDynamic_L2_norm_flow_time'],
                   marker='o', color='#FF0000', linewidth=3.0, markersize=10,
                   linestyle='-', label='RFDynamic (Random)')

        if 'RFDynamic_L2_norm_flow_time' in softrandom_df.columns:
            ax.plot(softrandom_df['frequency'], softrandom_df['RFDynamic_L2_norm_flow_time'],
                   marker='s', color='#0000FF', linewidth=3.0, markersize=10,
                   linestyle='--', label='RFDynamic (Softrandom)')

        ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold', fontsize=14)
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')

        x_ticks = [2**i for i in range(1, 17)]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
        ax.set_xlim(left=2)

        ax.set_title('RFDynamic: Random vs Softrandom', fontweight='bold', fontsize=14)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, which='both')

        plt.tight_layout()
        output_file = os.path.join(output_dir, 'RFDynamic_random_vs_softrandom.pdf')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, format='pdf', bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {output_file}")

    # Plot 3: Combined ratio comparison (Random vs Softrandom for all algorithms)
    fig, ax = plt.subplots(figsize=(14, 8))

    algo_pairs = [('Dynamic_BAL', 'BAL'), ('RFDynamic', 'RMLF')]
    colors = ['#FF0000', '#0000FF']
    markers = ['o', 's']

    for idx, (our_algo, baseline_algo) in enumerate(algo_pairs):
        if our_algo in random_data and baseline_algo in random_data:
            our_df = random_data[our_algo].sort_values('frequency')
            baseline_df = random_data[baseline_algo].sort_values('frequency')

            our_col = f'{our_algo}_L2_norm_flow_time'
            baseline_col = f'{baseline_algo}_L2_norm_flow_time'

            if our_col in our_df.columns and baseline_col in baseline_df.columns:
                merged = pd.merge(
                    our_df[['frequency', our_col]],
                    baseline_df[['frequency', baseline_col]],
                    on='frequency'
                )
                merged['ratio'] = merged[our_col] / merged[baseline_col]

                ax.plot(merged['frequency'], merged['ratio'],
                       marker=markers[idx], color=colors[idx], linewidth=2.5, markersize=8,
                       linestyle='-', label=f'{our_algo}/{baseline_algo} (Random)')

        if our_algo in softrandom_data and baseline_algo in softrandom_data:
            our_df = softrandom_data[our_algo].sort_values('frequency')
            baseline_df = softrandom_data[baseline_algo].sort_values('frequency')

            our_col = f'{our_algo}_L2_norm_flow_time'
            baseline_col = f'{baseline_algo}_L2_norm_flow_time'

            if our_col in our_df.columns and baseline_col in baseline_df.columns:
                merged = pd.merge(
                    our_df[['frequency', our_col]],
                    baseline_df[['frequency', baseline_col]],
                    on='frequency'
                )
                merged['ratio'] = merged[our_col] / merged[baseline_col]

                ax.plot(merged['frequency'], merged['ratio'],
                       marker=markers[idx], color=colors[idx], linewidth=2.5, markersize=8,
                       linestyle='--', label=f'{our_algo}/{baseline_algo} (Softrandom)')

    ax.axhline(y=1.0, color='#808080', linestyle=':', linewidth=2.0, alpha=0.7, label='Ratio = 1')

    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)
    ax.set_ylabel('L2-Norm Ratio', fontweight='bold', fontsize=14)
    ax.set_xscale('log', base=2)

    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    ax.set_xlim(left=2)

    ax.set_title('Performance Ratio: Random vs Softrandom Comparison', fontweight='bold', fontsize=14)
    ax.legend(loc='best', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    output_file = os.path.join(output_dir, 'all_algorithms_random_vs_softrandom_ratio.pdf')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_file}")


def plot_longest_h_ratio(df, title, output_file):
    """
    Plot longest consecutive H duration ratio vs coherence time.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    df = df.sort_values('frequency')

    ax.plot(df['frequency'], df['longest_H_percentage'],
           marker='o', color='#FF0000', linewidth=3.0, markersize=10,
           label='Longest Consecutive H Duration Ratio')

    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)
    ax.set_ylabel('Longest H Duration Ratio (%)', fontweight='bold', fontsize=14)
    ax.set_xscale('log', base=2)

    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    ax.set_xlim(left=2)

    ax.set_title(title, fontweight='bold', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_file}")


def plot_mode_comparison_for_algorithm(algorithm, output_dir):
    """
    Create mode comparison plots showing how different modes perform.
    Helps justify the best mode selection.
    """
    case_type = 'Bounded_Pareto_random_result'
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", case_type)

    if not os.path.exists(algorithm_dir):
        return

    pattern = os.path.join(algorithm_dir, f"{case_type}_{algorithm}_njobs100_*.csv")
    files = sorted(glob.glob(pattern))[:NUM_RUNS]

    if not files:
        return

    all_dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_dfs.append(df)
        except Exception as e:
            continue

    if not all_dfs:
        return

    combined_df = pd.concat(all_dfs, ignore_index=True)

    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    mode_colors = {
        1: '#000000',     # Black
        2: '#FF0000',     # Red
        3: '#00AA00',     # Green
        4: '#0000FF',     # Blue
        5: '#FF00FF',     # Magenta
        6: '#FFD700'      # Gold
    }

    for mode in range(1, 7):
        col_name = f'{algorithm}_njobs100_mode{mode}_L2_norm_flow_time'
        if col_name not in combined_df.columns:
            continue

        grouped = combined_df.groupby('frequency')[col_name].mean().reset_index()
        grouped = grouped.sort_values('frequency')

        ax.plot(grouped['frequency'], grouped[col_name],
               marker='o', color=mode_colors[mode], linewidth=2.5, markersize=8,
               label=f'Mode {mode}')

    best_mode = find_best_mode()
    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=14)
    ax.set_ylabel('L2-Norm Flow Time', fontweight='bold', fontsize=14)
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')

    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    ax.set_xlim(left=2)

    ax.set_title(f'{algorithm}: Mode Comparison (Best: Mode {best_mode})', fontweight='bold', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    output_file = os.path.join(output_dir, f'{algorithm}_mode_comparison.pdf')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved: {output_file}")


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

    # Group G: Ratio plots (Figure 4.3, 4.4, 4.8, 4.9)
    # Dynamic_BAL vs BAL L2 ratio
    plot_ratio_comparison(
        data_dict,
        'Dynamic_BAL', 'BAL',
        'L2_norm_flow_time',
        f'Dynamic_BAL vs BAL - L2 Norm Ratio\n{case_name}',
        os.path.join(output_dir, 'Dynamic_BAL_vs_BAL_L2_ratio.pdf'),
        metric_label='L2-Norm Ratio (Dynamic_BAL / BAL)'
    )

    # Dynamic_BAL vs BAL max flow time ratio
    if has_max_flow_time:
        plot_ratio_comparison(
            data_dict,
            'Dynamic_BAL', 'BAL',
            'maximum_flow_time',
            f'Dynamic_BAL vs BAL - Max Flow Time Ratio\n{case_name}',
            os.path.join(output_dir, 'Dynamic_BAL_vs_BAL_max_ratio.pdf'),
            metric_label='Max Flow Time Ratio (Dynamic_BAL / BAL)'
        )

    # RFDynamic vs RMLF L2 ratio
    plot_ratio_comparison(
        data_dict,
        'RFDynamic', 'RMLF',
        'L2_norm_flow_time',
        f'RFDynamic vs RMLF - L2 Norm Ratio\n{case_name}',
        os.path.join(output_dir, 'RFDynamic_vs_RMLF_L2_ratio.pdf'),
        metric_label='L2-Norm Ratio (RFDynamic / RMLF)'
    )

    # RFDynamic vs RMLF max flow time ratio
    if has_max_flow_time:
        plot_ratio_comparison(
            data_dict,
            'RFDynamic', 'RMLF',
            'maximum_flow_time',
            f'RFDynamic vs RMLF - Max Flow Time Ratio\n{case_name}',
            os.path.join(output_dir, 'RFDynamic_vs_RMLF_max_ratio.pdf'),
            metric_label='Max Flow Time Ratio (RFDynamic / RMLF)'
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


def process_strategy_selection():
    """Process strategy selection percentage plots for all Dynamic algorithms"""
    logger.info("\n" + "=" * 80)
    logger.info("Processing Strategy Selection Plots")
    logger.info("=" * 80)

    output_dir = os.path.join(OUTPUT_PATH, 'strategy_selection')
    os.makedirs(output_dir, exist_ok=True)

    mode_data_cache = {}

    for algorithm in DYNAMIC_ALGORITHMS:
        logger.info(f"\nProcessing {algorithm} strategy selection...")

        mode_data = load_strategy_selection_data(algorithm, 'avg_30')

        if mode_data:
            plot_strategy_selection(algorithm, mode_data, output_dir, 'avg_30')
            mode_data_cache[algorithm] = mode_data
        else:
            logger.warning(f"No strategy selection data found for {algorithm}")

    # Figure 4.7: Dynamic vs Dynamic_BAL strategy comparison
    if 'Dynamic' in mode_data_cache and 'Dynamic_BAL' in mode_data_cache:
        logger.info("\nProcessing Dynamic vs Dynamic_BAL strategy comparison...")
        plot_strategy_comparison('Dynamic', 'Dynamic_BAL',
                                mode_data_cache['Dynamic'], mode_data_cache['Dynamic_BAL'],
                                output_dir)


def process_mode_comparison():
    """Process mode comparison plots for all Dynamic algorithms"""
    logger.info("\n" + "=" * 80)
    logger.info("Processing Mode Comparison Plots")
    logger.info("=" * 80)

    output_dir = os.path.join(OUTPUT_PATH, 'mode_comparison')
    os.makedirs(output_dir, exist_ok=True)

    for algorithm in DYNAMIC_ALGORITHMS:
        logger.info(f"\nProcessing {algorithm} mode comparison...")
        plot_mode_comparison_for_algorithm(algorithm, output_dir)


def process_longest_h_plots():
    """Process longest consecutive H duration ratio plots"""
    logger.info("\n" + "=" * 80)
    logger.info("Processing Longest H Duration Plots")
    logger.info("=" * 80)

    output_dir = os.path.join(OUTPUT_PATH, 'longest_h_ratio')
    os.makedirs(output_dir, exist_ok=True)

    # Non-combination cases
    non_combo_cases = ['Bounded_Pareto_random', 'Bounded_Pareto_softrandom',
                       'normal_random', 'normal_softrandom']

    for case_type in non_combo_cases:
        logger.info(f"\nProcessing {case_type}...")

        df = load_longest_h_data(case_type)

        if df is not None:
            plot_longest_h_ratio(
                df,
                f'Longest Consecutive H Duration Ratio\n{case_type}',
                os.path.join(output_dir, f'{case_type}_longest_h.pdf')
            )
        else:
            expected_path = os.path.join(LONGEST_H_ANALYSIS_PATH, case_type)
            logger.warning(f"No longest H data found for {case_type}")
            logger.warning(f"  Expected directory: {expected_path}")
            logger.warning(f"  Expected structure: {expected_path}/freq_*/analysis.csv")

    # Combination cases
    combo_cases = ['Bounded_Pareto_combination_random', 'Bounded_Pareto_combination_softrandom',
                   'normal_combination_random', 'normal_combination_softrandom']

    for case_type in combo_cases:
        logger.info(f"\nProcessing {case_type}...")

        case_dir = os.path.join(LONGEST_H_ANALYSIS_PATH, case_type)
        if not os.path.exists(case_dir):
            continue

        for combo_name in os.listdir(case_dir):
            combo_path = os.path.join(case_dir, combo_name)
            if not os.path.isdir(combo_path):
                continue

            df = load_combination_longest_h_data(case_type, combo_name)

            if df is not None:
                case_output_dir = os.path.join(output_dir, case_type)
                os.makedirs(case_output_dir, exist_ok=True)

                plot_longest_h_ratio(
                    df,
                    f'Longest Consecutive H Duration Ratio\n{case_type} / {combo_name}',
                    os.path.join(case_output_dir, f'{combo_name}_longest_h.pdf')
                )


def process_chapter4_additional_plots():
    """Process additional Chapter 4 plots: H value comparison, Random vs Softrandom, Job Size Distribution, Load Performance"""
    logger.info("\n" + "=" * 80)
    logger.info("Processing Additional Chapter 4 Plots")
    logger.info("=" * 80)

    output_dir = os.path.join(OUTPUT_PATH, 'chapter4_additional')
    os.makedirs(output_dir, exist_ok=True)

    # Figure 4.2: Job Size Distribution PDF comparison
    logger.info("\nProcessing Job Size Distribution plots...")
    plot_job_size_distribution(output_dir)

    # Figure 4.11: Different H value performance comparison
    logger.info("\nProcessing H value performance comparison...")
    plot_h_value_performance(output_dir)

    # Figure 4.12: Different load performance comparison
    logger.info("\nProcessing Load Performance comparison...")
    plot_load_performance(output_dir)

    # Figure 4.16: Random vs Softrandom comparison
    logger.info("\nProcessing Random vs Softrandom comparison...")
    plot_random_vs_softrandom(output_dir)


def main():
    """Main execution function"""
    logger.info("\n" + "=" * 80)
    logger.info("ALGORITHM COMPARISON PLOTTER - CHAPTER 4 FIGURES")
    logger.info("=" * 80)

    best_mode = find_best_mode()
    logger.info(f"Using mode{best_mode} for all Dynamic algorithms")

    # Original comparison plots (includes ratio plots now)
    process_non_combination_cases()
    process_combination_cases()

    # New Chapter 4 plots
    process_strategy_selection()
    process_mode_comparison()
    process_longest_h_plots()

    # Additional Chapter 4 plots (H value comparison, Random vs Softrandom)
    process_chapter4_additional_plots()

    logger.info("\n" + "=" * 80)
    logger.info("ALL TASKS COMPLETED SUCCESSFULLY!")
    logger.info(f"Output directory: {OUTPUT_PATH}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
