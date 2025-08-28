import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define expanded comparison sets for all value types
# Using the full set of columns for all comparisons
comparison_columns = [
    "Rdynamic_sqrt_6/RR_ratio",
    "Rdynamic_sqrt_6/SRPT_ratio",
    "Rdynamic_sqrt_6/SETF_ratio",
    "Rdynamic_sqrt_6/FCFS_ratio",
    "Rdynamic_sqrt_6/RMLF_ratio",
    "Rdynamic_sqrt_6/Dynamic_ratio",
    "Rdynamic_sqrt_8/RR_ratio",
    "Rdynamic_sqrt_8/SRPT_ratio",
    "Rdynamic_sqrt_8/SETF_ratio",
    "Rdynamic_sqrt_8/FCFS_ratio",
    "Rdynamic_sqrt_8/RMLF_ratio",
    "Rdynamic_sqrt_8/Dynamic_ratio",
    "Rdynamic_sqrt_10/RR_ratio",
    "Rdynamic_sqrt_10/SRPT_ratio",
    "Rdynamic_sqrt_10/SETF_ratio",
    "Rdynamic_sqrt_10/FCFS_ratio",
    "Rdynamic_sqrt_10/RMLF_ratio",
    "Rdynamic_sqrt_10/Dynamic_ratio",
    "Dynamic/SRPT_ratio",
    "Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio",
    "Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio",
    "Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio",
    "Rdynamic_sqrt_2/RR_ratio",
    "Rdynamic_sqrt_2/SRPT_ratio",
    "Rdynamic_sqrt_2/SETF_ratio",
    "Rdynamic_sqrt_2/FCFS_ratio",
    "Rdynamic_sqrt_2/RMLF_ratio",
    "Rdynamic_sqrt_2/Dynamic_ratio",
    "Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio",
    "Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio",
    "Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio",
    "RMLF/FCFS_ratio"
]

# Define the frequencies and categories
frequencies = ["1", "10", "100", "500", "1000", "10000"]
categories = ["", "softrandom_"]  # Empty string for the regular category

# Define markers and line styles
markers = [
    {'marker': 'o', 'size': 8},   # Circle
    {'marker': '^', 'size': 10},  # Large upward triangle
    {'marker': 's', 'size': 8},   # Square
    {'marker': 'v', 'size': 10},  # Large downward triangle
    {'marker': 'D', 'size': 8},   # Diamond
    {'marker': '*', 'size': 10},  # Star
    {'marker': 'p', 'size': 8},   # Pentagon
    {'marker': 'h', 'size': 10}   # Hexagon
]

# Define line styles for algorithms
line_styles = {
    'RR': '-',
    'SRPT': '--',
    'SETF': '-.',
    'FCFS': ':',
    'RMLF': '-',
    'Dynamic': '--',
    'Rdynamic_sqrt_2': '-',
    'Rdynamic_sqrt_6': '--',
    'Rdynamic_sqrt_8': '-.',
    'Rdynamic_sqrt_10': ':'
}

# Enhanced color scheme for better visibility
algorithm_colors = {
    'RR': '#FF0000',         # Red
    'SRPT': '#0000FF',       # Blue
    'SETF': '#00CC00',       # Green
    'FCFS': '#9900CC',       # Purple
    'RMLF': '#FF6600',       # Orange
    'Dynamic': '#996633',    # Brown
    'Rdynamic_sqrt_2': '#FF00FF',  # Magenta
    'Rdynamic_sqrt_6': '#00CCCC',  # Teal
    'Rdynamic_sqrt_8': '#FFCC00',  # Gold
    'Rdynamic_sqrt_10': '#00FF00'  # Lime
}

# Create mapping for short names (for display purposes only)
algorithm_display_names = {
    'Rdynamic_sqrt_2': 'RDY_2',
    'Rdynamic_sqrt_6': 'RDY_6',
    'Rdynamic_sqrt_8': 'RDY_8',
    'Rdynamic_sqrt_10': 'RDY_10',
}

# Create a mapping function to convert any Rdynamic name to RDY format
def get_rdy_display_name(name):
    """Convert any Rdynamic_sqrt_X name to RDY_X format"""
    if 'Rdynamic_sqrt_' in name:
        # Extract the number at the end
        try:
            num = name.split('_')[-1]
            return f"RDY_{num}"
        except:
            pass
    # Return from mapping if available, otherwise return original
    return algorithm_display_names.get(name, name)

