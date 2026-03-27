#!/usr/bin/env python3
"""
Chapter 4 Figure Generator - avg30 + Soft Random Only
======================================================

Two data groups:
1. avg30 - single distribution experiments
2. softrandom combination - multi-distribution experiments

Style rules:
- Our algorithms (Dynamic, Dynamic_BAL, RFDynamic): SOLID + FILLED markers + THICK lines
- Primary comparison (SRPT/RMLF/FCFS): SOLID + FILLED markers + MEDIUM lines
- Other baselines: DASHED + HOLLOW markers + THIN lines

Author: Melo Wu
Date: 2025-01
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import glob
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
BASE_PATH = "."  # Change to: "C:/Users/MeloWu/Desktop/ultimus"
ANALYSIS_PATH = os.path.join(BASE_PATH, "Analysis")
ALGORITHM_RESULT_PATH = os.path.join(BASE_PATH, "algorithm_result")
OUTPUT_PATH = os.path.join(BASE_PATH, "figures")

# ============================================================================
# ALGORITHM CONFIGURATION
# ============================================================================
DYNAMIC_ALGORITHMS = {
    'Dynamic': {
        'efficiency_col': 'SRPT_percentage',
        'fairness_col': 'FCFS_percentage',
        'efficiency_name': 'SRPT',
        'analysis_dir': 'Dynamic_analysis',
        'file_prefix': 'Dynamic',
    },
    'Dynamic_BAL': {
        'efficiency_col': 'BAL_percentage',
        'fairness_col': 'FCFS_percentage',
        'efficiency_name': 'BAL',
        'analysis_dir': 'Dynamic_BAL_analysis',
        'file_prefix': 'Dynamic_BAL',
    },
    'RFDynamic': {
        'efficiency_col': 'RMLF_percentage',
        'fairness_col': 'FCFS_percentage',
        'efficiency_name': 'RMLF',
        'analysis_dir': 'RFDynamic_analysis',
        'file_prefix': 'RFDynamic',
    },
}

CLAIRVOYANT_BASELINES = ['BAL', 'SRPT', 'FCFS', 'SJF', 'RR']
NON_CLAIRVOYANT_BASELINES = ['RMLF', 'MLFQ', 'FCFS', 'SETF', 'RR']

LOOKBACKS = [1, 2, 4, 8, 16]
LOOKBACK_ALL = 0
ALL_LOOKBACKS = LOOKBACKS + [LOOKBACK_ALL]
NUM_ROUNDS = 5
INTER_ARRIVAL_TIMES = list(range(20, 42, 2))
DEFAULT_BATCH_SIZE = 100

# ============================================================================
# AVG30 DISTRIBUTION CONFIGURATIONS
# ============================================================================
BP_CONFIGS = [
    {'H': 64, 'L': 16.77, 'name': 'bp-h64', 'title': 'Bounded Pareto ($H=2^6$, $H/L \\approx 3.8$)'},
    {'H': 512, 'L': 7.92, 'name': 'bp-h512', 'title': 'Bounded Pareto ($H=2^9$, $H/L \\approx 65$)'},
    {'H': 4096, 'L': 5.65, 'name': 'bp-h4096', 'title': 'Bounded Pareto ($H=2^{12}$, $H/L \\approx 725$)'},
    {'H': 32768, 'L': 4.64, 'name': 'bp-h32768', 'title': 'Bounded Pareto ($H=2^{15}$, $H/L \\approx 7065$)'},
    {'H': 262144, 'L': 4.07, 'name': 'bp-h262144', 'title': 'Bounded Pareto ($H=2^{18}$, $H/L \\approx 64359$)'},
]

NORMAL_CONFIGS = [
    {'std': 6, 'mean': 30, 'name': 'normal-std6', 'title': 'Normal ($\\mu=30$, $\\sigma=6$, CV=0.20)'},
    {'std': 9, 'mean': 30, 'name': 'normal-std9', 'title': 'Normal ($\\mu=30$, $\\sigma=9$, CV=0.30)'},
    {'std': 12, 'mean': 30, 'name': 'normal-std12', 'title': 'Normal ($\\mu=30$, $\\sigma=12$, CV=0.40)'},
    {'std': 15, 'mean': 30, 'name': 'normal-std15', 'title': 'Normal ($\\mu=30$, $\\sigma=15$, CV=0.50)'},
    {'std': 18, 'mean': 30, 'name': 'normal-std18', 'title': 'Normal ($\\mu=30$, $\\sigma=18$, CV=0.60)'},
]

# ============================================================================
# SOFT RANDOM COMBINATION CONFIGURATIONS - Clean titles (H values only)
# ============================================================================
SOFTRANDOM_COMBINATION_CONFIGS = {
    'two': [
        {'name': 'two_combination_H64_H512_pair_1', 'title': 'Soft Random ($H=2^6, 2^9$)', 'h_values': [64, 512]},
        {'name': 'two_combination_H512_H4096_pair_2', 'title': 'Soft Random ($H=2^9, 2^{12}$)', 'h_values': [512, 4096]},
        {'name': 'two_combination_H4096_H32768_pair_3', 'title': 'Soft Random ($H=2^{12}, 2^{15}$)', 'h_values': [4096, 32768]},
        {'name': 'two_combination_H32768_H262144_pair_4', 'title': 'Soft Random ($H=2^{15}, 2^{18}$)', 'h_values': [32768, 262144]},
    ],
    'three': [
        {'name': 'three_combination_H64_H512_H4096_triplet_1', 'title': 'Soft Random ($H=2^6, 2^9, 2^{12}$)', 'h_values': [64, 512, 4096]},
        {'name': 'three_combination_H512_H4096_H32768_triplet_2', 'title': 'Soft Random ($H=2^9, 2^{12}, 2^{15}$)', 'h_values': [512, 4096, 32768]},
        {'name': 'three_combination_H4096_H32768_H262144_triplet_3', 'title': 'Soft Random ($H=2^{12}, 2^{15}, 2^{18}$)', 'h_values': [4096, 32768, 262144]},
    ],
    'four': [
        {'name': 'four_combination_H64_H512_H4096_H32768_quadruplet_1', 'title': 'Soft Random ($H=2^6, 2^9, 2^{12}, 2^{15}$)', 'h_values': [64, 512, 4096, 32768]},
        {'name': 'four_combination_H512_H4096_H32768_H262144_quadruplet_2', 'title': 'Soft Random ($H=2^9, 2^{12}, 2^{15}, 2^{18}$)', 'h_values': [512, 4096, 32768, 262144]},
    ],
}

X_TICKS = list(range(20, 42, 2))
X_LIMITS = (19, 41)

# ============================================================================
# HIGH CONTRAST COLOR SCHEME
# ============================================================================
COLORS = {
    # Our algorithms - bright colors
    'Dynamic': '#D62728',       # Red
    'Dynamic_BAL': '#9467BD',   # Purple
    'RFDynamic': '#FF7F0E',     # Orange
    
    # Clairvoyant baselines
    'BAL': '#1F77B4',           # Blue
    'SRPT': '#2CA02C',          # Green
    'FCFS': '#17BECF',          # Cyan
    'SJF': '#E377C2',           # Pink
    'RR': '#7F7F7F',            # Gray
    
    # Non-clairvoyant baselines
    'RMLF': '#2CA02C',          # Green
    'MLFQ': '#1F77B4',          # Blue
    'SETF': '#BCBD22',          # Yellow-green
}

MARKERS = {
    'Dynamic': 'o',      # Circle
    'Dynamic_BAL': 's',  # Square
    'RFDynamic': '^',    # Triangle up
    'BAL': 'D',          # Diamond
    'SRPT': 'v',         # Triangle down
    'FCFS': 'p',         # Pentagon
    'SJF': 'h',          # Hexagon
    'RR': '*',           # Star
    'RMLF': 'v',         # Triangle down
    'MLFQ': 'D',         # Diamond
    'SETF': 'h',         # Hexagon
}

OFFSETS = {
    'Dynamic': -0.3,
    'Dynamic_BAL': 0.3,
    'RFDynamic': 0.0,
    'BAL': 0.0, 'SRPT': 0.0, 'FCFS': 0.0, 'SJF': 0.0, 'RR': 0.0,
    'RMLF': 0.0, 'MLFQ': 0.0, 'SETF': 0.0,
}

# ============================================================================
# STYLE DEFINITIONS
# ============================================================================
def get_our_algo_style(color):
    """Our algorithms: solid + filled + thick"""
    return {
        'linestyle': '-', 
        'linewidth': 3.5, 
        'markersize': 12,
        'markerfacecolor': color,
        'markeredgecolor': 'black',
        'markeredgewidth': 1.2,
    }

def get_primary_style():
    """Primary comparison: solid + filled + medium"""
    return {
        'linestyle': '-', 
        'linewidth': 2.8, 
        'markersize': 10,
        'markeredgecolor': 'black', 
        'markeredgewidth': 0.8,
    }

def get_secondary_style():
    """Other baselines: dashed + hollow + thin"""
    return {
        'linestyle': '--', 
        'linewidth': 1.5, 
        'markersize': 8,
        'markerfacecolor': 'white',
        'markeredgewidth': 1.5,
        'alpha': 0.85
    }

def apply_offset(x_data, algo_name):
    offset = OFFSETS.get(algo_name, 0.0)
    return np.array(x_data) + offset

def setup_plot_style():
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (10, 6), 'font.size': 11, 'axes.labelsize': 13,
        'axes.titlesize': 13, 'legend.fontsize': 9, 'axes.grid': True,
        'grid.alpha': 0.3, 'savefig.dpi': 300, 'savefig.bbox': 'tight', 'font.family': 'serif',
    })


# ============================================================================
# DATA LOADING - AVG30
# ============================================================================
def load_baseline_l2norm(algorithm: str) -> Optional[pd.DataFrame]:
    """Load L2-norm data for baseline algorithm from avg30_result."""
    algo_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "avg30_result")
    if not os.path.exists(algo_dir):
        return None
    
    all_data = []
    for iat in INTER_ARRIVAL_TIMES:
        for pat in [f"{iat}_{algorithm}_1_result.csv", f"{iat}_{algorithm}_result.csv"]:
            path = os.path.join(algo_dir, pat)
            if os.path.exists(path):
                try:
                    all_data.append(pd.read_csv(path))
                except:
                    pass
                break
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    l2_col = f'{algorithm}_L2_norm_flow_time'
    if l2_col not in combined.columns:
        return None
    
    result = pd.DataFrame({
        'arrival_rate': combined['Mean_inter_arrival_time'],
        'bp_L': combined['bp_parameter_L'],
        'bp_H': combined['bp_parameter_H'],
        'L2_norm': combined[l2_col],
    })
    logger.info(f"Loaded avg30: {algorithm} ({len(result)} rows)")
    return result


def load_dynamic_l2norm(algorithm: str, k: int, batch_size: int = DEFAULT_BATCH_SIZE) -> Optional[pd.DataFrame]:
    """Load L2-norm data for Dynamic algorithm from avg30_result."""
    algo_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "avg30_result")
    if not os.path.exists(algo_dir):
        return None

    all_files = glob.glob(os.path.join(algo_dir, "*.csv"))
    if not all_files:
        return None

    all_data = []
    for f in sorted(all_files):
        try:
            df = pd.read_csv(f)
            all_data.append(df)
        except:
            pass

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)

    # Find L2 column for k (lookback) - try exact batch_size first, then any njobs
    l2_col = None
    patterns = [
        f'{algorithm}_njobs{batch_size}_mode{k}_L2_norm_flow_time',
        f'{algorithm}_njobs{batch_size}_k{k}_L2_norm_flow_time',
    ]
    for p in patterns:
        if p in combined.columns:
            l2_col = p
            break

    # Fallback: try any njobs value with exact mode/k match
    if l2_col is None:

        # Match _mode{k}_ exactly (not mode16 when k=1)
        mode_pattern = re.compile(
            rf'^{re.escape(algorithm)}_njobs\d+_mode{k}_L2_norm_flow_time$'
        )
        k_pattern = re.compile(
            rf'^{re.escape(algorithm)}_njobs\d+_k{k}_L2_norm_flow_time$'
        )
        for c in combined.columns:
            if mode_pattern.match(c) or k_pattern.match(c):
                l2_col = c
                break

    if l2_col is None:
        return None

    required = ['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H']
    if not all(c in combined.columns for c in required):
        return None

    result = combined.groupby(['Mean_inter_arrival_time', 'bp_parameter_L', 'bp_parameter_H'])[l2_col].mean().reset_index()
    result = result.rename(columns={
        'Mean_inter_arrival_time': 'arrival_rate',
        'bp_parameter_L': 'bp_L',
        'bp_parameter_H': 'bp_H',
        l2_col: 'L2_norm'
    })

    logger.info(f"Loaded avg30: {algorithm} k={k} B={batch_size} ({len(result)} rows)")
    return result


def load_selection_data(algorithm: str, k: int, batch_size: int = DEFAULT_BATCH_SIZE) -> Optional[pd.DataFrame]:
    """Load algorithm selection data from Analysis folder."""
    config = DYNAMIC_ALGORITHMS[algorithm]

    # Try new k-based path first, then legacy mode-based path
    k_dir = os.path.join(ANALYSIS_PATH, config['analysis_dir'], 'avg_30', f'k_{k}')
    mode_dir = os.path.join(ANALYSIS_PATH, config['analysis_dir'], 'avg_30', f'mode_{k}')
    analysis_dir = k_dir if os.path.exists(k_dir) else mode_dir
    if not os.path.exists(analysis_dir):
        return None

    # Try new k-based filename first, then legacy mode-based
    patterns_to_try = [
        os.path.join(analysis_dir, f"{config['file_prefix']}_avg_30_nJobsPerRound_{batch_size}_k_{k}_round_*.csv"),
        os.path.join(analysis_dir, f"{config['file_prefix']}_avg_30_nJobsPerRound_{batch_size}_mode_{k}_round_*.csv"),
    ]
    files = []
    for pat in patterns_to_try:
        files = sorted(glob.glob(pat))[:NUM_ROUNDS]
        if files:
            break
    if not files:
        return None

    try:
        combined = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        eff_col, fair_col = config['efficiency_col'], config['fairness_col']
        if eff_col not in combined.columns:
            return None

        result = combined.groupby(['arrival_rate', 'bp_L', 'bp_H']).agg({eff_col: 'mean', fair_col: 'mean'}).reset_index()
        result = result.rename(columns={eff_col: 'efficiency_pct', fair_col: 'fairness_pct'})
        return result
    except:
        return None


# ============================================================================
# DATA LOADING - SOFT RANDOM COMBINATION
# ============================================================================
def load_baseline_softrandom(algorithm: str, combo_name: str) -> Optional[pd.DataFrame]:
    """Load baseline data for soft random combination with 5-round averaging."""
    folder = 'Bounded_Pareto_combination_softrandom_result'
    
    if combo_name.startswith('two_'):
        subfolder = 'two_result'
    elif combo_name.startswith('three_'):
        subfolder = 'three_result'
    elif combo_name.startswith('four_'):
        subfolder = 'four_result'
    else:
        return None
    
    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", folder, subfolder)
    if not os.path.exists(base_dir):
        return None
    
    all_data = []
    for round_num in range(1, 6):
        patterns = [
            f"{combo_name}_{algorithm}_{round_num}_result.csv",
            f"{combo_name}_{algorithm}_result_{round_num}.csv",
        ]
        for pat in patterns:
            fpath = os.path.join(base_dir, pat)
            if os.path.exists(fpath):
                try:
                    df = pd.read_csv(fpath)
                    all_data.append(df)
                except:
                    pass
                break
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    l2_col = f'{algorithm}_L2_norm_flow_time'
    
    if l2_col not in combined.columns:
        l2_cols = [c for c in combined.columns if 'l2' in c.lower() and 'norm' in c.lower()]
        if l2_cols:
            l2_col = l2_cols[0]
        else:
            return None
    
    result = combined.groupby('frequency')[l2_col].mean().reset_index()
    result = result.rename(columns={'frequency': 'arrival_rate', l2_col: 'L2_norm'})
    
    logger.info(f"Loaded softrandom: {algorithm} {combo_name} ({len(result)} rows)")
    return result


def load_dynamic_softrandom(algorithm: str, combo_name: str, k: int, batch_size: int = DEFAULT_BATCH_SIZE) -> Optional[pd.DataFrame]:
    """Load Dynamic algorithm data for soft random combination with 5-round averaging."""
    folder = 'Bounded_Pareto_combination_softrandom_result'

    if combo_name.startswith('two_'):
        subfolder = 'two_result'
    elif combo_name.startswith('three_'):
        subfolder = 'three_result'
    elif combo_name.startswith('four_'):
        subfolder = 'four_result'
    else:
        return None

    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", folder, subfolder)
    if not os.path.exists(base_dir):
        return None

    all_data = []
    for round_num in range(1, 6):
        file_patterns = [
            f"{combo_name}_{algorithm}_njobs{batch_size}_{round_num}.csv",
            f"{combo_name}_{algorithm}_{round_num}.csv",
        ]
        for pat in file_patterns:
            fpath = os.path.join(base_dir, pat)
            if os.path.exists(fpath):
                try:
                    df = pd.read_csv(fpath)
                    all_data.append(df)
                except:
                    pass
                break

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)

    # Find L2 column: try exact batch_size first, then any njobs
    l2_col = None
    col_patterns = [
        f'{algorithm}_njobs{batch_size}_mode{k}_L2_norm_flow_time',
        f'{algorithm}_njobs{batch_size}_k{k}_L2_norm_flow_time',
    ]
    for p in col_patterns:
        if p in combined.columns:
            l2_col = p
            break

    if l2_col is None:

        mode_pattern = re.compile(
            rf'^{re.escape(algorithm)}_njobs\d+_mode{k}_L2_norm_flow_time$'
        )
        for c in combined.columns:
            if mode_pattern.match(c):
                l2_col = c
                break

    if l2_col is None:
        return None

    result = combined.groupby('frequency')[l2_col].mean().reset_index()
    result = result.rename(columns={'frequency': 'arrival_rate', l2_col: 'L2_norm'})

    logger.info(f"Loaded softrandom: {algorithm} k={k} {combo_name} ({len(result)} rows)")
    return result


def load_dynamic_softrandom_all_lookbacks(algorithm: str, combo_name: str) -> Dict[int, pd.DataFrame]:
    """Load all lookback values for Dynamic algorithm."""
    return {k: df for k in ALL_LOOKBACKS if (df := load_dynamic_softrandom(algorithm, combo_name, k)) is not None}


def load_selection_data_softrandom(algorithm: str, combo_name: str, k: int, batch_size: int = DEFAULT_BATCH_SIZE) -> Optional[pd.DataFrame]:
    """Load algorithm selection data for soft random combination."""
    config = DYNAMIC_ALGORITHMS[algorithm]

    if combo_name.startswith('two_'):
        subfolder = 'two_result'
    elif combo_name.startswith('three_'):
        subfolder = 'three_result'
    elif combo_name.startswith('four_'):
        subfolder = 'four_result'
    else:
        return None

    # Try k-based path first, then legacy mode-based
    for folder_name in [f'k_{k}', f'mode_{k}']:
        analysis_dir = os.path.join(ANALYSIS_PATH, config['analysis_dir'],
                                    'Bounded_Pareto_combination_softrandom_result', subfolder, folder_name)
        if not os.path.exists(analysis_dir):
            continue

        for file_tag in [f'k_{k}', f'mode_{k}']:
            pattern = os.path.join(analysis_dir, f"{combo_name}_{config['file_prefix']}*{file_tag}*.csv")
            files = sorted(glob.glob(pattern))[:NUM_ROUNDS]
            if files:
                try:
                    combined = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
                    eff_col, fair_col = config['efficiency_col'], config['fairness_col']
                    if eff_col in combined.columns and fair_col in combined.columns:
                        if 'frequency' in combined.columns:
                            result = combined.groupby('frequency').agg({eff_col: 'mean', fair_col: 'mean'}).reset_index()
                            result = result.rename(columns={'frequency': 'arrival_rate', eff_col: 'efficiency_pct', fair_col: 'fairness_pct'})
                            logger.info(f"Loaded selection softrandom: {algorithm} {combo_name} k={k}")
                            return result
                except Exception as e:
                    logger.warning(f"Failed to load selection data: {e}")

    # Try loading from result files and computing selection percentages
    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result",
                           'Bounded_Pareto_combination_softrandom_result', subfolder)
    if not os.path.exists(base_dir):
        return None

    all_data = []
    for round_num in range(1, 6):
        file_patterns = [
            f"{combo_name}_{algorithm}_njobs{batch_size}_{round_num}.csv",
            f"{combo_name}_{algorithm}_{round_num}.csv",
        ]
        for pat in file_patterns:
            fpath = os.path.join(base_dir, pat)
            if os.path.exists(fpath):
                try:
                    df = pd.read_csv(fpath)
                    all_data.append(df)
                except:
                    pass
                break

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)
    eff_col, fair_col = config['efficiency_col'], config['fairness_col']

    # Try k-based and legacy mode-based column patterns
    col_patterns = [
        (eff_col, fair_col),
        (f'{algorithm}_njobs{batch_size}_k{k}_SRPT_pct', f'{algorithm}_njobs{batch_size}_k{k}_FCFS_pct'),
        (f'{algorithm}_k{k}_SRPT_pct', f'{algorithm}_k{k}_FCFS_pct'),
        (f'{algorithm}_njobs{batch_size}_mode{k}_SRPT_pct', f'{algorithm}_njobs{batch_size}_mode{k}_FCFS_pct'),
        (f'{algorithm}_mode{k}_SRPT_pct', f'{algorithm}_mode{k}_FCFS_pct'),
        (f'{algorithm}_njobs{batch_size}_k{k}_BAL_pct', f'{algorithm}_njobs{batch_size}_k{k}_FCFS_pct'),
        (f'{algorithm}_njobs{batch_size}_k{k}_RMLF_pct', f'{algorithm}_njobs{batch_size}_k{k}_FCFS_pct'),
    ]

    for eff_try, fair_try in col_patterns:
        if eff_try in combined.columns and fair_try in combined.columns:
            if 'frequency' in combined.columns:
                result = combined.groupby('frequency').agg({eff_try: 'mean', fair_try: 'mean'}).reset_index()
                result = result.rename(columns={'frequency': 'arrival_rate', eff_try: 'efficiency_pct', fair_try: 'fairness_pct'})
                logger.info(f"Loaded selection softrandom: {algorithm} {combo_name} k={k}")
                return result

    return None


# ============================================================================
# FILTER FUNCTIONS
# ============================================================================
def filter_bp(df: pd.DataFrame, H: float) -> pd.DataFrame:
    return df[(df['bp_L'] < df['bp_H']) & np.isclose(df['bp_H'], H, rtol=0.05)].sort_values('arrival_rate')

def filter_normal(df: pd.DataFrame, mean: float, std: float) -> pd.DataFrame:
    return df[(df['bp_L'] > df['bp_H']) & np.isclose(df['bp_L'], mean, rtol=0.05) & np.isclose(df['bp_H'], std, rtol=0.05)].sort_values('arrival_rate')

def _get_short_name(combo_name: str) -> str:
    """Extract H values for clean filename: two_combination_H64_H512_pair_1 -> H64_H512"""
    import re
    h_values = re.findall(r'H\d+', combo_name)
    return '_'.join(h_values) if h_values else combo_name


# ============================================================================
# FIND BEST MODE
# ============================================================================
def find_common_best_k() -> int:
    """Find common best lookback k using softrandom data."""
    test_combo = SOFTRANDOM_COMBINATION_CONFIGS['two'][0]['name']

    best_ks = {}
    for algo in DYNAMIC_ALGORITHMS:
        k_data = load_dynamic_softrandom_all_lookbacks(algo, test_combo)

        if LOOKBACK_ALL not in k_data:
            best_ks[algo] = 16
            continue

        k_all_df = k_data[LOOKBACK_ALL]
        best, min_diff = 16, float('inf')

        for k in LOOKBACKS:
            if k not in k_data:
                continue
            merged = k_all_df.merge(k_data[k], on='arrival_rate', suffixes=('_all', '_k'))
            if len(merged) > 0:
                diff = np.mean(np.abs(merged['L2_norm_all'] - merged['L2_norm_k']))
                if diff < min_diff:
                    min_diff, best = diff, k

        best_ks[algo] = best
        logger.info(f"Best k for {algo}: {best}")

    # Majority vote
    from collections import Counter
    votes = Counter(best_ks.values())
    common_k = votes.most_common(1)[0][0]

    logger.info(f"Common k selected: {common_k}")
    return common_k


# ============================================================================
# AVG30 - ALGORITHM SELECTION FIGURES (Clearer visualization)
# ============================================================================
def generate_avg30_algorithm_selection_figures(common_k: int):
    """Generate algorithm selection figures for avg30 data - clearer visualization."""
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_algorithm_selection")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating avg30 Algorithm Selection Figures ===")

    # Load data
    data_c = {algo: load_selection_data(algo, common_k) for algo in ['Dynamic', 'Dynamic_BAL']}
    data_c = {k: v for k, v in data_c.items() if v is not None}

    data_nc = load_selection_data('RFDynamic', common_k)
    
    # Bounded Pareto
    for config in BP_CONFIGS:
        _gen_clairvoyant_selection_bp(data_c, config, output_dir)
        _gen_nonclairvoyant_selection_bp(data_nc, config, output_dir)
    
    # Normal
    for config in NORMAL_CONFIGS:
        _gen_clairvoyant_selection_normal(data_c, config, output_dir)
        _gen_nonclairvoyant_selection_normal(data_nc, config, output_dir)


def _gen_clairvoyant_selection_bp(data: Dict, config: dict, output_dir: str):
    """Clairvoyant Algorithm Selection - BP with subplots for each algorithm"""
    H, name, title = config['H'], config['name'], config['title']
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle(f'Clairvoyant Algorithm Selection\n{title}', fontweight='bold', fontsize=13)
    
    algo_list = ['Dynamic', 'Dynamic_BAL']
    
    for idx, algo in enumerate(algo_list):
        ax = axes[idx]
        
        if algo not in data:
            ax.set_visible(False)
            continue
        
        df = filter_bp(data[algo], H)
        if len(df) == 0:
            ax.set_visible(False)
            continue
        
        eff_name = DYNAMIC_ALGORITHMS[algo]['efficiency_name']
        color = COLORS[algo]
        
        # Efficiency (solid, thick, filled)
        ax.plot(df['arrival_rate'], df['efficiency_pct'],
                marker=MARKERS[algo], color=color,
                linestyle='-', linewidth=3.0, markersize=10,
                markerfacecolor=color, markeredgecolor='black', markeredgewidth=1.0,
                label=f'{eff_name}')
        
        # FCFS (dashed, thin, hollow)
        ax.plot(df['arrival_rate'], df['fairness_pct'],
                marker=MARKERS[algo], color=color,
                linestyle='--', linewidth=2.0, markersize=8,
                markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
                label='FCFS', alpha=0.8)
        
        ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=11)
        if idx == 0:
            ax.set_ylabel('Algorithm Selection (%)', fontweight='bold', fontsize=11)
        ax.set_title(algo, fontweight='bold', fontsize=12)
        ax.legend(loc='center right', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 105)
        ax.set_xticks(X_TICKS)
        ax.set_xlim(X_LIMITS)
        ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_algo_selection_clairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_algo_selection_clairvoyant_{name}.pdf")


def _gen_clairvoyant_selection_normal(data: Dict, config: dict, output_dir: str):
    """Clairvoyant Algorithm Selection - Normal with subplots for each algorithm"""
    std, mean, name, title = config['std'], config['mean'], config['name'], config['title']
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle(f'Clairvoyant Algorithm Selection\n{title}', fontweight='bold', fontsize=13)
    
    algo_list = ['Dynamic', 'Dynamic_BAL']
    
    for idx, algo in enumerate(algo_list):
        ax = axes[idx]
        
        if algo not in data:
            ax.set_visible(False)
            continue
        
        df = filter_normal(data[algo], mean, std)
        if len(df) == 0:
            ax.set_visible(False)
            continue
        
        eff_name = DYNAMIC_ALGORITHMS[algo]['efficiency_name']
        color = COLORS[algo]
        
        # FCFS (solid, thick, filled) - dominant in normal
        ax.plot(df['arrival_rate'], df['fairness_pct'],
                marker=MARKERS[algo], color=color,
                linestyle='-', linewidth=3.0, markersize=10,
                markerfacecolor=color, markeredgecolor='black', markeredgewidth=1.0,
                label='FCFS')
        
        # Efficiency (dashed, thin, hollow)
        ax.plot(df['arrival_rate'], df['efficiency_pct'],
                marker=MARKERS[algo], color=color,
                linestyle='--', linewidth=2.0, markersize=8,
                markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
                label=eff_name, alpha=0.8)
        
        ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=11)
        if idx == 0:
            ax.set_ylabel('Algorithm Selection (%)', fontweight='bold', fontsize=11)
        ax.set_title(algo, fontweight='bold', fontsize=12)
        ax.legend(loc='center right', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 105)
        ax.set_xticks(X_TICKS)
        ax.set_xlim(X_LIMITS)
        ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_algo_selection_clairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_algo_selection_clairvoyant_{name}.pdf")


def _gen_nonclairvoyant_selection_bp(data: Optional[pd.DataFrame], config: dict, output_dir: str):
    """Non-clairvoyant Algorithm Selection - BP"""
    if data is None:
        return
    
    H, name, title = config['H'], config['name'], config['title']
    df = filter_bp(data, H)
    if len(df) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    color = COLORS['RFDynamic']
    
    # RMLF (solid, thick, filled)
    ax.plot(df['arrival_rate'], df['efficiency_pct'],
            marker=MARKERS['RFDynamic'], color=color,
            linestyle='-', linewidth=3.0, markersize=10,
            markerfacecolor=color, markeredgecolor='black', markeredgewidth=1.0,
            label='RMLF')
    
    # FCFS (dashed, thin, hollow)
    ax.plot(df['arrival_rate'], df['fairness_pct'],
            marker=MARKERS['RFDynamic'], color=color,
            linestyle='--', linewidth=2.0, markersize=8,
            markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
            label='FCFS', alpha=0.8)
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('Algorithm Selection (%)', fontweight='bold', fontsize=12)
    ax.set_title(f'Non-Clairvoyant Algorithm Selection (RFDynamic)\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='center right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-5, 105)
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_algo_selection_nonclairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_algo_selection_nonclairvoyant_{name}.pdf")


def _gen_nonclairvoyant_selection_normal(data: Optional[pd.DataFrame], config: dict, output_dir: str):
    """Non-clairvoyant Algorithm Selection - Normal"""
    if data is None:
        return
    
    std, mean, name, title = config['std'], config['mean'], config['name'], config['title']
    df = filter_normal(data, mean, std)
    if len(df) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    color = COLORS['RFDynamic']
    
    # FCFS (solid, thick, filled) - dominant in normal
    ax.plot(df['arrival_rate'], df['fairness_pct'],
            marker=MARKERS['RFDynamic'], color=color,
            linestyle='-', linewidth=3.0, markersize=10,
            markerfacecolor=color, markeredgecolor='black', markeredgewidth=1.0,
            label='FCFS')
    
    # RMLF (dashed, thin, hollow)
    ax.plot(df['arrival_rate'], df['efficiency_pct'],
            marker=MARKERS['RFDynamic'], color=color,
            linestyle='--', linewidth=2.0, markersize=8,
            markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
            label='RMLF', alpha=0.8)
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('Algorithm Selection (%)', fontweight='bold', fontsize=12)
    ax.set_title(f'Non-Clairvoyant Algorithm Selection (RFDynamic)\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='center right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-5, 105)
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_algo_selection_nonclairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_algo_selection_nonclairvoyant_{name}.pdf")


# ============================================================================
# SOFT RANDOM - ALGORITHM SELECTION FIGURES
# ============================================================================
def generate_softrandom_algorithm_selection_figures(common_k: int):
    """Generate algorithm selection figures for soft random combinations."""
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_algorithm_selection_softrandom")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating Soft Random Algorithm Selection Figures ===")

    for combo_type, configs in SOFTRANDOM_COMBINATION_CONFIGS.items():
        for config in configs:
            combo_name = config['name']
            title = config['title']
            short_name = _get_short_name(combo_name)

            # Load clairvoyant selection data
            data_c = {}
            for algo in ['Dynamic', 'Dynamic_BAL']:
                df = load_selection_data_softrandom(algo, combo_name, common_k)
                if df is not None:
                    data_c[algo] = df

            # Load non-clairvoyant selection data
            data_nc = load_selection_data_softrandom('RFDynamic', combo_name, common_k)
            
            # Generate figures
            if data_c:
                _gen_softrandom_clairvoyant_selection(data_c, title, short_name, output_dir)
            if data_nc is not None:
                _gen_softrandom_nonclairvoyant_selection(data_nc, title, short_name, output_dir)


def _gen_softrandom_clairvoyant_selection(data: Dict, title: str, short_name: str, output_dir: str):
    """Generate clairvoyant algorithm selection figure for soft random."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle(f'Clairvoyant Algorithm Selection\n{title}', fontweight='bold', fontsize=13)
    
    algo_list = ['Dynamic', 'Dynamic_BAL']
    
    for idx, algo in enumerate(algo_list):
        ax = axes[idx]
        
        if algo not in data:
            ax.set_visible(False)
            continue
        
        df = data[algo]
        if len(df) == 0:
            ax.set_visible(False)
            continue
        
        eff_name = DYNAMIC_ALGORITHMS[algo]['efficiency_name']
        color = COLORS[algo]
        
        # Efficiency (solid, thick, filled)
        ax.plot(df['arrival_rate'], df['efficiency_pct'],
                marker=MARKERS[algo], color=color,
                linestyle='-', linewidth=3.0, markersize=10,
                markerfacecolor=color, markeredgecolor='black', markeredgewidth=1.0,
                label=f'{eff_name}')
        
        # FCFS (dashed, thin, hollow)
        ax.plot(df['arrival_rate'], df['fairness_pct'],
                marker=MARKERS[algo], color=color,
                linestyle='--', linewidth=2.0, markersize=8,
                markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
                label='FCFS', alpha=0.8)
        
        ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=11)
        if idx == 0:
            ax.set_ylabel('Algorithm Selection (%)', fontweight='bold', fontsize=11)
        ax.set_title(algo, fontweight='bold', fontsize=12)
        ax.legend(loc='center right', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 105)
        ax.set_xticks(X_TICKS)
        ax.set_xlim(X_LIMITS)
        ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_algo_selection_clairvoyant_{short_name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_algo_selection_clairvoyant_{short_name}.pdf")


def _gen_softrandom_nonclairvoyant_selection(data: pd.DataFrame, title: str, short_name: str, output_dir: str):
    """Generate non-clairvoyant algorithm selection figure for soft random."""
    fig, ax = plt.subplots(figsize=(10, 6))
    color = COLORS['RFDynamic']
    
    # RMLF (solid, thick, filled)
    ax.plot(data['arrival_rate'], data['efficiency_pct'],
            marker=MARKERS['RFDynamic'], color=color,
            linestyle='-', linewidth=3.0, markersize=10,
            markerfacecolor=color, markeredgecolor='black', markeredgewidth=1.0,
            label='RMLF')
    
    # FCFS (dashed, thin, hollow)
    ax.plot(data['arrival_rate'], data['fairness_pct'],
            marker=MARKERS['RFDynamic'], color=color,
            linestyle='--', linewidth=2.0, markersize=8,
            markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
            label='FCFS', alpha=0.8)
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('Algorithm Selection (%)', fontweight='bold', fontsize=12)
    ax.set_title(f'Non-Clairvoyant Algorithm Selection (RFDynamic)\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='center right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-5, 105)
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_algo_selection_nonclairvoyant_{short_name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_algo_selection_nonclairvoyant_{short_name}.pdf")


# ============================================================================
# SOFT RANDOM - MODE COMPARISON FIGURES
# ============================================================================
def generate_softrandom_lookback_comparison_figures():
    """Generate lookback (k) comparison figures for each algorithm in each soft random combination.
    X-axis: Coherence time (2 to 2^16), Y-axis: L²-norm
    One figure per algorithm per combination, showing all k values.
    """
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_lookback_comparison_softrandom")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating Soft Random Lookback Comparison Figures ===")

    # Lookback colors and styles
    k_colors = {
        1: '#1f77b4',   # Blue
        2: '#ff7f0e',   # Orange
        4: '#2ca02c',   # Green
        8: '#d62728',   # Red
        16: '#9467bd',  # Purple
        LOOKBACK_ALL: '#8c564b',  # Brown - k=all
    }
    k_markers = {1: 'o', 2: 's', 4: '^', 8: 'D', 16: 'v', LOOKBACK_ALL: 'p'}
    k_labels = {1: '$k=1$', 2: '$k=2$', 4: '$k=4$', 8: '$k=8$', 16: '$k=16$', LOOKBACK_ALL: '$k=\\mathrm{all}$'}

    for combo_type, configs in SOFTRANDOM_COMBINATION_CONFIGS.items():
        for config in configs:
            combo_name = config['name']
            title = config['title']
            short_name = _get_short_name(combo_name)

            for algo in DYNAMIC_ALGORITHMS.keys():
                k_data = load_dynamic_softrandom_all_lookbacks(algo, combo_name)

                if not k_data:
                    logger.warning(f"No data for {algo} {combo_name}")
                    continue

                fig, ax = plt.subplots(figsize=(12, 7))

                for k_val in sorted(k_data.keys()):
                    df = k_data[k_val]
                    if df is None or len(df) == 0:
                        continue

                    color = k_colors.get(k_val, 'gray')
                    marker = k_markers.get(k_val, 'o')
                    label = k_labels.get(k_val, f'$k={k_val}$')

                    ax.plot(df['arrival_rate'], df['L2_norm'],
                            marker=marker, color=color,
                            linestyle='-', linewidth=2.5, markersize=8,
                            markerfacecolor=color, markeredgecolor='black', markeredgewidth=0.8,
                            label=label)

                ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=12)
                ax.set_ylabel('$L^2$-norm of Flow Time', fontweight='bold', fontsize=12)
                ax.set_title(f'{algo} Lookback Comparison\n{title}', fontweight='bold', fontsize=13)
                ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
                ax.grid(True, alpha=0.3)
                ax.set_xscale('log', base=2)

                x_ticks = [2**i for i in range(1, 17)]
                ax.set_xticks(x_ticks)
                ax.set_xticklabels([f'$2^{{{i}}}$' for i in range(1, 17)])
                ax.set_xlim(2, 2**16)

                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, f"fig_lookback_comparison_{algo}_{short_name}.pdf"), dpi=300)
                plt.close()
                logger.info(f"Generated: fig_lookback_comparison_{algo}_{short_name}.pdf")


