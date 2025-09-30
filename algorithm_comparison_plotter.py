"""
Enhanced Algorithm Comparison Plotter

IMPORTANT: Before running this script, please update the BASE_DATA_PATH variable below
to point to the directory containing your 'ultimus' folder.

Example:
- If your data is at: /Users/melowu/Desktop/ultimus/SRPT_result/avg30_result
- Set BASE_DATA_PATH = "/Users/melowu/Desktop"

The script will automatically construct the full paths from there.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
from pathlib import Path
import logging
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure base paths - UPDATE THESE TO MATCH YOUR DIRECTORY STRUCTURE
BASE_DATA_PATH = "/Users/melowu/Desktop/"  # Change this to your base path
ULTIMUS_PATH = os.path.join(BASE_DATA_PATH, "ultimus")
DYNAMIC_ANALYSIS_PATH = os.path.join(BASE_DATA_PATH, "ultimus/Dynamic_analysis")

# Define algorithms
ALGORITHMS = ['BAL', 'FCFS', 'Dynamic', 'SRPT', 'RR', 'SETF','SJF']

# Define global color and marker schemes for consistency
ALGORITHM_COLORS = {
    'RR': '#1f77b4',        # blue
    'SRPT': '#ff7f0e',      # orange
    'SETF': '#2ca02c',      # green
    'FCFS': '#d62728',      # red
    'BAL': '#9467bd',       # purple
    'Dynamic': '#8c564b',   # brown
    'SJF': '#17becf'
}

ALGORITHM_MARKERS = {
    'RR': 'o',              # circle
    'SRPT': 's',            # square
    'SETF': '^',            # triangle up
    'FCFS': 'v',            # triangle down
    'BAL': 'D',             # diamond
    'Dynamic': 'x',         # x
    'SJF': 'P'
}

# Define colors and markers for Dynamic modes
DYNAMIC_COLORS = {
    'Dynamic_njobs100_mode1_L2_norm_flow_time': '#1f77b4',   # blue
    'Dynamic_njobs100_mode2_L2_norm_flow_time': '#ff7f0e',   # orange
    'Dynamic_njobs100_mode3_L2_norm_flow_time': '#2ca02c',   # green
    'Dynamic_njobs100_mode4_L2_norm_flow_time': '#d62728',   # red
    'Dynamic_njobs100_mode5_L2_norm_flow_time': '#9467bd',   # purple
    'Dynamic_njobs100_mode6_L2_norm_flow_time': '#8c564b',   # brown
}

DYNAMIC_MARKERS = {
    'Dynamic_njobs100_mode1_L2_norm_flow_time': '^',         # triangle up
    'Dynamic_njobs100_mode2_L2_norm_flow_time': 'v',         # triangle down
    'Dynamic_njobs100_mode3_L2_norm_flow_time': 's',         # square
    'Dynamic_njobs100_mode4_L2_norm_flow_time': 'D',         # diamond
    'Dynamic_njobs100_mode5_L2_norm_flow_time': 'o',         # circle
    'Dynamic_njobs100_mode6_L2_norm_flow_time': 'x',         # x
}

# Colors and markers for percentile analysis
PERCENTILE_COLORS = {
    '1%': '#e74c3c',    # red
    '5%': '#f39c12',    # orange  
    '10%': '#3498db'    # blue
}

PERCENTILE_MARKERS = {
    '1%': 'o',          # circle
    '5%': 's',          # square
    '10%': '^'          # triangle
}

def validate_paths():
    """Validate that the configured paths exist"""
    logger.info("Validating configured paths...")
    logger.info(f"BASE_DATA_PATH: {BASE_DATA_PATH}")
    logger.info(f"ULTIMUS_PATH: {ULTIMUS_PATH}")
    logger.info(f"DYNAMIC_ANALYSIS_PATH: {DYNAMIC_ANALYSIS_PATH}")
    
    if not os.path.exists(BASE_DATA_PATH):
        logger.error(f"BASE_DATA_PATH does not exist: {BASE_DATA_PATH}")
        return False
    
    if not os.path.exists(ULTIMUS_PATH):
        logger.error(f"ULTIMUS_PATH does not exist: {ULTIMUS_PATH}")
        logger.error("Please check your BASE_DATA_PATH configuration")
        return False
    
    # Check if any algorithm directories exist
    found_algorithms = []
    for algorithm in ALGORITHMS:
        algo_path = os.path.join(ULTIMUS_PATH, f"{algorithm}_result")
        if os.path.exists(algo_path):
            found_algorithms.append(algorithm)
    
    if found_algorithms:
        logger.info(f"Found algorithm directories: {found_algorithms}")
    else:
        logger.warning("No algorithm directories found in ULTIMUS_PATH")
    
    return True

def setup_plot_style():
    """Set up matplotlib style for publication-quality plots"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (10, 6),
        'font.size': 12,
        'font.family': 'sans-serif',
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 11,
        'lines.linewidth': 2,
        'lines.markersize': 8,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        'axes.linewidth': 1.5,
        'axes.edgecolor': 'black',
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1
    })

