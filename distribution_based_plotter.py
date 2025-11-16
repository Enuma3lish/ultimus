"""
Distribution-Based Algorithm Comparison Plotter

This script creates graphs separated by distribution type:
1. Normal distribution (when bp_parameter_L > bp_parameter_H)
2. Bounded-Pareto distribution (when bp_parameter_L <= bp_parameter_H)

For each distribution type, graphs are created for clairvoyant and non-clairvoyant algorithms.
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
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
OUTPUT_PATH = os.path.join(BASE_DATA_PATH, "distribution_based_plots")

# Create output directory
os.makedirs(OUTPUT_PATH, exist_ok=True)

# ============================================================================
# ALGORITHM DEFINITIONS
# ============================================================================
# Clairvoyant algorithms (know job sizes)
CLAIRVOYANT_ALGORITHMS = ['SRPT', 'SJF', 'BAL', 'RR', 'FCFS', 'Dynamic']

# Non-clairvoyant algorithms (don't know job sizes)
NON_CLAIRVOYANT_ALGORITHMS = ['RMLF', 'MLFQ', 'RR', 'FCFS', 'RFDynamic', 'SETF']

# Dynamic algorithms with modes
DYNAMIC_ALGORITHMS = ['Dynamic', 'RFDynamic']

# ============================================================================
# COLOR AND MARKER SCHEMES - ULTRA HIGH CONTRAST
# ============================================================================
ALGORITHM_COLORS = {
    'RR': '#0000FF',        # Pure Blue
    'SRPT': '#FF0000',      # Pure Red - MAXIMUM CONTRAST
    'SETF': '#00FF00',      # Pure Green
    'FCFS': '#FF00FF',      # Magenta
    'BAL': '#800080',       # Purple
    'RMLF': '#000000',      # Black - HIGH CONTRAST
    'MLFQ': '#FFD700',      # Gold/Yellow - ULTRA VISIBLE (very different from blue RR)
    'RFDynamic': '#00FFFF', # Cyan
    'SJF': '#8B4513',       # Saddle Brown
    'Dynamic': '#FF1493'    # Deep Pink
}

ALGORITHM_MARKERS = {
    'RR': 'o',              # Circle
    'SRPT': 'D',            # Diamond - LARGE AND VISIBLE
    'SETF': '^',            # Triangle up
    'FCFS': 'v',            # Triangle down
    'BAL': 's',             # Square
    'RMLF': 'P',            # Plus filled - HIGH CONTRAST
    'MLFQ': '*',            # Star - HIGH CONTRAST
    'RFDynamic': 'h',       # Hexagon
    'SJF': 'X',             # X filled
    'Dynamic': 'p'          # Pentagon
}

# Line styles to differentiate overlapping algorithms
ALGORITHM_LINESTYLES = {
    'RR': '-',              # Solid
    'SRPT': '-',            # Solid - THICK
    'SETF': '-',            # Solid
    'FCFS': '-',            # Solid
    'BAL': '-',             # Solid
    'RMLF': '-',            # Solid
    'MLFQ': '--',           # Dashed - DIFFERENT FROM RR
    'RFDynamic': '-',       # Solid
    'SJF': '-',             # Solid
    'Dynamic': ':',         # Dotted - DIFFERENT FROM FCFS
}

def setup_plot_style():
    """Set up matplotlib style for publication-quality plots with enhanced readability"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (18, 10),     # Even larger figure
        'font.size': 16,                 # Larger base font
        'axes.labelsize': 20,            # Larger axis labels
        'axes.titlesize': 22,            # Larger title
        'legend.fontsize': 15,           # Larger legend
        'xtick.labelsize': 15,           # Larger x-tick labels
        'ytick.labelsize': 15,           # Larger y-tick labels
        'lines.linewidth': 4.5,          # Thicker lines
        'lines.markersize': 16,          # Larger markers
        'lines.markeredgewidth': 3.0,    # Thicker marker edges
        'axes.grid': True,
        'grid.alpha': 0.4,               # More visible grid
        'grid.linewidth': 1.0,           # Thicker grid
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.labelweight': 'bold',      # Bold axis labels
        'axes.titleweight': 'bold',      # Bold title
    })

# ============================================================================
# DATA LOADING AND PROCESSING
# ============================================================================