# ============================================================================
# AVG30 - L2-NORM FIGURES
# ============================================================================
def generate_avg30_l2norm_figures(common_k: int):
    """Generate L2-norm figures for avg30 data."""
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_l2norm_avg30")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating avg30 L²-norm Figures ===")

    # Load baselines
    baseline_c = {algo: load_baseline_l2norm(algo) for algo in CLAIRVOYANT_BASELINES}
    baseline_c = {k: v for k, v in baseline_c.items() if v is not None}

    baseline_nc = {algo: load_baseline_l2norm(algo) for algo in NON_CLAIRVOYANT_BASELINES}
    baseline_nc = {k: v for k, v in baseline_nc.items() if v is not None}

    # Load Dynamic
    dynamic_c = {algo: load_dynamic_l2norm(algo, common_k) for algo in ['Dynamic', 'Dynamic_BAL']}
    dynamic_c = {k: v for k, v in dynamic_c.items() if v is not None}

    dynamic_nc = load_dynamic_l2norm('RFDynamic', common_k)
    
    # Generate BP figures
    for config in BP_CONFIGS:
        _gen_clairvoyant_l2norm_bp(baseline_c, dynamic_c, config, output_dir)
        _gen_nonclairvoyant_l2norm_bp(baseline_nc, dynamic_nc, config, output_dir)
    
    # Generate Normal figures
    for config in NORMAL_CONFIGS:
        _gen_clairvoyant_l2norm_normal(baseline_c, dynamic_c, config, output_dir)
        _gen_nonclairvoyant_l2norm_normal(baseline_nc, dynamic_nc, config, output_dir)


