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
BASE_DATA_PATH = "/home/melowu/Work/ultimus"
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
    'SRPT': '#FF0000',    # Bright Red - High contrast
    'SETF': '#2ca02c',    # Green
    'FCFS': '#FFD700',    # Gold - High contrast
    'BAL': '#9467bd',     # Purple
    'Dynamic': '#FF6600', # Vibrant Orange - High contrast
    'Dynamic_BAL': '#FF00FF',  # Magenta - High contrast
    'RMLF': '#000000',    # Black - High contrast
    'MLFQ': '#bcbd22',    # Olive
    'RFDynamic': '#00FFFF', # Bright Cyan - High contrast
    'SJF': '#a0522d'      # Sienna
}

ALGORITHM_MARKERS = {
    'RR': 'o',    'SRPT': 'D',  'SETF': '^',  'FCFS': 's',
    'BAL': 'P',   'Dynamic': 'v', 'Dynamic_BAL': 'p', 'RMLF': '*',
    'MLFQ': 'h',  'RFDynamic': '<', 'SJF': 'X'
}

# Highlighted algorithms (FCFS, SRPT, RMLF, Dynamic, Dynamic_BAL, RFDynamic) - use thicker lines
HIGHLIGHTED_ALGORITHMS = ['FCFS', 'SRPT', 'RMLF', 'Dynamic', 'Dynamic_BAL', 'RFDynamic']

# Mode colors for mode comparison plots
MODE_COLORS = {
    1: '#e74c3c', 2: '#3498db', 3: '#2ecc71', 
    4: '#f39c12', 5: '#9b59b6', 6: '#1abc9c'
}

MODE_MARKERS = {
    1: 'o', 2: 's', 3: '^', 4: 'v', 5: 'D', 6: 'P'
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
        'lines.linewidth': 3.0,
        'lines.markersize': 12,
        'lines.markeredgewidth': 2.0,
        'axes.grid': True,
        'grid.alpha': 0.4,
        'grid.linewidth': 0.8,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
    })

# ============================================================================
# BENCHMARK MODE SELECTION FOR DYNAMIC ALGORITHMS
# ============================================================================
DYNAMIC_BENCHMARK_MODES = {}
RFDYNAMIC_BENCHMARK_MODE = None

def find_rfdynamic_benchmark_mode():
    """
    Find RFDynamic's best mode based on highest frequency in all random cases
    Excludes mode 6 from consideration
    
    Returns:
        Best mode number (1-5)
    """
    global RFDYNAMIC_BENCHMARK_MODE
    
    if RFDYNAMIC_BENCHMARK_MODE is not None:
        return RFDYNAMIC_BENCHMARK_MODE
    
    # Aggregate the Bounded_Pareto random data for RFDynamic
    df = aggregate_random_softrandom_data('RFDynamic', 'Bounded_Pareto', 'random')
    
    if df is None:
        logger.warning(f"No random data for RFDynamic, defaulting to mode5")
        RFDYNAMIC_BENCHMARK_MODE = 5
        return 5
    
    mode_win_counts = {i: 0 for i in range(1, 6)}  # Modes 1-5 (exclude mode 6)
    
    for _, row in df.iterrows():
        mode_values = {}
        for i in range(1, 6):  # Only check modes 1-5
            col_name = f'RFDynamic_njobs100_mode{i}_L2_norm_flow_time'
            if col_name in df.columns and pd.notna(row[col_name]):
                mode_values[i] = row[col_name]
        
        if mode_values:
            best_mode = min(mode_values.items(), key=lambda x: x[1])[0]
            mode_win_counts[best_mode] += 1
    
    benchmark_mode = max(mode_win_counts.items(), key=lambda x: x[1])[0]
    logger.info(f"RFDynamic benchmark mode (excluding mode 6): mode{benchmark_mode}")
    logger.info(f"  Mode win counts: {mode_win_counts}")
    
    RFDYNAMIC_BENCHMARK_MODE = benchmark_mode
    return benchmark_mode

