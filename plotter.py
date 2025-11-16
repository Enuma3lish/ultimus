#!/usr/bin/env python3
"""
Combined Algorithm Comparison Plotter

Features:
1. Groups results by BP_parameter (L, H pairs)
2. For Bounded Pareto (L <= H): Create one graph per (L, H) combination
3. For Normal distribution: Group by std (H value), create graphs titled "Result in normal:std={H}"
4. X-axis for avg cases: Mean_inter_arrival_time
5. X-axis for random/softrandom: coherence_time
6. Y-axis: L2-norm flow time
7. Titles show distribution information
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import logging
from matplotlib.ticker import MaxNLocator

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

os.makedirs(OUTPUT_PATH, exist_ok=True)

# ============================================================================
# ALGORITHM DEFINITIONS
# ============================================================================
CLAIRVOYANT_ALGORITHMS = ['SRPT', 'SJF', 'Dynamic', 'BAL', 'Dynamic_BAL', 'RR', 'FCFS']
NON_CLAIRVOYANT_ALGORITHMS = ['RMLF', 'MLFQ', 'RR', 'FCFS', 'RFDynamic', 'SETF']
DYNAMIC_ALGORITHMS = ['Dynamic', 'Dynamic_BAL', 'RFDynamic']
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
    'RMLF': '#404040',    # Dark Gray
    'MLFQ': '#bcbd22',    # Olive
    'RFDynamic': '#17becf', # Cyan
    'SJF': '#a0522d'      # Sienna
}

ALGORITHM_MARKERS = {
    'RR': 'o',    'SRPT': 's',  'SETF': '^',  'FCFS': 'v',
    'BAL': 'D',   'Dynamic': 'x', 'Dynamic_BAL': 'P', 'RMLF': '*',
    'MLFQ': 'p',  'RFDynamic': 'h', 'SJF': 'X'
}

def setup_plot_style():
    """Set up matplotlib style"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (14, 8),
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
# BENCHMARK MODE SELECTION FOR DYNAMIC ALGORITHMS
# ============================================================================
RFDYNAMIC_BENCHMARK_MODE = None

def find_rfdynamic_benchmark_from_random():
    """Find RFDynamic's benchmark mode based on random case results"""
    global RFDYNAMIC_BENCHMARK_MODE

    if RFDYNAMIC_BENCHMARK_MODE is not None:
        return RFDYNAMIC_BENCHMARK_MODE

    algorithm = 'RFDynamic'
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")
    data_file = os.path.join(algorithm_dir, f"{algorithm}_final_random_result.csv")

    if not os.path.exists(data_file):
        logger.warning(f"RFDynamic random result file not found, defaulting to mode5")
        RFDYNAMIC_BENCHMARK_MODE = 5
        return 5

    try:
        df = pd.read_csv(data_file)
        mode_win_counts = {i: 0 for i in range(1, 6)}

        for _, row in df.iterrows():
            mode_values = {}
            for i in range(1, 6):
                col_name = f'mode{i}_L2_norm_flow_time'
                if col_name in df.columns and pd.notna(row[col_name]):
                    mode_values[i] = row[col_name]

            if mode_values:
                best_mode = min(mode_values.items(), key=lambda x: x[1])[0]
                mode_win_counts[best_mode] += 1

        benchmark_mode = max(mode_win_counts.items(), key=lambda x: x[1])[0]
        logger.info(f"RFDynamic benchmark mode: mode{benchmark_mode}")
        RFDYNAMIC_BENCHMARK_MODE = benchmark_mode
        return benchmark_mode

    except Exception as e:
        logger.warning(f"Error finding RFDynamic benchmark: {e}, defaulting to mode5")
        RFDYNAMIC_BENCHMARK_MODE = 5
        return 5