def _gen_clairvoyant_l2norm_bp(baseline: Dict, dynamic: Dict, config: dict, output_dir: str):
    """Clairvoyant L2-norm - BP"""
    H, name, title = config['H'], config['name'], config['title']
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    # Secondary baselines (dashed + hollow)
    for algo in ['BAL', 'FCFS', 'SJF', 'RR']:
        if algo in baseline:
            df = filter_bp(baseline[algo], H)
            if len(df) > 0:
                ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS[algo],
                        color=COLORS[algo], label=algo, zorder=1, **get_secondary_style())
    
    # Primary baseline SRPT (solid + filled)
    if 'SRPT' in baseline:
        df = filter_bp(baseline['SRPT'], H)
        if len(df) > 0:
            ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS['SRPT'],
                    color=COLORS['SRPT'], label='SRPT', zorder=5, **get_primary_style())
    
    # Our algorithms (solid + filled + thick)
    for algo in ['Dynamic', 'Dynamic_BAL']:
        if algo in dynamic:
            df = filter_bp(dynamic[algo], H)
            if len(df) > 0:
                x_data = apply_offset(df['arrival_rate'].values, algo)
                ax.plot(x_data, df['L2_norm'], marker=MARKERS[algo],
                        color=COLORS[algo], label=algo, zorder=10, **get_our_algo_style(COLORS[algo]))
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
    ax.set_title(f'Clairvoyant $\\ell_2$-Norm Comparison\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_l2norm_clairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_l2norm_clairvoyant_{name}.pdf")


def _gen_clairvoyant_l2norm_normal(baseline: Dict, dynamic: Dict, config: dict, output_dir: str):
    """Clairvoyant L2-norm - Normal"""
    std, mean, name, title = config['std'], config['mean'], config['name'], config['title']
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    # Secondary baselines
    for algo in ['BAL', 'SRPT', 'SJF', 'RR']:
        if algo in baseline:
            df = filter_normal(baseline[algo], mean, std)
            if len(df) > 0:
                ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS[algo],
                        color=COLORS[algo], label=algo, zorder=1, **get_secondary_style())
    
    # Primary baseline FCFS
    if 'FCFS' in baseline:
        df = filter_normal(baseline['FCFS'], mean, std)
        if len(df) > 0:
            ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS['FCFS'],
                    color=COLORS['FCFS'], label='FCFS', zorder=5, **get_primary_style())
    
    # Our algorithms
    for algo in ['Dynamic', 'Dynamic_BAL']:
        if algo in dynamic:
            df = filter_normal(dynamic[algo], mean, std)
            if len(df) > 0:
                x_data = apply_offset(df['arrival_rate'].values, algo)
                ax.plot(x_data, df['L2_norm'], marker=MARKERS[algo],
                        color=COLORS[algo], label=algo, zorder=10, **get_our_algo_style(COLORS[algo]))
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
    ax.set_title(f'Clairvoyant $\\ell_2$-Norm Comparison\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_l2norm_clairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_l2norm_clairvoyant_{name}.pdf")


def _gen_nonclairvoyant_l2norm_bp(baseline: Dict, dynamic: Optional[pd.DataFrame], config: dict, output_dir: str):
    """Non-clairvoyant L2-norm - BP"""
    H, name, title = config['H'], config['name'], config['title']
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    # Secondary baselines
    for algo in ['MLFQ', 'FCFS', 'SETF', 'RR']:
        if algo in baseline:
            df = filter_bp(baseline[algo], H)
            if len(df) > 0:
                ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS[algo],
                        color=COLORS[algo], label=algo, zorder=1, **get_secondary_style())
    
    # Primary baseline RMLF
    if 'RMLF' in baseline:
        df = filter_bp(baseline['RMLF'], H)
        if len(df) > 0:
            ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS['RMLF'],
                    color=COLORS['RMLF'], label='RMLF', zorder=5, **get_primary_style())
    
    # Our algorithm
    if dynamic is not None:
        df = filter_bp(dynamic, H)
        if len(df) > 0:
            x_data = apply_offset(df['arrival_rate'].values, 'RFDynamic')
            ax.plot(x_data, df['L2_norm'], marker=MARKERS['RFDynamic'],
                    color=COLORS['RFDynamic'], label='RFDynamic', zorder=10, **get_our_algo_style(COLORS['RFDynamic']))
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
    ax.set_title(f'Non-Clairvoyant $\\ell_2$-Norm Comparison\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_l2norm_nonclairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_l2norm_nonclairvoyant_{name}.pdf")


def _gen_nonclairvoyant_l2norm_normal(baseline: Dict, dynamic: Optional[pd.DataFrame], config: dict, output_dir: str):
    """Non-clairvoyant L2-norm - Normal"""
    std, mean, name, title = config['std'], config['mean'], config['name'], config['title']
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    # Secondary baselines
    for algo in ['RMLF', 'MLFQ', 'SETF', 'RR']:
        if algo in baseline:
            df = filter_normal(baseline[algo], mean, std)
            if len(df) > 0:
                ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS[algo],
                        color=COLORS[algo], label=algo, zorder=1, **get_secondary_style())
    
    # Primary baseline FCFS
    if 'FCFS' in baseline:
        df = filter_normal(baseline['FCFS'], mean, std)
        if len(df) > 0:
            ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS['FCFS'],
                    color=COLORS['FCFS'], label='FCFS', zorder=5, **get_primary_style())
    
    # Our algorithm
    if dynamic is not None:
        df = filter_normal(dynamic, mean, std)
        if len(df) > 0:
            x_data = apply_offset(df['arrival_rate'].values, 'RFDynamic')
            ax.plot(x_data, df['L2_norm'], marker=MARKERS['RFDynamic'],
                    color=COLORS['RFDynamic'], label='RFDynamic', zorder=10, **get_our_algo_style(COLORS['RFDynamic']))
    
    ax.set_xlabel('Mean Inter-arrival Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
    ax.set_title(f'Non-Clairvoyant $\\ell_2$-Norm Comparison\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_xticks(X_TICKS)
    ax.set_xlim(X_LIMITS)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"fig_l2norm_nonclairvoyant_{name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_l2norm_nonclairvoyant_{name}.pdf")


# ============================================================================
# COMBINATION COMPARISON COLORS & MARKERS
# ============================================================================
COMBINATION_COLORS = [
    '#1F77B4',  # Blue
    '#D62728',  # Red
    '#2CA02C',  # Green
    '#FF7F0E',  # Orange
    '#9467BD',  # Purple
    '#8C564B',  # Brown
    '#E377C2',  # Pink
    '#7F7F7F',  # Gray
    '#BCBD22',  # Yellow-green
    '#17BECF',  # Cyan
]

COMBINATION_MARKERS = ['o', 's', '^', 'v', 'D', 'p', 'h', '*', 'X', 'P']


def get_combination_style(color):
    """Combination comparison: solid + filled + medium"""
    return {
        'linestyle': '-',
        'linewidth': 2.0,
        'markersize': 8,
        'markerfacecolor': color,
        'markeredgecolor': 'black',
        'markeredgewidth': 0.8,
    }


# ============================================================================
# DATA LOADING - COMBINATION COMPARISON (Longest H Duration Ratio)
# ============================================================================
def load_combination_h_duration_data(analysis_path: str, dist_type: str) -> Dict[str, pd.DataFrame]:
    """
    Load combination data for Longest H Duration Ratio comparison.

    Reads BAL result CSVs from algorithm_result/BAL_result/ and extracts
    the BAL_longest_H_L2_norm column, averaging across rounds.

    Args:
        analysis_path: Path to Analysis folder (unused, kept for API compat)
        dist_type: 'Bounded_Pareto' or 'normal'

    Returns:
        Dict mapping combination_name -> DataFrame with columns ['freq', 'percentage']
    """
    if dist_type == 'Bounded_Pareto':
        combo_folder = os.path.join(ALGORITHM_RESULT_PATH, 'BAL_result',
                                    'Bounded_Pareto_combination_softrandom_result')
    else:
        combo_folder = os.path.join(ALGORITHM_RESULT_PATH, 'BAL_result',
                                    'normal_combination_softrandom_result')

    if not os.path.exists(combo_folder):
        logger.warning(f"Combination folder not found: {combo_folder}")
        return {}

    result = {}

    # Iterate over sub-folders: two_result, three_result, four_result
    for subfolder in ['two_result', 'three_result', 'four_result']:
        sub_path = os.path.join(combo_folder, subfolder)
        if not os.path.exists(sub_path):
            continue

        # Group CSV files by combination name (strip _BAL_{round}_result.csv)
        combo_files: Dict[str, list] = {}
        for fname in os.listdir(sub_path):
            if not fname.endswith('_result.csv') or 'combination' not in fname:
                continue
            # e.g. two_combination_H64_H512_pair_1_BAL_1_result.csv
            # strip _BAL_{round}_result.csv to get the combo name
            m = re.match(r'^(.+)_BAL_\d+_result\.csv$', fname)
            if m:
                combo_name = m.group(1)
                combo_files.setdefault(combo_name, []).append(
                    os.path.join(sub_path, fname))

        for combo_name, files in combo_files.items():
            all_dfs = []
            for fpath in sorted(files):
                try:
                    all_dfs.append(pd.read_csv(fpath))
                except Exception as e:
                    logger.debug(f"Error reading {fpath}: {e}")

            if not all_dfs:
                continue

            combined = pd.concat(all_dfs, ignore_index=True)
            if 'BAL_longest_H_L2_norm' not in combined.columns or 'BAL_L2_norm_flow_time' not in combined.columns:
                continue

            combined['Longest_H_Ratio'] = (combined['BAL_longest_H_L2_norm'] / combined['BAL_L2_norm_flow_time']) * 100

            avg = combined.groupby('frequency')['Longest_H_Ratio'].mean().reset_index()
            avg = avg.rename(columns={'frequency': 'freq',
                                      'Longest_H_Ratio': 'percentage'})
            avg = avg.sort_values('freq')

            if len(avg) > 0:
                result[combo_name] = avg
                logger.info(f"Loaded {dist_type}: {combo_name} ({len(avg)} points)")

    return result


def format_combination_label(combo_name: str, dist_type: str) -> str:
    """
    Format combination folder name to legend label.
    
    Examples:
        'four_combination_H64_H512_H4096_H32768' -> 'BP_four_combination_H64_H512_H4096_H32768'
        'two_combination_std6_std9' -> 'normal_two_combination_std6_std9'
    """
    if dist_type == 'Bounded_Pareto':
        prefix = 'BP'
    else:
        prefix = 'normal'
    
    # Extract combination type (two, three, four)
    parts = combo_name.split('_')
    if len(parts) >= 2:
        combo_type = parts[0]  # two, three, four
        # Get the rest (H values or std values)
        remaining = '_'.join(parts[1:])  # combination_H64_H512...
        remaining = remaining.replace('combination_', '')
        return f"{prefix}_{combo_type}_combination_{remaining}"
    
    return f"{prefix}_{combo_name}"


def generate_combination_comparison_figures(analysis_path: str = None, output_path: str = None):
    """
    Generate Longest H Duration Ratio comparison figures for combination softrandom data.
    
    Output:
        - Bounded_Pareto_Longest H_Duration_Ratio.pdf
        - normal_Longest H_Duration_Ratio.pdf
    """
    setup_plot_style()
    
    if analysis_path is None:
        analysis_path = ANALYSIS_PATH
    if output_path is None:
        output_path = OUTPUT_PATH
    
    os.makedirs(output_path, exist_ok=True)
    
    logger.info("\n=== Generating Combination Comparison Figures ===")
    
    for dist_type in ['Bounded_Pareto', 'normal']:
        # Load all combination data
        combo_data = load_combination_h_duration_data(analysis_path, dist_type)
        
        if not combo_data:
            logger.warning(f"No combination data found for {dist_type}")
            continue
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Sort combinations for consistent ordering
        sorted_combos = sorted(combo_data.keys())
        
        # Plot each combination
        for idx, combo_name in enumerate(sorted_combos):
            df = combo_data[combo_name]
            color = COMBINATION_COLORS[idx % len(COMBINATION_COLORS)]
            marker = COMBINATION_MARKERS[idx % len(COMBINATION_MARKERS)]
            label = format_combination_label(combo_name, dist_type)
            
            ax.plot(df['freq'], df['percentage'], 
                    marker=marker, color=color, label=label,
                    **get_combination_style(color))
        
        # Configure axes
        ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=12)
        ax.set_ylabel('Percentage (%)', fontweight='bold', fontsize=12)
        
        if dist_type == 'Bounded_Pareto':
            title = 'Bounded Pareto Combination Softrandom\nLongest H Duration Ratio (%)'
        else:
            title = 'Normal Combination Softrandom\nLongest H Duration Ratio (%)'
        
        ax.set_title(title, fontweight='bold', fontsize=13)
        
        # Log scale for x-axis (base 2)
        ax.set_xscale('log', base=2)
        ax.set_xlim(2**0, 2**17)
        x_ticks = [2**i for i in range(1, 17)]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f'$2^{{{i}}}$' for i in range(1, 17)])
        
        # Legend - two columns for many items
        ax.legend(loc='upper left', framealpha=0.95, fontsize=9, 
                  edgecolor='black', ncol=2)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save figure
        output_file = os.path.join(output_path, f"{dist_type}_Longest H_Duration_Ratio.pdf")
        plt.savefig(output_file, dpi=300)
        plt.close()
        logger.info(f"Generated: {output_file}")