# Ensure directory for plots exists or is created
plots_dir = "log/img/"
os.makedirs(plots_dir, exist_ok=True)

# Function to create individual plots showing specific algorithm ratios
def create_individual_plots(data, output_dir, freq_value, category_name):
    # Filter to only include columns that actually exist in the data
    available_columns = [col for col in comparison_columns if col in data.columns]
    
    if not available_columns:
        print(f"None of the specified comparison columns found in data")
        return
    
    # Group the ratio columns by algorithm type
    algorithm_groups = {}
    for col in available_columns:
        parts = col.split('/')
        if len(parts) >= 2:
            numerator = parts[0]
            if numerator not in algorithm_groups:
                algorithm_groups[numerator] = []
            algorithm_groups[numerator].append(col)
    
    # Create the plot
    plt.figure(figsize=(14, 10))
    
    # Plot each ratio column
    marker_idx = 0
    for col in available_columns:
        # Skip if column has no data
        if data[col].isnull().all():
            continue
        
        # Parse the ratio column to determine style and label
        parts = col.split('/')
        if len(parts) < 2:
            continue
            
        numerator = parts[0]
        
        # Extract full denominator name before _ratio suffix
        if '_ratio' in parts[1]:
            denominator = parts[1].split('_ratio')[0]  # Gets the full algorithm name
        else:
            denominator = parts[1]
        
        # Choose marker style
        marker_style = markers[marker_idx % len(markers)]
        marker_idx += 1
        
        # Determine color and line style
        if numerator in algorithm_colors:
            color = algorithm_colors[numerator]
            linestyle = line_styles.get(numerator, '-')
        elif denominator in algorithm_colors:
            color = algorithm_colors[denominator]
            linestyle = line_styles.get(denominator, '-')
        else:
            color = 'black'  # Default
            linestyle = '-'
        
        # Format label with short names for all cases
        num_display = get_rdy_display_name(numerator)
        denom_display = get_rdy_display_name(denominator)
        label = f"{num_display} vs {denom_display}"
        
        # Sort and plot valid data
        valid_data = data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
        
        if valid_data.empty:
            continue
        
        plt.plot(
            valid_data['arrival_rate'],
            valid_data[col],
            marker=marker_style['marker'],
            markersize=marker_style['size'],
            linestyle=linestyle,
            label=label,
            color=color
        )
    
    # Add horizontal line at y=1 (indicates equal performance)
    plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
    
    # Format category name for display
    display_category = "Standard" if category_name == "" else "SoftRandom"
    
    # Add titles, labels, and legend
    plt.title(f'Algorithm Comparison Ratios - {display_category} (Freq={freq_value})', fontsize=14)
    plt.xlabel('Mean Interarrival Time', fontsize=12)
    plt.ylabel('Ratio (Lower is Better)', fontsize=12)
    
    # Handle legend - limit number of items to avoid overcrowding
    handles, labels = plt.gca().get_legend_handles_labels()
    if len(handles) > 15:
        # Use a smaller font and place it outside
        plt.legend(fontsize=8, bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        plt.legend(title='Comparison', loc='best', fontsize=10)
        
    plt.grid(True, alpha=0.3)
    
    # Set fixed y-axis limits from 0.0 to 2.0 as requested
    plt.ylim(0.0, 2.0)
    plt.yticks(np.arange(0.0, 2.1, 0.1))  # Set y-ticks every 0.2
    
    # Set appropriate x-ticks based on data range
    x_values = data['arrival_rate'].dropna().unique()
    if len(x_values) > 0:
        min_x = max(min(x_values), 0)
        max_x = max(x_values)
        
        # Calculate appropriate step size
        step = max(1, (max_x - min_x) / 10)
        plt.xticks(np.arange(min_x, max_x + step, step))
    
    # Adjust layout and save
    plt.tight_layout()
    
    # Format category for filename
    file_category = "standard" if category_name == "" else "softrandom"
    filename = f'{output_dir}/Algorithm_Comparison_{file_category}_freq{freq_value}.pdf'
    
    plt.savefig(filename)
    print(f"Created plot: {filename}")
    plt.close()

# Function to create RDY variant comparison plots - focusing on sqrt comparisons
def create_rdynamic_comparison_plots(data, output_dir, freq_value, category_name):
    # Define Rdynamic comparison ratio columns to analyze with comments for clarity
    rdynamic_comparison_columns = [
        "Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio",    # RDY_6 vs RDY_8
        "Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio",   # RDY_6 vs RDY_10
        "Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio",   # RDY_8 vs RDY_10
        "Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio",    # RDY_2 vs RDY_6
        "Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio",    # RDY_2 vs RDY_8
        "Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio"    # RDY_2 vs RDY_10
    ]
    
    # Check if these columns exist in the data
    available_columns = [col for col in rdynamic_comparison_columns if col in data.columns]
    if not available_columns:
        print("No Rdynamic comparison columns found in the data")
        return
    
    # Create the plot
    plt.figure(figsize=(14, 10))
    
    # Plot each comparison column
    marker_idx = 0
    for col in available_columns:
        # Extract the variants being compared - handle the full names
        parts = col.split('/')
        variant1 = parts[0]  # First part (Rdynamic_sqrt_X)
        
        # Extract second part and remove _ratio suffix
        variant2_part = parts[1] 
        if '_ratio' in variant2_part:
            variant2 = variant2_part.split('_ratio')[0]
        else:
            variant2 = variant2_part
        
        # Choose marker
        marker_style = markers[marker_idx % len(markers)]
        marker_idx += 1
        
        # Pick colors based on variants
        color1 = algorithm_colors.get(variant1, 'black')
        color2 = algorithm_colors.get(variant2, 'black')
        color = color1
        
        # Always use the more robust extraction approach for Rdynamic comparisons
        v1_display = get_rdy_display_name(variant1)
        v2_display = get_rdy_display_name(variant2)
        label = f"{v1_display} vs {v2_display}"
        
        # Sort by arrival_rate and plot
        valid_data = data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
        
        if not valid_data.empty:
            plt.plot(
                valid_data['arrival_rate'],
                valid_data[col],
                marker=marker_style['marker'],
                markersize=marker_style['size'],
                linestyle='-',
                label=label,
                color=color
            )
    
    # Add horizontal line at y=1 (indicates equal performance)
    plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
    
    # Format category name for display
    display_category = "Standard" if category_name == "" else "SoftRandom"
    
    # Add titles, labels, and legend
    plt.title(f'RDY Variant Comparisons - {display_category} (Freq={freq_value})', fontsize=14)
    plt.xlabel('Mean Interarrival Time', fontsize=12)
    plt.ylabel('Ratio', fontsize=12)
    plt.legend(title='Comparison', loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Set fixed y-axis limits from 0.0 to 2.0 as requested
    plt.ylim(0.0, 2.0)
    plt.yticks(np.arange(0.0, 2.1, 0.1))  # Set y-ticks every 0.2
    
    # Set appropriate x-ticks
    x_values = data['arrival_rate'].dropna().unique()
    if len(x_values) > 0:
        min_x = max(min(x_values), 0)
        max_x = max(x_values)
        step = max(1, (max_x - min_x) / 10)
        plt.xticks(np.arange(min_x, max_x + step, step))
    
    # Format category for filename
    file_category = "standard" if category_name == "" else "softrandom"
    filename = f'{output_dir}/RDY_Variant_Comparison_{file_category}_freq{freq_value}.pdf'
    
    # Save plot
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Created plot: {filename}")
    plt.close()

# Function to create plots comparing algorithm vs benchmark for each variant
def create_algorithm_variant_plots(data, output_dir, freq_value, category_name):
    # Define variants to analyze (keeping the original names for data access)
    variants = ["Rdynamic_sqrt_2", "Rdynamic_sqrt_6", "Rdynamic_sqrt_8", "Rdynamic_sqrt_10", "Dynamic"]
    
    # Define benchmarks to compare against
    benchmarks = ["RR", "SRPT", "SETF", "FCFS", "RMLF", "Dynamic"]
    
    # For each variant, create plots comparing it against benchmarks
    for variant in variants:
        plt.figure(figsize=(14, 10))
        
        # Find ratio columns for this variant
        ratio_columns = []
        for benchmark in benchmarks:
            col_name = f"{variant}/{benchmark}_ratio"
            if col_name in data.columns:
                ratio_columns.append(col_name)
        
        if not ratio_columns:
            plt.close()
            continue
        
        # Plot each benchmark comparison
        marker_idx = 0
        for col in ratio_columns:
            # Extract benchmark name
            benchmark = col.split('/')[1].split('_')[0]
            
            # Skip comparing variant to itself
            if variant == benchmark:
                continue
            
            # Choose marker and color
            marker_style = markers[marker_idx % len(markers)]
            marker_idx += 1
            color = algorithm_colors.get(benchmark, 'black')
            
            # Sort and plot valid data
            valid_data = data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
            
            # Get display names
            variant_display = get_rdy_display_name(variant)
            benchmark_display = get_rdy_display_name(benchmark)
            
            if not valid_data.empty:
                plt.plot(
                    valid_data['arrival_rate'],
                    valid_data[col],
                    marker=marker_style['marker'],
                    markersize=marker_style['size'],
                    linestyle='-',
                    label=f"{variant_display} vs {benchmark_display}",
                    color=color
                )
        
        # Add horizontal line at y=1
        plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
        
        # Format for display
        display_category = "Standard" if category_name == "" else "SoftRandom"
        variant_str = get_rdy_display_name(variant)
        
        # Add titles and labels
        plt.title(f'{variant_str} vs Benchmarks - {display_category} (Freq={freq_value})', fontsize=14)
        plt.xlabel('Mean Interarrival Time', fontsize=12)
        plt.ylabel('Ratio (Lower is Better)', fontsize=12)
        plt.legend(title='Comparison', loc='best', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Set fixed y-axis limits from 0.0 to 2.0 as requested
        plt.ylim(0.0, 2.0)
        plt.yticks(np.arange(0.0, 2.1, 0.2))  # Set y-ticks every 0.2
        
        # Set x-ticks
        x_values = data['arrival_rate'].dropna().unique()
        if len(x_values) > 0:
            min_x = max(min(x_values), 0)
            max_x = max(x_values)
            step = max(1, (max_x - min_x) / 10)
            plt.xticks(np.arange(min_x, max_x + step, step))
        
        # Format category for filename
        file_category = "standard" if category_name == "" else "softrandom"
        
        # Save plot
        plt.tight_layout()
        # Use short name for filename if available
        variant_short = get_rdy_display_name(variant)
        variant_filename = variant_short.replace('/', '_').replace(' ', '_')
        filename = f'{output_dir}/{variant_filename}_vs_Benchmarks_{file_category}_freq{freq_value}.pdf'
        plt.savefig(filename)
        print(f"Created plot: {filename}")
        plt.close()

# Define file mappings for "avg" results that are in different directories
avg_file_mappings = {
    "avg_30": "compare_avg_30/all_result_avg_30_cp100.csv",
    "avg_60": "compare_avg_60/all_result_avg_60_cp100.csv",
    "avg_90": "compare_avg_90/all_result_avg_90_cp100.csv"
}

# Process regular "avg" frequencies
for avg_freq, file_path in avg_file_mappings.items():
    if os.path.exists(file_path):
        try:
            # Create directory for output files - use the exact avg_xx format for directory name
            output_dir = f"{plots_dir}/{avg_freq}"
            os.makedirs(output_dir, exist_ok=True)
            
            # Load the data
            data = pd.read_csv(file_path)
            
            # Check for empty DataFrame
            if data.empty:
                print(f"Warning: Empty data file: {file_path}")
                continue
            
            # Debug: Print column names
            print(f"File: {file_path}")
            print(f"Columns: {data.columns.tolist()}")
            
            # Clean data - ensure numerical columns are properly converted
            for col in data.columns:
                if col != 'arrival_rate' and col != 'bp_parameter':
                    if data[col].dtype == object:  # String type
                        try:
                            data[col] = pd.to_numeric(data[col], errors='coerce')
                            print(f"Converted column {col} to numeric")
                        except Exception as e:
                            print(f"Error converting {col} to numeric: {e}")
            
            # Drop rows with NaN in key columns
            data = data.dropna(subset=['arrival_rate'])
            
            # Extract just the number from avg_freq for display purposes
            freq_number = avg_freq.split('_')[1]
            
            # Check if bp_parameter column exists
            if 'bp_parameter' in data.columns:
                # Group data by bp_parameter
                bp_parameters = data['bp_parameter'].unique()
                
                for bp_param in bp_parameters:
                    # Create a specific directory for this bp_parameter
                    bp_dir = f"{output_dir}/{bp_param}"
                    os.makedirs(bp_dir, exist_ok=True)
                    
                    # Filter data for this bp_parameter
                    bp_data = data[data['bp_parameter'] == bp_param]
                    
                    if not bp_data.empty:
                        # Create plots specifically for this bp_parameter
                        create_individual_plots(bp_data, bp_dir, f"{freq_number}_{bp_param}", "")
                        create_rdynamic_comparison_plots(bp_data, bp_dir, f"{freq_number}_{bp_param}", "")
                        create_algorithm_variant_plots(bp_data, bp_dir, f"{freq_number}_{bp_param}", "")
                        
                        print(f"Created plots for {avg_freq} with bp_parameter={bp_param}")
            else:
                # No bp_parameter column, just create standard plots
                standard_dir = f"{output_dir}/standard"
                os.makedirs(standard_dir, exist_ok=True)
                
                create_individual_plots(data, standard_dir, freq_number, "")
                create_rdynamic_comparison_plots(data, standard_dir, freq_number, "")
                create_algorithm_variant_plots(data, standard_dir, freq_number, "")
                
                print(f"Created standard plots for {avg_freq} (no bp_parameter column)")
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")

# Process the regular (non-softrandom) frequencies - THIS IS THE NEW SECTION
for freq in frequencies:
    # Define the file path for regular frequency data
    file_path = f'freq_comp_result/all_result_freq_{freq}_cp30.csv'
    
    # Create directory for output files
    output_dir = f"{plots_dir}/freq_{freq}/standard"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the data
    if os.path.exists(file_path):
        try:
            # Try to read with default settings
            data = pd.read_csv(file_path)
            
            # Check for empty DataFrame
            if data.empty:
                print(f"Warning: Empty data file: {file_path}")
                continue
            
            # Debug: Print column names
            print(f"File: {file_path}")
            print(f"Columns: {data.columns.tolist()}")
            
            # Clean data - ensure numerical columns are properly converted
            for col in data.columns:
                if col != 'arrival_rate':
                    if data[col].dtype == object:  # String type
                        try:
                            data[col] = pd.to_numeric(data[col], errors='coerce')
                            print(f"Converted column {col} to numeric")
                        except Exception as e:
                            print(f"Error converting {col} to numeric: {e}")
            
            # Drop rows with NaN in key columns
            data = data.dropna(subset=['arrival_rate'])
            
            # Create plots (use empty string for standard category)
            create_individual_plots(data, output_dir, freq, "")
            create_rdynamic_comparison_plots(data, output_dir, freq, "")
            create_algorithm_variant_plots(data, output_dir, freq, "")
            
            print(f"Created all plots for standard freq_{freq}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")

# Process the softrandom frequencies
for freq in frequencies:
    # Define the file path for softrandom data
    file_path = f'softrandom_comp_result/all_result_softrandom_{freq}_cp30.csv'
    
    # Create directory for output files
    output_dir = f"{plots_dir}/freq_{freq}/softrandom"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the data
    if os.path.exists(file_path):
        try:
            # Try to read with default settings
            data = pd.read_csv(file_path)
            
            # Check for empty DataFrame
            if data.empty:
                print(f"Warning: Empty data file: {file_path}")
                continue
            
            # Debug: Print column names
            print(f"File: {file_path}")
            print(f"Columns: {data.columns.tolist()}")
            
            # Clean data - ensure numerical columns are properly converted
            for col in data.columns:
                if col != 'arrival_rate':
                    if data[col].dtype == object:  # String type
                        try:
                            data[col] = pd.to_numeric(data[col], errors='coerce')
                            print(f"Converted column {col} to numeric")
                        except Exception as e:
                            print(f"Error converting {col} to numeric: {e}")
            
            # Drop rows with NaN in key columns
            data = data.dropna(subset=['arrival_rate'])
            
            # Create plots (use softrandom_ for category)
            create_individual_plots(data, output_dir, freq, "softrandom_")
            create_rdynamic_comparison_plots(data, output_dir, freq, "softrandom_")
            create_algorithm_variant_plots(data, output_dir, freq, "softrandom_")
            
            print(f"Created all plots for softrandom_{freq}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")