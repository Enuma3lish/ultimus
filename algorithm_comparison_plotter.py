import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_plot_style():
    """Set up matplotlib style for better-looking plots"""
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3

def create_dynamic_plot(df, output_path, plot_title):
    """
    Create DYNAMIC comparison plot
    
    Args:
        df: DataFrame with algorithm results
        output_path: Path for saving plot (without extension)
        plot_title: Title for the plot
    """
    
    # Define colors and markers for different algorithms
    colors = ['blue', 'green', 'orange', 'purple', 'brown', 'red']
    markers = ['^', 'v', 's', 'o', 'D', 'x']
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # DYNAMIC comparisons
    dynamic_comparisons = [
        ('DYNAMIC_L2_Norm/RR_L2_Norm', 'DYNAMIC vs RR'),
        ('DYNAMIC_L2_Norm/SRPT_L2_Norm', 'DYNAMIC vs SRPT'),
        ('DYNAMIC_L2_Norm/FCFS_L2_Norm', 'DYNAMIC vs FCFS'),
        ('DYNAMIC_L2_Norm/RMLF_L2_Norm', 'DYNAMIC vs RMLF'),
        ('DYNAMIC_L2_Norm/RFdynamic_L2_Norm', 'DYNAMIC vs RFdynamic'),
        ('DYNAMIC_L2_Norm/BAL_L2_Norm', 'DYNAMIC vs BAL')
    ]
    
    # Calculate ratios for DYNAMIC
    for i, (ratio_name, label) in enumerate(dynamic_comparisons):
        algo_name = ratio_name.split('/')[1].replace('_L2_Norm', '')
        if f'DYNAMIC_L2_Norm' in df.columns and f'{algo_name}_L2_Norm' in df.columns:
            ratio_values = df['DYNAMIC_L2_Norm'] / df[f'{algo_name}_L2_Norm']
            ax.plot(df['arrival_rate'], ratio_values, 
                    color=colors[i], marker=markers[i], linewidth=2, 
                    markersize=8, label=label)
    
    # Add baseline line
    ax.axhline(y=1, color='black', linestyle='-', linewidth=2, label='Baseline (y=1)')
    ax.set_xlabel('Arrival Rate', fontsize=12)
    ax.set_ylabel('Performance Ratio', fontsize=12)
    ax.set_title(f'DYNAMIC Algorithm Comparison\n{plot_title}', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(19, 41)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(f"{output_path}_DYNAMIC.pdf", dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved DYNAMIC comparison plot to {output_path}_DYNAMIC.pdf")

def create_rfdynamic_plot(df, output_path, plot_title):
    """
    Create RFdynamic comparison plot
    
    Args:
        df: DataFrame with algorithm results
        output_path: Path for saving plot (without extension)
        plot_title: Title for the plot
    """
    
    # Define colors and markers for different algorithms
    colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'red']
    markers = ['^', 'v', 's', 'o', 'D', '*', 'x']
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # RFdynamic comparisons
    rfdynamic_comparisons = [
        ('RFdynamic_L2_Norm/RR_L2_Norm', 'RFdynamic vs RR'),
        ('RFdynamic_L2_Norm/SRPT_L2_Norm', 'RFdynamic vs SRPT'),
        ('RFdynamic_L2_Norm/SETF_L2_Norm', 'RFdynamic vs SETF'),
        ('RFdynamic_L2_Norm/FCFS_L2_Norm', 'RFdynamic vs FCFS'),
        ('RFdynamic_L2_Norm/RMLF_L2_Norm', 'RFdynamic vs RMLF'),
        ('RFdynamic_L2_Norm/DYNAMIC_L2_Norm', 'RFdynamic vs DYNAMIC'),
        ('RFdynamic_L2_Norm/BAL_L2_Norm', 'RFdynamic vs BAL')
    ]
    
    # Calculate ratios for RFdynamic
    for i, (ratio_name, label) in enumerate(rfdynamic_comparisons):
        algo_name = ratio_name.split('/')[1].replace('_L2_Norm', '')
        if f'RFdynamic_L2_Norm' in df.columns and f'{algo_name}_L2_Norm' in df.columns:
            ratio_values = df['RFdynamic_L2_Norm'] / df[f'{algo_name}_L2_Norm']
            ax.plot(df['arrival_rate'], ratio_values, 
                    color=colors[i], marker=markers[i], linewidth=2, 
                    markersize=8, label=label)
    
    # Add baseline line
    ax.axhline(y=1, color='black', linestyle='-', linewidth=2, label='Baseline (y=1)')
    ax.set_xlabel('Arrival Rate', fontsize=12)
    ax.set_ylabel('Performance Ratio', fontsize=12)
    ax.set_title(f'RFdynamic Algorithm Comparison\n{plot_title}', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(19, 41)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(f"{output_path}_RFdynamic.pdf", dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved RFdynamic comparison plot to {output_path}_RFdynamic.pdf")

def create_bal_plot(df, output_path, plot_title):
    """
    Create BAL comparison plot
    
    Args:
        df: DataFrame with algorithm results
        output_path: Path for saving plot (without extension)
        plot_title: Title for the plot
    """
    
    # Define colors and markers for different algorithms
    colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'red']
    markers = ['^', 'v', 's', 'o', 'D', '*', 'x']
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # BAL comparisons
    bal_comparisons = [
        ('BAL_L2_Norm/RR_L2_Norm', 'BAL vs RR'),
        ('BAL_L2_Norm/SRPT_L2_Norm', 'BAL vs SRPT'),
        ('BAL_L2_Norm/SETF_L2_Norm', 'BAL vs SETF'),
        ('BAL_L2_Norm/FCFS_L2_Norm', 'BAL vs FCFS'),
        ('BAL_L2_Norm/RMLF_L2_Norm', 'BAL vs RMLF'),
        ('BAL_L2_Norm/DYNAMIC_L2_Norm', 'BAL vs DYNAMIC'),
        ('BAL_L2_Norm/RFdynamic_L2_Norm', 'BAL vs RFdynamic')
    ]
    
    # Calculate ratios for BAL
    for i, (ratio_name, label) in enumerate(bal_comparisons):
        algo_name = ratio_name.split('/')[1].replace('_L2_Norm', '')
        if f'BAL_L2_Norm' in df.columns and f'{algo_name}_L2_Norm' in df.columns:
            ratio_values = df['BAL_L2_Norm'] / df[f'{algo_name}_L2_Norm']
            ax.plot(df['arrival_rate'], ratio_values, 
                    color=colors[i], marker=markers[i], linewidth=2, 
                    markersize=8, label=label)
    
    # Add baseline line
    ax.axhline(y=1, color='black', linestyle='-', linewidth=2, label='Baseline (y=1)')
    ax.set_xlabel('Arrival Rate', fontsize=12)
    ax.set_ylabel('Performance Ratio', fontsize=12)
    ax.set_title(f'BAL Algorithm Comparison\n{plot_title}', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(19, 41)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(f"{output_path}_BAL.pdf", dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved BAL comparison plot to {output_path}_BAL.pdf")

def aggregate_and_save_phase1_files(base_dir, output_dir):
    """
    Aggregate phase1 files by bp_parameter and avg_size, save as combined CSV files
    
    Args:
        base_dir: Directory containing phase1 files
        output_dir: Directory to save combined CSV files
    
    Returns:
        List of tuples (csv_file_path, bp_parameter, avg_size)
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    avg_sizes = ['30', '60', '90']
    saved_files = []
    
    for avg_size in avg_sizes:
        pattern = f"{base_dir}/phase1_results_avg_{avg_size}_*.csv"
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No files found for pattern: {pattern}")
            continue
        
        # Read all files for this avg_size
        all_data = []
        for file in sorted(files):
            try:
                df = pd.read_csv(file)
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                continue
        
        if not all_data:
            continue
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Group by bp_parameter
        bp_parameter_groups = combined_df.groupby('bp_parameter')
        
        for bp_param, group_df in bp_parameter_groups:
            try:
                # Sort by arrival_rate
                group_df = group_df.sort_values('arrival_rate').reset_index(drop=True)
                
                # Create safe filename from bp_parameter
                # Parse the bp_parameter string to extract L and H values
                import ast
                bp_dict = ast.literal_eval(bp_param)
                L_val = bp_dict['L']
                H_val = bp_dict['H']
                
                # Create filename with bp_parameter info
                safe_filename = f"L{L_val}_H{H_val}_avg{avg_size}"
                output_file = f"{output_dir}/{safe_filename}.csv"
                
                # Save CSV file
                group_df.to_csv(output_file, index=False)
                saved_files.append((output_file, bp_param, avg_size))
                
                logger.info(f"Saved bp_parameter {bp_param} for avg_{avg_size} to {output_file}")
                
            except Exception as e:
                logger.error(f"Error processing bp_parameter {bp_param} for avg_{avg_size}: {e}")
                continue
    
    return saved_files

def process_freq_files(input_dir, output_dir, folder_type="random"):
    """
    Process frequency-based files
    
    Args:
        input_dir: Directory containing frequency files
        output_dir: Output directory for plots
        folder_type: Type of folder (random or softrandom)
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all freq files
    pattern = f"{input_dir}/freq_*_combined_results.csv"
    files = glob.glob(pattern)
    
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            
            # Extract frequency number from filename
            filename = os.path.basename(file_path)
            freq_num = filename.split('_')[1]  # freq_1_combined_results.csv -> 1
            
            # Create output filename
            if folder_type == "random":
                output_filename = f"freq_{freq_num}_combined_results"
            else:  # softrandom
                output_filename = f"softrandom_{freq_num}_combined_results"
            
            output_path = os.path.join(output_dir, output_filename)
            plot_title = f"Frequency {freq_num} - {folder_type.capitalize()}"
            
            # Create separate comparison plots
            create_dynamic_plot(df, output_path, plot_title)
            create_rfdynamic_plot(df, output_path, plot_title)
            create_bal_plot(df, output_path, plot_title)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

def process_softrandom_files(input_dir, output_dir):
    """
    Process softrandom frequency-based files
    
    Args:
        input_dir: Directory containing softrandom files
        output_dir: Output directory for plots
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all softrandom freq files
    pattern = f"{input_dir}/freq_*_combined_results.csv"
    files = glob.glob(pattern)
    
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            
            # Extract frequency number from filename
            filename = os.path.basename(file_path)
            freq_num = filename.split('_')[1]  # freq_1_combined_results.csv -> 1
            
            # Create output filename (replace freq with softrandom)
            output_filename = f"softrandom_{freq_num}_combined_results"
            output_path = os.path.join(output_dir, output_filename)
            plot_title = f"Softrandom Frequency {freq_num}"
            
            # Create separate comparison plots
            create_dynamic_plot(df, output_path, plot_title)
            create_rfdynamic_plot(df, output_path, plot_title)
            create_bal_plot(df, output_path, plot_title)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

def process_phase1_files(input_dir, output_dir):
    """
    Process phase1 files by aggregating them by bp_parameter, saving CSV, then creating plots
    
    Args:
        input_dir: Directory containing phase1 files
        output_dir: Output directory for plots
    """
    # Create output directories
    csv_output_dir = f"{output_dir}/csv"
    plot_output_dir = f"{output_dir}/plots"
    os.makedirs(csv_output_dir, exist_ok=True)
    os.makedirs(plot_output_dir, exist_ok=True)
    
    # Step 1: Aggregate and save CSV files grouped by bp_parameter
    saved_csv_files = aggregate_and_save_phase1_files(input_dir, csv_output_dir)
    
    # Step 2: Process each saved CSV file to create plots
    for csv_file, bp_param, avg_size in saved_csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # Parse bp_parameter to get L and H values for title and filename
            import ast
            bp_dict = ast.literal_eval(bp_param)
            L_val = bp_dict['L']
            H_val = bp_dict['H']
            
            # Create plot title
            plot_title = f"bp_parameter: L={L_val}, H={H_val} (avg_{avg_size})"
            
            # Create PDF filename as requested: {'L': 16.772, 'H': 64}_avg30.pdf
            pdf_filename = f"{bp_param}_avg{avg_size}"
            output_path = os.path.join(plot_output_dir, pdf_filename)
            
            # Create separate comparison plots
            create_dynamic_plot(df, output_path, plot_title)
            create_rfdynamic_plot(df, output_path, plot_title)
            create_bal_plot(df, output_path, plot_title)
            
        except Exception as e:
            logger.error(f"Error processing CSV file {csv_file}: {e}")
            continue

def main():
    """
    Main function to process all types of files and generate comparison plots
    """
    logger.info("Starting algorithm comparison plot generation...")
    
    # Define input paths
    phase1_path = "/Users/melowu/Desktop/ultimus/phase1"
    freq_path = "/Users/melowu/Desktop/ultimus/freq"
    softrandom_path = "/Users/melowu/Desktop/ultimus/softrandom"
    
    # Define output base directory
    output_base = "/Users/melowu/Desktop/ultimus/result"
    
    # Set up plot style
    setup_plot_style()
    
    # Create base result directory
    os.makedirs(output_base, exist_ok=True)
    
    try:
        # Process phase1 files (aggregate by avg_size, save CSV, then create plots)
        logger.info("Processing phase1 files...")
        process_phase1_files(phase1_path, f"{output_base}/phase1")
        
        # Process freq files (random data)
        logger.info("Processing frequency files (random)...")
        process_freq_files(freq_path, f"{output_base}/random", "random")
        
        # Process softrandom files
        logger.info("Processing softrandom files...")
        process_softrandom_files(softrandom_path, f"{output_base}/softrandom")
        
        logger.info("All plots generated successfully!")
        
        # Print summary
        result_dirs = [
            f"{output_base}/phase1/plots", 
            f"{output_base}/random", 
            f"{output_base}/softrandom"
        ]
        total_pdfs = 0
        for result_dir in result_dirs:
            if os.path.exists(result_dir):
                pdf_files = glob.glob(f"{result_dir}/*.pdf")
                total_pdfs += len(pdf_files)
                logger.info(f"Generated {len(pdf_files)} plots in {result_dir}")
        
        logger.info(f"Total PDF files generated: {total_pdfs}")
        
        # Also show CSV files created
        csv_dir = f"{output_base}/phase1/csv"
        if os.path.exists(csv_dir):
            csv_files = glob.glob(f"{csv_dir}/*.csv")
            logger.info(f"Generated {len(csv_files)} combined CSV files in {csv_dir}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()