# ============================================================================
# SOFT RANDOM COMBINATION - L2-NORM FIGURES
# ============================================================================
def generate_softrandom_l2norm_figures(common_k: int):
    """Generate L2-norm figures for soft random combination data."""
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_l2norm_softrandom")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating Soft Random L²-norm Figures ===")

    for combo_type, configs in SOFTRANDOM_COMBINATION_CONFIGS.items():
        for config in configs:
            combo_name = config['name']
            title = config['title']

            _gen_clairvoyant_softrandom(combo_name, title, common_k, output_dir)
            _gen_nonclairvoyant_softrandom(combo_name, title, common_k, output_dir)


def _gen_clairvoyant_softrandom(combo_name: str, title: str, k: int, output_dir: str):
    """Clairvoyant L2-norm - Soft Random"""
    fig, ax = plt.subplots(figsize=(11, 7))

    # Secondary baselines
    for algo in ['BAL', 'FCFS', 'SJF', 'RR']:
        df = load_baseline_softrandom(algo, combo_name)
        if df is not None and len(df) > 0:
            ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS[algo],
                    color=COLORS[algo], label=algo, zorder=1, **get_secondary_style())

    # Primary baseline SRPT
    df_srpt = load_baseline_softrandom('SRPT', combo_name)
    if df_srpt is not None and len(df_srpt) > 0:
        ax.plot(df_srpt['arrival_rate'], df_srpt['L2_norm'], marker=MARKERS['SRPT'],
                color=COLORS['SRPT'], label='SRPT', zorder=5, **get_primary_style())

    # Our algorithms
    for algo in ['Dynamic', 'Dynamic_BAL']:
        df = load_dynamic_softrandom(algo, combo_name, k)
        if df is not None and len(df) > 0:
            x_data = apply_offset(df['arrival_rate'].values, algo)
            ax.plot(x_data, df['L2_norm'], marker=MARKERS[algo],
                    color=COLORS[algo], label=algo, zorder=10, **get_our_algo_style(COLORS[algo]))
    
    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
    ax.set_title(f'Clairvoyant $\\ell_2$-Norm Comparison\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='upper left', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xlim(2**1, 2**16)
    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{i}}}$' for i in range(1, 17)])
    
    plt.tight_layout()
    # Clean filename - extract H values only
    short_name = _get_short_name(combo_name)
    plt.savefig(os.path.join(output_dir, f"fig_l2norm_clairvoyant_{short_name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_l2norm_clairvoyant_{short_name}.pdf")


def _gen_nonclairvoyant_softrandom(combo_name: str, title: str, k: int, output_dir: str):
    """Non-clairvoyant L2-norm - Soft Random"""
    fig, ax = plt.subplots(figsize=(11, 7))

    # Secondary baselines
    for algo in ['MLFQ', 'FCFS', 'SETF', 'RR']:
        df = load_baseline_softrandom(algo, combo_name)
        if df is not None and len(df) > 0:
            ax.plot(df['arrival_rate'], df['L2_norm'], marker=MARKERS[algo],
                    color=COLORS[algo], label=algo, zorder=1, **get_secondary_style())

    # Primary baseline RMLF
    df_rmlf = load_baseline_softrandom('RMLF', combo_name)
    if df_rmlf is not None and len(df_rmlf) > 0:
        ax.plot(df_rmlf['arrival_rate'], df_rmlf['L2_norm'], marker=MARKERS['RMLF'],
                color=COLORS['RMLF'], label='RMLF', zorder=5, **get_primary_style())

    # Our algorithm
    df = load_dynamic_softrandom('RFDynamic', combo_name, k)
    if df is not None and len(df) > 0:
        x_data = apply_offset(df['arrival_rate'].values, 'RFDynamic')
        ax.plot(x_data, df['L2_norm'], marker=MARKERS['RFDynamic'],
                color=COLORS['RFDynamic'], label='RFDynamic', zorder=10, **get_our_algo_style(COLORS['RFDynamic']))
    
    ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=12)
    ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
    ax.set_title(f'Non-Clairvoyant $\\ell_2$-Norm Comparison\n{title}', fontweight='bold', fontsize=13)
    ax.legend(loc='upper left', framealpha=0.95, fontsize=10, edgecolor='black')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xlim(2**1, 2**16)
    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'$2^{{{i}}}$' for i in range(1, 17)])
    
    plt.tight_layout()
    short_name = _get_short_name(combo_name)
    plt.savefig(os.path.join(output_dir, f"fig_l2norm_nonclairvoyant_{short_name}.pdf"), dpi=300)
    plt.close()
    logger.info(f"Generated: fig_l2norm_nonclairvoyant_{short_name}.pdf")