def analyze_job_sizes_for_percentiles(data_type="random"):
    """
    Analyze job sizes to calculate percentile ratios for random/softrandom data
    
    Parameters:
    data_type (str): "random" or "softrandom"
    
    Returns:
    DataFrame with coherence_time and percentile ratios
    """
    logger.info(f"Analyzing job sizes for {data_type} data...")
    
    # Look for original job data files
    data_dir = os.path.join(BASE_DATA_PATH, "data")
    
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory not found: {data_dir}")
        return None
    
    coherence_times = [pow(2, j) for j in range(1, 17, 1)]
    results = []
    
    for ct in coherence_times:
        if data_type == "random":
            # Look for random frequency files
            pattern = f"{data_dir}/freq_{ct}_*/random_freq_{ct}.csv"
        else:
            # Look for softrandom frequency files  
            pattern = f"{data_dir}/softrandom_*/freq_{ct}_*/softrandom_freq_{ct}.csv"
        
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No {data_type} files found for coherence time {ct}")
            continue
        
        # Collect all job sizes for this coherence time
        all_job_sizes = []
        total_size = 0
        
        for file in files:
            try:
                df = pd.read_csv(file)
                job_sizes = df['job_size'].values
                all_job_sizes.extend(job_sizes)
                total_size += job_sizes.sum()
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                continue
        
        if not all_job_sizes:
            continue
        
        # Calculate percentiles
        all_job_sizes = np.array(all_job_sizes)
        p99 = np.percentile(all_job_sizes, 99)  # Top 1%
        p95 = np.percentile(all_job_sizes, 95)  # Top 5%
        p90 = np.percentile(all_job_sizes, 90)  # Top 10%
        
        # Calculate ratios
        large_1_percent = all_job_sizes[all_job_sizes >= p99].sum()
        large_5_percent = all_job_sizes[all_job_sizes >= p95].sum()
        large_10_percent = all_job_sizes[all_job_sizes >= p90].sum()
        
        ratio_1_percent = large_1_percent / total_size if total_size > 0 else 0
        ratio_5_percent = large_5_percent / total_size if total_size > 0 else 0
        ratio_10_percent = large_10_percent / total_size if total_size > 0 else 0
        
        results.append({
            'coherence_time': ct,
            'ratio_1_percent': ratio_1_percent,
            'ratio_5_percent': ratio_5_percent,
            'ratio_10_percent': ratio_10_percent
        })
        
        logger.info(f"Coherence time {ct}: 1%={ratio_1_percent:.4f}, 5%={ratio_5_percent:.4f}, 10%={ratio_10_percent:.4f}")
    
    if results:
        return pd.DataFrame(results)
    return None

