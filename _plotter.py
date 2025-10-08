"""
Enhanced Algorithm Comparison Plotter v2 - Fixed Version

Key Features:
1. Modified best selection (mode7/mode6 ratio <= 1.1)
2. Best vs Worst case comparison
3. Dynamic_BAL added to all comparisons
4. Dynamic vs Dynamic_BAL direct comparison
5. Mode comparison plots (all modes 1-7)
6. Maximum flow time comparison (ALL algorithms)
7. BAL/FCFS/SRPT percentage plots (auto-detect)
8. Heavy tail analysis for random and softrandom cases

Paths:
- Normal results: /home/melowu/Work/ultimus/algorithm_result/
- Worst case: /home/melowu/Work/ultimus/worst_case/
- Analysis: /home/melowu/Work/ultimus/Analysis/Dynamic_analysis/ and Dynamic_BAL_analysis/
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
from pathlib import Path
import logging

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
WORST_CASE_PATH = os.path.join(BASE_DATA_PATH, "worst_case")
DYNAMIC_ANALYSIS_PATH = os.path.join(BASE_DATA_PATH, "Analysis/Dynamic_analysis")
DYNAMIC_BAL_ANALYSIS_PATH = os.path.join(BASE_DATA_PATH, "Analysis/Dynamic_BAL_analysis")

# ============================================================================
# ALGORITHM DEFINITIONS
# ============================================================================
ALGORITHMS = ['BAL', 'FCFS', 'Dynamic', 'Dynamic_BAL', 'SRPT', 'RR', 'SETF', 'SJF']

# ============================================================================
# COLOR AND MARKER SCHEMES
# ============================================================================
ALGORITHM_COLORS = {
    'RR': '#1f77b4',
    'SRPT': '#ff7f0e',
    'SETF': '#2ca02c',
    'FCFS': '#d62728',
    'BAL': '#9467bd',
    'Dynamic': '#8c564b',
    'Dynamic_BAL': '#e377c2',
    'SJF': '#17becf'
}

ALGORITHM_MARKERS = {
    'RR': 'o',
    'SRPT': 's',
    'SETF': '^',
    'FCFS': 'v',
    'BAL': 'D',
    'Dynamic': 'x',
    'Dynamic_BAL': 'P',
    'SJF': '*'
}

BEST_WORST_COLORS = {'best': '#2ecc71', 'worst': '#e74c3c'}
BEST_WORST_MARKERS = {'best': 'o', 'worst': 's'}

# ============================================================================
# MATPLOTLIB SETUP
# ============================================================================
def setup_plot_style():
    """Set up matplotlib style for publication-quality plots"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (10, 6),
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'legend.fontsize': 11,
        'lines.linewidth': 2,
        'lines.markersize': 8,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
    })

# ============================================================================
# BEST SETTING SELECTION (MODE 7 vs MODE 6)
# ============================================================================
def find_best_dynamic_setting_v2(df, algorithm_type="Dynamic"):
    """
    Find best Dynamic/Dynamic_BAL setting:
    - If mode7_L2 / mode6_L2 <= 1.1, pick mode7
    - Otherwise pick mode6
    """
    if algorithm_type == "Dynamic":
        mode6_col = 'Dynamic_njobs100_mode6_L2_norm_flow_time'
        mode7_col = 'Dynamic_njobs100_mode7_L2_norm_flow_time'
    else:  # Dynamic_BAL
        mode6_col = 'Dynamic_BAL_njobs100_mode6_L2_norm_flow_time'
        mode7_col = 'Dynamic_BAL_njobs100_mode7_L2_norm_flow_time'
    
    if mode6_col not in df.columns or mode7_col not in df.columns:
        logger.warning(f"Mode 6 or 7 not found for {algorithm_type}, falling back to best available")
        mode_cols = [col for col in df.columns if algorithm_type in col and 'mode' in col and 'L2_norm' in col]
        if mode_cols:
            best_col = df[mode_cols].mean().idxmin()
            logger.info(f"Using fallback best setting: {best_col}")
            return best_col
        return None
    
    mode6_mean = df[mode6_col].mean()
    mode7_mean = df[mode7_col].mean()
    
    if mode6_mean > 0:
        ratio = mode7_mean / mode6_mean
        if ratio <= 1.1:
            logger.info(f"{algorithm_type}: mode7/mode6 = {ratio:.4f} <= 1.1, selecting mode7")
            return mode7_col
        else:
            logger.info(f"{algorithm_type}: mode7/mode6 = {ratio:.4f} > 1.1, selecting mode6")
            return mode6_col
    else:
        logger.warning(f"{algorithm_type}: mode6 mean is 0, defaulting to mode7")
        return mode7_col