# ============================================================================
# DATA LOADING - SINGLE-DISTRIBUTION SOFTRANDOM (for sensitivity analysis)
# ============================================================================
BATCH_SIZES = [25, 50, 100, 200, 500]

def load_dynamic_softrandom_single_dist(algorithm: str, batch_size: int, k: int,
                                         dist_type: str = 'Bounded_Pareto') -> Optional[pd.DataFrame]:
    """
    Load single-distribution softrandom data for a specific algorithm, batch size, and k.

    Files: {dist_type}_softrandom_result_{algo}_njobs{B}_{round}.csv
    Columns: frequency, {algo}_njobs{B}_mode{k}_L2_norm_flow_time, ...
    Returns DataFrame with columns ['frequency', 'L2_norm'].
    """
    folder = f"{dist_type}_softrandom_result"
    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", folder)
    if not os.path.exists(base_dir):
        return None

    all_data = []
    for round_num in range(1, 10):  # up to 9 rounds
        fname = f"{folder}_{algorithm}_njobs{batch_size}_{round_num}.csv"
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            try:
                all_data.append(pd.read_csv(fpath))
            except:
                pass

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)

    # Find L2 column: {algo}_njobs{B}_mode{k}_L2_norm_flow_time
    l2_col = f'{algorithm}_njobs{batch_size}_mode{k}_L2_norm_flow_time'
    if l2_col not in combined.columns:
        # Fallback search
        l2_cols = [c for c in combined.columns if 'L2_norm' in c and f'mode{k}_' in c]
        if l2_cols:
            l2_col = l2_cols[0]
        else:
            return None

    if 'frequency' not in combined.columns:
        return None

    result = combined.groupby('frequency')[l2_col].mean().reset_index()
    result = result.rename(columns={'frequency': 'frequency', l2_col: 'L2_norm'})
    return result