def create_job_size_percentile_plot(random_data, softrandom_data, output_path):
    """
    Create job size percentile ratio plots for random and softrandom data
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot random data
    if random_data is not None:
        for percentile in ['1%', '5%', '10%']:
            col_name = f'ratio_{percentile.rstrip("%")}_percent'
            if col_name in random_data.columns:
                ax1.plot(random_data['coherence_time'], random_data[col_name],
                        color=PERCENTILE_COLORS[percentile],
                        marker=PERCENTILE_MARKERS[percentile],
                        linewidth=2, markersize=8,
                        label=f'Top {percentile}',
                        alpha=0.9)
        
        ax1.set_xscale('log', base=2)
        ax1.set_xlabel('Coherence Time', fontsize=14)
        ax1.set_ylabel('Job Size Ratio', fontsize=14)
        ax1.set_title('Random: Large Job Size Ratios', fontsize=16, fontweight='bold')
        ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Plot softrandom data
    if softrandom_data is not None:
        for percentile in ['1%', '5%', '10%']:
            col_name = f'ratio_{percentile.rstrip("%")}_percent'
            if col_name in softrandom_data.columns:
                ax2.plot(softrandom_data['coherence_time'], softrandom_data[col_name],
                        color=PERCENTILE_COLORS[percentile],
                        marker=PERCENTILE_MARKERS[percentile],
                        linewidth=2, markersize=8,
                        label=f'Top {percentile}',
                        alpha=0.9)
        
        ax2.set_xscale('log', base=2)
        ax2.set_xlabel('Coherence Time', fontsize=14)
        ax2.set_ylabel('Job Size Ratio', fontsize=14)
        ax2.set_title('Softrandom: Large Job Size Ratios', fontsize=16, fontweight='bold')
        ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax2.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved job size percentile plot to {output_path}")

def create_best_dynamic_vs_algorithms_plot(df, best_dynamic_col, bp_param, output_path, data_type="general"):
    """
    Create plot showing best Dynamic setting vs each algorithm separately
    """
    plt.figure(figsize=(12, 8))
    
    algorithms = ['RR', 'SRPT', 'SETF', 'FCFS', 'BAL', 'SJF']
    
    if data_type == "general":
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Best Dynamic vs All Algorithms - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        df = df.sort_values('frequency').reset_index(drop=True)
        x_values = df['frequency'].values
        x_label = 'Coherence Time'
        title = f'Best Dynamic vs All Algorithms - {data_type.capitalize()}'
    
    # Plot best Dynamic setting
    if best_dynamic_col in df.columns:
        best_setting_display = best_dynamic_col.replace('Dynamic_njobs100_', '').replace('_L2_norm_flow_time', '')
        plt.plot(x_values, df[best_dynamic_col].values,
                color=ALGORITHM_COLORS['Dynamic'],
                marker=ALGORITHM_MARKERS['Dynamic'],
                linewidth=2.5, markersize=10,
                label=f'Dynamic {best_setting_display}',
                alpha=0.9)
    
    # Plot each algorithm
    for algo in algorithms:
        col_name = f'{algo}_L2_norm_flow_time'
        
        if col_name in df.columns:
            plt.plot(x_values, df[col_name].values,
                    color=ALGORITHM_COLORS[algo],
                    marker=ALGORITHM_MARKERS[algo],
                    linewidth=2, markersize=8,
                    label=algo,
                    alpha=0.9)
    
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('L2 Norm Flow Time', fontsize=14)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    if data_type in ["random", "softrandom"]:
        plt.xscale('log', base=2)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved best Dynamic vs algorithms plot to {output_path}")

def analyze_maximum_flow_time(data_type="random"):
    """
    Analyze maximum flow time for each algorithm across coherence times
    
    Parameters:
    data_type (str): "random" or "softrandom"
    
    Returns:
    DataFrame with coherence_time and maximum flow times for each algorithm
    """
    logger.info(f"Analyzing maximum flow time for {data_type} data...")
    
    coherence_times = [pow(2, j) for j in range(1, 17, 1)]
    results = []
    
    for ct in coherence_times:
        ct_result = {'coherence_time': ct}
        
        for algorithm in ALGORITHMS:
            result_dir = os.path.join(ULTIMUS_PATH, f"{algorithm}_result", f"{data_type}_result")
            
            if algorithm == 'Dynamic':
                pattern = f"{result_dir}/{data_type}_result_Dynamic_njobs100_*.csv"
            else:
                pattern = f"{result_dir}/{data_type}_result_{algorithm}_*.csv"
            
            files = glob.glob(pattern)
            
            if not files:
                continue
            
            max_flow_times = []
            
            for file in files:
                try:
                    df = pd.read_csv(file)
                    # Filter for current coherence time
                    ct_data = df[df['frequency'] == ct]
                    
                    if algorithm == 'Dynamic':
                        # For Dynamic, find maximum across all modes
                        max_cols = [col for col in ct_data.columns if 'max_flow_time' in col]
                        if max_cols:
                            for col in max_cols:
                                if not ct_data[col].empty:
                                    max_flow_times.extend(ct_data[col].dropna().values)
                    else:
                        # For other algorithms
                        max_col = f'{algorithm}_max_flow_time'
                        if max_col in ct_data.columns and not ct_data[max_col].empty:
                            max_flow_times.extend(ct_data[max_col].dropna().values)
                            
                except Exception as e:
                    logger.error(f"Error reading {file}: {e}")
                    continue
            
            if max_flow_times:
                if algorithm == 'Dynamic':
                    ct_result[f'{algorithm}_max_flow_time'] = np.mean(max_flow_times)
                else:
                    ct_result[f'{algorithm}_max_flow_time'] = np.mean(max_flow_times)
        
        if len(ct_result) > 1:  # More than just coherence_time
            results.append(ct_result)
    
    if results:
        return pd.DataFrame(results)
    return None

def create_maximum_flow_time_plots(random_data, softrandom_data, output_dir):
    """
    Create maximum flow time plots for random and softrandom data
    """
    os.makedirs(output_dir, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    algorithms = ['RR', 'SRPT', 'SETF', 'FCFS', 'BAL', 'Dynamic', 'SJF']
    
    # Plot random data
    if random_data is not None:
        for algo in algorithms:
            col_name = f'{algo}_max_flow_time'
            if col_name in random_data.columns:
                ax1.plot(random_data['coherence_time'], random_data[col_name],
                        color=ALGORITHM_COLORS[algo],
                        marker=ALGORITHM_MARKERS[algo],
                        linewidth=2, markersize=8,
                        label=algo,
                        alpha=0.9)
        
        ax1.set_xscale('log', base=2)
        ax1.set_xlabel('Coherence Time', fontsize=14)
        ax1.set_ylabel('Maximum Flow Time', fontsize=14)
        ax1.set_title('Random: Maximum Flow Time by Algorithm', fontsize=16, fontweight='bold')
        ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Plot softrandom data
    if softrandom_data is not None:
        for algo in algorithms:
            col_name = f'{algo}_max_flow_time'
            if col_name in softrandom_data.columns:
                ax2.plot(softrandom_data['coherence_time'], softrandom_data[col_name],
                        color=ALGORITHM_COLORS[algo],
                        marker=ALGORITHM_MARKERS[algo],
                        linewidth=2, markersize=8,
                        label=algo,
                        alpha=0.9)
        
        ax2.set_xscale('log', base=2)
        ax2.set_xlabel('Coherence Time', fontsize=14)
        ax2.set_ylabel('Maximum Flow Time', fontsize=14)
        ax2.set_title('Softrandom: Maximum Flow Time by Algorithm', fontsize=16, fontweight='bold')
        ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax2.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    output_path = f"{output_dir}/Maximum_Flow_Time_Comparison.pdf"
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved maximum flow time plots to {output_path}")

def process_avg30_results():
    """Process avg30 results for all algorithms"""
    
    for algorithm in ALGORITHMS:
        logger.info(f"Processing avg30 results for {algorithm}")
        
        result_dir = os.path.join(ULTIMUS_PATH, f"{algorithm}_result", "avg30_result")
        if not os.path.exists(result_dir):
            logger.warning(f"Directory {result_dir} not found")
            continue
            
        # Get all result files for this algorithm
        pattern = f"{result_dir}/*_{algorithm}_result_*.csv"
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No result files found for {algorithm}")
            continue
            
        # Group files by arrival rate (first number in filename)
        arrival_rate_groups = {}
        for file in files:
            filename = os.path.basename(file)
            arrival_rate = filename.split('_')[0]
            
            if arrival_rate not in arrival_rate_groups:
                arrival_rate_groups[arrival_rate] = []
            arrival_rate_groups[arrival_rate].append(file)
        
        # Process each arrival rate group
        all_results = []
        
        for arrival_rate, file_list in arrival_rate_groups.items():
            logger.info(f"Processing arrival rate {arrival_rate} for {algorithm} ({len(file_list)} files)")
            
            # Read all files for this arrival rate
            dfs = []
            for file in file_list:
                try:
                    df = pd.read_csv(file)
                    dfs.append(df)
                except Exception as e:
                    logger.error(f"Error reading {file}: {e}")
                    continue
            
            if not dfs:
                continue
                
            # Combine all dataframes
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Process based on algorithm type
            if algorithm == 'Dynamic':
                # For Dynamic, L2 norm columns have names
                l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
                
                # Group by bp_parameter_L and bp_parameter_H, then average
                grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
                
                arrival_rate_data = []
                for (arr_rate, bp_L, bp_H), group in grouped:
                    row_data = {
                        'arrival_rate': arr_rate,
                        'bp_parameter_L': bp_L,
                        'bp_parameter_H': bp_H
                    }
                    
                    # Average L2 norm values for each mode
                    for col in l2_cols:
                        if col in group.columns:
                            row_data[col] = group[col].mean()
                    
                    arrival_rate_data.append(row_data)
                    all_results.append(row_data)
                
            else:
                # For other algorithms, we now have proper column names
                l2_col_name = f'{algorithm}_L2_norm_flow_time'
                
                grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
                
                arrival_rate_data = []
                for (arr_rate, bp_L, bp_H), group in grouped:
                    if l2_col_name in group.columns:
                        row_data = {
                            'arrival_rate': arr_rate,
                            'bp_parameter_L': bp_L,
                            'bp_parameter_H': bp_H,
                            l2_col_name: group[l2_col_name].mean()
                        }
                        
                        arrival_rate_data.append(row_data)
                        all_results.append(row_data)
                    else:
                        logger.warning(f"L2 norm column {l2_col_name} not found in {algorithm} data")
                        continue
            
            # Create intermediate file for this arrival rate
            if arrival_rate_data:
                intermediate_df = pd.DataFrame(arrival_rate_data)
                intermediate_file = f"{arrival_rate}_avg_{algorithm}_result.csv"
                intermediate_df.to_csv(intermediate_file, index=False)
                logger.info(f"Created intermediate file: {intermediate_file}")
        
        # Create final combined file
        if all_results:
            final_df = pd.DataFrame(all_results)
            # Sort by arrival_rate and bp_parameter_L
            final_df = final_df.sort_values(['arrival_rate', 'bp_parameter_L'])
            
            output_file = f"{algorithm}_result_avg30.csv"
            final_df.to_csv(output_file, index=False)
            logger.info(f"Created final file: {output_file}")

def process_random_softrandom_results():
    """Process random and softrandom results"""
    
    for algorithm in ALGORITHMS:
        for result_type in ['random', 'softrandom']:
            logger.info(f"Processing {result_type} results for {algorithm}")
            
            result_dir = os.path.join(ULTIMUS_PATH, f"{algorithm}_result", f"{result_type}_result")
            if not os.path.exists(result_dir):
                logger.warning(f"Directory {result_dir} not found")
                continue
            
            if algorithm == 'Dynamic':
                # Dynamic case: files named like random_result_Dynamic_njobs100_{1-10}.csv
                pattern = f"{result_dir}/{result_type}_result_Dynamic_njobs100_*.csv"
                files = glob.glob(pattern)
                
                if not files:
                    logger.warning(f"No Dynamic {result_type} files found")
                    continue
                
                # Read all files and average by frequency
                all_dfs = []
                for file in files:
                    try:
                        df = pd.read_csv(file)
                        all_dfs.append(df)
                    except Exception as e:
                        logger.error(f"Error reading {file}: {e}")
                        continue
                
                if not all_dfs:
                    continue
                
                # Combine and average by frequency
                combined_df = pd.concat(all_dfs, ignore_index=True)
                l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
                
                # Group by frequency and average
                averaged_df = combined_df.groupby('frequency')[l2_cols].mean().reset_index()
                
                output_file = f"Dynamic_{result_type}_result_avg.csv"
                averaged_df.to_csv(output_file, index=False)
                logger.info(f"Created {output_file}")
                
            else:
                # Other algorithms: files like random_result_BAL_{1-10}.csv
                pattern = f"{result_dir}/{result_type}_result_{algorithm}_*.csv"
                files = glob.glob(pattern)
                
                if not files:
                    logger.warning(f"No {algorithm} {result_type} files found")
                    continue
                
                # Read all files
                frequency_data = {}
                l2_col_name = f'{algorithm}_L2_norm_flow_time'
                
                for file in files:
                    try:
                        df = pd.read_csv(file)
                        
                        # Process the data
                        for _, row in df.iterrows():
                            frequency = row['frequency']
                            l2_norm = row[l2_col_name]
                            
                            if frequency not in frequency_data:
                                frequency_data[frequency] = []
                            frequency_data[frequency].append(l2_norm)
                            
                    except Exception as e:
                        logger.error(f"Error reading {file}: {e}")
                        continue
                
                if not frequency_data:
                    continue
                
                # Average by frequency
                averaged_data = []
                for frequency, values in frequency_data.items():
                    averaged_data.append({
                        'frequency': frequency,
                        l2_col_name: np.mean(values)
                    })
                
                averaged_df = pd.DataFrame(averaged_data)
                averaged_df = averaged_df.sort_values('frequency')
                
                output_file = f"{algorithm}_{result_type}_result_avg.csv"
                averaged_df.to_csv(output_file, index=False)
                logger.info(f"Created {output_file}")

def process_dynamic_srpt_analysis():
    """Process Dynamic SRPT percentage analysis"""
    
    analysis_dir = os.path.join(DYNAMIC_ANALYSIS_PATH, "avg_30")
    if not os.path.exists(analysis_dir):
        logger.warning(f"Directory {analysis_dir} not found")
        return
    
    for mode in range(1, 7):  # modes 1-6
        logger.info(f"Processing Dynamic SRPT analysis for mode {mode}")
        
        # Find all round files for this mode
        pattern = f"{analysis_dir}/mode_{mode}/Dynamic_avg_30_nJobsPerRound_100_mode_{mode}_round_*.csv"
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No SRPT analysis files found for mode {mode}")
            continue
        
        # Read all round files
        all_dfs = []
        for file in files:
            try:
                df = pd.read_csv(file)
                all_dfs.append(df)
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                continue
        
        if not all_dfs:
            continue
        
        # Combine and average by arrival_rate, bp_L, bp_H
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Group by arrival_rate, bp_L, bp_H and average SRPT_percentage
        grouped = combined_df.groupby(['arrival_rate', 'bp_L', 'bp_H'])['SRPT_percentage'].mean().reset_index()
        grouped = grouped.sort_values(['arrival_rate', 'bp_L'])
        
        output_file = f"Dynamic_SRPT_percentage_mode{mode}_avg.csv"
        grouped.to_csv(output_file, index=False)
        logger.info(f"Created {output_file}")

def find_universal_best_dynamic_setting():
    """
    Find the best DYNAMIC setting across random + softrandom data
    """
    overall_counter = Counter()
    
    # Process random results
    random_file = "Dynamic_random_result_avg.csv"
    if os.path.exists(random_file):
        try:
            df = pd.read_csv(random_file)
            dynamic_cols = [col for col in df.columns if 'mode' in col and 'L2_norm_flow_time' in col]
            
            for idx, row in df.iterrows():
                dynamic_values = {col: row[col] for col in dynamic_cols if pd.notna(row[col])}
                
                if dynamic_values:
                    best_setting = min(dynamic_values, key=dynamic_values.get)
                    overall_counter[best_setting] += 1
                    
        except Exception as e:
            logger.error(f"Error processing random results: {e}")
    
    # Process softrandom results
    softrandom_file = "Dynamic_softrandom_result_avg.csv"
    if os.path.exists(softrandom_file):
        try:
            df = pd.read_csv(softrandom_file)
            dynamic_cols = [col for col in df.columns if 'mode' in col and 'L2_norm_flow_time' in col]
            
            for idx, row in df.iterrows():
                dynamic_values = {col: row[col] for col in dynamic_cols if pd.notna(row[col])}
                
                if dynamic_values:
                    best_setting = min(dynamic_values, key=dynamic_values.get)
                    overall_counter[best_setting] += 1
                    
        except Exception as e:
            logger.error(f"Error processing softrandom results: {e}")
    
    if overall_counter:
        logger.info("\nDynamic Setting Frequency Analysis:")
        for setting, count in overall_counter.most_common():
            logger.info(f"  {setting}: {count} occurrences")
        
        best_overall = overall_counter.most_common(1)[0][0]
        logger.info(f"\nUniversal best DYNAMIC setting: {best_overall}")
        return best_overall
    
    return "Dynamic_njobs100_mode1_L2_norm_flow_time"

def create_dynamic_comparison_plot(df, bp_param, output_path, data_type="general"):
    """
    Create comparison plot for all Dynamic settings showing L2 norm values
    """
    plt.figure(figsize=(10, 6))
    
    # Get all DYNAMIC columns
    dynamic_cols = sorted([col for col in df.columns if 'mode' in col and 'L2_norm_flow_time' in col])
    
    if data_type == "general":
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Dynamic Settings Comparison - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:  # frequency data (random/softrandom)
        df = df.sort_values('frequency').reset_index(drop=True)
        x_values = df['frequency'].values
        x_label = 'Frequency'
        title = f'Dynamic Settings Comparison - {data_type.capitalize()}'
    
    # Plot each Dynamic setting with consistent colors and markers
    for col in dynamic_cols:
        if col in df.columns and col in DYNAMIC_COLORS:
            # Extract mode number and create cleaner label
            mode_num = col.split('mode')[1].split('_')[0]
            label = f'Mode {mode_num}'
            
            plt.plot(x_values, df[col].values,
                    color=DYNAMIC_COLORS[col],
                    marker=DYNAMIC_MARKERS[col],
                    linewidth=2, markersize=8,
                    label=label,
                    alpha=0.9)
    
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('L2 Norm Flow Time', fontsize=14)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    if data_type in ["random", "softrandom"]:
        plt.xscale('log', base=2)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved Dynamic comparison plot to {output_path}")

def create_performance_ratio_plot(df, best_dynamic_col, bp_param, output_path, data_type="general"):
    """
    Create performance ratio plot: Dynamic_best/other_algorithms
    """
    plt.figure(figsize=(10, 6))
    
    algorithms = ['RR', 'SRPT', 'SETF', 'FCFS', 'BAL','SJF']
    
    # Format the best setting for display
    best_setting_display = best_dynamic_col.replace('Dynamic_njobs100_', '').replace('_L2_norm_flow_time', '')
    
    if data_type == "general":
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Performance Ratio Dynamic {best_setting_display} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        df = df.sort_values('frequency').reset_index(drop=True)
        x_values = df['frequency'].values
        x_label = 'Frequency'
        title = f'Performance Ratio Dynamic {best_setting_display} - {data_type.capitalize()}'
    
    # Plot ratios with consistent colors and markers
    for algo in algorithms:
        col_name = f'{algo}_L2_norm_flow_time'
        
        if col_name in df.columns and best_dynamic_col in df.columns:
            ratio = df[best_dynamic_col] / df[col_name]
            label = f'Dynamic {best_setting_display} / {algo}'
            
            plt.plot(x_values, ratio,
                    color=ALGORITHM_COLORS[algo],
                    marker=ALGORITHM_MARKERS[algo],
                    linewidth=2, markersize=8,
                    label=label,
                    alpha=0.9)
    
    # Add reference line at y=1
    plt.axhline(y=1, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('Performance Ratio', fontsize=14)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    if data_type in ["random", "softrandom"]:
        plt.xscale('log', base=2)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved performance ratio plot to {output_path}")

def create_srpt_percentage_plots_all_modes(output_dir):
    """
    Create SRPT percentage plots for each mode separately
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for mode in range(1, 7):
        filename = f"Dynamic_SRPT_percentage_mode{mode}_avg.csv"
        
        if not os.path.exists(filename):
            logger.warning(f"SRPT percentage file not found: {filename}")
            continue
        
        try:
            df = pd.read_csv(filename)
            df = df.sort_values(['arrival_rate', 'bp_L'])
            
            # Group by bp_L, bp_H and plot each combination
            bp_groups = df.groupby(['bp_L', 'bp_H'])
            
            for (bp_L, bp_H), group in bp_groups:
                plt.figure(figsize=(10, 6))
                
                plt.plot(group['arrival_rate'].values, group['SRPT_percentage'].values,
                        color='#d62728', marker='o', linewidth=2.5, markersize=8,
                        label=f'SRPT Percentage')
                
                plt.xlabel('Arrival Rate', fontsize=14)
                plt.ylabel('SRPT Percentage (%)', fontsize=14)
                plt.title(f'SRPT Usage in Mode {mode} - BP: L={bp_L:.3f}, H={bp_H}',
                         fontsize=16, fontweight='bold')
                plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
                plt.grid(True, alpha=0.3, linestyle='--')
                
                plt.xlim(18, 42)
                plt.xticks(range(20, 42, 2))
                plt.ylim(0, 105)
                
                plt.tight_layout()
                output_path = f"{output_dir}/SRPT_Mode{mode}_L{bp_L:.3f}_H{bp_H}.pdf"
                plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Saved SRPT percentage plot for mode {mode}, L={bp_L:.3f}, H={bp_H}")
            
        except Exception as e:
            logger.error(f"Error creating SRPT plot for mode {mode}: {e}")

