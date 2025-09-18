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

# Define global color and marker schemes for consistency
ALGORITHM_COLORS = {
    'RR': '#1f77b4',        # blue
    'Srpt': '#ff7f0e',      # orange
    'SETF': '#2ca02c',      # green
    'Fcfs': '#d62728',      # red
    'Bal': '#9467bd',       # purple
    'Sjf': '#8c564b',       # brown
}

ALGORITHM_MARKERS = {
    'RR': 'o',              # circle
    'Srpt': 's',            # square
    'SETF': '^',            # triangle up
    'Fcfs': 'v',            # triangle down
    'Bal': 'D',             # diamond
    'Sjf': 'x',             # x
}

# Define colors and markers for Dynamic modes
DYNAMIC_COLORS = {
    'DYNAMIC_mode1_njobs100': '#1f77b4',   # blue
    'DYNAMIC_mode2_njobs100': '#ff7f0e',   # orange
    'DYNAMIC_mode3_njobs100': '#2ca02c',   # green
    'DYNAMIC_mode4_njobs100': '#d62728',   # red
    'DYNAMIC_mode5_njobs100': '#9467bd',   # purple
    'DYNAMIC_mode6_njobs100': '#8c564b',   # brown
}

DYNAMIC_MARKERS = {
    'DYNAMIC_mode1_njobs100': '^',         # triangle up
    'DYNAMIC_mode2_njobs100': 'v',         # triangle down
    'DYNAMIC_mode3_njobs100': 's',         # square
    'DYNAMIC_mode4_njobs100': 'D',         # diamond
    'DYNAMIC_mode5_njobs100': 'o',         # circle
    'DYNAMIC_mode6_njobs100': 'x',         # x
}

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

def find_universal_best_dynamic_setting(phase1_dir, result_dir):
    """
    Find the best DYNAMIC setting across avg30 + random + softrandom data
    """
    overall_counter = Counter()
    
    # Process only avg_30 files
    pattern = f"{phase1_dir}/phase1_results_avg_30_*.csv"
    files = glob.glob(pattern)
    
    for file in files:
        try:
            df = pd.read_csv(file)
            dynamic_cols = [col for col in df.columns if col.startswith('DYNAMIC_mode')]
            
            if not dynamic_cols:
                continue
            
            for idx, row in df.iterrows():
                dynamic_values = {col: row[col] for col in dynamic_cols if pd.notna(row[col])}
                
                if dynamic_values:
                    best_setting = min(dynamic_values, key=dynamic_values.get)
                    overall_counter[best_setting] += 1
                    
        except Exception as e:
            logger.error(f"Error processing {file}: {e}")
            continue
    
    # Process random_result.csv
    random_file = f"{result_dir}/random_result.csv"
    if os.path.exists(random_file):
        try:
            df = pd.read_csv(random_file)
            dynamic_cols = [col for col in df.columns if col.startswith('DYNAMIC_mode')]
            
            for idx, row in df.iterrows():
                dynamic_values = {col: row[col] for col in dynamic_cols if pd.notna(row[col])}
                
                if dynamic_values:
                    best_setting = min(dynamic_values, key=dynamic_values.get)
                    overall_counter[best_setting] += 1
                    
        except Exception as e:
            logger.error(f"Error processing random file: {e}")
    
    # Process softrandom_result.csv
    softrandom_file = f"{result_dir}/softrandom_result.csv"
    if os.path.exists(softrandom_file):
        try:
            df = pd.read_csv(softrandom_file)
            dynamic_cols = [col for col in df.columns if col.startswith('DYNAMIC_mode')]
            
            for idx, row in df.iterrows():
                dynamic_values = {col: row[col] for col in dynamic_cols if pd.notna(row[col])}
                
                if dynamic_values:
                    best_setting = min(dynamic_values, key=dynamic_values.get)
                    overall_counter[best_setting] += 1
                    
        except Exception as e:
            logger.error(f"Error processing softrandom file: {e}")
    
    if overall_counter:
        logger.info("\nDynamic Setting Frequency Analysis:")
        for setting, count in overall_counter.most_common():
            logger.info(f"  {setting}: {count} occurrences")
        
        best_overall = overall_counter.most_common(1)[0][0]
        logger.info(f"\nUniversal best DYNAMIC setting: {best_overall}")
        return best_overall
    
    return "DYNAMIC_mode1_njobs100"