def load_baseline_softrandom_single_dist(algorithm: str,
                                          dist_type: str = 'Bounded_Pareto') -> Optional[pd.DataFrame]:
    """Load baseline (non-dynamic) single-distribution softrandom data."""
    folder = f"{dist_type}_softrandom_result"
    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", folder)
    if not os.path.exists(base_dir):
        return None

    all_data = []
    for round_num in range(1, 10):
        fname = f"{folder}_{algorithm}_{round_num}.csv"
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            try:
                all_data.append(pd.read_csv(fpath))
            except:
                pass

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)
    l2_col = f'{algorithm}_L2_norm_flow_time'
    if l2_col not in combined.columns:
        return None

    result = combined.groupby('frequency')[l2_col].mean().reset_index()
    result = result.rename(columns={l2_col: 'L2_norm'})
    return result


# ============================================================================
# §4.4 LOOKBACK SENSITIVITY FIGURES
# ============================================================================
def generate_lookback_sensitivity_figures(batch_size: int = DEFAULT_BATCH_SIZE):
    """
    §4.4 Lookback Sensitivity: sweep k in {1, 2, 4, 8, 16, all(0)}
    Fixed B=batch_size, using Bounded Pareto softrandom data.
    X-axis: coherence time, Y-axis: L2-norm, one line per k.
    One figure per algorithm.
    """
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_lookback_sensitivity")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating §4.4 Lookback Sensitivity Figures ===")

    k_values = ALL_LOOKBACKS  # [1, 2, 4, 8, 16, 0]
    k_colors = {1: '#1f77b4', 2: '#ff7f0e', 4: '#2ca02c', 8: '#d62728', 16: '#9467bd', 0: '#8c564b'}
    k_markers = {1: 'o', 2: 's', 4: '^', 8: 'D', 16: 'v', 0: 'p'}
    k_labels = {1: '$k=1$', 2: '$k=2$', 4: '$k=4$', 8: '$k=8$', 16: '$k=16$', 0: '$k=\\mathrm{all}$'}

    for algo in DYNAMIC_ALGORITHMS.keys():
        fig, ax = plt.subplots(figsize=(11, 7))
        has_data = False

        for k_val in k_values:
            df = load_dynamic_softrandom_single_dist(algo, batch_size, k_val)
            if df is None:
                continue

            has_data = True
            color = k_colors.get(k_val, 'gray')
            marker = k_markers.get(k_val, 'o')
            label = k_labels.get(k_val, f'$k={k_val}$')

            df_sorted = df.sort_values('frequency')
            ax.plot(df_sorted['frequency'], df_sorted['L2_norm'],
                    marker=marker, color=color,
                    linestyle='-', linewidth=2.5, markersize=9,
                    markerfacecolor=color, markeredgecolor='black', markeredgewidth=0.8,
                    label=label)

        if not has_data:
            plt.close()
            logger.warning(f"No lookback sensitivity data for {algo}")
            continue

        ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=12)
        ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
        ax.set_title(f'{algo} Lookback Sensitivity ($B={batch_size}$)',
                     fontweight='bold', fontsize=13)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        ax.set_xscale('log', base=2)
        x_ticks = [2**i for i in range(1, 17)]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f'$2^{{{i}}}$' for i in range(1, 17)])
        ax.set_xlim(2, 2**16)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"fig_lookback_sensitivity_{algo}.pdf"), dpi=300)
        plt.close()
        logger.info(f"Generated: fig_lookback_sensitivity_{algo}.pdf")