def aggregate_random_softrandom_data(algorithm, distribution_type, random_type):
    """
    Aggregate random/softrandom data from individual files
    
    Args:
        algorithm: Algorithm name
        distribution_type: 'Bounded_Pareto' or 'normal'
        random_type: 'random' or 'softrandom'
    
    Returns:
        DataFrame with aggregated results or None
    """
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result")
    result_dir = os.path.join(algorithm_dir, f"{distribution_type}_{random_type}_result")
    
    if not os.path.exists(result_dir):
        logger.warning(f"Directory not found: {result_dir}")
        return None
    
    # Find all result files
    if algorithm in DYNAMIC_ALGORITHMS:
        pattern = os.path.join(result_dir, f"{distribution_type}_{random_type}_result_{algorithm}_njobs100_*.csv")
    else:
        pattern = os.path.join(result_dir, f"{distribution_type}_{random_type}_result_{algorithm}_*.csv")
    
    files = sorted(glob.glob(pattern))
    
    if not files:
        logger.warning(f"No files found for {algorithm} in {result_dir}")
        return None
    
    all_dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            # Rename 'frequency' to 'coherence_time' for consistency
            if 'frequency' in df.columns:
                df.rename(columns={'frequency': 'coherence_time'}, inplace=True)
            all_dfs.append(df)
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue
    
    if not all_dfs:
        return None
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Group by coherence_time and average
    if algorithm in DYNAMIC_ALGORITHMS:
        # Get all mode columns
        mode_cols = [col for col in combined_df.columns if 'mode' in col and 'L2_norm_flow_time' in col]
        group_cols = ['coherence_time'] + mode_cols
        grouped = combined_df.groupby('coherence_time')[mode_cols].mean().reset_index()
    else:
        l2_col = f'{algorithm}_L2_norm_flow_time'
        if l2_col not in combined_df.columns:
            logger.warning(f"Column {l2_col} not found in {algorithm} data")
            return None
        grouped = combined_df.groupby('coherence_time')[l2_col].mean().reset_index()
    
    # Save aggregated result
    output_filename = f"{algorithm}_{distribution_type}_{random_type}_result.csv"
    output_path = os.path.join(algorithm_dir, output_filename)
    grouped.to_csv(output_path, index=False)
    logger.info(f"  Saved aggregated data: {output_filename}")
    
    return grouped

def find_benchmark_mode_exclude_1_6(algorithm):
    """
    Find benchmark mode for Dynamic algorithms based on highest frequency in random cases
    Excludes mode 1 and mode 6 from consideration
    
    Returns:
        Best mode number (2-5)
    """
    global DYNAMIC_BENCHMARK_MODES
    
    if algorithm in DYNAMIC_BENCHMARK_MODES:
        return DYNAMIC_BENCHMARK_MODES[algorithm]
    
    # First, aggregate the Bounded_Pareto random data
    df = aggregate_random_softrandom_data(algorithm, 'Bounded_Pareto', 'random')
    
    if df is None:
        logger.warning(f"No random data for {algorithm}, defaulting to mode5")
        DYNAMIC_BENCHMARK_MODES[algorithm] = 5
        return 5
    
    mode_win_counts = {i: 0 for i in range(2, 6)}  # Only modes 2-5
    
    for _, row in df.iterrows():
        mode_values = {}
        for i in range(2, 6):  # Only check modes 2-5
            col_name = f'{algorithm}_njobs100_mode{i}_L2_norm_flow_time'
            if col_name in df.columns and pd.notna(row[col_name]):
                mode_values[i] = row[col_name]
        
        if mode_values:
            best_mode = min(mode_values.items(), key=lambda x: x[1])[0]
            mode_win_counts[best_mode] += 1
    
    benchmark_mode = max(mode_win_counts.items(), key=lambda x: x[1])[0]
    logger.info(f"{algorithm} benchmark mode (excluding 1&6): mode{benchmark_mode}")
    logger.info(f"  Mode win counts: {mode_win_counts}")
    
    DYNAMIC_BENCHMARK_MODES[algorithm] = benchmark_mode
    return benchmark_mode