def create_dynamic_comparison_plot(df, bp_param, output_path, data_type="general"):
    """
    Create comparison plot for all Dynamic settings showing L2 norm values
    """
    plt.figure(figsize=(10, 6))
    
    # Get all DYNAMIC columns
    dynamic_cols = sorted([col for col in df.columns if col.startswith('DYNAMIC_mode')])
    
    if data_type == "general":
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Dynamic Settings Comparison - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:  # frequency data (random/softrandom)
        freq_numbers = []
        for freq in df['frequency']:
            num = int(freq.split('_')[1])
            freq_numbers.append(num)
        df['freq_number'] = freq_numbers
        df = df.sort_values('freq_number').reset_index(drop=True)
        x_values = df['freq_number'].values
        x_label = 'Coherence Time'
        title = f'Dynamic Settings Comparison - {data_type.capitalize()}'
    
    # Plot each Dynamic setting with consistent colors and markers
    for col in dynamic_cols:
        if col in df.columns and col in DYNAMIC_COLORS:
            # Extract mode number and create cleaner label
            mode_num = col.split('mode')[1].split('_')[0]
            label = f'Mode {mode_num}'  # Clean label: "Mode 1", "Mode 2", etc.
            
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
        plt.xticks(x_values, x_values, rotation=45)
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
    
    algorithms = ['RR', 'Srpt', 'SETF', 'Fcfs', 'Bal', 'Sjf']
    
    # Format the best setting for display
    best_setting_display = best_dynamic_col.replace('DYNAMIC_', '').replace('_', ' ')
    
    if data_type == "general":
        df = df.sort_values('arrival_rate').reset_index(drop=True)
        x_values = df['arrival_rate'].values
        x_label = 'Arrival Rate'
        title = f'Performance Ratio Dynamic {best_setting_display} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}'
    else:
        freq_numbers = []
        for freq in df['frequency']:
            num = int(freq.split('_')[1])
            freq_numbers.append(num)
        df['freq_number'] = freq_numbers
        df = df.sort_values('freq_number').reset_index(drop=True)
        x_values = df['freq_number'].values
        x_label = 'Coherence Time'
        title = f'Performance Ratio Dynamic {best_setting_display} - {data_type.capitalize()}'
    
    # Plot ratios with consistent colors and markers
    for algo in algorithms:
        col_name = algo
        # Handle case variations
        for col in df.columns:
            if col.upper() == algo.upper():
                col_name = col
                break
        
        if col_name in df.columns and best_dynamic_col in df.columns:
            ratio = df[best_dynamic_col] / df[col_name]
            # Updated label format
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
        plt.xticks(x_values, x_values, rotation=45)
    else:
        plt.xlim(18, 42)
        plt.xticks(range(20, 42, 2))
    
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved performance ratio plot to {output_path}")

def create_srpt_percentage_plots_all_modes(dynamic_analysis_dir, bp_param, output_dir):
    """
    Create SRPT percentage plots for each mode separately (only for avg30)
    """
    modes = [1, 2, 3, 4, 5, 6]
    njobs = 100
    avg_type = "30"
    
    os.makedirs(output_dir, exist_ok=True)
    
    for mode in modes:
        filename = f"{dynamic_analysis_dir}/avg{avg_type}_mode_{mode}/Dynamic_avg_{avg_type}_nJobsPerRound_{njobs}_mode_{mode}.csv"
        
        if not os.path.exists(filename):
            logger.warning(f"Dynamic analysis file not found for mode {mode}")
            continue
        
        try:
            df = pd.read_csv(filename)
            
            if 'L' in df.columns:
                df = df[df['L'] == bp_param['L']]
            
            if df.empty:
                logger.warning(f"No data found for BP parameter L={bp_param['L']} in mode {mode}")
                continue
            
            df = df.sort_values('arrival_rate').reset_index(drop=True)
            
            plt.figure(figsize=(10, 6))
            
            if 'SRPT_percentage' in df.columns:
                plt.plot(df['arrival_rate'].values, df['SRPT_percentage'].values,
                        color='#d62728', marker='o', linewidth=2.5, markersize=8,
                        label=f'SRPT Percentage')
            
            plt.xlabel('Arrival Rate', fontsize=14)
            plt.ylabel('SRPT Percentage (%)', fontsize=14)
            plt.title(f'SRPT Usage in Mode {mode} - BP: L={bp_param["L"]:.3f}, H={bp_param["H"]}',
                     fontsize=16, fontweight='bold')
            plt.legend(loc='best', frameon=True, fancybox=True, shadow=True)
            plt.grid(True, alpha=0.3, linestyle='--')
            
            plt.xlim(18, 42)
            plt.xticks(range(20, 42, 2))
            plt.ylim(0, 105)
            
            plt.tight_layout()
            output_path = f"{output_dir}/SRPT_Mode{mode}_L{bp_param['L']:.3f}_H{bp_param['H']}.pdf"
            plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved SRPT percentage plot for mode {mode}")
            
        except Exception as e:
            logger.error(f"Error creating SRPT plot for mode {mode}: {e}")