def find_benchmark_mode(df, algorithm):
    """Find the benchmark mode for a Dynamic algorithm"""
    if algorithm == 'RFDynamic':
        benchmark_mode = find_rfdynamic_benchmark_from_random()
        return benchmark_mode, f'mode{benchmark_mode}_L2_norm_flow_time'

    # For other Dynamic algorithms, use mode closest to mode 6
    mode_columns = [col for col in df.columns if 'mode' in col and 'L2_norm_flow_time' in col]

    if not mode_columns or 'mode6_L2_norm_flow_time' not in df.columns:
        logger.warning(f"No mode columns for {algorithm}, defaulting to mode5")
        return 5, 'mode5_L2_norm_flow_time'

    mode6_values = df['mode6_L2_norm_flow_time'].values
    mode_distances = {}

    for i in range(1, 6):
        col_name = f'mode{i}_L2_norm_flow_time'
        if col_name in df.columns:
            mode_values = df[col_name].values
            distance = np.mean(np.abs(mode_values - mode6_values))
            mode_distances[i] = distance

    if not mode_distances:
        return 5, 'mode5_L2_norm_flow_time'

    benchmark_mode = min(mode_distances.items(), key=lambda x: x[1])[0]
    logger.info(f"Benchmark mode for {algorithm}: mode{benchmark_mode}")
    return benchmark_mode, f'mode{benchmark_mode}_L2_norm_flow_time'

# ============================================================================
# DATA LOADING
# ============================================================================

def load_algorithm_avg_data(algorithm, avg_type):
    """Load avg30/avg60/avg90 data for an algorithm"""
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", f"{avg_type}_result")

    if not os.path.exists(algorithm_dir):
        return None

    pattern = os.path.join(algorithm_dir, f"*_{algorithm}_*_result.csv")
    files = sorted(glob.glob(pattern))

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

    # Handle Dynamic algorithms
    if algorithm in DYNAMIC_ALGORITHMS:
        best_mode = find_rfdynamic_benchmark_from_random() if algorithm == 'RFDynamic' else 5
        best_mode_col = f'{algorithm}_njobs100_mode{best_mode}_L2_norm_flow_time'

        if best_mode_col not in combined_df.columns:
            return None

        grouped = combined_df.groupby(['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H'])[best_mode_col].mean().reset_index()
        grouped.rename(columns={best_mode_col: f'{algorithm}_L2_norm_flow_time'}, inplace=True)
        grouped['best_mode'] = best_mode
    else:
        l2_col_name = f'{algorithm}_L2_norm_flow_time'

        if l2_col_name not in combined_df.columns:
            return None

        grouped = combined_df.groupby(['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H'])[l2_col_name].mean().reset_index()

    return grouped

def is_normal_distribution(bp_L, bp_H):
    """Determine if parameters represent Normal distribution"""
    # Normal distribution: bp_L > bp_H (mean > std case, or small H values like 6, 9, 12)
    return bp_L > bp_H

# ============================================================================
# PLOTTING FUNCTIONS - AVG CASES
# ============================================================================