def find_best_mode_from_random_softrandom(algorithm):
    """
    Find the best mode (excluding mode 6) for Dynamic algorithms using random+softrandom results

    This function counts the frequency of each mode being the best (lowest L2 norm) across
    all random and softrandom test cases, and selects the mode that wins most frequently.

    Args:
        algorithm: Algorithm name ('Dynamic' or 'RFDynamic')

    Returns:
        Best mode number (1-5)
    """
    # Load random and softrandom result files
    random_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "random_result")
    softrandom_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "softrandom_result")

    all_files = []
    if os.path.exists(random_dir):
        pattern = os.path.join(random_dir, f"*{algorithm}*.csv")
        all_files.extend(glob.glob(pattern))

    if os.path.exists(softrandom_dir):
        pattern = os.path.join(softrandom_dir, f"*{algorithm}*.csv")
        all_files.extend(glob.glob(pattern))

    if not all_files:
        logger.warning(f"No random/softrandom files found for {algorithm}, using default mode 5")
        return 5

    logger.info(f"Analyzing {len(all_files)} random+softrandom files for {algorithm}")

    # Count how many times each mode has the lowest L2 norm
    mode_win_count = {i: 0 for i in range(1, 6)}
    total_cases = 0

    for file_path in all_files:
        try:
            df = pd.read_csv(file_path)

            # For each frequency (row), find which mode has the lowest L2 norm
            for _, row in df.iterrows():
                mode_values = {}
                for i in range(1, 6):
                    col_name = f'{algorithm}_njobs100_mode{i}_L2_norm_flow_time'
                    if col_name in df.columns and pd.notna(row[col_name]):
                        mode_values[i] = row[col_name]

                if mode_values:
                    best_mode = min(mode_values.items(), key=lambda x: x[1])[0]
                    mode_win_count[best_mode] += 1
                    total_cases += 1

        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            continue

    if total_cases == 0:
        logger.warning(f"No valid data found for {algorithm}, using default mode 5")
        return 5

    # Find mode with highest win count
    best_mode = max(mode_win_count.items(), key=lambda x: x[1])[0]

    # Calculate percentages
    mode_percentages = {mode: (count / total_cases * 100) for mode, count in mode_win_count.items()}

    logger.info(f"{algorithm}: Best mode from random+softrandom analysis = mode{best_mode}")
    logger.info(f"  Total test cases: {total_cases}")
    logger.info(f"  Mode win counts: {mode_win_count}")
    logger.info(f"  Mode win percentages: {dict(sorted(mode_percentages.items()))}")

    return best_mode

def find_best_mode_except_6(df, algorithm):
    """
    DEPRECATED: Old method using avg data mean
    Find the best mode (excluding mode 6) for Dynamic algorithms

    Args:
        df: DataFrame with mode columns
        algorithm: Algorithm name ('Dynamic' or 'RFDynamic')

    Returns:
        Best mode number (1-5)
    """
    mode_columns = []
    for i in range(1, 6):  # modes 1-5 only
        col_name = f'{algorithm}_njobs100_mode{i}_L2_norm_flow_time'
        if col_name in df.columns:
            mode_columns.append((i, col_name))

    if not mode_columns:
        logger.warning(f"No mode columns found for {algorithm}")
        return 5  # Default to mode 5

    # Calculate mean L2 norm for each mode
    mode_means = {}
    for mode_num, col_name in mode_columns:
        mode_means[mode_num] = df[col_name].mean()

    # Find mode with lowest mean
    best_mode = min(mode_means.items(), key=lambda x: x[1])[0]

    logger.info(f"{algorithm}: Best mode (excluding mode 6) = mode{best_mode}")
    logger.info(f"  Mode means: {mode_means}")

    return best_mode