def process_all_data(phase1_dir, result_dir, dynamic_analysis_dir, output_base):
    """
    Process avg30, random, and softrandom data with consistent styling
    """
    # Find the universal best DYNAMIC setting
    best_setting = find_universal_best_dynamic_setting(phase1_dir, result_dir)
    logger.info(f"Using universal best setting: {best_setting}")
    
    # Process avg_30 data only
    logger.info("\nProcessing avg_30 data...")
    
    pattern = f"{phase1_dir}/phase1_results_avg_30_*.csv"
    files = glob.glob(pattern)
    
    if files:
        all_data = []
        for file in files:
            try:
                df = pd.read_csv(file)
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            bp_groups = combined_df.groupby(['bp_parameter_L', 'bp_parameter_H'])
            
            # Create output directories
            dynamic_comp_dir = f"{output_base}/dynamic_comparisons_avg30"
            ratio_dir = f"{output_base}/performance_ratios_avg30"
            srpt_dir = f"{output_base}/srpt_percentages_avg30"
            
            os.makedirs(dynamic_comp_dir, exist_ok=True)
            os.makedirs(ratio_dir, exist_ok=True)
            os.makedirs(srpt_dir, exist_ok=True)
            
            for (L, H), group_df in bp_groups:
                bp_param = {'L': L, 'H': H}
                group_df = group_df.sort_values('arrival_rate')
                
                # Dynamic comparison plot
                dynamic_output = f"{dynamic_comp_dir}/Dynamic_Comparison_L{L:.3f}_H{H}.pdf"
                create_dynamic_comparison_plot(group_df, bp_param, dynamic_output, "general")
                
                # Performance ratio plot
                ratio_output = f"{ratio_dir}/Performance_Ratio_L{L:.3f}_H{H}.pdf"
                create_performance_ratio_plot(group_df, best_setting, bp_param, ratio_output, "general")
                
                # SRPT percentage plots for all modes
                create_srpt_percentage_plots_all_modes(dynamic_analysis_dir, bp_param, srpt_dir)
    
    # Process random data
    logger.info("\nProcessing random frequency data...")
    random_file = f"{result_dir}/random_result.csv"
    if os.path.exists(random_file):
        df = pd.read_csv(random_file)
        
        # Dynamic comparison
        dynamic_output = f"{output_base}/Dynamic_Comparison_Random.pdf"
        create_dynamic_comparison_plot(df, {}, dynamic_output, "random")
        
        # Performance ratio
        ratio_output = f"{output_base}/Performance_Ratio_Random.pdf"
        create_performance_ratio_plot(df, best_setting, {}, ratio_output, "random")
    
    # Process softrandom data
    logger.info("\nProcessing softrandom frequency data...")
    softrandom_file = f"{result_dir}/softrandom_result.csv"
    if os.path.exists(softrandom_file):
        df = pd.read_csv(softrandom_file)
        
        # Dynamic comparison
        dynamic_output = f"{output_base}/Dynamic_Comparison_Softrandom.pdf"
        create_dynamic_comparison_plot(df, {}, dynamic_output, "softrandom")
        
        # Performance ratio
        ratio_output = f"{output_base}/Performance_Ratio_Softrandom.pdf"
        create_performance_ratio_plot(df, best_setting, {}, ratio_output, "softrandom")

def main():
    """
    Main function to generate all plots with consistent styling
    """
    logger.info("="*60)
    logger.info("Starting algorithm comparison plot generation...")
    logger.info("Processing: avg30, random, and softrandom data only")
    logger.info("="*60)
    
    # Define paths
    phase1_dir = "phase1"
    result_dir = "result"
    dynamic_analysis_dir = "Dynamic_analysis"
    output_base = "algorithm_plots"
    
    # Set up plot style
    setup_plot_style()
    
    # Create base output directory
    os.makedirs(output_base, exist_ok=True)
    
    try:
        # Process all data
        process_all_data(phase1_dir, result_dir, dynamic_analysis_dir, output_base)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("Plot generation completed successfully!")
        
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