# ============================================================================
# DATA LOADING
# ============================================================================

def load_algorithm_avg_data(algorithm, avg_type):
    """Load avg30/avg60/avg90 data for an algorithm"""
    logger.info(f"  Loading {algorithm} from {avg_type}...")
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", f"{avg_type}_result")

    if not os.path.exists(algorithm_dir):
        logger.warning(f"  Directory not found: {algorithm_dir}")
        return None

    # Try the standard pattern first
    pattern = os.path.join(algorithm_dir, f"*_{algorithm}_*_result.csv")
    files = sorted(glob.glob(pattern))
    
    # If no files found, try alternative pattern (for Dynamic algorithms)
    if not files:
        pattern = os.path.join(algorithm_dir, f"*_{algorithm}_result_*.csv")
        files = sorted(glob.glob(pattern))
    
    logger.info(f"  Found {len(files)} files for {algorithm}")

    if not files:
        logger.warning(f"  No files found for {algorithm}")
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
    
    # Standardize column name: rename 'arrival_rate' to 'Mean_inter_arrival_time' if needed
    if 'arrival_rate' in combined_df.columns:
        combined_df.rename(columns={'arrival_rate': 'Mean_inter_arrival_time'}, inplace=True)

    # Handle Dynamic algorithms - just keep all mode columns
    if algorithm in DYNAMIC_ALGORITHMS:
        # Group and average all mode columns
        mode_cols = [col for col in combined_df.columns if 'mode' in col and 'L2_norm_flow_time' in col]
        group_cols = ['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H']
        
        logger.info(f"  Found mode columns: {mode_cols}")
        grouped = combined_df.groupby(group_cols)[mode_cols].mean().reset_index()
        
        # Find best mode for this algorithm
        best_mode = find_benchmark_mode_exclude_1_6(algorithm) if algorithm != 'RFDynamic' else find_rfdynamic_benchmark_mode()
        best_mode_col = f'{algorithm}_njobs100_mode{best_mode}_L2_norm_flow_time'
        
        logger.info(f"  Best mode for {algorithm}: {best_mode}, looking for column: {best_mode_col}")
        
        if best_mode_col in grouped.columns:
            grouped[f'{algorithm}_L2_norm_flow_time'] = grouped[best_mode_col]
            grouped['best_mode'] = best_mode
            logger.info(f"  Successfully created {algorithm}_L2_norm_flow_time column")
        else:
            logger.warning(f"  Column {best_mode_col} not found in grouped dataframe!")
            logger.warning(f"  Available columns: {grouped.columns.tolist()}")
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
    """Plot Bounded Pareto (L <= H) results with overload/underload regions"""
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
        fig, ax = plt.subplots(figsize=(12, 7))

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

            # Highlight settings - use filled markers for highlighted, hollow for others
            if algorithm in HIGHLIGHTED_ALGORITHMS:
                linewidth = 3.5
                markersize = 12
                zorder = 10
                fillstyle = 'full'
            else:
                linewidth = 1.5
                markersize = 7
                zorder = 5
                fillstyle = 'none'

            ax.plot(param_df['Mean_inter_arrival_time'], param_df[l2_col],
                   marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                   color=ALGORITHM_COLORS.get(algorithm, 'black'),
                   linewidth=linewidth,
                   markersize=markersize,
                   fillstyle=fillstyle,
                   markeredgewidth=2.5,
                   markeredgecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                   label=label,
                   zorder=zorder)
            plotted_any = True

        if not plotted_any:
            plt.close()
            continue

        ax.set_xlabel('Mean job interarrival time', fontweight='bold', fontsize=11)
        ax.set_ylabel('L2-Norm Flow Time (log scale)', fontweight='bold', fontsize=11)
        ax.set_yscale('log')
        ax.set_xlim(20, 40)
        ax.set_xticks(range(20, 41, 2))
        ax.set_title(f'{group_name} - Bounded Pareto Distribution (L={bp_L:.3f}, H={bp_H})',
                    fontweight='bold', fontsize=12, pad=15)
        ax.legend(loc='best', framealpha=0.95, fontsize=9, ncol=2)
        ax.grid(True, alpha=0.3, which='both', linestyle='-', linewidth=0.5)
        plt.tight_layout()
        
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
        fig, ax = plt.subplots(figsize=(12, 7))

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

            # Highlight settings - filled for highlighted, hollow for others
            if algorithm in HIGHLIGHTED_ALGORITHMS:
                linewidth = 3.5
                markersize = 12
                zorder = 10
                fillstyle = 'full'
            else:
                linewidth = 1.5
                markersize = 7
                zorder = 5
                fillstyle = 'none'

            ax.plot(std_df['Mean_inter_arrival_time'], std_df[l2_col],
                   marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                   color=ALGORITHM_COLORS.get(algorithm, 'black'),
                   linewidth=linewidth,
                   markersize=markersize,
                   fillstyle=fillstyle,
                   markeredgewidth=2.5,
                   markeredgecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                   label=label,
                   zorder=zorder)
            plotted_any = True

        if not plotted_any:
            plt.close()
            continue

        ax.set_xlabel('Mean job interarrival time', fontweight='bold', fontsize=11)
        ax.set_ylabel('L2-Norm Flow Time (log scale)', fontweight='bold', fontsize=11)
        ax.set_yscale('log')
        ax.set_xlim(20, 40)
        ax.set_xticks(range(20, 41, 2))
        ax.set_title(f'{group_name} - Result in normal: std={int(std_val)}',
                    fontweight='bold', fontsize=12, pad=15)
        ax.legend(loc='best', framealpha=0.95, fontsize=9, ncol=2)
        ax.grid(True, alpha=0.3, which='both', linestyle='-', linewidth=0.5)
        plt.tight_layout()

        output_file = os.path.join(OUTPUT_PATH,
                                   f"normal_{group_name}_{avg_type}_std_{std_val}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

# ============================================================================
# PLOTTING FUNCTIONS - RANDOM/SOFTRANDOM CASES
# ============================================================================

def plot_random_or_softrandom(algorithms, result_type, group_name, distribution_type):
    """
    Plot random or softrandom results for a specific distribution type
    
    Args:
        algorithms: List of algorithms
        result_type: 'random' or 'softrandom'
        group_name: 'clairvoyant' or 'non_clairvoyant'
        distribution_type: 'Bounded_Pareto' or 'normal'
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))
    
    plotted_any = False
    
    for algorithm in algorithms:
        # First aggregate the data
        df = aggregate_random_softrandom_data(algorithm, distribution_type, result_type)
        
        if df is None:
            continue
        
        try:
            if algorithm in DYNAMIC_ALGORITHMS:
                if algorithm == 'RFDynamic':
                    algo_mode = find_rfdynamic_benchmark_mode()
                else:
                    algo_mode = find_benchmark_mode_exclude_1_6(algorithm)
                
                algo_col = f'{algorithm}_njobs100_mode{algo_mode}_L2_norm_flow_time'
                
                if algo_col in df.columns:
                    label = f"{algorithm} (mode{algo_mode})"
                    
                    # Highlight FCFS, SRPT, RMLF with thicker lines
                    if algorithm in HIGHLIGHTED_ALGORITHMS:
                        linewidth = 3.0
                        markersize = 8
                        zorder = 10
                        markevery = 1
                    else:
                        linewidth = 2.0
                        markersize = 6
                        zorder = 5
                        markevery = 2
                    
                    ax.plot(df['coherence_time'], df[algo_col],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linewidth=linewidth,
                           markersize=markersize,
                           markevery=markevery,
                           markeredgewidth=0.5,
                           markeredgecolor='white',
                           label=label,
                           alpha=0.9,
                           zorder=zorder)
                    plotted_any = True
            else:
                l2_col = f'{algorithm}_L2_norm_flow_time'
                if l2_col in df.columns:
                    # Highlight FCFS, SRPT, RMLF with thicker lines
                    if algorithm in HIGHLIGHTED_ALGORITHMS:
                        linewidth = 3.0
                        markersize = 8
                        zorder = 10
                        markevery = 1
                    else:
                        linewidth = 2.0
                        markersize = 6
                        zorder = 5
                        markevery = 2
                    
                    ax.plot(df['coherence_time'], df[l2_col],
                           marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                           color=ALGORITHM_COLORS.get(algorithm, 'black'),
                           linewidth=linewidth,
                           markersize=markersize,
                           markevery=markevery,
                           markeredgewidth=0.5,
                           markeredgecolor='white',
                           label=algorithm,
                           alpha=0.9,
                           zorder=zorder)
                    plotted_any = True
        
        except Exception as e:
            logger.warning(f"Error plotting {algorithm}: {e}")
            continue
    
    if not plotted_any:
        plt.close()
        logger.warning(f"No data plotted for {group_name} {distribution_type} {result_type}")
        return
    
    ax.set_xlabel('Coherence Time (CPU Time)', fontweight='bold')
    ax.set_ylabel('L2-Norm Flow Time (log scale)', fontweight='bold')
    ax.set_yscale('log')
    
    dist_label = "Bounded Pareto" if distribution_type == "Bounded_Pareto" else "Normal"
    ax.set_title(f'{group_name.replace("_", " ").title()} - {result_type.capitalize()}\nDistribution: {dist_label}',
                fontweight='bold', pad=20)
    
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, which='both', linestyle='-', linewidth=0.5)
    ax.set_xscale('log', base=2)
    ax.set_xlim(left=2)
    
    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    
    output_file = os.path.join(OUTPUT_PATH, 
                               f"{group_name}_{distribution_type}_{result_type}_comparison.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved: {output_file}")

# ============================================================================
# MODE COMPARISON PLOTTING FUNCTIONS
# ============================================================================

def plot_mode_comparison_avg(algorithm, avg_type):
    """
    Plot mode comparison for Dynamic algorithms in avg cases
    One plot per (L, H) combination, comparing all 6 modes
    
    Args:
        algorithm: Dynamic algorithm name
        avg_type: 'avg30', 'avg60', or 'avg90'
    """
    if algorithm not in DYNAMIC_ALGORITHMS:
        return
    
    logger.info(f"Creating mode comparison plots for {algorithm} - {avg_type}...")
    
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", f"{avg_type}_result")
    
    if not os.path.exists(algorithm_dir):
        logger.warning(f"Directory not found: {algorithm_dir}")
        return
    
    pattern = os.path.join(algorithm_dir, f"*_{algorithm}_*_result.csv")
    files = sorted(glob.glob(pattern))
    
    if not files:
        logger.warning(f"No files found for {algorithm} in {algorithm_dir}")
        return
    
    all_dfs = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            all_dfs.append(df)
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue
    
    if not all_dfs:
        return
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Standardize column name: rename 'arrival_rate' to 'Mean_inter_arrival_time' if needed
    if 'arrival_rate' in combined_df.columns:
        combined_df.rename(columns={'arrival_rate': 'Mean_inter_arrival_time'}, inplace=True)
    
    # Get all unique (L, H) pairs
    param_pairs = combined_df[['bp_parameter_L', 'bp_parameter_H']].drop_duplicates()
    
    for _, row in param_pairs.iterrows():
        bp_L = row['bp_parameter_L']
        bp_H = row['bp_parameter_H']
        
        # Filter data for this (L, H) pair
        pair_df = combined_df[(combined_df['bp_parameter_L'] == bp_L) & 
                             (combined_df['bp_parameter_H'] == bp_H)].copy()
        
        if pair_df.empty:
            continue
        
        # Group by Mean_inter_arrival_time and average
        grouped = pair_df.groupby('Mean_inter_arrival_time').mean().reset_index()
        
        setup_plot_style()
        fig, ax = plt.subplots(figsize=(14, 8))
        
        plotted_any = False
        
        # Plot each mode
        for mode in range(1, 7):
            mode_col = f'{algorithm}_njobs100_mode{mode}_L2_norm_flow_time'
            
            if mode_col not in grouped.columns:
                continue
            
            ax.plot(grouped['Mean_inter_arrival_time'], grouped[mode_col],
                   marker=MODE_MARKERS.get(mode, 'o'),
                   color=MODE_COLORS.get(mode, 'black'),
                   linewidth=3.0,
                   markersize=12,
                   markeredgewidth=2.0,
                   markeredgecolor='white',
                   label=f"mode{mode}")
            plotted_any = True
        
        if not plotted_any:
            plt.close()
            continue
        
        ax.set_xlabel('Mean Inter-Arrival Time', fontweight='bold')
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold')
        
        # Determine distribution type for title
        if is_normal_distribution(bp_L, bp_H):
            title = f'{algorithm} Mode Comparison - {avg_type}\nNormal Distribution (std={bp_H})'
            filename = f"{algorithm}_mode_comparison_{avg_type}_normal_std_{bp_H}.png"
        else:
            title = f'{algorithm} Mode Comparison - {avg_type}\nBounded Pareto (L={bp_L:.3f}, H={bp_H})'
            filename = f"{algorithm}_mode_comparison_{avg_type}_BP_L_{bp_L:.3f}_H_{bp_H}.png"
        
        ax.set_title(title, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.9, ncol=2)
        ax.grid(True, alpha=0.3)
        
        output_file = os.path.join(OUTPUT_PATH, filename)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"  Saved: {output_file}")

def plot_mode_comparison_random(algorithm, distribution_type, random_type):
    """
    Plot mode comparison for Dynamic algorithms in random/softrandom cases
    
    Args:
        algorithm: Dynamic algorithm name
        distribution_type: 'Bounded_Pareto' or 'normal'
        random_type: 'random' or 'softrandom'
    """
    if algorithm not in DYNAMIC_ALGORITHMS:
        return
    
    logger.info(f"Creating mode comparison plot for {algorithm} - {distribution_type} {random_type}...")
    
    # Aggregate data first
    df = aggregate_random_softrandom_data(algorithm, distribution_type, random_type)
    
    if df is None:
        return
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(14, 8))
    
    plotted_any = False
    
    # Plot each mode
    for mode in range(1, 7):
        mode_col = f'{algorithm}_njobs100_mode{mode}_L2_norm_flow_time'
        
        if mode_col not in df.columns:
            continue
        
        ax.plot(df['coherence_time'], df[mode_col],
               marker=MODE_MARKERS.get(mode, 'o'),
               color=MODE_COLORS.get(mode, 'black'),
               linewidth=3.0,
               markersize=12,
               markeredgewidth=2.0,
               markeredgecolor='white',
               label=f"mode{mode}")
        plotted_any = True
    
    if not plotted_any:
        plt.close()
        return
    
    ax.set_xlabel('Coherence Time (CPU Time)', fontweight='bold')
    ax.set_ylabel('L2-Norm Flow Time', fontweight='bold')
    
    dist_label = "Bounded Pareto" if distribution_type == "Bounded_Pareto" else "Normal"
    ax.set_title(f'{algorithm} Mode Comparison - {random_type.capitalize()}\nDistribution: {dist_label}',
                fontweight='bold', pad=20)
    
    ax.legend(loc='best', framealpha=0.9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)
    ax.set_xlim(left=2)
    
    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{int(np.log2(x))}}}$' for x in x_ticks])
    
    output_file = os.path.join(OUTPUT_PATH, 
                               f"{algorithm}_mode_comparison_{distribution_type}_{random_type}.png")
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

    # First, aggregate random/softrandom data to determine benchmark modes
    logger.info(f"\n{'='*80}")
    logger.info("Aggregating random/softrandom data to determine benchmark modes")
    logger.info(f"{'='*80}")
    
    for distribution_type in ['Bounded_Pareto', 'normal']:
        for random_type in ['random', 'softrandom']:
            logger.info(f"\nAggregating {distribution_type} {random_type} data...")
            for algo in ALL_ALGORITHMS:
                aggregate_random_softrandom_data(algo, distribution_type, random_type)
    
    # Determine benchmark modes for Dynamic algorithms
    logger.info(f"\n{'='*80}")
    logger.info("Determining benchmark modes for Dynamic algorithms")
    logger.info(f"{'='*80}")
    
    for algo in DYNAMIC_ALGORITHMS:
        if algo == 'RFDynamic':
            find_rfdynamic_benchmark_mode()
        else:
            find_benchmark_mode_exclude_1_6(algo)

    # Process avg types
    for avg_type in ['avg30']:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {avg_type}")
        logger.info(f"{'='*80}")

        # Load clairvoyant algorithms
        clairvoyant_data = {}
        for algo in CLAIRVOYANT_ALGORITHMS:
            df = load_algorithm_avg_data(algo, avg_type)
            if df is not None:
                clairvoyant_data[algo] = df
        
        logger.info(f"Loaded clairvoyant algorithms: {list(clairvoyant_data.keys())}")

        # Load non-clairvoyant algorithms
        non_clairvoyant_data = {}
        for algo in NON_CLAIRVOYANT_ALGORITHMS:
            df = load_algorithm_avg_data(algo, avg_type)
            if df is not None:
                non_clairvoyant_data[algo] = df
        
        logger.info(f"Loaded non-clairvoyant algorithms: {list(non_clairvoyant_data.keys())}")

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
        
        # Create mode comparison plots for Dynamic algorithms
        logger.info(f"\n{'='*80}")
        logger.info(f"Creating mode comparison plots for {avg_type}")
        logger.info(f"{'='*80}")
        
        for algo in DYNAMIC_ALGORITHMS:
            plot_mode_comparison_avg(algo, avg_type)

    # Create algorithm comparison plots
    logger.info(f"\n{'='*80}")
    logger.info("Creating algorithm comparison plots for random/softrandom")
    logger.info(f"{'='*80}")
    
    for distribution_type in ['Bounded_Pareto', 'normal']:
        for result_type in ['random', 'softrandom']:
            plot_random_or_softrandom(CLAIRVOYANT_ALGORITHMS, result_type,
                                     "clairvoyant", distribution_type)
            plot_random_or_softrandom(NON_CLAIRVOYANT_ALGORITHMS, result_type,
                                     "non_clairvoyant", distribution_type)
    
    # Create mode comparison plots for Dynamic algorithms
    logger.info(f"\n{'='*80}")
    logger.info("Creating mode comparison plots for random/softrandom")
    logger.info(f"{'='*80}")
    
    for distribution_type in ['Bounded_Pareto', 'normal']:
        for random_type in ['random', 'softrandom']:
            for algo in DYNAMIC_ALGORITHMS:
                plot_mode_comparison_random(algo, distribution_type, random_type)

    logger.info("\n" + "=" * 80)
    logger.info("ALL TASKS COMPLETED SUCCESSFULLY!")
    logger.info(f"Output directory: {OUTPUT_PATH}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