def load_algorithm_data(algorithm, avg_type='avg30'):
    """
    Load data for a single algorithm from avg30/avg60/avg90 results

    Args:
        algorithm: Algorithm name (e.g., 'MLFQ', 'SRPT', 'Dynamic')
        avg_type: Type of average ('avg30', 'avg60', 'avg90')

    Returns:
        DataFrame with combined data from all trial runs
    """
    algorithm_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", f"{avg_type}_result")

    if not os.path.exists(algorithm_dir):
        logger.warning(f"Directory not found: {algorithm_dir}")
        return None

    # Get all CSV files for this algorithm
    # Try two patterns: "*_{algorithm}_*_result.csv" and "*_{algorithm}_result_*.csv"
    pattern1 = os.path.join(algorithm_dir, f"*_{algorithm}_*_result.csv")
    pattern2 = os.path.join(algorithm_dir, f"*_{algorithm}_result_*.csv")
    files = sorted(glob.glob(pattern1) + glob.glob(pattern2))

    if not files:
        logger.warning(f"No result files found for {algorithm} in {avg_type}")
        return None

    logger.info(f"Loading {algorithm} data: found {len(files)} files")

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

    # Combine all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Handle Dynamic algorithms differently
    if algorithm in DYNAMIC_ALGORITHMS:
        # For Dynamic algorithms, we need to select the best mode (excluding mode 6)
        # Use random+softrandom benchmark to find the best mode
        best_mode = find_best_mode_from_random_softrandom(algorithm)
        best_mode_col = f'{algorithm}_njobs100_mode{best_mode}_L2_norm_flow_time'

        if best_mode_col not in combined_df.columns:
            logger.warning(f"Column {best_mode_col} not found in {algorithm} data")
            return None

        # Average across trials for the best mode
        grouped = combined_df.groupby(['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H'])[best_mode_col].mean().reset_index()

        # Rename the column to standard format for plotting
        grouped.rename(columns={best_mode_col: f'{algorithm}_L2_norm_flow_time'}, inplace=True)

        # Add mode info to the dataframe for reference
        grouped['best_mode'] = best_mode

    else:
        # Regular algorithms
        l2_col_name = f'{algorithm}_L2_norm_flow_time'

        if l2_col_name not in combined_df.columns:
            logger.warning(f"Column {l2_col_name} not found in {algorithm} data")
            return None

        # Average across trials
        grouped = combined_df.groupby(['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H'])[l2_col_name].mean().reset_index()

    return grouped

def load_all_algorithms_data(algorithms, avg_type='avg30'):
    """
    Load data for multiple algorithms

    Args:
        algorithms: List of algorithm names
        avg_type: Type of average ('avg30', 'avg60', 'avg90')

    Returns:
        Dictionary mapping algorithm name to DataFrame
    """
    data_dict = {}

    for algorithm in algorithms:
        df = load_algorithm_data(algorithm, avg_type)
        if df is not None:
            data_dict[algorithm] = df
            logger.info(f"Loaded {algorithm}: {len(df)} rows")

    return data_dict

def separate_by_distribution(df):
    """
    Separate data into normal and bounded-Pareto groups

    Args:
        df: DataFrame with bp_parameter_L and bp_parameter_H columns

    Returns:
        Tuple of (normal_df, bounded_pareto_df)
    """
    # Normal: bp_parameter_L > bp_parameter_H
    normal_df = df[df['bp_parameter_L'] > df['bp_parameter_H']].copy()

    # Bounded-Pareto: bp_parameter_L <= bp_parameter_H
    bounded_pareto_df = df[df['bp_parameter_L'] <= df['bp_parameter_H']].copy()

    return normal_df, bounded_pareto_df

# ============================================================================
# PLOTTING FUNCTIONS FOR NORMAL DISTRIBUTION
# ============================================================================