# ============================================================================
# HEAVY TAIL ANALYSIS
# ============================================================================
def draw_heavy_tail(output_dir="heavy_tail_analysis"):
    """
    Analyze heavy-tail distribution in job sizes for random and softrandom cases.
    Shows what percentage of total work is done by the TOP X% of jobs (by size).
    FIXED: Now directly plots top X% contribution (not bottom X%).
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    data_base_path = "/home/melowu/Work/ultimus/data"
    
    # Frequency values (2^1 to 2^16)
    frequencies = [2**i for i in range(1, 17)]
    
    # Configuration for top X% of largest jobs
    percentile_config = {
        'heavy_0.01': {
            'label': 'Top 1% (largest jobs)', 
            'color': '#e74c3c', 
            'marker': 'o', 
            'percentile': 0.01
        },
        'heavy_0.015': {
            'label': 'Top 1.5% (largest jobs)', 
            'color': '#f39c12', 
            'marker': 's', 
            'percentile': 0.015
        },
        'heavy_0.1': {
            'label': 'Top 10% (largest jobs)', 
            'color': '#27ae60', 
            'marker': '^', 
            'percentile': 0.1
        }
    }
    
    # Process Random case
    logger.info("Analyzing heavy tail for Random case...")
    random_results = {key: {'frequencies': [], 'ratios': []} for key in percentile_config.keys()}
    
    for freq in frequencies:
        freq_ratios = {key: [] for key in percentile_config.keys()}
        
        # Random has 10 iterations (1-10)
        for iteration in range(1, 11):
            csv_path = os.path.join(data_base_path, f"freq_{freq}_{iteration}", f"random_freq_{freq}.csv")
            
            if not os.path.exists(csv_path):
                logger.warning(f"File not found: {csv_path}")
                continue
            
            try:
                df = pd.read_csv(csv_path)
                
                if 'job_size' not in df.columns:
                    logger.warning(f"'job_size' column not found in {csv_path}")
                    continue
                
                job_sizes = df['job_size'].values
                total_jobs = len(job_sizes)
                total_size = np.sum(job_sizes)
                
                if total_size == 0:
                    continue
                
                # Sort job sizes in ascending order
                sorted_sizes = np.sort(job_sizes)
                
                # Calculate ratios for each percentile
                for key, config in percentile_config.items():
                    percentile = config['percentile']
                    # Number of top jobs to include
                    n_top = int(total_jobs * percentile)
                    
                    if n_top > 0:
                        # Sum of TOP X% largest jobs
                        top_sum = np.sum(sorted_sizes[-n_top:])
                    else:
                        top_sum = 0
                    
                    # FIXED: Now showing fraction done by TOP X% (not bottom)
                    ratio = top_sum / total_size
                    freq_ratios[key].append(ratio)
                
            except Exception as e:
                logger.error(f"Error reading {csv_path}: {e}")
                continue
        
        # Average across all iterations for this frequency
        for key in percentile_config.keys():
            if freq_ratios[key]:
                avg_ratio = np.mean(freq_ratios[key])
                random_results[key]['frequencies'].append(freq)
                random_results[key]['ratios'].append(avg_ratio)
    
    # Plot Random case
    if any(random_results[key]['frequencies'] for key in percentile_config.keys()):
        plt.figure(figsize=(12, 8))
        
        for key, config in percentile_config.items():
            if random_results[key]['frequencies']:
                plt.plot(random_results[key]['frequencies'], 
                        random_results[key]['ratios'],
                        color=config['color'],
                        marker=config['marker'],
                        linewidth=2.5,
                        markersize=10,
                        label=config['label'],
                        alpha=0.9)
        
        plt.xscale('log', base=2)
        plt.xlabel('Coherence Time (Frequency)', fontsize=14)
        plt.ylabel('Fraction of Total Work Done by Top X%', fontsize=14)
        plt.title('Heavy Tail Analysis - Random Case\n(Higher values = Heavier tail = More work in fewer jobs)', 
                 fontsize=16, fontweight='bold')
        plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.ylim(0, 1.05)
        
        # Add reference lines
        plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3, linewidth=1, 
                   label='50% of work')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, "heavy_tail_random.jpg")
        plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved heavy tail plot for Random case to {output_path}")
        
        # Print statistics
        for key, config in percentile_config.items():
            if random_results[key]['ratios']:
                avg = np.mean(random_results[key]['ratios'])
                logger.info(f"  Random - {config['label']}: {avg:.1%} of work on average")
    
    # Process Softrandom case
    logger.info("Analyzing heavy tail for Softrandom case...")
    softrandom_results = {key: {'frequencies': [], 'ratios': []} for key in percentile_config.keys()}
    
    for freq in frequencies:
        freq_ratios = {key: [] for key in percentile_config.keys()}
        
        # Softrandom has 10 directories (softrandom_1 to softrandom_10)
        for iteration in range(1, 11):
            softrandom_dir = os.path.join(data_base_path, f"softrandom_{iteration}")
            csv_path = os.path.join(softrandom_dir, f"freq_{freq}_{iteration}", f"softrandom_freq_{freq}.csv")
            
            if not os.path.exists(csv_path):
                logger.warning(f"File not found: {csv_path}")
                continue
            
            try:
                df = pd.read_csv(csv_path)
                
                if 'job_size' not in df.columns:
                    logger.warning(f"'job_size' column not found in {csv_path}")
                    continue
                
                job_sizes = df['job_size'].values
                total_jobs = len(job_sizes)
                total_size = np.sum(job_sizes)
                
                if total_size == 0:
                    continue
                
                # Sort job sizes in ascending order
                sorted_sizes = np.sort(job_sizes)
                
                # Calculate ratios for each percentile
                for key, config in percentile_config.items():
                    percentile = config['percentile']
                    # Number of top jobs to include
                    n_top = int(total_jobs * percentile)
                    
                    if n_top > 0:
                        # Sum of TOP X% largest jobs
                        top_sum = np.sum(sorted_sizes[-n_top:])
                    else:
                        top_sum = 0
                    
                    # FIXED: Now showing fraction done by TOP X% (not bottom)
                    ratio = top_sum / total_size
                    freq_ratios[key].append(ratio)
                
            except Exception as e:
                logger.error(f"Error reading {csv_path}: {e}")
                continue
        
        # Average across all iterations for this frequency
        for key in percentile_config.keys():
            if freq_ratios[key]:
                avg_ratio = np.mean(freq_ratios[key])
                softrandom_results[key]['frequencies'].append(freq)
                softrandom_results[key]['ratios'].append(avg_ratio)
    
    # Plot Softrandom case
    if any(softrandom_results[key]['frequencies'] for key in percentile_config.keys()):
        plt.figure(figsize=(12, 8))
        
        for key, config in percentile_config.items():
            if softrandom_results[key]['frequencies']:
                plt.plot(softrandom_results[key]['frequencies'], 
                        softrandom_results[key]['ratios'],
                        color=config['color'],
                        marker=config['marker'],
                        linewidth=2.5,
                        markersize=10,
                        label=config['label'],
                        alpha=0.9)
        
        plt.xscale('log', base=2)
        plt.xlabel('Coherence Time (Frequency)', fontsize=14)
        plt.ylabel('Fraction of Total Work Done by Top X%', fontsize=14)
        plt.title('Heavy Tail Analysis - Softrandom Case\n(Higher values = Heavier tail = More work in fewer jobs)', 
                 fontsize=16, fontweight='bold')
        plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.ylim(0, 1.05)
        
        # Add reference lines
        plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3, linewidth=1, 
                   label='50% of work')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, "heavy_tail_softrandom.jpg")
        plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved heavy tail plot for Softrandom case to {output_path}")
        
        # Print statistics
        for key, config in percentile_config.items():
            if softrandom_results[key]['ratios']:
                avg = np.mean(softrandom_results[key]['ratios'])
                logger.info(f"  Softrandom - {config['label']}: {avg:.1%} of work on average")
    logger.info("Heavy tail analysis completed")
# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================
def process_avg_results(avg_types=['avg30', 'avg60', 'avg90']):
    """Process avg results from algorithm_result directory for different avg types"""
    
    for avg_type in avg_types:
        logger.info(f"Processing {avg_type} results...")
        
        for algorithm in ALGORITHMS:
            logger.info(f"  Processing {avg_type} results for {algorithm}")
            
            result_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", f"{avg_type}_result")
            
            if not os.path.exists(result_dir):
                logger.warning(f"  Directory {result_dir} not found")
                continue
            
            # Fix: Different pattern for Dynamic/Dynamic_BAL to match actual file naming
            if algorithm in ['Dynamic', 'Dynamic_BAL']:
                # Pattern matches: 20_Dynamic_result_1.csv or 20_Dynamic_BAL_result_1.csv
                pattern = f"{result_dir}/*_{algorithm}_result*.csv"
            else:
                # Original pattern for other algorithms
                pattern = f"{result_dir}/*_{algorithm}_*_result*.csv"
            
            files = glob.glob(pattern)
            
            if not files:
                logger.warning(f"  No result files found for {algorithm} in {avg_type}")
                continue
                
            arrival_rate_groups = {}
            for file in files:
                filename = os.path.basename(file)
                arrival_rate = filename.split('_')[0]
                
                if arrival_rate not in arrival_rate_groups:
                    arrival_rate_groups[arrival_rate] = []
                arrival_rate_groups[arrival_rate].append(file)
            
            all_results = []
            
            for arrival_rate, file_list in arrival_rate_groups.items():
                dfs = []
                for file in file_list:
                    try:
                        df = pd.read_csv(file)
                        dfs.append(df)
                    except Exception as e:
                        logger.error(f"  Error reading {file}: {e}")
                        continue
                
                if not dfs:
                    continue
                    
                combined_df = pd.concat(dfs, ignore_index=True)
                
                if algorithm in ['Dynamic', 'Dynamic_BAL']:
                    l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
                    grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
                    
                    for (arr_rate, bp_L, bp_H), group in grouped:
                        row_data = {
                            'arrival_rate': arr_rate,
                            'bp_parameter_L': bp_L,
                            'bp_parameter_H': bp_H
                        }
                        for col in l2_cols:
                            if col in group.columns:
                                row_data[col] = group[col].mean()
                        all_results.append(row_data)
                else:
                    l2_col_name = f'{algorithm.upper()}_L2_norm_flow_time'
                    grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
                    
                    for (arr_rate, bp_L, bp_H), group in grouped:
                        if l2_col_name in group.columns:
                            row_data = {
                                'arrival_rate': arr_rate,
                                'bp_parameter_L': bp_L,
                                'bp_parameter_H': bp_H,
                                l2_col_name: group[l2_col_name].mean()
                            }
                            all_results.append(row_data)
                        else:
                            logger.warning(f"  Column {l2_col_name} not found in {algorithm} data")
            
            if all_results:
                final_df = pd.DataFrame(all_results)
                final_df = final_df.sort_values(['arrival_rate', 'bp_parameter_L'])
                
                output_file = f"{algorithm}_result_{avg_type}.csv"
                final_df.to_csv(output_file, index=False)
                logger.info(f"  Created final file: {output_file}")
def process_random_softrandom_results():
    """Process random and softrandom results - handles both L2_norm and maximum_flow_time"""
    
    for algorithm in ALGORITHMS:
        for result_type in ['random', 'softrandom']:
            logger.info(f"Processing {result_type} results for {algorithm}")
            
            result_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", f"{result_type}_result")
            
            if not os.path.exists(result_dir):
                logger.warning(f"Directory {result_dir} not found")
                continue
            
            if algorithm in ['Dynamic', 'Dynamic_BAL']:
                pattern = f"{result_dir}/{result_type}_result_{algorithm}_njobs100_*.csv"
            else:
                pattern = f"{result_dir}/{result_type}_result_{algorithm}_*.csv"
            
            files = glob.glob(pattern)
            
            if not files:
                logger.warning(f"No {algorithm} {result_type} files found")
                continue
            
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
            
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            if algorithm in ['Dynamic', 'Dynamic_BAL']:
                l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
                max_cols = [col for col in combined_df.columns if 'maximum_flow_time' in col]
                all_cols = l2_cols + max_cols
                
                if all_cols:
                    averaged_df = combined_df.groupby('frequency')[all_cols].mean().reset_index()
                else:
                    logger.warning(f"No L2 or max columns found for {algorithm} {result_type}")
                    continue
            else:
                l2_col_name = f'{algorithm.upper()}_L2_norm_flow_time'
                max_col_name = f'{algorithm.upper()}_maximum_flow_time'
                
                cols_to_average = []
                if l2_col_name in combined_df.columns:
                    cols_to_average.append(l2_col_name)
                if max_col_name in combined_df.columns:
                    cols_to_average.append(max_col_name)
                
                if not cols_to_average:
                    logger.warning(f"No L2 or max columns found for {algorithm} {result_type}")
                    continue
                
                averaged_df = combined_df.groupby('frequency')[cols_to_average].mean().reset_index()
            
            output_file = f"{algorithm}_{result_type}_result_avg.csv"
            averaged_df.to_csv(output_file, index=False)
            logger.info(f"Created {output_file} with columns: {list(averaged_df.columns)}")

def process_dynamic_analysis(algorithm_type="Dynamic"):
    """Process Dynamic/Dynamic_BAL percentage analysis - supports BAL/FCFS and SRPT/FCFS"""
    
    if algorithm_type == "Dynamic":
        analysis_dir = os.path.join(DYNAMIC_ANALYSIS_PATH, "avg_30")
    else:
        analysis_dir = os.path.join(DYNAMIC_BAL_ANALYSIS_PATH, "avg_30")
    
    if not os.path.exists(analysis_dir):
        logger.warning(f"Directory {analysis_dir} not found")
        return
    
    for mode in range(1, 8):
        logger.info(f"Processing {algorithm_type} analysis for mode {mode}")
        
        mode_dir = os.path.join(analysis_dir, f"mode_{mode}")
        pattern = f"{mode_dir}/{algorithm_type}_avg_30_nJobsPerRound_100_mode_{mode}_round_*.csv"
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No analysis files found for {algorithm_type} mode {mode}")
            continue
        
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
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Auto-detect percentage columns
        has_fcfs = 'FCFS_percentage' in combined_df.columns
        has_bal = 'BAL_percentage' in combined_df.columns
        has_srpt = 'SRPT_percentage' in combined_df.columns
        
        if has_fcfs and has_bal:
            # BAL + FCFS case
            combined_df['FCFS_percentage'] = pd.to_numeric(combined_df['FCFS_percentage'], errors='coerce')
            combined_df['BAL_percentage'] = pd.to_numeric(combined_df['BAL_percentage'], errors='coerce')
            combined_df = combined_df.dropna(subset=['FCFS_percentage', 'BAL_percentage'])
            
            if combined_df.empty:
                logger.warning(f"No valid numeric data for {algorithm_type} mode {mode}")
                continue
            
            grouped = combined_df.groupby(['arrival_rate', 'bp_L', 'bp_H'])[['FCFS_percentage', 'BAL_percentage']].mean().reset_index()
            
        elif has_fcfs and has_srpt:
            # SRPT + FCFS case
            combined_df['FCFS_percentage'] = pd.to_numeric(combined_df['FCFS_percentage'], errors='coerce')
            combined_df['SRPT_percentage'] = pd.to_numeric(combined_df['SRPT_percentage'], errors='coerce')
            combined_df = combined_df.dropna(subset=['FCFS_percentage', 'SRPT_percentage'])
            
            if combined_df.empty:
                logger.warning(f"No valid numeric data for {algorithm_type} mode {mode}")
                continue
            
            grouped = combined_df.groupby(['arrival_rate', 'bp_L', 'bp_H'])[['FCFS_percentage', 'SRPT_percentage']].mean().reset_index()
            
        else:
            logger.warning(f"Percentage columns not found in {algorithm_type} mode {mode}")
            continue
        
        grouped = grouped.sort_values(['arrival_rate', 'bp_L'])
        
        output_file = f"{algorithm_type}_percentages_mode{mode}_avg.csv"
        grouped.to_csv(output_file, index=False)
        logger.info(f"Created {output_file}")
# ============================================================================
# PLOTTING FUNCTIONS

# Fix 2: Add plt.close() to create_dynamic_vs_dynamic_bal_comparison
def create_dynamic_vs_dynamic_bal_comparison(best_dynamic_col, best_bal_col, bp_param, output_path, data_type="avg30"):
    """Compare Dynamic vs Dynamic_BAL"""
    import re
    dynamic_mode_match = re.search(r'mode(\d+)', best_dynamic_col)
    bal_mode_match = re.search(r'mode(\d+)', best_bal_col)
    
    dynamic_mode = dynamic_mode_match.group(1) if dynamic_mode_match else '?'
    bal_mode = bal_mode_match.group(1) if bal_mode_match else '?'
    # Handle different data types
    if data_type in ["avg30", "avg60", "avg90"]:
        dynamic_file = f"Dynamic_result_{data_type}.csv"
        bal_file = f"Dynamic_BAL_result_{data_type}.csv"
        title = f'Dynamic (Mode {dynamic_mode}) vs Dynamic_BAL (Mode {bal_mode})\n{data_type.upper()} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        dynamic_file = f"Dynamic_{data_type}_result_avg.csv"
        bal_file = f"Dynamic_BAL_{data_type}_result_avg.csv"
    
    if not os.path.exists(dynamic_file) or not os.path.exists(bal_file):
        logger.warning("Dynamic or Dynamic_BAL file not found")
        return
    
    dynamic_df = pd.read_csv(dynamic_file)
    bal_df = pd.read_csv(bal_file)
    
    plt.figure(figsize=(12, 8))
    
    if data_type in ["avg30", "avg60", "avg90"]:
        dynamic_df = dynamic_df[(dynamic_df['bp_parameter_L'] == bp_param['L']) & 
                                (dynamic_df['bp_parameter_H'] == bp_param['H'])]
        bal_df = bal_df[(bal_df['bp_parameter_L'] == bp_param['L']) & 
                        (bal_df['bp_parameter_H'] == bp_param['H'])]
        
        if dynamic_df.empty or bal_df.empty:
            logger.warning(f"No data for bp_L={bp_param['L']}, bp_H={bp_param['H']}")
            plt.close()
            return
        
        dynamic_df = dynamic_df.sort_values('arrival_rate')
        bal_df = bal_df.sort_values('arrival_rate')
        
        x_values = dynamic_df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Dynamic vs Dynamic_BAL - {data_type.upper()} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        dynamic_df = dynamic_df.sort_values('frequency')
        bal_df = bal_df.sort_values('frequency')
        
        x_values = dynamic_df['frequency'].values
        x_label = 'Coherence Time'
        title = f'Dynamic vs Dynamic_BAL - {data_type.capitalize()}'
    
    if best_dynamic_col in dynamic_df.columns:
        dynamic_label = best_dynamic_col.replace('Dynamic_njobs100_', '').replace('_L2_norm_flow_time', '')
        plt.plot(x_values, dynamic_df[best_dynamic_col].values,
                color=ALGORITHM_COLORS['Dynamic'],
                marker=ALGORITHM_MARKERS['Dynamic'],
                linewidth=2.5, markersize=10,
                label=f'Dynamic {dynamic_label}',
                alpha=0.9)
    
    if best_bal_col in bal_df.columns:
        bal_label = best_bal_col.replace('Dynamic_BAL_njobs100_', '').replace('_L2_norm_flow_time', '')
        plt.plot(x_values, bal_df[best_bal_col].values,
                color=ALGORITHM_COLORS['Dynamic_BAL'],
                marker=ALGORITHM_MARKERS['Dynamic_BAL'],
                linewidth=2.5, markersize=10,
                label=f'Dynamic_BAL {bal_label}',
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
    plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
    plt.close()  # IMPORTANT: Close figure to free memory
    
    logger.info(f"Saved Dynamic vs Dynamic_BAL comparison to {output_path}")


# Fix 3: Add plt.close() to create_all_algorithms_comparison
def create_all_algorithms_comparison(df, best_dynamic_col, best_bal_col, bp_param, output_path, data_type="avg30"):
    """Compare all algorithms including Dynamic and Dynamic_BAL"""
    
    plt.figure(figsize=(14, 8))
    
    algorithms_to_plot = ['RR', 'SRPT', 'SETF', 'FCFS', 'BAL', 'SJF']
    
    if data_type in ["avg30", "avg60", "avg90"]:
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'All Algorithms Comparison - {data_type.upper()} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        df = df.sort_values('frequency').reset_index(drop=True)
        x_values = df['frequency'].values
        x_label = 'Coherence Time'
        title = f'All Algorithms Comparison - {data_type.capitalize()}'
    
    if best_dynamic_col in df.columns:
        dynamic_label = best_dynamic_col.replace('Dynamic_njobs100_', '').replace('_L2_norm_flow_time', '')
        plt.plot(x_values, df[best_dynamic_col].values,
                color=ALGORITHM_COLORS['Dynamic'],
                marker=ALGORITHM_MARKERS['Dynamic'],
                linewidth=2.5, markersize=10,
                label=f'Dynamic {dynamic_label}',
                alpha=0.9)
    
    if best_bal_col in df.columns:
        bal_label = best_bal_col.replace('Dynamic_BAL_njobs100_', '').replace('_L2_norm_flow_time', '')
        plt.plot(x_values, df[best_bal_col].values,
                color=ALGORITHM_COLORS['Dynamic_BAL'],
                marker=ALGORITHM_MARKERS['Dynamic_BAL'],
                linewidth=2.5, markersize=10,
                label=f'Dynamic_BAL {bal_label}',
                alpha=0.9)
    
    for algo in algorithms_to_plot:
        col_name = f'{algo.upper()}_L2_norm_flow_time'
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
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True, ncol=2)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    if data_type in ["random", "softrandom"]:
        plt.xscale('log', base=2)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    plt.tight_layout()
    plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
    plt.close()  # IMPORTANT: Close figure to free memory
    
    logger.info(f"Saved all algorithms comparison to {output_path}")


# Fix 4: Add plt.close() to create_mode_comparison_plots
def create_mode_comparison_plots(algorithm_type="Dynamic", data_type="avg30", bp_param=None, output_path=None):
    """Create plots comparing all modes (1-7)"""
    
    if data_type in ["avg30", "avg60", "avg90"]:
        file_name = f"{algorithm_type}_result_{data_type}.csv"
    else:
        file_name = f"{algorithm_type}_{data_type}_result_avg.csv"
    
    if not os.path.exists(file_name):
        logger.warning(f"File not found: {file_name}")
        return
    
    df = pd.read_csv(file_name)
    
    plt.figure(figsize=(12, 8))
    
    if data_type in ["avg30", "avg60", "avg90"]:
        if bp_param is None:
            logger.warning("bp_param required for avg data")
            plt.close()
            return
        
        df = df[(df['bp_parameter_L'] == bp_param['L']) & 
                (df['bp_parameter_H'] == bp_param['H'])]
        
        if df.empty:
            logger.warning(f"No data for bp_L={bp_param['L']}, bp_H={bp_param['H']}")
            plt.close()
            return
        
        df = df.sort_values('arrival_rate')
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'{algorithm_type} - All Modes Comparison - {data_type.upper()}\nBP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        df = df.sort_values('frequency')
        x_values = df['frequency'].values
        x_label = 'Coherence Time'
        title = f'{algorithm_type} - All Modes Comparison ({data_type.capitalize()})'
    
    mode_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    mode_markers = ['^', 'v', 's', 'D', 'o', 'x', 'P']
    
    for mode in range(1, 8):
        col_name = f'{algorithm_type}_njobs100_mode{mode}_L2_norm_flow_time'
        if col_name in df.columns:
            plt.plot(x_values, df[col_name].values,
                    color=mode_colors[mode-1],
                    marker=mode_markers[mode-1],
                    linewidth=2, markersize=8,
                    label=f'Mode {mode}',
                    alpha=0.9)
    
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('L2 Norm Flow Time', fontsize=14)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True, ncol=2)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    if data_type in ["random", "softrandom"]:
        plt.xscale('log', base=2)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
        plt.close()  # IMPORTANT: Close figure to free memory
        logger.info(f"Saved mode comparison plot to {output_path}")
# ============================================================================
# WORST CASE DATA PROCESSING FUNCTIONS
# ============================================================================

def process_worst_case_avg_results(avg_types=['avg30', 'avg60', 'avg90']):
    """
    Process worst case avg results and create averaged CSV files.
    Output format: {Algorithm}_result_{avg_type}_worst_case.csv
    """
    logger.info("\n" + "="*60)
    logger.info("PROCESSING WORST CASE AVG DATA")
    logger.info("="*60)
    
    for avg_type in avg_types:
        logger.info(f"\nProcessing worst case {avg_type} results...")
        
        for algorithm in ALGORITHMS:
            logger.info(f"  Processing worst case {avg_type} for {algorithm}")
            
            result_dir = os.path.join(WORST_CASE_PATH, f"{algorithm}_result", f"{avg_type}_result")
            
            if not os.path.exists(result_dir):
                logger.warning(f"  Directory {result_dir} not found")
                continue
            
            # Pattern to match files
            if algorithm in ['Dynamic', 'Dynamic_BAL']:
                # Files like: 20_Dynamic_BAL_result_1.csv or 20_Dynamic_result_1.csv
                pattern = f"{result_dir}/*_{algorithm}_result*.csv"
            else:
                pattern = f"{result_dir}/*_{algorithm}_*_result*.csv"
            
            files = glob.glob(pattern)
            
            if not files:
                logger.warning(f"  No worst case files found for {algorithm} in {avg_type}")
                logger.warning(f"  Pattern: {pattern}")
                continue
            
            logger.info(f"  Found {len(files)} files")
            
            # Group files by arrival rate
            arrival_rate_groups = {}
            for file in files:
                filename = os.path.basename(file)
                arrival_rate = filename.split('_')[0]
                
                if arrival_rate not in arrival_rate_groups:
                    arrival_rate_groups[arrival_rate] = []
                arrival_rate_groups[arrival_rate].append(file)
            
            all_results = []
            
            for arrival_rate, file_list in arrival_rate_groups.items():
                dfs = []
                for file in file_list:
                    try:
                        df = pd.read_csv(file)
                        dfs.append(df)
                    except Exception as e:
                        logger.error(f"  Error reading {file}: {e}")
                        continue
                
                if not dfs:
                    continue
                
                combined_df = pd.concat(dfs, ignore_index=True)
                
                if algorithm in ['Dynamic', 'Dynamic_BAL']:
                    # Get all L2 norm columns (should be njobs1_mode1)
                    l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
                    
                    # Verify it's njobs1
                    njobs1_cols = [col for col in l2_cols if 'njobs1' in col]
                    if not njobs1_cols:
                        logger.warning(f"  ⚠️  No njobs1 columns found for {algorithm} - might be wrong data!")
                    
                    grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
                    
                    for (arr_rate, bp_L, bp_H), group in grouped:
                        row_data = {
                            'arrival_rate': arr_rate,
                            'bp_parameter_L': bp_L,
                            'bp_parameter_H': bp_H
                        }
                        for col in l2_cols:
                            if col in group.columns:
                                row_data[col] = group[col].mean()
                        all_results.append(row_data)
                else:
                    l2_col_name = f'{algorithm.upper()}_L2_norm_flow_time'
                    grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
                    
                    for (arr_rate, bp_L, bp_H), group in grouped:
                        if l2_col_name in group.columns:
                            row_data = {
                                'arrival_rate': arr_rate,
                                'bp_parameter_L': bp_L,
                                'bp_parameter_H': bp_H,
                                l2_col_name: group[l2_col_name].mean()
                            }
                            all_results.append(row_data)
            
            if all_results:
                final_df = pd.DataFrame(all_results)
                final_df = final_df.sort_values(['arrival_rate', 'bp_parameter_L'])
                
                # Output file with _worst_case suffix
                output_file = f"{algorithm}_result_{avg_type}_worst_case.csv"
                final_df.to_csv(output_file, index=False)
                logger.info(f"  ✅ Created: {output_file}")


def process_worst_case_random_softrandom_results():
    """
    Process worst case random and softrandom results.
    Output format: {Algorithm}_{random/softrandom}_result_avg_worst_case.csv
    """
    logger.info("\n" + "="*60)
    logger.info("PROCESSING WORST CASE RANDOM/SOFTRANDOM DATA")
    logger.info("="*60)
    
    for algorithm in ALGORITHMS:
        for result_type in ['random', 'softrandom']:
            logger.info(f"\nProcessing worst case {result_type} for {algorithm}")
            
            result_dir = os.path.join(WORST_CASE_PATH, f"{algorithm}_result", f"{result_type}_result")
            
            if not os.path.exists(result_dir):
                logger.warning(f"  Directory {result_dir} not found")
                continue
            
            # Pattern to match files
            if algorithm in ['Dynamic', 'Dynamic_BAL']:
                # Files like: random_result_Dynamic_BAL_njobs1_1.csv
                pattern = f"{result_dir}/{result_type}_result_{algorithm}_njobs1_*.csv"
            else:
                pattern = f"{result_dir}/{result_type}_result_{algorithm}_*.csv"
            
            files = glob.glob(pattern)
            
            if not files:
                logger.warning(f"  No worst case files found for {algorithm} {result_type}")
                logger.warning(f"  Pattern: {pattern}")
                continue
            
            logger.info(f"  Found {len(files)} files")
            
            all_dfs = []
            for file in files:
                try:
                    df = pd.read_csv(file)
                    all_dfs.append(df)
                except Exception as e:
                    logger.error(f"  Error reading {file}: {e}")
                    continue
            
            if not all_dfs:
                continue
            
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            if algorithm in ['Dynamic', 'Dynamic_BAL']:
                # Get all L2 and max flow time columns
                l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
                max_cols = [col for col in combined_df.columns if 'maximum_flow_time' in col]
                all_cols = l2_cols + max_cols
                
                # Verify njobs1
                njobs1_cols = [col for col in l2_cols if 'njobs1' in col]
                if not njobs1_cols:
                    logger.warning(f"  ⚠️  No njobs1 columns found - might be wrong data!")
                
                if all_cols:
                    averaged_df = combined_df.groupby('frequency')[all_cols].mean().reset_index()
                else:
                    logger.warning(f"  No L2 or max columns found")
                    continue
            else:
                l2_col_name = f'{algorithm.upper()}_L2_norm_flow_time'
                max_col_name = f'{algorithm.upper()}_maximum_flow_time'
                
                cols_to_average = []
                if l2_col_name in combined_df.columns:
                    cols_to_average.append(l2_col_name)
                if max_col_name in combined_df.columns:
                    cols_to_average.append(max_col_name)
                
                if not cols_to_average:
                    logger.warning(f"  No columns to average")
                    continue
                
                averaged_df = combined_df.groupby('frequency')[cols_to_average].mean().reset_index()
            
            # Output file with _worst_case suffix
            output_file = f"{algorithm}_{result_type}_result_avg_worst_case.csv"
            averaged_df.to_csv(output_file, index=False)
            logger.info(f"  ✅ Created: {output_file}")


# ============================================================================
# UPDATED LOAD WORST CASE FUNCTION
# ============================================================================

def load_worst_case_data(algorithm, data_type="avg30"):
    """
    Load PRE-PROCESSED worst case data from averaged CSV files.
    These files should be generated by process_worst_case_*_results() functions.
    """
    if data_type in ["avg30", "avg60", "avg90"]:
        worst_file = f"{algorithm}_result_{data_type}_worst_case.csv"
    else:
        worst_file = f"{algorithm}_{data_type}_result_avg_worst_case.csv"
    
    if not os.path.exists(worst_file):
        logger.error(f"❌ Worst case file not found: {worst_file}")
        logger.error(f"   Make sure to run process_worst_case functions first!")
        return None
    
    try:
        df = pd.read_csv(worst_file)
        logger.info(f"✓ Loaded worst case: {worst_file}")
        
        # Verify this is worst case data (should have njobs1 for Dynamic/Dynamic_BAL)
        if algorithm in ['Dynamic', 'Dynamic_BAL']:
            l2_cols = [col for col in df.columns if 'L2_norm' in col]
            njobs1_cols = [col for col in l2_cols if 'njobs1' in col]
            njobs100_cols = [col for col in l2_cols if 'njobs100' in col]
            
            if njobs100_cols and not njobs1_cols:
                logger.error(f"❌ File contains njobs100, not njobs1 - this is WRONG!")
                return None
            
            if njobs1_cols:
                logger.info(f"   Worst case columns: {njobs1_cols}")
            else:
                logger.warning(f"   ⚠️ No njobs1 columns found in file")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error loading {worst_file}: {e}")
        return None


# ============================================================================
# UPDATED COMPARISON FUNCTION
# ============================================================================

def create_best_worst_comparison(algorithm, best_col, bp_param, output_path, data_type="avg30"):
    """
    Compare BEST case (njobs100_mode6/7) vs WORST case (njobs1_mode1).
    Uses pre-processed worst case files.
    """
    
    # Load best case data
    if data_type in ["avg30", "avg60", "avg90"]:
        best_file = f"{algorithm}_result_{data_type}.csv"
    else:
        best_file = f"{algorithm}_{data_type}_result_avg.csv"
    
    if not os.path.exists(best_file):
        logger.warning(f"Best case file not found: {best_file}")
        return
    
    best_df = pd.read_csv(best_file)
    
    # Load worst case data (pre-processed)
    worst_df = load_worst_case_data(algorithm, data_type)
    
    if worst_df is None:
        logger.error(f"❌ Cannot create comparison - no worst case data for {algorithm}")
        return
    
    # Extract which mode is being used for "best"
    import re
    if algorithm in ['Dynamic', 'Dynamic_BAL']:
        mode_match = re.search(r'mode(\d+)', best_col)
        best_mode_num = mode_match.group(1) if mode_match else '?'
        best_mode_label = f"Mode {best_mode_num}"
        
        # Verify best_col uses njobs100
        if 'njobs100' not in best_col:
            logger.warning(f"⚠️  Best column doesn't contain 'njobs100': {best_col}")
    else:
        best_mode_label = algorithm
    
    plt.figure(figsize=(12, 8))
    
    # Filter and prepare data
    if data_type in ["avg30", "avg60", "avg90"]:
        best_df_filtered = best_df[
            (best_df['bp_parameter_L'] == bp_param['L']) & 
            (best_df['bp_parameter_H'] == bp_param['H'])
        ]
        worst_df_filtered = worst_df[
            (worst_df['bp_parameter_L'] == bp_param['L']) & 
            (worst_df['bp_parameter_H'] == bp_param['H'])
        ]
        
        if best_df_filtered.empty or worst_df_filtered.empty:
            logger.warning(f"No data for bp_L={bp_param['L']}, bp_H={bp_param['H']}")
            plt.close()
            return
        
        best_df_filtered = best_df_filtered.sort_values('arrival_rate')
        worst_df_filtered = worst_df_filtered.sort_values('arrival_rate')
        
        x_values = best_df_filtered['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = (f'{algorithm}: Best (njobs100 {best_mode_label}) vs Worst (njobs1 Mode1)\n'
                f'{data_type.upper()} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}')
    else:
        best_df = best_df.sort_values('frequency')
        worst_df = worst_df.sort_values('frequency')
        
        x_values = best_df['frequency'].values
        x_label = 'Coherence Time'
        title = (f'{algorithm}: Best (njobs100 {best_mode_label}) vs Worst (njobs1 Mode1)\n'
                f'{data_type.capitalize()}')
        
        best_df_filtered = best_df
        worst_df_filtered = worst_df
    
    # Get best case values
    if best_col not in best_df_filtered.columns:
        logger.error(f"❌ Column {best_col} not found in best case data")
        logger.error(f"   Available: {[c for c in best_df_filtered.columns if 'L2' in c]}")
        plt.close()
        return
    
    best_values = best_df_filtered[best_col].values
    
    # Find worst case column (njobs1_mode1)
    if algorithm in ['Dynamic', 'Dynamic_BAL']:
        worst_col = f'{algorithm}_njobs1_mode1_L2_norm_flow_time'
        
        if worst_col not in worst_df_filtered.columns:
            # Try to find any njobs1_mode1 column
            mode1_cols = [col for col in worst_df_filtered.columns 
                         if 'njobs1' in col and 'mode1' in col and 'L2_norm' in col]
            
            if mode1_cols:
                worst_col = mode1_cols[0]
                logger.info(f"Using worst case column: {worst_col}")
            else:
                logger.error(f"❌ No njobs1_mode1 column found!")
                logger.error(f"   Available: {[c for c in worst_df_filtered.columns if 'L2' in c]}")
                plt.close()
                return
    else:
        worst_col = best_col  # Same column name for other algorithms
    
    if worst_col not in worst_df_filtered.columns:
        logger.error(f"❌ Column {worst_col} not found in worst case data")
        plt.close()
        return
    
    worst_values = worst_df_filtered[worst_col].values
    
    # Validate alignment
    if len(best_values) != len(worst_values):
        logger.error(f"❌ Length mismatch: best={len(best_values)}, worst={len(worst_values)}")
        plt.close()
        return
    
    logger.info(f"📊 Comparing:")
    logger.info(f"   Best:  {best_col}")
    logger.info(f"   Worst: {worst_col}")
    
    # Calculate ratio
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = best_values / worst_values
        ratio = np.where(np.isfinite(ratio), ratio, np.nan)
    
    valid_ratios = ~np.isnan(ratio)
    if not np.any(valid_ratios):
        logger.error(f"❌ No valid ratios computed")
        plt.close()
        return
    
    # Plot
    plt.plot(x_values, ratio,
             color=BEST_WORST_COLORS['best'],
             marker=BEST_WORST_MARKERS['best'],
             linewidth=2.5, markersize=10,
             label=f'Best/Worst Ratio',
             alpha=0.9)
    
    plt.axhline(y=1, color='gray', linestyle='--', alpha=0.5, linewidth=1, 
                label='Equal Performance')
    
    valid_ratio_values = ratio[valid_ratios]
    mean_ratio = np.mean(valid_ratio_values)
    plt.axhline(y=mean_ratio, color='blue', linestyle=':', alpha=0.3, linewidth=1.5, 
                label=f'Mean: {mean_ratio:.3f}')
    
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('Performance Ratio (Best/Worst)\nLower = Better', fontsize=14)
    plt.title(title, fontsize=15, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True, fontsize=10)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    if data_type in ["random", "softrandom"]:
        plt.xscale('log', base=2)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    # Statistics box
    stats_text = (f'Best:  {best_mode_label} (njobs100)\n'
                 f'Worst: Mode1 (njobs1)\n'
                 f'─────────────────\n'
                 f'Mean:  {mean_ratio:.3f}\n'
                 f'Min:   {np.min(valid_ratio_values):.3f}\n'
                 f'Max:   {np.max(valid_ratio_values):.3f}')
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
             fontsize=9, family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Saved: {output_path}")
    logger.info(f"   Mean ratio: {mean_ratio:.3f}x")


# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

def validate_worst_case_setup():
    """Validate worst case directory and file structure"""
    logger.info("\n" + "="*60)
    logger.info("VALIDATING WORST CASE DIRECTORY")
    logger.info("="*60)
    
    if not os.path.exists(WORST_CASE_PATH):
        logger.error(f"❌ Worst case path not found: {WORST_CASE_PATH}")
        return False
    
    # Check for key algorithms and data types
    checks = [
        ('Dynamic', 'avg30'),
        ('Dynamic_BAL', 'avg30'),
        ('Dynamic', 'random'),
        ('Dynamic_BAL', 'random')
    ]
    
    found_valid = False
    for algorithm, data_type in checks:
        result_dir = os.path.join(WORST_CASE_PATH, f"{algorithm}_result", f"{data_type}_result")
        
        if os.path.exists(result_dir):
            files = os.listdir(result_dir)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            if csv_files:
                logger.info(f"✓ Found {len(csv_files)} files in {algorithm}/{data_type}")
                found_valid = True
                
                # Check one file
                sample_file = os.path.join(result_dir, csv_files[0])
                try:
                    df = pd.read_csv(sample_file)
                    njobs1_cols = [c for c in df.columns if 'njobs1' in c and 'L2' in c]
                    if njobs1_cols:
                        logger.info(f"  ✓ Contains njobs1 columns: {njobs1_cols[0]}")
                    else:
                        logger.warning(f"  ⚠️ No njobs1 columns in {csv_files[0]}")
                except Exception as e:
                    logger.error(f"  Error reading file: {e}")
            else:
                logger.warning(f"✗ No CSV files in {algorithm}/{data_type}")
        else:
            logger.warning(f"✗ Directory not found: {result_dir}")
    
    logger.info("="*60 + "\n")
    return found_valid

def create_max_flow_time_comparison(best_dynamic_col, best_bal_col, output_path, data_type="random"):
    """Compare maximum flow time for Dynamic and Dynamic_BAL"""
    
    dynamic_file = f"Dynamic_{data_type}_result_avg.csv"
    bal_file = f"Dynamic_BAL_{data_type}_result_avg.csv"
    
    if not os.path.exists(dynamic_file) or not os.path.exists(bal_file):
        logger.warning(f"Dynamic or Dynamic_BAL {data_type} file not found")
        return
    
    dynamic_df = pd.read_csv(dynamic_file)
    bal_df = pd.read_csv(bal_file)
    
    dynamic_max_col = best_dynamic_col.replace('L2_norm_flow_time', 'maximum_flow_time')
    bal_max_col = best_bal_col.replace('L2_norm_flow_time', 'maximum_flow_time')
    
    if dynamic_max_col not in dynamic_df.columns or bal_max_col not in bal_df.columns:
        logger.warning("Max flow time columns not found")
        return
    
    dynamic_df = dynamic_df.sort_values('frequency')
    bal_df = bal_df.sort_values('frequency')
    
    plt.figure(figsize=(12, 8))
    
    dynamic_label = best_dynamic_col.replace('Dynamic_njobs100_', '').replace('_L2_norm_flow_time', '')
    plt.plot(dynamic_df['frequency'].values, dynamic_df[dynamic_max_col].values,
            color=ALGORITHM_COLORS['Dynamic'],
            marker=ALGORITHM_MARKERS['Dynamic'],
            linewidth=2.5, markersize=10,
            label=f'Dynamic {dynamic_label}',
            alpha=0.9)
    
    bal_label = best_bal_col.replace('Dynamic_BAL_njobs100_', '').replace('_L2_norm_flow_time', '')
    plt.plot(bal_df['frequency'].values, bal_df[bal_max_col].values,
            color=ALGORITHM_COLORS['Dynamic_BAL'],
            marker=ALGORITHM_MARKERS['Dynamic_BAL'],
            linewidth=2.5, markersize=10,
            label=f'Dynamic_BAL {bal_label}',
            alpha=0.9)
    
    plt.xscale('log', base=2)
    plt.xlabel('Coherence Time', fontsize=14)
    plt.ylabel('Maximum Flow Time', fontsize=14)
    plt.title(f'Maximum Flow Time Comparison - {data_type.capitalize()}', fontsize=16, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved max flow time comparison to {output_path}")

def create_all_algorithms_max_flow_comparison(output_path, data_type="random"):
    """Compare maximum flow time for ALL algorithms"""
    
    plt.figure(figsize=(14, 8))
    
    algorithms_to_plot = ['BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF', 'Dynamic', 'Dynamic_BAL']
    found_any = False
    
    for algorithm in algorithms_to_plot:
        file_name = f"{algorithm}_{data_type}_result_avg.csv"
        
        if not os.path.exists(file_name):
            logger.warning(f"File not found: {file_name}")
            continue
        
        df = pd.read_csv(file_name)
        df = df.sort_values('frequency')
        
        # Find maximum flow time column (note: "maximum" not "max")
        if algorithm in ['Dynamic', 'Dynamic_BAL']:
            l2_cols = [col for col in df.columns if 'L2_norm_flow_time' in col]
            if l2_cols:
                best_mode_col = df[l2_cols].mean().idxmin()
                max_col = best_mode_col.replace('L2_norm_flow_time', 'maximum_flow_time')
            else:
                logger.warning(f"No L2 columns found for {algorithm}")
                continue
        else:
            max_col = f'{algorithm.upper()}_maximum_flow_time'
        
        if max_col not in df.columns:
            logger.warning(f"Column {max_col} not found for {algorithm}")
            continue
        
        plt.plot(df['frequency'].values, df[max_col].values,
                color=ALGORITHM_COLORS[algorithm],
                marker=ALGORITHM_MARKERS[algorithm],
                linewidth=2, markersize=8,
                label=algorithm,
                alpha=0.9)
        found_any = True
    
    if not found_any:
        logger.warning("No maximum flow time data found for any algorithm")
        plt.close()
        return
    
    plt.xscale('log', base=2)
    plt.xlabel('Coherence Time', fontsize=14)
    plt.ylabel('Maximum Flow Time', fontsize=14)
    plt.title(f'All Algorithms - Maximum Flow Time Comparison ({data_type.capitalize()})', 
              fontsize=16, fontweight='bold')
    plt.legend(loc='best', frameon=True, fancybox=True, shadow=True, ncol=2)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved all algorithms max flow time comparison to {output_path}")

def create_percentage_plots_all_modes(algorithm_type="Dynamic", output_dir="percentage_plots"):
    """Create percentage plots for each mode - auto-detects BAL/FCFS or SRPT/FCFS"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    for mode in range(1, 8):
        filename = f"{algorithm_type}_percentages_mode{mode}_avg.csv"
        
        if not os.path.exists(filename):
            logger.warning(f"Percentage file not found: {filename}")
            continue
        
        try:
            df = pd.read_csv(filename)
            df = df.sort_values(['arrival_rate', 'bp_L'])
            
            # Auto-detect which percentage columns exist
            has_bal = 'BAL_percentage' in df.columns
            has_srpt = 'SRPT_percentage' in df.columns
            has_fcfs = 'FCFS_percentage' in df.columns
            
            if not (has_fcfs and (has_bal or has_srpt)):
                logger.warning(f"Required percentage columns not found in {filename}")
                continue
            
            bp_groups = df.groupby(['bp_L', 'bp_H'])
            
            for (bp_L, bp_H), group in bp_groups:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
                
                # Plot first algorithm (BAL or SRPT)
                if has_bal:
                    ax1.plot(group['arrival_rate'].values, group['BAL_percentage'].values,
                            color='#9467bd', marker='D', linewidth=2.5, markersize=8,
                            label='BAL Percentage')
                    ax1.set_ylabel('BAL Percentage (%)', fontsize=14)
                    ax1.set_title(f'{algorithm_type} Mode {mode} - BAL Usage\nBP: L={bp_L:.3f}, H={bp_H}',
                                 fontsize=16, fontweight='bold')
                elif has_srpt:
                    ax1.plot(group['arrival_rate'].values, group['SRPT_percentage'].values,
                            color='#ff7f0e', marker='s', linewidth=2.5, markersize=8,
                            label='SRPT Percentage')
                    ax1.set_ylabel('SRPT Percentage (%)', fontsize=14)
                    ax1.set_title(f'{algorithm_type} Mode {mode} - SRPT Usage\nBP: L={bp_L:.3f}, H={bp_H}',
                                 fontsize=16, fontweight='bold')
                
                ax1.set_xlabel('Arrival Rate', fontsize=14)
                ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
                ax1.grid(True, alpha=0.3, linestyle='--')
                ax1.set_xlim(18, 42)
                ax1.set_xticks(range(20, 42, 2))
                ax1.set_ylim(0, 105)
                
                # Plot FCFS
                ax2.plot(group['arrival_rate'].values, group['FCFS_percentage'].values,
                        color='#d62728', marker='v', linewidth=2.5, markersize=8,
                        label='FCFS Percentage')
                ax2.set_xlabel('Arrival Rate', fontsize=14)
                ax2.set_ylabel('FCFS Percentage (%)', fontsize=14)
                ax2.set_title(f'{algorithm_type} Mode {mode} - FCFS Usage\nBP: L={bp_L:.3f}, H={bp_H}',
                             fontsize=16, fontweight='bold')
                ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
                ax2.grid(True, alpha=0.3, linestyle='--')
                ax2.set_xlim(18, 42)
                ax2.set_xticks(range(20, 42, 2))
                ax2.set_ylim(0, 105)
                
                plt.tight_layout()
                
                suffix = "BAL_FCFS" if has_bal else "SRPT_FCFS"
                output_path = f"{output_dir}/{algorithm_type}_Mode{mode}_L{bp_L:.3f}_H{bp_H}_{suffix}_Percentages.jpg"
                plt.savefig(output_path, format='jpg', dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Saved percentage plot for {algorithm_type} mode {mode}")
            
        except Exception as e:
            logger.error(f"Error creating percentage plot for {algorithm_type} mode {mode}: {e}")

# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================
def process_all_data(output_base):
    """Process all data and generate all plots for avg30, avg60, avg90"""
    
    logger.info("Step 1: Processing raw data files...")
    process_avg_results(['avg30', 'avg60', 'avg90'])
    process_random_softrandom_results()
    process_dynamic_analysis("Dynamic")
    process_dynamic_analysis("Dynamic_BAL")
    
    # Dictionary to store data for each avg type
    avg_types = ['avg30', 'avg60', 'avg90']
    all_data = {}
    best_settings = {}
    
    for avg_type in avg_types:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {avg_type} data...")
        logger.info(f"{'='*60}")
        
        logger.info(f"Step 2: Loading processed {avg_type} data...")
        avg_dynamic = pd.read_csv(f"Dynamic_result_{avg_type}.csv") if os.path.exists(f"Dynamic_result_{avg_type}.csv") else None
        avg_bal = pd.read_csv(f"Dynamic_BAL_result_{avg_type}.csv") if os.path.exists(f"Dynamic_BAL_result_{avg_type}.csv") else None
        
        logger.info(f"Step 3: Finding best settings for {avg_type}...")
        best_dynamic = find_best_dynamic_setting_v2(avg_dynamic, "Dynamic") if avg_dynamic is not None else None
        best_bal = find_best_dynamic_setting_v2(avg_bal, "Dynamic_BAL") if avg_bal is not None else None
        
        logger.info(f"Best Dynamic ({avg_type}): {best_dynamic}")
        logger.info(f"Best Dynamic_BAL ({avg_type}): {best_bal}")
        
        # Store best settings
        best_settings[avg_type] = {
            'Dynamic': best_dynamic,
            'Dynamic_BAL': best_bal
        }
        
        logger.info(f"Step 4: Merging algorithm data for {avg_type}...")
        avg_data = avg_dynamic.copy() if avg_dynamic is not None else None
        
        for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
            file_name = f"{algo}_result_{avg_type}.csv"
            if os.path.exists(file_name):
                algo_df = pd.read_csv(file_name)
                if avg_data is not None:
                    avg_data = avg_data.merge(algo_df, on=['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'], how='outer')
        
        all_data[avg_type] = avg_data
    
    # Load random and softrandom data (these are not affected by avg type)
    logger.info("\nStep 2b: Loading random and softrandom data...")
    random_dynamic = pd.read_csv("Dynamic_random_result_avg.csv") if os.path.exists("Dynamic_random_result_avg.csv") else None
    random_bal = pd.read_csv("Dynamic_BAL_random_result_avg.csv") if os.path.exists("Dynamic_BAL_random_result_avg.csv") else None
    softrandom_dynamic = pd.read_csv("Dynamic_softrandom_result_avg.csv") if os.path.exists("Dynamic_softrandom_result_avg.csv") else None
    softrandom_bal = pd.read_csv("Dynamic_BAL_softrandom_result_avg.csv") if os.path.exists("Dynamic_BAL_softrandom_result_avg.csv") else None
    
    best_dynamic_random = find_best_dynamic_setting_v2(random_dynamic, "Dynamic") if random_dynamic is not None else None
    best_bal_random = find_best_dynamic_setting_v2(random_bal, "Dynamic_BAL") if random_bal is not None else None
    best_dynamic_softrandom = find_best_dynamic_setting_v2(softrandom_dynamic, "Dynamic") if softrandom_dynamic is not None else None
    best_bal_softrandom = find_best_dynamic_setting_v2(softrandom_bal, "Dynamic_BAL") if softrandom_bal is not None else None
    
    # Merge random data
    random_data = random_dynamic.copy() if random_dynamic is not None else None
    for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
        file_name = f"{algo}_random_result_avg.csv"
        if os.path.exists(file_name) and random_data is not None:
            algo_df = pd.read_csv(file_name)
            random_data = random_data.merge(algo_df, on='frequency', how='outer')
    
    # Merge softrandom data
    softrandom_data = softrandom_dynamic.copy() if softrandom_dynamic is not None else None
    for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
        file_name = f"{algo}_softrandom_result_avg.csv"
        if os.path.exists(file_name) and softrandom_data is not None:
            algo_df = pd.read_csv(file_name)
            softrandom_data = softrandom_data.merge(algo_df, on='frequency', how='outer')
    
    logger.info("\nStep 5: Creating output directories...")
    percentage_dynamic_dir = f"{output_base}/percentages_dynamic"
    percentage_bal_dir = f"{output_base}/percentages_dynamic_bal"
    os.makedirs(percentage_dynamic_dir, exist_ok=True)
    os.makedirs(percentage_bal_dir, exist_ok=True)
    
    logger.info("\nStep 6: Generating percentage plots...")
    create_percentage_plots_all_modes("Dynamic", percentage_dynamic_dir)
    create_percentage_plots_all_modes("Dynamic_BAL", percentage_bal_dir)
    
    # Process each avg type
    for avg_type in avg_types:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing plots for {avg_type}...")
        logger.info(f"{'='*60}")
        
        avg_data = all_data[avg_type]
        if avg_data is None:
            logger.warning(f"No data available for {avg_type}, skipping...")
            continue
        
        best_dynamic = best_settings[avg_type]['Dynamic']
        best_bal = best_settings[avg_type]['Dynamic_BAL']
        
        # Create directories for this avg type
        best_worst_dir = f"{output_base}/{avg_type}/best_worst_compare"
        dynamic_vs_bal_dir = f"{output_base}/{avg_type}/dynamic_vs_dynamic_bal"
        all_algo_dir = f"{output_base}/{avg_type}/all_algorithms_with_dynamic_bal"
        mode_comparison_dir = f"{output_base}/{avg_type}/mode_comparisons"
        
        for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info(f"Step 7: Processing {avg_type} data...")
        bp_groups = avg_data.groupby(['bp_parameter_L', 'bp_parameter_H'])
        
        for (L, H), group_df in bp_groups:
            bp_param = {'L': L, 'H': H}
            
            output_path = f"{best_worst_dir}/Dynamic_BestWorst_L{L:.3f}_H{H}.jpg"
            create_best_worst_comparison('Dynamic', best_dynamic, bp_param, output_path, avg_type)
            
            output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_L{L:.3f}_H{H}.jpg"
            create_best_worst_comparison('Dynamic_BAL', best_bal, bp_param, output_path, avg_type)
            
            output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_L{L:.3f}_H{H}.jpg"
            create_dynamic_vs_dynamic_bal_comparison(best_dynamic, best_bal, bp_param, output_path, avg_type)
            
            output_path = f"{all_algo_dir}/All_Algorithms_L{L:.3f}_H{H}.jpg"
            create_all_algorithms_comparison(group_df, best_dynamic, best_bal, bp_param, output_path, avg_type)
            
            output_path = f"{mode_comparison_dir}/Dynamic_AllModes_L{L:.3f}_H{H}.jpg"
            create_mode_comparison_plots("Dynamic", avg_type, bp_param, output_path)
            
            output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_L{L:.3f}_H{H}.jpg"
            create_mode_comparison_plots("Dynamic_BAL", avg_type, bp_param, output_path)
    
    # Process random and softrandom data
    if random_data is not None:
        logger.info("\n{'='*60}")
        logger.info("Processing random data...")
        logger.info(f"{'='*60}")
        
        best_worst_dir = f"{output_base}/random/best_worst_compare"
        dynamic_vs_bal_dir = f"{output_base}/random/dynamic_vs_dynamic_bal"
        all_algo_dir = f"{output_base}/random/all_algorithms_with_dynamic_bal"
        mode_comparison_dir = f"{output_base}/random/mode_comparisons"
        max_flow_dir = f"{output_base}/random/max_flow_time_comparison"
        
        for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir, max_flow_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        output_path = f"{best_worst_dir}/Dynamic_BestWorst_Random.jpg"
        create_best_worst_comparison('Dynamic', best_dynamic_random, {}, output_path, "random")
        
        output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_Random.jpg"
        create_best_worst_comparison('Dynamic_BAL', best_bal_random, {}, output_path, "random")
        
        output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_Random.jpg"
        create_dynamic_vs_dynamic_bal_comparison(best_dynamic_random, best_bal_random, {}, output_path, "random")
        
        output_path = f"{all_algo_dir}/All_Algorithms_Random.jpg"
        create_all_algorithms_comparison(random_data, best_dynamic_random, best_bal_random, {}, output_path, "random")
        
        output_path = f"{mode_comparison_dir}/Dynamic_AllModes_Random.jpg"
        create_mode_comparison_plots("Dynamic", "random", None, output_path)
        
        output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_Random.jpg"
        create_mode_comparison_plots("Dynamic_BAL", "random", None, output_path)
        
        output_path = f"{max_flow_dir}/MaxFlowTime_Dynamic_vs_BAL_Random.jpg"
        create_max_flow_time_comparison(best_dynamic_random, best_bal_random, output_path, "random")
        
        output_path = f"{max_flow_dir}/MaxFlowTime_AllAlgorithms_Random.jpg"
        create_all_algorithms_max_flow_comparison(output_path, "random")
    
    if softrandom_data is not None:
        logger.info("\n{'='*60}")
        logger.info("Processing softrandom data...")
        logger.info(f"{'='*60}")
        
        best_worst_dir = f"{output_base}/softrandom/best_worst_compare"
        dynamic_vs_bal_dir = f"{output_base}/softrandom/dynamic_vs_dynamic_bal"
        all_algo_dir = f"{output_base}/softrandom/all_algorithms_with_dynamic_bal"
        mode_comparison_dir = f"{output_base}/softrandom/mode_comparisons"
        max_flow_dir = f"{output_base}/softrandom/max_flow_time_comparison"
        
        for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir, max_flow_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        output_path = f"{best_worst_dir}/Dynamic_BestWorst_Softrandom.jpg"
        create_best_worst_comparison('Dynamic', best_dynamic_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_Softrandom.jpg"
        create_best_worst_comparison('Dynamic_BAL', best_bal_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_Softrandom.jpg"
        create_dynamic_vs_dynamic_bal_comparison(best_dynamic_softrandom, best_bal_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{all_algo_dir}/All_Algorithms_Softrandom.jpg"
        create_all_algorithms_comparison(softrandom_data, best_dynamic_softrandom, best_bal_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{mode_comparison_dir}/Dynamic_AllModes_Softrandom.jpg"
        create_mode_comparison_plots("Dynamic", "softrandom", None, output_path)
        
        output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_Softrandom.jpg"
        create_mode_comparison_plots("Dynamic_BAL", "softrandom", None, output_path)
        
        output_path = f"{max_flow_dir}/MaxFlowTime_Dynamic_vs_BAL_Softrandom.jpg"
        create_max_flow_time_comparison(best_dynamic_softrandom, best_bal_softrandom, output_path, "softrandom")
        
        output_path = f"{max_flow_dir}/MaxFlowTime_AllAlgorithms_Softrandom.jpg"
        create_all_algorithms_max_flow_comparison(output_path, "softrandom")
# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """Main function with worst case processing"""
    logger.info("="*60)
    logger.info("Enhanced Algorithm Comparison Plotter v2 - Fixed Version")
    logger.info("="*60)
    
    setup_plot_style()
    
    # STEP 1: Validate worst case directory exists
    logger.info("\nSTEP 1: Validating worst case directory...")
    if not validate_worst_case_setup():
        logger.error("\n" + "!"*60)
        logger.error("WORST CASE DIRECTORY VALIDATION FAILED!")
        logger.error("Some comparisons will be skipped.")
        logger.error("!"*60 + "\n")
    
    output_base = "enhanced_algorithm_plots_v2"
    os.makedirs(output_base, exist_ok=True)
    
    try:
        # STEP 2: Process NORMAL case data (best case)
        logger.info("\n" + "="*60)
        logger.info("STEP 2: Processing NORMAL (BEST) case data...")
        logger.info("="*60)
        
        process_avg_results(['avg30', 'avg60', 'avg90'])
        process_random_softrandom_results()
        process_dynamic_analysis("Dynamic")
        process_dynamic_analysis("Dynamic_BAL")
        
        # STEP 3: Process WORST case data
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Processing WORST case data...")
        logger.info("="*60)
        
        process_worst_case_avg_results(['avg30', 'avg60', 'avg90'])
        process_worst_case_random_softrandom_results()
        
        # STEP 4: Load and analyze data
        logger.info("\n" + "="*60)
        logger.info("STEP 4: Finding best settings...")
        logger.info("="*60)
        
        avg_types = ['avg30', 'avg60', 'avg90']
        all_data = {}
        best_settings = {}
        
        for avg_type in avg_types:
            logger.info(f"\nAnalyzing {avg_type}...")
            
            avg_dynamic = pd.read_csv(f"Dynamic_result_{avg_type}.csv") if os.path.exists(f"Dynamic_result_{avg_type}.csv") else None
            avg_bal = pd.read_csv(f"Dynamic_BAL_result_{avg_type}.csv") if os.path.exists(f"Dynamic_BAL_result_{avg_type}.csv") else None
            
            best_dynamic = find_best_dynamic_setting_v2(avg_dynamic, "Dynamic") if avg_dynamic is not None else None
            best_bal = find_best_dynamic_setting_v2(avg_bal, "Dynamic_BAL") if avg_bal is not None else None
            
            logger.info(f"  Best Dynamic: {best_dynamic}")
            logger.info(f"  Best Dynamic_BAL: {best_bal}")
            
            best_settings[avg_type] = {
                'Dynamic': best_dynamic,
                'Dynamic_BAL': best_bal
            }
            
            # Merge all algorithm data
            avg_data = avg_dynamic.copy() if avg_dynamic is not None else None
            
            for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
                file_name = f"{algo}_result_{avg_type}.csv"
                if os.path.exists(file_name):
                    algo_df = pd.read_csv(file_name)
                    if avg_data is not None:
                        avg_data = avg_data.merge(algo_df, on=['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'], how='outer')
            
            all_data[avg_type] = avg_data
        
        # Load random and softrandom
        logger.info("\nLoading random and softrandom data...")
        random_dynamic = pd.read_csv("Dynamic_random_result_avg.csv") if os.path.exists("Dynamic_random_result_avg.csv") else None
        random_bal = pd.read_csv("Dynamic_BAL_random_result_avg.csv") if os.path.exists("Dynamic_BAL_random_result_avg.csv") else None
        softrandom_dynamic = pd.read_csv("Dynamic_softrandom_result_avg.csv") if os.path.exists("Dynamic_softrandom_result_avg.csv") else None
        softrandom_bal = pd.read_csv("Dynamic_BAL_softrandom_result_avg.csv") if os.path.exists("Dynamic_BAL_softrandom_result_avg.csv") else None
        
        best_dynamic_random = find_best_dynamic_setting_v2(random_dynamic, "Dynamic") if random_dynamic is not None else None
        best_bal_random = find_best_dynamic_setting_v2(random_bal, "Dynamic_BAL") if random_bal is not None else None
        best_dynamic_softrandom = find_best_dynamic_setting_v2(softrandom_dynamic, "Dynamic") if softrandom_dynamic is not None else None
        best_bal_softrandom = find_best_dynamic_setting_v2(softrandom_bal, "Dynamic_BAL") if softrandom_bal is not None else None
        
        # Merge random data
        random_data = random_dynamic.copy() if random_dynamic is not None else None
        for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
            file_name = f"{algo}_random_result_avg.csv"
            if os.path.exists(file_name) and random_data is not None:
                algo_df = pd.read_csv(file_name)
                random_data = random_data.merge(algo_df, on='frequency', how='outer')
        
        # Merge softrandom data
        softrandom_data = softrandom_dynamic.copy() if softrandom_dynamic is not None else None
        for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
            file_name = f"{algo}_softrandom_result_avg.csv"
            if os.path.exists(file_name) and softrandom_data is not None:
                algo_df = pd.read_csv(file_name)
                softrandom_data = softrandom_data.merge(algo_df, on='frequency', how='outer')
        
        # STEP 5: Create output directories
        logger.info("\n" + "="*60)
        logger.info("STEP 5: Creating output directories...")
        logger.info("="*60)
        
        percentage_dynamic_dir = f"{output_base}/percentages_dynamic"
        percentage_bal_dir = f"{output_base}/percentages_dynamic_bal"
        os.makedirs(percentage_dynamic_dir, exist_ok=True)
        os.makedirs(percentage_bal_dir, exist_ok=True)
        
        # STEP 6: Generate percentage plots
        logger.info("\nSTEP 6: Generating percentage plots...")
        create_percentage_plots_all_modes("Dynamic", percentage_dynamic_dir)
        create_percentage_plots_all_modes("Dynamic_BAL", percentage_bal_dir)
        
        # STEP 7: Generate plots for each avg type
        for avg_type in avg_types:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP 7: Generating {avg_type} plots...")
            logger.info(f"{'='*60}")
            
            avg_data = all_data[avg_type]
            if avg_data is None:
                logger.warning(f"No data for {avg_type}, skipping...")
                continue
            
            best_dynamic = best_settings[avg_type]['Dynamic']
            best_bal = best_settings[avg_type]['Dynamic_BAL']
            
            # Create directories
            best_worst_dir = f"{output_base}/{avg_type}/best_worst_compare"
            dynamic_vs_bal_dir = f"{output_base}/{avg_type}/dynamic_vs_dynamic_bal"
            all_algo_dir = f"{output_base}/{avg_type}/all_algorithms_with_dynamic_bal"
            mode_comparison_dir = f"{output_base}/{avg_type}/mode_comparisons"
            
            for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            bp_groups = avg_data.groupby(['bp_parameter_L', 'bp_parameter_H'])
            
            for (L, H), group_df in bp_groups:
                bp_param = {'L': L, 'H': H}
                
                logger.info(f"\nProcessing BP: L={L:.3f}, H={H}")
                
                # Best vs Worst comparisons
                try:
                    output_path = f"{best_worst_dir}/Dynamic_BestWorst_L{L:.3f}_H{H}.jpg"
                    create_best_worst_comparison('Dynamic', best_dynamic, bp_param, output_path, avg_type)
                except Exception as e:
                    logger.error(f"Error creating Dynamic best/worst: {e}")
                
                try:
                    output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_L{L:.3f}_H{H}.jpg"
                    create_best_worst_comparison('Dynamic_BAL', best_bal, bp_param, output_path, avg_type)
                except Exception as e:
                    logger.error(f"Error creating Dynamic_BAL best/worst: {e}")
                
                # Dynamic vs Dynamic_BAL
                try:
                    output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_L{L:.3f}_H{H}.jpg"
                    create_dynamic_vs_dynamic_bal_comparison(best_dynamic, best_bal, bp_param, output_path, avg_type)
                except Exception as e:
                    logger.error(f"Error creating Dynamic vs BAL: {e}")
                
                # All algorithms
                try:
                    output_path = f"{all_algo_dir}/All_Algorithms_L{L:.3f}_H{H}.jpg"
                    create_all_algorithms_comparison(group_df, best_dynamic, best_bal, bp_param, output_path, avg_type)
                except Exception as e:
                    logger.error(f"Error creating all algorithms comparison: {e}")
                
                # Mode comparisons
                try:
                    output_path = f"{mode_comparison_dir}/Dynamic_AllModes_L{L:.3f}_H{H}.jpg"
                    create_mode_comparison_plots("Dynamic", avg_type, bp_param, output_path)
                except Exception as e:
                    logger.error(f"Error creating Dynamic mode comparison: {e}")
                
                try:
                    output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_L{L:.3f}_H{H}.jpg"
                    create_mode_comparison_plots("Dynamic_BAL", avg_type, bp_param, output_path)
                except Exception as e:
                    logger.error(f"Error creating Dynamic_BAL mode comparison: {e}")
        
        # STEP 8: Process random data
        if random_data is not None:
            logger.info("\n{'='*60}")
            logger.info("STEP 8: Generating random plots...")
            logger.info(f"{'='*60}")
            
            best_worst_dir = f"{output_base}/random/best_worst_compare"
            dynamic_vs_bal_dir = f"{output_base}/random/dynamic_vs_dynamic_bal"
            all_algo_dir = f"{output_base}/random/all_algorithms_with_dynamic_bal"
            mode_comparison_dir = f"{output_base}/random/mode_comparisons"
            max_flow_dir = f"{output_base}/random/max_flow_time_comparison"
            
            for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir, max_flow_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            try:
                output_path = f"{best_worst_dir}/Dynamic_BestWorst_Random.jpg"
                create_best_worst_comparison('Dynamic', best_dynamic_random, {}, output_path, "random")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_Random.jpg"
                create_best_worst_comparison('Dynamic_BAL', best_bal_random, {}, output_path, "random")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_Random.jpg"
                create_dynamic_vs_dynamic_bal_comparison(best_dynamic_random, best_bal_random, {}, output_path, "random")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{all_algo_dir}/All_Algorithms_Random.jpg"
                create_all_algorithms_comparison(random_data, best_dynamic_random, best_bal_random, {}, output_path, "random")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{mode_comparison_dir}/Dynamic_AllModes_Random.jpg"
                create_mode_comparison_plots("Dynamic", "random", None, output_path)
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_Random.jpg"
                create_mode_comparison_plots("Dynamic_BAL", "random", None, output_path)
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{max_flow_dir}/MaxFlowTime_Dynamic_vs_BAL_Random.jpg"
                create_max_flow_time_comparison(best_dynamic_random, best_bal_random, output_path, "random")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{max_flow_dir}/MaxFlowTime_AllAlgorithms_Random.jpg"
                create_all_algorithms_max_flow_comparison(output_path, "random")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        # STEP 9: Process softrandom data
        if softrandom_data is not None:
            logger.info("\n{'='*60}")
            logger.info("STEP 9: Generating softrandom plots...")
            logger.info(f"{'='*60}")
            
            best_worst_dir = f"{output_base}/softrandom/best_worst_compare"
            dynamic_vs_bal_dir = f"{output_base}/softrandom/dynamic_vs_dynamic_bal"
            all_algo_dir = f"{output_base}/softrandom/all_algorithms_with_dynamic_bal"
            mode_comparison_dir = f"{output_base}/softrandom/mode_comparisons"
            max_flow_dir = f"{output_base}/softrandom/max_flow_time_comparison"
            
            for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir, max_flow_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            try:
                output_path = f"{best_worst_dir}/Dynamic_BestWorst_Softrandom.jpg"
                create_best_worst_comparison('Dynamic', best_dynamic_softrandom, {}, output_path, "softrandom")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_Softrandom.jpg"
                create_best_worst_comparison('Dynamic_BAL', best_bal_softrandom, {}, output_path, "softrandom")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_Softrandom.jpg"
                create_dynamic_vs_dynamic_bal_comparison(best_dynamic_softrandom, best_bal_softrandom, {}, output_path, "softrandom")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{all_algo_dir}/All_Algorithms_Softrandom.jpg"
                create_all_algorithms_comparison(softrandom_data, best_dynamic_softrandom, best_bal_softrandom, {}, output_path, "softrandom")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{mode_comparison_dir}/Dynamic_AllModes_Softrandom.jpg"
                create_mode_comparison_plots("Dynamic", "softrandom", None, output_path)
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_Softrandom.jpg"
                create_mode_comparison_plots("Dynamic_BAL", "softrandom", None, output_path)
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{max_flow_dir}/MaxFlowTime_Dynamic_vs_BAL_Softrandom.jpg"
                create_max_flow_time_comparison(best_dynamic_softrandom, best_bal_softrandom, output_path, "softrandom")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            try:
                output_path = f"{max_flow_dir}/MaxFlowTime_AllAlgorithms_Softrandom.jpg"
                create_all_algorithms_max_flow_comparison(output_path, "softrandom")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        # STEP 10: Heavy tail analysis
        logger.info("\nSTEP 10: Generating heavy tail analysis...")
        heavy_tail_dir = os.path.join(output_base, "heavy_tail_analysis")
        draw_heavy_tail(heavy_tail_dir)
        
        # FINAL SUMMARY
        logger.info("\n" + "="*60)
        logger.info("✅ PLOT GENERATION COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
        total_jpgs = len(glob.glob(f"{output_base}/**/*.jpg", recursive=True))
        logger.info(f"Total JPG files generated: {total_jpgs}")
        
        logger.info("\nGenerated folders:")
        for folder in sorted(os.listdir(output_base)):
            folder_path = os.path.join(output_base, folder)
            if os.path.isdir(folder_path):
                jpg_count = len(glob.glob(f"{folder_path}/**/*.jpg", recursive=True))
                logger.info(f"  {folder}: {jpg_count} JPGs")
        
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()