def plot_bounded_pareto_by_params(data_dict, group_name, avg_type):
    """Plot Bounded Pareto (L <= H) results, one graph per (L, H) pair"""
    logger.info(f"Creating Bounded Pareto plots for {group_name}...")

    all_bounded_data = {}
    for algorithm, df in data_dict.items():
        bounded_df = df[~df.apply(lambda row: is_normal_distribution(row['bp_parameter_L'], row['bp_parameter_H']), axis=1)].copy()
        if not bounded_df.empty:
            all_bounded_data[algorithm] = bounded_df

    if not all_bounded_data:
        logger.warning(f"No Bounded Pareto data for {group_name}")
        return

    # Get unique (L, H) pairs
    all_param_pairs = set()
    for df in all_bounded_data.values():
        for _, row in df[['bp_parameter_L', 'bp_parameter_H']].drop_duplicates().iterrows():
            all_param_pairs.add((row['bp_parameter_L'], row['bp_parameter_H']))

    all_param_pairs = sorted(all_param_pairs)

    for bp_L, bp_H in all_param_pairs:
        setup_plot_style()
        fig, ax = plt.subplots(figsize=(14, 8))

        plotted_any = False

        for algorithm, df in all_bounded_data.items():
            param_df = df[(df['bp_parameter_L'] == bp_L) & (df['bp_parameter_H'] == bp_H)].copy()

            if param_df.empty:
                continue

            param_df = param_df.sort_values('Mean_inter_arrival_time')
            l2_col = f'{algorithm}_L2_norm_flow_time'

            if l2_col not in param_df.columns:
                continue

            if algorithm in DYNAMIC_ALGORITHMS and 'best_mode' in param_df.columns:
                best_mode = param_df['best_mode'].iloc[0]
                label = f"{algorithm} (mode{best_mode})"
            else:
                label = algorithm

            ax.plot(param_df['Mean_inter_arrival_time'], param_df[l2_col],
                   marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                   color=ALGORITHM_COLORS.get(algorithm, 'black'),
                   linewidth=2.5,
                   markersize=10,
                   markeredgewidth=1.5,
                   markeredgecolor='white',
                   label=label)

            plotted_any = True

        if not plotted_any:
            plt.close()
            continue

        ax.set_xlabel('Mean Inter-Arrival Time', fontweight='bold')
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold')
        ax.set_title(f'{group_name} - Bounded Pareto Distribution (L={bp_L:.3f}, H={bp_H})',
                    fontweight='bold', pad=20)

        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        output_file = os.path.join(OUTPUT_PATH,
                                   f"bounded_pareto_{group_name}_{avg_type}_L_{bp_L:.3f}_H_{bp_H}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

def plot_normal_by_std(data_dict, group_name, avg_type):
    """Plot Normal distribution results, one graph per std (H value)"""
    logger.info(f"Creating Normal distribution plots for {group_name}...")

    all_normal_data = {}
    for algorithm, df in data_dict.items():
        normal_df = df[df.apply(lambda row: is_normal_distribution(row['bp_parameter_L'], row['bp_parameter_H']), axis=1)].copy()
        if not normal_df.empty:
            all_normal_data[algorithm] = normal_df

    if not all_normal_data:
        logger.warning(f"No Normal distribution data for {group_name}")
        return

    # Get unique H values (std)
    all_stds = set()
    for df in all_normal_data.values():
        all_stds.update(df['bp_parameter_H'].unique())

    all_stds = sorted(all_stds)

    for std_val in all_stds:
        setup_plot_style()
        fig, ax = plt.subplots(figsize=(14, 8))

        plotted_any = False

        for algorithm, df in all_normal_data.items():
            std_df = df[df['bp_parameter_H'] == std_val].copy()

            if std_df.empty:
                continue

            std_df = std_df.sort_values('Mean_inter_arrival_time')
            l2_col = f'{algorithm}_L2_norm_flow_time'

            if l2_col not in std_df.columns:
                continue

            if algorithm in DYNAMIC_ALGORITHMS and 'best_mode' in std_df.columns:
                best_mode = std_df['best_mode'].iloc[0]
                label = f"{algorithm} (mode{best_mode})"
            else:
                label = algorithm

            ax.plot(std_df['Mean_inter_arrival_time'], std_df[l2_col],
                   marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                   color=ALGORITHM_COLORS.get(algorithm, 'black'),
                   linewidth=2.5,
                   markersize=10,
                   markeredgewidth=1.5,
                   markeredgecolor='white',
                   label=label)

            plotted_any = True

        if not plotted_any:
            plt.close()
            continue

        ax.set_xlabel('Mean Inter-Arrival Time', fontweight='bold')
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold')
        ax.set_title(f'{group_name} - Result in normal: std={std_val}',
                    fontweight='bold', pad=20)

        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        output_file = os.path.join(OUTPUT_PATH,
                                   f"normal_{group_name}_{avg_type}_std_{std_val}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

# ============================================================================
# PLOTTING FUNCTIONS - RANDOM/SOFTRANDOM CASES
# ============================================================================

def plot_random_or_softrandom(algorithms, result_type, group_name, distribution_label):
    """
    Plot random or softrandom results

    Args:
        algorithms: List of algorithms
        result_type: 'random' or 'softrandom'
        group_name: 'clairvoyant' or 'non_clairvoyant'
        distribution_label: String describing the distribution (e.g., "Bounded Pareto L=4.073, H=262144")
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))

    for algorithm in algorithms:
        algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")

        if result_type == "random":
            data_file = os.path.join(algorithm_dir, f"{algorithm}_final_random_result.csv")
        else:
            data_file = os.path.join(algorithm_dir, f"{algorithm}_final_softrandom.csv")

        if not os.path.exists(data_file):
            continue

        try:
            df = pd.read_csv(data_file)

            if algorithm in DYNAMIC_ALGORITHMS:
                benchmark_mode_num, benchmark_col = find_benchmark_mode(df, algorithm)

                if benchmark_col in df.columns:
                    ax.plot(df['coherence_time'], df[benchmark_col],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linewidth=2.5,
                           markersize=10,
                           markeredgewidth=1.5,
                           markeredgecolor='white',
                           label=f"{algorithm} (mode{benchmark_mode_num})")
            else:
                if 'L2_norm_flow_time' in df.columns:
                    ax.plot(df['coherence_time'], df['L2_norm_flow_time'],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linewidth=2.5,
                           markersize=10,
                           markeredgewidth=1.5,
                           markeredgecolor='white',
                           label=algorithm)

        except Exception as e:
            logger.warning(f"Error plotting {algorithm}: {e}")
            continue

    ax.set_xlabel('Coherence Time (CPU Time)', fontweight='bold')
    ax.set_ylabel('L2-Norm Flow Time', fontweight='bold')
    ax.set_title(f'{group_name.replace("_", " ").title()} - {result_type.capitalize()}\nDistribution: {distribution_label}',
                fontweight='bold')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)
    ax.set_xlim(left=2)

    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])

    output_file = os.path.join(OUTPUT_PATH, f"{group_name}_{result_type}_comparison.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved: {output_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    logger.info("\n" + "=" * 80)
    logger.info("COMBINED ALGORITHM COMPARISON PLOTTER - STARTING")
    logger.info("=" * 80)

    # Process avg types
    for avg_type in ['avg30', 'avg60', 'avg90']:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {avg_type}")
        logger.info(f"{'='*80}")

        # Load clairvoyant algorithms
        clairvoyant_data = {}
        for algo in CLAIRVOYANT_ALGORITHMS:
            df = load_algorithm_avg_data(algo, avg_type)
            if df is not None:
                clairvoyant_data[algo] = df

        # Load non-clairvoyant algorithms
        non_clairvoyant_data = {}
        for algo in NON_CLAIRVOYANT_ALGORITHMS:
            df = load_algorithm_avg_data(algo, avg_type)
            if df is not None:
                non_clairvoyant_data[algo] = df

        # Create Bounded Pareto plots
        if clairvoyant_data:
            plot_bounded_pareto_by_params(clairvoyant_data, "Clairvoyant", avg_type)

        if non_clairvoyant_data:
            plot_bounded_pareto_by_params(non_clairvoyant_data, "Non-Clairvoyant", avg_type)

        # Create Normal distribution plots
        if clairvoyant_data:
            plot_normal_by_std(clairvoyant_data, "Clairvoyant", avg_type)

        if non_clairvoyant_data:
            plot_normal_by_std(non_clairvoyant_data, "Non-Clairvoyant", avg_type)

    # Process random and softrandom
    logger.info(f"\n{'='*80}")
    logger.info("Processing random and softrandom")
    logger.info(f"{'='*80}")

    for result_type in ['random', 'softrandom']:
        plot_random_or_softrandom(CLAIRVOYANT_ALGORITHMS, result_type,
                                 "clairvoyant", "Mixed Distributions")
        plot_random_or_softrandom(NON_CLAIRVOYANT_ALGORITHMS, result_type,
                                 "non_clairvoyant", "Mixed Distributions")

    logger.info("\n" + "=" * 80)
    logger.info("ALL TASKS COMPLETED SUCCESSFULLY!")
    logger.info(f"Output directory: {OUTPUT_PATH}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