def plot_normal_distribution_by_variance(data_dict, group_name, avg_type='avg30'):
    """
    Plot normal distribution results grouped by bp_parameter_H (variance)

    For normal distribution: bp_parameter_L > bp_parameter_H
    - Group by bp_parameter_H
    - X-axis: arrival_rate
    - Y-axis: L2_norm_flow_time
    """
    logger.info(f"Creating normal distribution plots for {group_name}...")

    # Collect all normal distribution data
    all_normal_data = {}

    for algorithm, df in data_dict.items():
        normal_df, _ = separate_by_distribution(df)
        if not normal_df.empty:
            all_normal_data[algorithm] = normal_df

    if not all_normal_data:
        logger.warning(f"No normal distribution data found for {group_name}")
        return

    # Get unique bp_parameter_H values (variances)
    all_variances = set()
    for df in all_normal_data.values():
        all_variances.update(df['bp_parameter_H'].unique())

    all_variances = sorted(all_variances)

    logger.info(f"Found {len(all_variances)} variance values for normal distribution: {all_variances}")

    # Create a plot for each variance
    for variance in all_variances:
        setup_plot_style()
        fig, ax = plt.subplots(figsize=(18, 10))

        plotted_any = False

        for algorithm, df in all_normal_data.items():
            # Filter for this variance
            variance_df = df[df['bp_parameter_H'] == variance].copy()

            if variance_df.empty:
                continue

            # Sort by arrival rate
            variance_df = variance_df.sort_values('Mean_inter_arrival_time')

            # Get the L2 norm column name
            l2_col = f'{algorithm}_L2_norm_flow_time'

            if l2_col not in variance_df.columns:
                continue

            # Create label with mode info if it's a Dynamic algorithm
            if algorithm in DYNAMIC_ALGORITHMS and 'best_mode' in variance_df.columns:
                best_mode = variance_df['best_mode'].iloc[0]
                label = f"{algorithm} (mode{best_mode})"
            else:
                label = algorithm

            # Special treatment for SRPT and MLFQ - extra thick and visible
            if algorithm == 'SRPT':
                linewidth = 5.5
                markersize = 17
            elif algorithm == 'MLFQ':
                linewidth = 6.0  # EXTRA THICK for MLFQ to stand out over RR
                markersize = 16
            else:
                linewidth = 4.0
                markersize = 14

            # Get line style and adjust dash pattern for MLFQ
            linestyle = ALGORITHM_LINESTYLES.get(algorithm, '-')
            dashes = None
            if algorithm == 'MLFQ':
                dashes = [15, 8]  # Wide dashes: 15 points on, 8 points off - VERY VISIBLE

            # Plot
            line = ax.plot(variance_df['Mean_inter_arrival_time'], variance_df[l2_col],
                   marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                   color=ALGORITHM_COLORS.get(algorithm, 'black'),
                   linestyle=linestyle,
                   linewidth=linewidth,
                   markersize=markersize,
                   markeredgewidth=2.5,
                   markeredgecolor='white',
                   markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                   label=label,
                   alpha=0.95,
                   zorder=10 if algorithm in ['SRPT', 'MLFQ'] else 5)  # Higher z-order for visibility

            # Apply custom dashes if needed
            if dashes is not None:
                line[0].set_dashes(dashes)

            plotted_any = True

        if not plotted_any:
            plt.close()
            continue

        ax.set_xlabel('Mean Inter-Arrival Time', fontweight='bold', fontsize=20)
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold', fontsize=20)
        ax.set_title(f'{group_name} Algorithms - Normal Distribution\nVariance (bp_parameter_H) = {variance}',
                    fontweight='bold', fontsize=22, pad=20)

        # Set x-axis to start from 20 and increase by 2
        x_min = 20
        x_max = 40
        ax.set_xlim(x_min - 1, x_max + 1)
        ax.set_xticks(range(x_min, x_max + 1, 2))

        # Format y-axis with scientific notation and more tick marks
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0), useMathText=True)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=10, integer=False))

        # Add minor ticks for better readability
        ax.minorticks_on()

        # Add grid for better readability
        ax.grid(True, alpha=0.5, which='major', linewidth=1.2, color='gray')
        ax.grid(True, alpha=0.25, which='minor', linestyle=':', linewidth=0.8, color='gray')

        # Enhanced legend with better visibility
        ax.legend(loc='best', framealpha=0.98, fancybox=True, shadow=True,
                 edgecolor='black', facecolor='white', frameon=True,
                 fontsize=15, ncol=1, borderpad=1.0, labelspacing=1.0)

        # Log how many algorithms and data points were plotted
        num_lines = len(ax.get_lines())
        logger.info(f"  Plotted {num_lines} algorithms for variance={variance}")

        # Log which algorithms were plotted
        for line in ax.get_lines():
            label = line.get_label()
            logger.info(f"    - {label}")

        # Save plot
        output_file = os.path.join(OUTPUT_PATH, f"normal_{group_name}_{avg_type}_variance_{variance}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

        # Also save data to CSV for detailed analysis
        csv_output = os.path.join(OUTPUT_PATH, f"normal_{group_name}_{avg_type}_variance_{variance}_data.csv")

        # Collect data from all plotted algorithms
        data_for_csv = {}
        for algorithm, df in all_normal_data.items():
            variance_df = df[df['bp_parameter_H'] == variance].copy()
            if variance_df.empty:
                continue

            variance_df = variance_df.sort_values('Mean_inter_arrival_time')
            l2_col = f'{algorithm}_L2_norm_flow_time'

            if l2_col in variance_df.columns:
                if algorithm in DYNAMIC_ALGORITHMS and 'best_mode' in variance_df.columns:
                    best_mode = variance_df['best_mode'].iloc[0]
                    col_name = f"{algorithm} (mode{best_mode})"
                else:
                    col_name = algorithm

                data_for_csv['Mean_inter_arrival_time'] = variance_df['Mean_inter_arrival_time'].values
                data_for_csv[col_name] = variance_df[l2_col].values

        if data_for_csv:
            import pandas as pd
            csv_df = pd.DataFrame(data_for_csv)
            csv_df.to_csv(csv_output, index=False, float_format='%.2f')
            logger.info(f"  Saved data: {csv_output}")

# ============================================================================
# PLOTTING FUNCTIONS FOR BOUNDED-PARETO DISTRIBUTION
# ============================================================================

def plot_bounded_pareto_by_params(data_dict, group_name, avg_type='avg30'):
    """
    Plot bounded-Pareto distribution results grouped by (bp_parameter_L, bp_parameter_H)

    For bounded-Pareto: bp_parameter_L <= bp_parameter_H
    - Group by (bp_parameter_L, bp_parameter_H)
    - X-axis: mean-inter-arrival_time (arrival_rate)
    - Y-axis: L2_norm_flow_time
    """
    logger.info(f"Creating bounded-Pareto plots for {group_name}...")

    # Collect all bounded-Pareto data
    all_bounded_data = {}

    for algorithm, df in data_dict.items():
        _, bounded_df = separate_by_distribution(df)
        if not bounded_df.empty:
            all_bounded_data[algorithm] = bounded_df

    if not all_bounded_data:
        logger.warning(f"No bounded-Pareto data found for {group_name}")
        return

    # Get unique (bp_parameter_L, bp_parameter_H) combinations
    all_param_pairs = set()
    for df in all_bounded_data.values():
        for _, row in df[['bp_parameter_L', 'bp_parameter_H']].drop_duplicates().iterrows():
            all_param_pairs.add((row['bp_parameter_L'], row['bp_parameter_H']))

    all_param_pairs = sorted(all_param_pairs)

    logger.info(f"Found {len(all_param_pairs)} parameter combinations for bounded-Pareto")

    # Create a plot for each parameter combination
    for bp_L, bp_H in all_param_pairs:
        setup_plot_style()
        fig, ax = plt.subplots(figsize=(18, 10))

        plotted_any = False

        for algorithm, df in all_bounded_data.items():
            # Filter for this parameter combination
            param_df = df[(df['bp_parameter_L'] == bp_L) & (df['bp_parameter_H'] == bp_H)].copy()

            if param_df.empty:
                continue

            # Sort by arrival rate
            param_df = param_df.sort_values('Mean_inter_arrival_time')

            # Get the L2 norm column name
            l2_col = f'{algorithm}_L2_norm_flow_time'

            if l2_col not in param_df.columns:
                continue

            # Create label with mode info if it's a Dynamic algorithm
            if algorithm in DYNAMIC_ALGORITHMS and 'best_mode' in param_df.columns:
                best_mode = param_df['best_mode'].iloc[0]
                label = f"{algorithm} (mode{best_mode})"
            else:
                label = algorithm

            # Special treatment for SRPT and MLFQ - extra thick and visible
            if algorithm == 'SRPT':
                linewidth = 5.5
                markersize = 17
            elif algorithm == 'MLFQ':
                linewidth = 6.0  # EXTRA THICK for MLFQ to stand out over RR
                markersize = 16
            else:
                linewidth = 4.0
                markersize = 14

            # Get line style and adjust dash pattern for MLFQ
            linestyle = ALGORITHM_LINESTYLES.get(algorithm, '-')
            dashes = None
            if algorithm == 'MLFQ':
                dashes = [15, 8]  # Wide dashes: 15 points on, 8 points off - VERY VISIBLE

            # Plot
            line = ax.plot(param_df['Mean_inter_arrival_time'], param_df[l2_col],
                   marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
                   color=ALGORITHM_COLORS.get(algorithm, 'black'),
                   linestyle=linestyle,
                   linewidth=linewidth,
                   markersize=markersize,
                   markeredgewidth=2.5,
                   markeredgecolor='white',
                   markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
                   label=label,
                   alpha=0.95,
                   zorder=10 if algorithm in ['SRPT', 'MLFQ'] else 5)  # Higher z-order for visibility

            # Apply custom dashes if needed
            if dashes is not None:
                line[0].set_dashes(dashes)

            plotted_any = True

        if not plotted_any:
            plt.close()
            continue

        ax.set_xlabel('Mean Inter-Arrival Time', fontweight='bold', fontsize=20)
        ax.set_ylabel('L2-Norm Flow Time', fontweight='bold', fontsize=20)
        ax.set_title(f'{group_name} Algorithms - Bounded-Pareto Distribution\n'
                    f'bp_parameter_L = {bp_L:.3f}, bp_parameter_H = {bp_H}',
                    fontweight='bold', fontsize=22, pad=20)

        # Set x-axis to start from 20 and increase by 2
        x_min = 20
        x_max = 40
        ax.set_xlim(x_min - 1, x_max + 1)
        ax.set_xticks(range(x_min, x_max + 1, 2))

        # Format y-axis with scientific notation and more tick marks
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0), useMathText=True)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=10, integer=False))

        # Add minor ticks for better readability
        ax.minorticks_on()

        # Add grid for better readability
        ax.grid(True, alpha=0.5, which='major', linewidth=1.2, color='gray')
        ax.grid(True, alpha=0.25, which='minor', linestyle=':', linewidth=0.8, color='gray')

        # Enhanced legend with better visibility
        ax.legend(loc='best', framealpha=0.98, fancybox=True, shadow=True,
                 edgecolor='black', facecolor='white', frameon=True,
                 fontsize=15, ncol=1, borderpad=1.0, labelspacing=1.0)

        # Log how many algorithms and data points were plotted
        num_lines = len(ax.get_lines())
        logger.info(f"  Plotted {num_lines} algorithms for L={bp_L:.3f}, H={bp_H}")

        # Log which algorithms were plotted
        for line in ax.get_lines():
            label = line.get_label()
            logger.info(f"    - {label}")

        # Save plot
        output_file = os.path.join(OUTPUT_PATH,
                                   f"bounded_pareto_{group_name}_{avg_type}_L_{bp_L:.3f}_H_{bp_H}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"  Saved: {output_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    logger.info("\n" + "=" * 80)
    logger.info("DISTRIBUTION-BASED ALGORITHM COMPARISON PLOTTER - STARTING")
    logger.info("=" * 80)

    # Process only avg30 as requested
    avg_type = 'avg30'

    logger.info(f"\nProcessing {avg_type} results...")

    # Load clairvoyant algorithms
    logger.info("\nLoading clairvoyant algorithms...")
    clairvoyant_data = load_all_algorithms_data(CLAIRVOYANT_ALGORITHMS, avg_type)

    # Load non-clairvoyant algorithms
    logger.info("\nLoading non-clairvoyant algorithms...")
    non_clairvoyant_data = load_all_algorithms_data(NON_CLAIRVOYANT_ALGORITHMS, avg_type)

    # Create plots for normal distribution
    logger.info("\n" + "=" * 80)
    logger.info("Creating Normal Distribution Plots")
    logger.info("=" * 80)

    if clairvoyant_data:
        plot_normal_distribution_by_variance(clairvoyant_data, "Clairvoyant", avg_type)

    if non_clairvoyant_data:
        plot_normal_distribution_by_variance(non_clairvoyant_data, "Non-Clairvoyant", avg_type)

    # Create plots for bounded-Pareto distribution
    logger.info("\n" + "=" * 80)
    logger.info("Creating Bounded-Pareto Distribution Plots")
    logger.info("=" * 80)

    if clairvoyant_data:
        plot_bounded_pareto_by_params(clairvoyant_data, "Clairvoyant", avg_type)

    if non_clairvoyant_data:
        plot_bounded_pareto_by_params(non_clairvoyant_data, "Non-Clairvoyant", avg_type)

    logger.info("\n" + "=" * 80)
    logger.info("ALL TASKS COMPLETED SUCCESSFULLY!")
    logger.info(f"Output directory: {OUTPUT_PATH}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