# ============================================================================
# §4.5 BATCH SIZE SENSITIVITY FIGURES
# ============================================================================
def generate_batch_size_sensitivity_figures(fixed_k: int = 8):
    """
    §4.5 Batch Size Sensitivity: sweep B in {25, 50, 100, 200, 500}
    Fixed k=fixed_k, using Bounded Pareto softrandom data.
    X-axis: coherence time, Y-axis: L2-norm, one line per B.
    One figure per algorithm.
    """
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_batch_size_sensitivity")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating §4.5 Batch Size Sensitivity Figures ===")

    b_colors = {25: '#1f77b4', 50: '#ff7f0e', 100: '#2ca02c', 200: '#d62728', 500: '#9467bd'}
    b_markers = {25: 'o', 50: 's', 100: '^', 200: 'D', 500: 'v'}

    for algo in DYNAMIC_ALGORITHMS.keys():
        fig, ax = plt.subplots(figsize=(11, 7))
        has_data = False

        for B in BATCH_SIZES:
            df = load_dynamic_softrandom_single_dist(algo, B, fixed_k)
            if df is None:
                continue

            has_data = True
            color = b_colors.get(B, 'gray')
            marker = b_markers.get(B, 'o')

            df_sorted = df.sort_values('frequency')
            ax.plot(df_sorted['frequency'], df_sorted['L2_norm'],
                    marker=marker, color=color,
                    linestyle='-', linewidth=2.5, markersize=9,
                    markerfacecolor=color, markeredgecolor='black', markeredgewidth=0.8,
                    label=f'$B={B}$')

        if not has_data:
            plt.close()
            logger.warning(f"No batch size sensitivity data for {algo}")
            continue

        ax.set_xlabel('Coherence Time', fontweight='bold', fontsize=12)
        ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
        ax.set_title(f'{algo} Batch Size Sensitivity ($k={fixed_k}$)',
                     fontweight='bold', fontsize=13)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        ax.set_xscale('log', base=2)
        x_ticks = [2**i for i in range(1, 17)]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f'$2^{{{i}}}$' for i in range(1, 17)])
        ax.set_xlim(2, 2**16)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"fig_batch_sensitivity_{algo}.pdf"), dpi=300)
        plt.close()
        logger.info(f"Generated: fig_batch_sensitivity_{algo}.pdf")


# ============================================================================
# §4.6 TIME-VARYING WORKLOAD FIGURES
# ============================================================================
TIMEVARYING_RESULT_PATH = os.path.join(ALGORITHM_RESULT_PATH, "time_varying_result")

def load_timevarying_baseline(algorithm: str) -> Optional[pd.DataFrame]:
    """
    Load time-varying workload baseline results.
    Expected file: time_varying_result/{algo}_time_varying_{round}.csv
    Columns: job_index, {algo}_L2_norm_flow_time
    Returns DataFrame with columns ['job_index', 'L2_norm'].
    """
    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "time_varying_result")
    if not os.path.exists(base_dir):
        return None

    all_data = []
    for round_num in range(1, 10):
        for pat in [f"{algorithm}_time_varying_{round_num}.csv",
                    f"time_varying_{algorithm}_{round_num}.csv"]:
            fpath = os.path.join(base_dir, pat)
            if os.path.exists(fpath):
                try:
                    all_data.append(pd.read_csv(fpath))
                except:
                    pass
                break

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)
    l2_col = f'{algorithm}_L2_norm_flow_time'
    if l2_col not in combined.columns:
        l2_cols = [c for c in combined.columns if 'L2_norm' in c]
        if l2_cols:
            l2_col = l2_cols[0]
        else:
            return None

    idx_col = 'job_index' if 'job_index' in combined.columns else 'batch_index'
    if idx_col not in combined.columns:
        # Use row index
        combined[idx_col] = range(len(combined))

    result = combined.groupby(idx_col)[l2_col].mean().reset_index()
    result = result.rename(columns={idx_col: 'index', l2_col: 'L2_norm'})
    return result


def load_timevarying_dynamic(algorithm: str, k: int, batch_size: int = DEFAULT_BATCH_SIZE) -> Optional[pd.DataFrame]:
    """
    Load time-varying workload dynamic algorithm results.
    Expected file: time_varying_result/{algo}_time_varying_njobs{B}_{round}.csv
    Columns: job_index/batch_index, {algo}_njobs{B}_mode{k}_L2_norm_flow_time
    """
    base_dir = os.path.join(ALGORITHM_RESULT_PATH, f"{algorithm}_result", "time_varying_result")
    if not os.path.exists(base_dir):
        return None

    all_data = []
    for round_num in range(1, 10):
        for pat in [f"{algorithm}_time_varying_njobs{batch_size}_{round_num}.csv",
                    f"time_varying_{algorithm}_njobs{batch_size}_{round_num}.csv"]:
            fpath = os.path.join(base_dir, pat)
            if os.path.exists(fpath):
                try:
                    all_data.append(pd.read_csv(fpath))
                except:
                    pass
                break

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)

    l2_col = None
    for p in [f'{algorithm}_njobs{batch_size}_mode{k}_L2_norm_flow_time',
              f'{algorithm}_mode{k}_L2_norm_flow_time']:
        if p in combined.columns:
            l2_col = p
            break
    if l2_col is None:
        l2_cols = [c for c in combined.columns if 'L2_norm' in c and f'mode{k}' in c]
        if l2_cols:
            l2_col = l2_cols[0]
        else:
            return None

    idx_col = 'job_index' if 'job_index' in combined.columns else 'batch_index'
    if idx_col not in combined.columns:
        combined[idx_col] = range(len(combined))

    result = combined.groupby(idx_col)[l2_col].mean().reset_index()
    result = result.rename(columns={idx_col: 'index', l2_col: 'L2_norm'})
    return result


def generate_timevarying_figures(common_k: int, batch_size: int = DEFAULT_BATCH_SIZE):
    """
    §4.6 Time-Varying Workload: piecewise-stationary distribution.
    First 5,000 jobs: BP-H64, Last 5,000 jobs: BP-H262144.

    Generates:
      - fig_timevarying_l2norm_clairvoyant.pdf
        (Dynamic, Dynamic_BAL vs SRPT, FCFS, BAL, RR)
      - fig_timevarying_l2norm_nonclairvoyant.pdf
        (RFDynamic vs RMLF, MLFQ, SETF, RR)
    """
    setup_plot_style()
    output_dir = os.path.join(OUTPUT_PATH, "sec4_timevarying")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("\n=== Generating §4.6 Time-Varying Workload Figures ===")

    switch_point = 5000  # job index where distribution changes

    # --- Clairvoyant figure ---
    fig, ax = plt.subplots(figsize=(12, 7))
    has_data = False

    # Baselines
    for algo in CLAIRVOYANT_BASELINES:
        df = load_timevarying_baseline(algo)
        if df is not None and len(df) > 0:
            has_data = True
            ax.plot(df['index'], df['L2_norm'], marker=MARKERS[algo],
                    color=COLORS[algo], label=algo, zorder=1, markevery=max(1, len(df)//20),
                    **get_secondary_style())

    # Our algorithms
    for algo in ['Dynamic', 'Dynamic_BAL']:
        df = load_timevarying_dynamic(algo, common_k, batch_size)
        if df is not None and len(df) > 0:
            has_data = True
            ax.plot(df['index'], df['L2_norm'], marker=MARKERS[algo],
                    color=COLORS[algo], label=algo, zorder=10, markevery=max(1, len(df)//20),
                    **get_our_algo_style(COLORS[algo]))

    if has_data:
        ax.axvline(x=switch_point, color='gray', linestyle=':', linewidth=2, alpha=0.7,
                   label='Distribution switch')
        ax.set_xlabel('Job Index', fontweight='bold', fontsize=12)
        ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
        ax.set_title('Clairvoyant Time-Varying Workload\n'
                     'BP-$H=2^6$ (first 5k) $\\rightarrow$ BP-$H=2^{18}$ (last 5k)',
                     fontweight='bold', fontsize=13)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "fig_timevarying_l2norm_clairvoyant.pdf"), dpi=300)
        logger.info("Generated: fig_timevarying_l2norm_clairvoyant.pdf")
    else:
        logger.warning("No clairvoyant time-varying data found. "
                       "Run time-varying experiments first.")
    plt.close()

    # --- Non-clairvoyant figure ---
    fig, ax = plt.subplots(figsize=(12, 7))
    has_data = False

    for algo in NON_CLAIRVOYANT_BASELINES:
        df = load_timevarying_baseline(algo)
        if df is not None and len(df) > 0:
            has_data = True
            ax.plot(df['index'], df['L2_norm'], marker=MARKERS[algo],
                    color=COLORS[algo], label=algo, zorder=1, markevery=max(1, len(df)//20),
                    **get_secondary_style())

    df = load_timevarying_dynamic('RFDynamic', common_k, batch_size)
    if df is not None and len(df) > 0:
        has_data = True
        ax.plot(df['index'], df['L2_norm'], marker=MARKERS['RFDynamic'],
                color=COLORS['RFDynamic'], label='RFDynamic', zorder=10,
                markevery=max(1, len(df)//20),
                **get_our_algo_style(COLORS['RFDynamic']))

    if has_data:
        ax.axvline(x=switch_point, color='gray', linestyle=':', linewidth=2, alpha=0.7,
                   label='Distribution switch')
        ax.set_xlabel('Job Index', fontweight='bold', fontsize=12)
        ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
        ax.set_title('Non-Clairvoyant Time-Varying Workload\n'
                     'BP-$H=2^6$ (first 5k) $\\rightarrow$ BP-$H=2^{18}$ (last 5k)',
                     fontweight='bold', fontsize=13)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "fig_timevarying_l2norm_nonclairvoyant.pdf"), dpi=300)
        logger.info("Generated: fig_timevarying_l2norm_nonclairvoyant.pdf")
    else:
        logger.warning("No non-clairvoyant time-varying data found. "
                       "Run time-varying experiments first.")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================
# =============================================================================
# §4.6 Distribution Shift Experiment
# =============================================================================