def process_all_data(output_base):
    """
    Process avg30, random, and softrandom data with enhanced features
    """
    # First, process and create the averaged data files
    process_avg30_results()
    process_random_softrandom_results()
    process_dynamic_srpt_analysis()
    
    # Find the universal best DYNAMIC setting
    best_setting = find_universal_best_dynamic_setting()
    logger.info(f"Using universal best setting: {best_setting}")
    
    # NEW FEATURE 1: Analyze job size percentiles
    logger.info("\n" + "="*50)
    logger.info("ANALYZING JOB SIZE PERCENTILES")
    logger.info("="*50)
    
    random_percentile_data = analyze_job_sizes_for_percentiles("random")
    softrandom_percentile_data = analyze_job_sizes_for_percentiles("softrandom")
    
    if random_percentile_data is not None or softrandom_percentile_data is not None:
        percentile_output = f"{output_base}/Job_Size_Percentile_Analysis.pdf"
        create_job_size_percentile_plot(random_percentile_data, softrandom_percentile_data, percentile_output)
    
    # NEW FEATURE 3: Analyze maximum flow times
    logger.info("\n" + "="*50)
    logger.info("ANALYZING MAXIMUM FLOW TIMES")
    logger.info("="*50)
    
    random_max_flow_data = analyze_maximum_flow_time("random")
    softrandom_max_flow_data = analyze_maximum_flow_time("softrandom")
    
    if random_max_flow_data is not None or softrandom_max_flow_data is not None:
        max_flow_dir = f"{output_base}/maximum_flow_time"
        create_maximum_flow_time_plots(random_max_flow_data, softrandom_max_flow_data, max_flow_dir)
    
    # Load and merge processed data
    avg30_data = None
    random_data = None
    softrandom_data = None
    
    # Load Dynamic data
    try:
        if os.path.exists("Dynamic_result_avg30.csv"):
            avg30_data = pd.read_csv("Dynamic_result_avg30.csv")
        if os.path.exists("Dynamic_random_result_avg.csv"):
            random_data = pd.read_csv("Dynamic_random_result_avg.csv")
        if os.path.exists("Dynamic_softrandom_result_avg.csv"):
            softrandom_data = pd.read_csv("Dynamic_softrandom_result_avg.csv")
    except Exception as e:
        logger.error(f"Error loading Dynamic data: {e}")
    
    # Load other algorithm data and merge
    for algo in ['BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
        try:
            # Merge avg30 data
            if avg30_data is not None and os.path.exists(f"{algo}_result_avg30.csv"):
                algo_data = pd.read_csv(f"{algo}_result_avg30.csv")
                avg30_data = avg30_data.merge(algo_data, on=['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'], how='outer')
            
            # Merge random data
            if random_data is not None and os.path.exists(f"{algo}_random_result_avg.csv"):
                algo_data = pd.read_csv(f"{algo}_random_result_avg.csv")
                random_data = random_data.merge(algo_data, on='frequency', how='outer')
            
            # Merge softrandom data
            if softrandom_data is not None and os.path.exists(f"{algo}_softrandom_result_avg.csv"):
                algo_data = pd.read_csv(f"{algo}_softrandom_result_avg.csv")
                softrandom_data = softrandom_data.merge(algo_data, on='frequency', how='outer')
                
        except Exception as e:
            logger.error(f"Error loading {algo} data: {e}")
    
    # Process avg_30 data
    if avg30_data is not None:
        logger.info("\nProcessing avg_30 data...")
        
        bp_groups = avg30_data.groupby(['bp_parameter_L', 'bp_parameter_H'])
        
        # Create output directories
        dynamic_comp_dir = f"{output_base}/dynamic_comparisons_avg30"
        ratio_dir = f"{output_base}/performance_ratios_avg30"
        srpt_dir = f"{output_base}/srpt_percentages_avg30"
        best_dynamic_dir = f"{output_base}/best_dynamic_vs_algorithms_avg30"  # NEW
        
        os.makedirs(dynamic_comp_dir, exist_ok=True)
        os.makedirs(ratio_dir, exist_ok=True)
        os.makedirs(srpt_dir, exist_ok=True)
        os.makedirs(best_dynamic_dir, exist_ok=True)  # NEW
        
        for (L, H), group_df in bp_groups:
            bp_param = {'L': L, 'H': H}
            group_df = group_df.sort_values('arrival_rate')
            
            # Dynamic comparison plot
            dynamic_output = f"{dynamic_comp_dir}/Dynamic_Comparison_L{L:.3f}_H{H}.pdf"
            create_dynamic_comparison_plot(group_df, bp_param, dynamic_output, "general")
            
            # Performance ratio plot
            ratio_output = f"{ratio_dir}/Performance_Ratio_L{L:.3f}_H{H}.pdf"
            create_performance_ratio_plot(group_df, best_setting, bp_param, ratio_output, "general")
            
            # NEW FEATURE 2: Best Dynamic vs all algorithms
            best_dynamic_output = f"{best_dynamic_dir}/Best_Dynamic_vs_Algorithms_L{L:.3f}_H{H}.pdf"
            create_best_dynamic_vs_algorithms_plot(group_df, best_setting, bp_param, best_dynamic_output, "general")
        
        # SRPT percentage plots for all modes
        create_srpt_percentage_plots_all_modes(srpt_dir)
    
    # Process random data
    if random_data is not None:
        logger.info("\nProcessing random frequency data...")
        
        # Dynamic comparison
        dynamic_output = f"{output_base}/Dynamic_Comparison_Random.pdf"
        create_dynamic_comparison_plot(random_data, {}, dynamic_output, "random")
        
        # Performance ratio
        ratio_output = f"{output_base}/Performance_Ratio_Random.pdf"
        create_performance_ratio_plot(random_data, best_setting, {}, ratio_output, "random")
        
        # NEW FEATURE 2: Best Dynamic vs all algorithms for random
        best_dynamic_output = f"{output_base}/Best_Dynamic_vs_Algorithms_Random.pdf"
        create_best_dynamic_vs_algorithms_plot(random_data, best_setting, {}, best_dynamic_output, "random")
    
    # Process softrandom data
    if softrandom_data is not None:
        logger.info("\nProcessing softrandom frequency data...")
        
        # Dynamic comparison
        dynamic_output = f"{output_base}/Dynamic_Comparison_Softrandom.pdf"
        create_dynamic_comparison_plot(softrandom_data, {}, dynamic_output, "softrandom")
        
        # Performance ratio
        ratio_output = f"{output_base}/Performance_Ratio_Softrandom.pdf"
        create_performance_ratio_plot(softrandom_data, best_setting, {}, ratio_output, "softrandom")
        
        # NEW FEATURE 2: Best Dynamic vs all algorithms for softrandom
        best_dynamic_output = f"{output_base}/Best_Dynamic_vs_Algorithms_Softrandom.pdf"
        create_best_dynamic_vs_algorithms_plot(softrandom_data, best_setting, {}, best_dynamic_output, "softrandom")

def main():
    """
    Main function to generate all plots with enhanced features
    """
    logger.info("="*60)
    logger.info("Starting ENHANCED algorithm comparison plot generation...")
    logger.info("NEW FEATURES:")
    logger.info("1. Job size percentile analysis (1%, 5%, 10%)")
    logger.info("2. Best Dynamic vs all algorithms comparison")
    logger.info("3. Maximum flow time analysis")
    logger.info("="*60)
    
    # Validate paths first
    if not validate_paths():
        logger.error("Path validation failed. Please check your path configuration at the top of the script.")
        return
    
    # Set up plot style
    setup_plot_style()
    
    # Define output directory
    output_base = "enhanced_algorithm_plots"
    
    # Create base output directory
    os.makedirs(output_base, exist_ok=True)
    
    try:
        # Process all data with new features
        process_all_data(output_base)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("ENHANCED plot generation completed successfully!")
        
        total_pdfs = len(glob.glob(f"{output_base}/**/*.pdf", recursive=True))
        logger.info(f"Total PDF files generated: {total_pdfs}")
        
        # List generated files by category
        for root, dirs, files in os.walk(output_base):
            pdf_files = [f for f in files if f.endswith('.pdf')]
            if pdf_files:
                logger.info(f"\n{root}:")
                for pdf in pdf_files:
                    logger.info(f"  - {pdf}")
        
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()