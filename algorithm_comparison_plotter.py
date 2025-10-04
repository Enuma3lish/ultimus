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
# DATA PROCESSING FUNCTIONS
# ============================================================================
def process_avg30_results():
    """Process avg30 results from algorithm_result directory"""
    
    for algorithm in ALGORITHMS:
        logger.info(f"Processing avg30 results for {algorithm}")
        
        result_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "avg30_result")
        
        if not os.path.exists(result_dir):
            logger.warning(f"Directory {result_dir} not found")
            continue
            
        pattern = f"{result_dir}/*_{algorithm}_*_result*.csv"
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No result files found for {algorithm}")
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
                    logger.error(f"Error reading {file}: {e}")
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
                        logger.warning(f"Column {l2_col_name} not found in {algorithm} data")
        
        if all_results:
            final_df = pd.DataFrame(all_results)
            final_df = final_df.sort_values(['arrival_rate', 'bp_parameter_L'])
            
            output_file = f"{algorithm}_result_avg30.csv"
            final_df.to_csv(output_file, index=False)
            logger.info(f"Created final file: {output_file}")

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

def load_worst_case_data(algorithm, data_type="avg30"):
    """Load worst case data for comparison"""
    if data_type == "avg30":
        result_dir = os.path.join(WORST_CASE_PATH, f"{algorithm}_result", "avg30_result")
        pattern = f"{result_dir}/*_{algorithm}_*_result*.csv"
    else:
        result_dir = os.path.join(WORST_CASE_PATH, f"{algorithm}_result", f"{data_type}_result")
        if algorithm in ['Dynamic', 'Dynamic_BAL']:
            pattern = f"{result_dir}/{data_type}_result_{algorithm}_njobs100_*.csv"
        else:
            pattern = f"{result_dir}/{data_type}_result_{algorithm}_*.csv"
    
    files = glob.glob(pattern)
    if not files:
        logger.warning(f"No worst case files found for {algorithm} ({data_type})")
        return None
    
    all_dfs = []
    for file in files:
        try:
            df = pd.read_csv(file)
            all_dfs.append(df)
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")
            continue
    
    if not all_dfs:
        return None
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    if algorithm in ['Dynamic', 'Dynamic_BAL']:
        if data_type == "avg30":
            grouped = combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])
            result = []
            for (arr_rate, bp_L, bp_H), group in grouped:
                row_data = {'arrival_rate': arr_rate, 'bp_parameter_L': bp_L, 'bp_parameter_H': bp_H}
                l2_cols = [col for col in group.columns if 'L2_norm_flow_time' in col]
                for col in l2_cols:
                    row_data[col] = group[col].mean()
                result.append(row_data)
            return pd.DataFrame(result)
        else:
            l2_cols = [col for col in combined_df.columns if 'L2_norm_flow_time' in col]
            return combined_df.groupby('frequency')[l2_cols].mean().reset_index()
    else:
        l2_col = f'{algorithm.upper()}_L2_norm_flow_time'
        if data_type == "avg30":
            return combined_df.groupby(['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'])[l2_col].mean().reset_index()
        else:
            return combined_df.groupby('frequency')[l2_col].mean().reset_index()

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================
def create_best_worst_comparison(algorithm, best_col, bp_param, output_path, data_type="avg30"):
    """Compare best case vs worst case results"""
    
    if data_type == "avg30":
        best_file = f"{algorithm}_result_avg30.csv"
    else:
        best_file = f"{algorithm}_{data_type}_result_avg.csv"
    
    if not os.path.exists(best_file):
        logger.warning(f"Best case file not found: {best_file}")
        return
    
    best_df = pd.read_csv(best_file)
    worst_df = load_worst_case_data(algorithm, data_type)
    
    if worst_df is None:
        logger.warning(f"No worst case data for {algorithm}")
        return
    
    plt.figure(figsize=(12, 8))
    
    if data_type == "avg30":
        best_df_filtered = best_df[(best_df['bp_parameter_L'] == bp_param['L']) & 
                                     (best_df['bp_parameter_H'] == bp_param['H'])]
        worst_df_filtered = worst_df[(worst_df['bp_parameter_L'] == bp_param['L']) & 
                                       (worst_df['bp_parameter_H'] == bp_param['H'])]
        
        if best_df_filtered.empty or worst_df_filtered.empty:
            logger.warning(f"No data for bp_L={bp_param['L']}, bp_H={bp_param['H']}")
            return
        
        best_df_filtered = best_df_filtered.sort_values('arrival_rate')
        worst_df_filtered = worst_df_filtered.sort_values('arrival_rate')
        
        x_values = best_df_filtered['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'{algorithm}: Best vs Worst Case - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        best_df = best_df.sort_values('frequency')
        worst_df = worst_df.sort_values('frequency')
        
        x_values = best_df['frequency'].values
        x_label = 'Coherence Time'
        title = f'{algorithm}: Best vs Worst Case - {data_type.capitalize()}'
        
        best_df_filtered = best_df
        worst_df_filtered = worst_df
    
    if best_col in best_df_filtered.columns:
        best_values = best_df_filtered[best_col].values
    else:
        logger.warning(f"Column {best_col} not found in best case data")
        return
    
    worst_col = best_col.replace('mode6', 'mode1').replace('mode7', 'mode1')
    if worst_col not in worst_df_filtered.columns:
        logger.warning(f"Column {worst_col} not found in worst case data")
        return
    
    worst_values = worst_df_filtered[worst_col].values
    
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = best_values / worst_values
        ratio = np.where(np.isfinite(ratio), ratio, np.nan)
    
    plt.plot(x_values, ratio,
            color=BEST_WORST_COLORS['best'],
            marker=BEST_WORST_MARKERS['best'],
            linewidth=2.5, markersize=10,
            label='Best/Worst Ratio',
            alpha=0.9)
    
    plt.axhline(y=1, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel('Performance Ratio (Best/Worst)', fontsize=14)
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
    
    logger.info(f"Saved best vs worst comparison to {output_path}")

def create_dynamic_vs_dynamic_bal_comparison(best_dynamic_col, best_bal_col, bp_param, output_path, data_type="avg30"):
    """Compare Dynamic vs Dynamic_BAL"""
    
    if data_type == "avg30":
        dynamic_file = "Dynamic_result_avg30.csv"
        bal_file = "Dynamic_BAL_result_avg30.csv"
    else:
        dynamic_file = f"Dynamic_{data_type}_result_avg.csv"
        bal_file = f"Dynamic_BAL_{data_type}_result_avg.csv"
    
    if not os.path.exists(dynamic_file) or not os.path.exists(bal_file):
        logger.warning("Dynamic or Dynamic_BAL file not found")
        return
    
    dynamic_df = pd.read_csv(dynamic_file)
    bal_df = pd.read_csv(bal_file)
    
    plt.figure(figsize=(12, 8))
    
    if data_type == "avg30":
        dynamic_df = dynamic_df[(dynamic_df['bp_parameter_L'] == bp_param['L']) & 
                                (dynamic_df['bp_parameter_H'] == bp_param['H'])]
        bal_df = bal_df[(bal_df['bp_parameter_L'] == bp_param['L']) & 
                        (bal_df['bp_parameter_H'] == bp_param['H'])]
        
        if dynamic_df.empty or bal_df.empty:
            logger.warning(f"No data for bp_L={bp_param['L']}, bp_H={bp_param['H']}")
            return
        
        dynamic_df = dynamic_df.sort_values('arrival_rate')
        bal_df = bal_df.sort_values('arrival_rate')
        
        x_values = dynamic_df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Dynamic vs Dynamic_BAL - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
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
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved Dynamic vs Dynamic_BAL comparison to {output_path}")

def create_all_algorithms_comparison(df, best_dynamic_col, best_bal_col, bp_param, output_path, data_type="avg30"):
    """Compare all algorithms including Dynamic and Dynamic_BAL"""
    
    plt.figure(figsize=(14, 8))
    
    algorithms_to_plot = ['RR', 'SRPT', 'SETF', 'FCFS', 'BAL', 'SJF']
    
    if data_type == "avg30":
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'All Algorithms Comparison - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
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
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved all algorithms comparison to {output_path}")

def create_mode_comparison_plots(algorithm_type="Dynamic", data_type="avg30", bp_param=None, output_path=None):
    """Create plots comparing all modes (1-7)"""
    
    if data_type == "avg30":
        file_name = f"{algorithm_type}_result_avg30.csv"
    else:
        file_name = f"{algorithm_type}_{data_type}_result_avg.csv"
    
    if not os.path.exists(file_name):
        logger.warning(f"File not found: {file_name}")
        return
    
    df = pd.read_csv(file_name)
    
    plt.figure(figsize=(12, 8))
    
    if data_type == "avg30":
        if bp_param is None:
            logger.warning("bp_param required for avg30 data")
            return
        
        df = df[(df['bp_parameter_L'] == bp_param['L']) & 
                (df['bp_parameter_H'] == bp_param['H'])]
        
        if df.empty:
            logger.warning(f"No data for bp_L={bp_param['L']}, bp_H={bp_param['H']}")
            return
        
        df = df.sort_values('arrival_rate')
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'{algorithm_type} - All Modes Comparison\nBP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
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
        plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved mode comparison plot to {output_path}")

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
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
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
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
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
                output_path = f"{output_dir}/{algorithm_type}_Mode{mode}_L{bp_L:.3f}_H{bp_H}_{suffix}_Percentages.pdf"
                plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Saved percentage plot for {algorithm_type} mode {mode}")
            
        except Exception as e:
            logger.error(f"Error creating percentage plot for {algorithm_type} mode {mode}: {e}")

# ============================================================================
# MAIN PROCESSING PIPELINE
# ============================================================================
def process_all_data(output_base):
    """Process all data and generate all plots"""
    
    logger.info("Step 1: Processing raw data files...")
    process_avg30_results()
    process_random_softrandom_results()
    process_dynamic_analysis("Dynamic")
    process_dynamic_analysis("Dynamic_BAL")
    
    logger.info("Step 2: Loading processed data...")
    avg30_dynamic = pd.read_csv("Dynamic_result_avg30.csv") if os.path.exists("Dynamic_result_avg30.csv") else None
    avg30_bal = pd.read_csv("Dynamic_BAL_result_avg30.csv") if os.path.exists("Dynamic_BAL_result_avg30.csv") else None
    random_dynamic = pd.read_csv("Dynamic_random_result_avg.csv") if os.path.exists("Dynamic_random_result_avg.csv") else None
    random_bal = pd.read_csv("Dynamic_BAL_random_result_avg.csv") if os.path.exists("Dynamic_BAL_random_result_avg.csv") else None
    softrandom_dynamic = pd.read_csv("Dynamic_softrandom_result_avg.csv") if os.path.exists("Dynamic_softrandom_result_avg.csv") else None
    softrandom_bal = pd.read_csv("Dynamic_BAL_softrandom_result_avg.csv") if os.path.exists("Dynamic_BAL_softrandom_result_avg.csv") else None
    
    logger.info("Step 3: Finding best settings...")
    best_dynamic_avg30 = find_best_dynamic_setting_v2(avg30_dynamic, "Dynamic") if avg30_dynamic is not None else None
    best_bal_avg30 = find_best_dynamic_setting_v2(avg30_bal, "Dynamic_BAL") if avg30_bal is not None else None
    best_dynamic_random = find_best_dynamic_setting_v2(random_dynamic, "Dynamic") if random_dynamic is not None else None
    best_bal_random = find_best_dynamic_setting_v2(random_bal, "Dynamic_BAL") if random_bal is not None else None
    best_dynamic_softrandom = find_best_dynamic_setting_v2(softrandom_dynamic, "Dynamic") if softrandom_dynamic is not None else None
    best_bal_softrandom = find_best_dynamic_setting_v2(softrandom_bal, "Dynamic_BAL") if softrandom_bal is not None else None
    
    logger.info(f"Best Dynamic (avg30): {best_dynamic_avg30}")
    logger.info(f"Best Dynamic_BAL (avg30): {best_bal_avg30}")
    
    logger.info("Step 4: Merging algorithm data...")
    avg30_data = avg30_dynamic.copy() if avg30_dynamic is not None else None
    random_data = random_dynamic.copy() if random_dynamic is not None else None
    softrandom_data = softrandom_dynamic.copy() if softrandom_dynamic is not None else None
    
    for algo in ['Dynamic_BAL', 'BAL', 'FCFS', 'SRPT', 'RR', 'SETF', 'SJF']:
        for data_type, data_df in [('avg30', avg30_data), ('random', random_data), ('softrandom', softrandom_data)]:
            if data_df is None:
                continue
            
            file_name = f"{algo}_{data_type}_result_avg.csv" if data_type != "avg30" else f"{algo}_result_avg30.csv"
            if os.path.exists(file_name):
                algo_df = pd.read_csv(file_name)
                if data_type == "avg30":
                    data_df = data_df.merge(algo_df, on=['arrival_rate', 'bp_parameter_L', 'bp_parameter_H'], how='outer')
                else:
                    data_df = data_df.merge(algo_df, on='frequency', how='outer')
                
                if data_type == 'avg30':
                    avg30_data = data_df
                elif data_type == 'random':
                    random_data = data_df
                else:
                    softrandom_data = data_df
    
    logger.info("Step 5: Creating output directories...")
    best_worst_dir = f"{output_base}/best_worst_compare"
    dynamic_vs_bal_dir = f"{output_base}/dynamic_vs_dynamic_bal"
    all_algo_dir = f"{output_base}/all_algorithms_with_dynamic_bal"
    mode_comparison_dir = f"{output_base}/mode_comparisons"
    max_flow_dir = f"{output_base}/max_flow_time_comparison"
    percentage_dynamic_dir = f"{output_base}/percentages_dynamic"
    percentage_bal_dir = f"{output_base}/percentages_dynamic_bal"
    
    for dir_path in [best_worst_dir, dynamic_vs_bal_dir, all_algo_dir, mode_comparison_dir, 
                     max_flow_dir, percentage_dynamic_dir, percentage_bal_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    logger.info("Step 6: Generating percentage plots...")
    create_percentage_plots_all_modes("Dynamic", percentage_dynamic_dir)
    create_percentage_plots_all_modes("Dynamic_BAL", percentage_bal_dir)
    
    if avg30_data is not None:
        logger.info("Step 7: Processing avg30 data...")
        bp_groups = avg30_data.groupby(['bp_parameter_L', 'bp_parameter_H'])
        
        for (L, H), group_df in bp_groups:
            bp_param = {'L': L, 'H': H}
            
            output_path = f"{best_worst_dir}/Dynamic_BestWorst_L{L:.3f}_H{H}.pdf"
            create_best_worst_comparison('Dynamic', best_dynamic_avg30, bp_param, output_path, "avg30")
            
            output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_L{L:.3f}_H{H}.pdf"
            create_best_worst_comparison('Dynamic_BAL', best_bal_avg30, bp_param, output_path, "avg30")
            
            output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_L{L:.3f}_H{H}.pdf"
            create_dynamic_vs_dynamic_bal_comparison(best_dynamic_avg30, best_bal_avg30, bp_param, output_path, "avg30")
            
            output_path = f"{all_algo_dir}/All_Algorithms_L{L:.3f}_H{H}.pdf"
            create_all_algorithms_comparison(group_df, best_dynamic_avg30, best_bal_avg30, bp_param, output_path, "avg30")
            
            output_path = f"{mode_comparison_dir}/Dynamic_AllModes_L{L:.3f}_H{H}.pdf"
            create_mode_comparison_plots("Dynamic", "avg30", bp_param, output_path)
            
            output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_L{L:.3f}_H{H}.pdf"
            create_mode_comparison_plots("Dynamic_BAL", "avg30", bp_param, output_path)
    
    if random_data is not None:
        logger.info("Step 8: Processing random data...")
        
        output_path = f"{best_worst_dir}/Dynamic_BestWorst_Random.pdf"
        create_best_worst_comparison('Dynamic', best_dynamic_random, {}, output_path, "random")
        
        output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_Random.pdf"
        create_best_worst_comparison('Dynamic_BAL', best_bal_random, {}, output_path, "random")
        
        output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_Random.pdf"
        create_dynamic_vs_dynamic_bal_comparison(best_dynamic_random, best_bal_random, {}, output_path, "random")
        
        output_path = f"{all_algo_dir}/All_Algorithms_Random.pdf"
        create_all_algorithms_comparison(random_data, best_dynamic_random, best_bal_random, {}, output_path, "random")
        
        output_path = f"{mode_comparison_dir}/Dynamic_AllModes_Random.pdf"
        create_mode_comparison_plots("Dynamic", "random", None, output_path)
        
        output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_Random.pdf"
        create_mode_comparison_plots("Dynamic_BAL", "random", None, output_path)
        
        output_path = f"{max_flow_dir}/MaxFlowTime_Dynamic_vs_BAL_Random.pdf"
        create_max_flow_time_comparison(best_dynamic_random, best_bal_random, output_path, "random")
        
        output_path = f"{max_flow_dir}/MaxFlowTime_AllAlgorithms_Random.pdf"
        create_all_algorithms_max_flow_comparison(output_path, "random")
    
    if softrandom_data is not None:
        logger.info("Step 9: Processing softrandom data...")
        
        output_path = f"{best_worst_dir}/Dynamic_BestWorst_Softrandom.pdf"
        create_best_worst_comparison('Dynamic', best_dynamic_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{best_worst_dir}/Dynamic_BAL_BestWorst_Softrandom.pdf"
        create_best_worst_comparison('Dynamic_BAL', best_bal_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{dynamic_vs_bal_dir}/Dynamic_vs_BAL_Softrandom.pdf"
        create_dynamic_vs_dynamic_bal_comparison(best_dynamic_softrandom, best_bal_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{all_algo_dir}/All_Algorithms_Softrandom.pdf"
        create_all_algorithms_comparison(softrandom_data, best_dynamic_softrandom, best_bal_softrandom, {}, output_path, "softrandom")
        
        output_path = f"{mode_comparison_dir}/Dynamic_AllModes_Softrandom.pdf"
        create_mode_comparison_plots("Dynamic", "softrandom", None, output_path)
        
        output_path = f"{mode_comparison_dir}/Dynamic_BAL_AllModes_Softrandom.pdf"
        create_mode_comparison_plots("Dynamic_BAL", "softrandom", None, output_path)
        
        output_path = f"{max_flow_dir}/MaxFlowTime_Dynamic_vs_BAL_Softrandom.pdf"
        create_max_flow_time_comparison(best_dynamic_softrandom, best_bal_softrandom, output_path, "softrandom")
        
        output_path = f"{max_flow_dir}/MaxFlowTime_AllAlgorithms_Softrandom.pdf"
        create_all_algorithms_max_flow_comparison(output_path, "softrandom")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """Main function"""
    logger.info("="*60)
    logger.info("Enhanced Algorithm Comparison Plotter v2 - Fixed Version")
    logger.info("="*60)
    
    setup_plot_style()
    
    output_base = "enhanced_algorithm_plots_v2"
    os.makedirs(output_base, exist_ok=True)
    
    try:
        process_all_data(output_base)
        
        logger.info("\n" + "="*60)
        logger.info("Plot generation completed successfully!")
        total_pdfs = len(glob.glob(f"{output_base}/**/*.pdf", recursive=True))
        logger.info(f"Total PDF files generated: {total_pdfs}")
        
        logger.info("\nGenerated folders:")
        for folder in sorted(os.listdir(output_base)):
            folder_path = os.path.join(output_base, folder)
            if os.path.isdir(folder_path):
                pdf_count = len(glob.glob(f"{folder_path}/*.pdf"))
                logger.info(f"  {folder}: {pdf_count} PDFs")
        
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()