def _load_distribution_shift_data():
    """
    Load per-seed distribution shift CSVs (B=100, k=16).
    Returns:
        baselines: dict[algo_name] -> np.array shape (num_seeds, 100)
        framework: dict[algo_name] -> np.array shape (num_seeds, 100)
    """
    shift_dir = os.path.join(ALGORITHM_RESULT_PATH, "distribution_shift_result")
    seeds = range(1, 11)

    baseline_algos = ['SRPT', 'FCFS', 'BAL', 'SJF', 'RR', 'RMLF', 'MLFQ', 'SETF']
    framework_algos = ['Dynamic', 'Dynamic_BAL', 'RFDynamic']

    baselines = {}
    framework = {}

    for seed in seeds:
        bl_csv = os.path.join(shift_dir, f"seed_{seed}", "baselines", "per_batch_l2.csv")
        if os.path.exists(bl_csv):
            df = pd.read_csv(bl_csv)
            for algo in baseline_algos:
                if algo in df.columns:
                    baselines.setdefault(algo, []).append(df[algo].values)

        fw_csv = os.path.join(shift_dir, f"seed_{seed}", "B_100", "per_batch_l2.csv")
        if os.path.exists(fw_csv):
            df = pd.read_csv(fw_csv)
            for algo in framework_algos:
                if algo in df.columns:
                    framework.setdefault(algo, []).append(df[algo].values)

    for k in baselines:
        baselines[k] = np.array(baselines[k])
    for k in framework:
        framework[k] = np.array(framework[k])

    return baselines, framework


def plot_distribution_shift():
    """
    §4.6 Distribution Shift: aggregate across 10 seeds, B=100, k=16.
    Produces 2 figures: clairvoyant + non-clairvoyant.
    Style matches generate_timevarying_figures().
    """
    setup_plot_style()

    baselines, framework = _load_distribution_shift_data()

    if not baselines and not framework:
        logger.warning("No distribution shift data found.")
        return

    out_dir = os.path.join(OUTPUT_PATH, "sec4_timevarying")
    os.makedirs(out_dir, exist_ok=True)

    EVAL_WINDOW = 100
    switch_point = 5000

    def make_job_index(n_batches):
        return np.arange(1, n_batches + 1) * EVAL_WINDOW - EVAL_WINDOW // 2

    # ---- Clairvoyant figure ----
    fig, ax = plt.subplots(figsize=(12, 7))
    has_data = False

    # Secondary baselines
    for algo in ['BAL', 'FCFS', 'SJF', 'RR']:
        if algo in baselines and len(baselines[algo]) > 0:
            mean = np.mean(baselines[algo], axis=0)
            x = make_job_index(len(mean))
            ax.plot(x, mean, marker=MARKERS[algo], color=COLORS[algo],
                    label=algo, zorder=1, markevery=max(1, len(mean) // 20),
                    markeredgecolor=COLORS[algo], **get_secondary_style())
            has_data = True

    # Primary baseline: SRPT
    if 'SRPT' in baselines and len(baselines['SRPT']) > 0:
        mean = np.mean(baselines['SRPT'], axis=0)
        x = make_job_index(len(mean))
        ax.plot(x, mean, marker=MARKERS['SRPT'], color=COLORS['SRPT'],
                label='SRPT', zorder=5, markevery=max(1, len(mean) // 20),
                markerfacecolor=COLORS['SRPT'], **get_primary_style())
        has_data = True

    # Our algorithms: Dynamic, Dynamic_BAL
    for algo in ['Dynamic', 'Dynamic_BAL']:
        if algo in framework and len(framework[algo]) > 0:
            data = framework[algo]
            mean = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            x = make_job_index(len(mean))
            color = COLORS[algo]
            ax.plot(x, mean, marker=MARKERS[algo], color=color,
                    label=algo, zorder=10, markevery=max(1, len(mean) // 20),
                    **get_our_algo_style(color))
            lower = np.maximum(mean - std, mean / 3.0)
            ax.fill_between(x, lower, mean + std, color=color, alpha=0.12, zorder=5)
            has_data = True

    if has_data:
        ax.axvline(x=switch_point, color='gray', linestyle=':', linewidth=2, alpha=0.7,
                   label='Distribution switch')
        ax.set_xlabel('Job Index', fontweight='bold', fontsize=12)
        ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
        ax.set_title('Clairvoyant Distribution Shift\n'
                     'BP-$H=2^6$ (first 5k) $\\rightarrow$ BP-$H=2^{18}$ (last 5k)',
                     fontweight='bold', fontsize=13)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        plt.tight_layout()
        fig.savefig(os.path.join(out_dir, 'fig_timevarying_clairvoyant.pdf'),
                    dpi=300, bbox_inches='tight')
        logger.info("  Saved fig_timevarying_clairvoyant.pdf")
    plt.close(fig)

    # ---- Non-clairvoyant figure ----
    fig, ax = plt.subplots(figsize=(12, 7))
    has_data = False

    # Secondary baselines
    for algo in ['MLFQ', 'FCFS', 'SETF', 'RR']:
        if algo in baselines and len(baselines[algo]) > 0:
            mean = np.mean(baselines[algo], axis=0)
            x = make_job_index(len(mean))
            ax.plot(x, mean, marker=MARKERS[algo], color=COLORS[algo],
                    label=algo, zorder=1, markevery=max(1, len(mean) // 20),
                    markeredgecolor=COLORS[algo], **get_secondary_style())
            has_data = True

    # Primary baseline: RMLF
    if 'RMLF' in baselines and len(baselines['RMLF']) > 0:
        mean = np.mean(baselines['RMLF'], axis=0)
        x = make_job_index(len(mean))
        ax.plot(x, mean, marker=MARKERS['RMLF'], color=COLORS['RMLF'],
                label='RMLF', zorder=5, markevery=max(1, len(mean) // 20),
                markerfacecolor=COLORS['RMLF'], **get_primary_style())
        has_data = True

    # Our algorithm: RFDynamic
    if 'RFDynamic' in framework and len(framework['RFDynamic']) > 0:
        data = framework['RFDynamic']
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        x = make_job_index(len(mean))
        color = COLORS['RFDynamic']
        ax.plot(x, mean, marker=MARKERS['RFDynamic'], color=color,
                label='RFDynamic', zorder=10, markevery=max(1, len(mean) // 20),
                **get_our_algo_style(color))
        lower = np.maximum(mean - std, mean / 3.0)
        ax.fill_between(x, lower, mean + std, color=color, alpha=0.12, zorder=5)
        has_data = True

    if has_data:
        ax.axvline(x=switch_point, color='gray', linestyle=':', linewidth=2, alpha=0.7,
                   label='Distribution switch')
        ax.set_xlabel('Job Index', fontweight='bold', fontsize=12)
        ax.set_ylabel('$\\ell_2$-Norm Flow Time', fontweight='bold', fontsize=12)
        ax.set_title('Non-Clairvoyant Distribution Shift\n'
                     'BP-$H=2^6$ (first 5k) $\\rightarrow$ BP-$H=2^{18}$ (last 5k)',
                     fontweight='bold', fontsize=13)
        ax.legend(loc='best', framealpha=0.95, fontsize=10, edgecolor='black')
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        plt.tight_layout()
        fig.savefig(os.path.join(out_dir, 'fig_timevarying_nonclairvoyant.pdf'),
                    dpi=300, bbox_inches='tight')
        logger.info("  Saved fig_timevarying_nonclairvoyant.pdf")
    plt.close(fig)

    logger.info(f"  Distribution shift figures saved to {out_dir}/")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Chapter 4 Figure Generator')
    parser.add_argument('--batch-size', '-B', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'Batch size for experiments (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--lookback', '-k', type=int, default=None,
                        help='Override common best k (default: auto-detect)')
    parser.add_argument('--distribution-shift', action='store_true',
                        help='Generate only the distribution shift figures')
    args = parser.parse_args()

    if args.distribution_shift:
        logger.info("Generating distribution shift figures only...")
        plot_distribution_shift()
        return

    logger.info("=" * 70)
    logger.info("Chapter 4 Figure Generator - avg30 + Soft Random")
    logger.info(f"  Batch size (B): {args.batch_size}")
    logger.info("=" * 70)

    # Step 1: Find common best lookback k
    logger.info("\n=== Finding Common Best Lookback k ===")
    if args.lookback is not None:
        common_k = args.lookback
        logger.info(f"Using user-specified k={common_k}")
    else:
        common_k = find_common_best_k()
    logger.info(f"\n>>> Using COMMON k={common_k} <<<\n")

    # Step 2: avg30 Algorithm Selection
    logger.info("\n=== avg30 Algorithm Selection Figures ===")
    generate_avg30_algorithm_selection_figures(common_k)

    # Step 3: Soft Random Lookback Comparison (all k values per algorithm per combination)
    logger.info("\n=== Soft Random Lookback Comparison Figures ===")
    generate_softrandom_lookback_comparison_figures()

    # Step 4: avg30 L2-norm
    logger.info("\n=== avg30 L²-norm Figures ===")
    generate_avg30_l2norm_figures(common_k)

    # Step 5: Soft Random L2-norm
    logger.info("\n=== Soft Random L²-norm Figures ===")
    generate_softrandom_l2norm_figures(common_k)

    # Step 6: Combination Comparison (Longest H Duration Ratio)
    logger.info("\n=== Combination Comparison Figures ===")
    generate_combination_comparison_figures()

    # Step 7: §4.4 Lookback Sensitivity
    logger.info("\n=== §4.4 Lookback Sensitivity Figures ===")
    generate_lookback_sensitivity_figures(args.batch_size)

    # Step 8: §4.5 Batch Size Sensitivity
    logger.info("\n=== §4.5 Batch Size Sensitivity Figures ===")
    generate_batch_size_sensitivity_figures(fixed_k=common_k)

    # Step 9: §4.6 Time-Varying Workload
    logger.info("\n=== §4.6 Time-Varying Workload Figures ===")
    generate_timevarying_figures(common_k, args.batch_size)

    # Step 10: §4.6 Distribution Shift
    logger.info("\n=== §4.6 Distribution Shift Figures ===")
    plot_distribution_shift()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info(f"All figures generated using common k={common_k}, B={args.batch_size}")
    for subdir in ['sec4_algorithm_selection', 'sec4_lookback_comparison_softrandom',
                    'sec4_l2norm_avg30', 'sec4_l2norm_softrandom',
                    'sec4_lookback_sensitivity', 'sec4_batch_size_sensitivity',
                    'sec4_timevarying', 'sec4_distribution_shift', 'figures']:
        path = os.path.join(OUTPUT_PATH, subdir)
        if os.path.exists(path):
            count = len([f for f in os.listdir(path) if f.endswith('.pdf')])
            logger.info(f"{subdir}: {count} figures")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()