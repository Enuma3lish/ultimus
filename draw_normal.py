import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define expanded comparison sets for all avg values
# Using the full set of columns for all avg values
new_comparison_columns = [
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

# Checkpoint columns removed as requested

comparison_sets = {
    "30": new_comparison_columns,
    "60": new_comparison_columns,
    "90": new_comparison_columns
}

# Load the parameters
bp_parameter_30 = [
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)}
]

bp_parameter_60 = [
    {"L": 56.300, "H": pow(2, 6)},
    {"L": 18.900, "H": pow(2, 9)},
    {"L": 12.400, "H": pow(2, 12)},
    {"L": 9.800, "H": pow(2, 15)},
    {"L": 8.500, "H": pow(2, 18)}
]

bp_parameter_90 = [
    {"L": 32.300, "H": pow(2, 9)},
    {"L": 19.700, "H": pow(2, 12)},
    {"L": 15.300, "H": pow(2, 15)},
    {"L": 13.000, "H": pow(2, 18)}
]

# Map the avg values to their respective bp_parameter lists
bp_parameter_map = {
    "30": bp_parameter_30,
    "60": bp_parameter_60,
    "90": bp_parameter_90
}

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

# Function to get the index of a bp_parameter in the ordered list
def get_bp_index(bp_param, param_list):
    # Handle string or numeric bp_param
    if isinstance(bp_param, str):
        # Try to extract L value from the string
        import re
        
        # Look for patterns like L=16.772 or L=16.77
        l_value_match = re.search(r'L=(\d+\.?\d*)', bp_param)
        if l_value_match:
            l_value = float(l_value_match.group(1))
            # Find closest matching L value in param_list
            for i, param in enumerate(param_list):
                if abs(param['L'] - l_value) < 0.1:  # Allow small difference for rounding
                    return i
        else:
            # Fallback to string matching if regex fails
            for i, param in enumerate(param_list):
                # Try different string formats
                if any([
                    f"{param['L']:.3f}" in bp_param,
                    f"{param['L']}" in bp_param,
                    f"{param['L']:.1f}" in bp_param,
                    # Include format with no trailing zeros
                    f"{float(param['L'])}" in bp_param
                ]):
                    return i
    elif isinstance(bp_param, (int, float)):
        # If bp_param is a number, find closest matching L value
        for i, param in enumerate(param_list):
            if abs(param['L'] - bp_param) < 0.1:  # Allow small difference
                return i
    
    # Return default index if no match found
    print(f"Warning: Could not match BP parameter '{bp_param}' to any in the list")
    return 0  # Return first index as default instead of max

# Function to create individual plots for each bp_parameter showing specific algorithm ratios
def create_individual_bp_plots(data, bp_parameter, output_dir, avg_value):
    # Use only the specific comparison set for this avg value
    ratio_columns = comparison_sets.get(avg_value, [])
    
    if not ratio_columns:
        print(f"No comparison columns defined for avg value {avg_value}")
        return
    
    # Filter to only include columns that actually exist in the data
    ratio_columns = [col for col in ratio_columns if col in data.columns]
    
    if not ratio_columns:
        print(f"None of the specified comparison columns for avg value {avg_value} found in data")
        return
    
    # Get unique bp_parameters
    if 'bp_parameter' in data.columns:
        unique_bp_params = data['bp_parameter'].unique()
        try:
            # Sort bp_parameters based on the L value
            unique_bp_params = sorted(unique_bp_params, key=lambda x: get_bp_index(x, bp_parameter))
        except Exception as e:
            print(f"Error sorting bp_parameters: {e}")
    else:
        print("Warning: 'bp_parameter' column not found in data")
        return
    
    # Group the ratio columns by algorithm type
    algorithm_groups = {}
    for col in ratio_columns:
        parts = col.split('/')
        if len(parts) >= 2:
            numerator = parts[0]
            if numerator not in algorithm_groups:
                algorithm_groups[numerator] = []
            algorithm_groups[numerator].append(col)
    
    # Create a separate plot for each BP parameter
    for bp_param in unique_bp_params:
        plt.figure(figsize=(14, 10))
        specific_data = data[data['bp_parameter'] == bp_param]
        
        if specific_data.empty:
            print(f"No data for BP parameter {bp_param}")
            plt.close()
            continue
        
        # Plot each ratio column
        marker_idx = 0
        for col in ratio_columns:
            # Skip if column doesn't exist or has no data
            if col not in specific_data.columns or specific_data[col].isnull().all():
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
            valid_data = specific_data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
            
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
        
        # Checkpoint data removed as requested
        
        # Add horizontal line at y=1 (indicates equal performance)
        plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
        
        # Format BP parameter for title and filename
        bp_param_str = str(bp_param).replace("=", "_").replace(" ", "_").replace(".", "p")
        
        # Add titles, labels, and legend
        plt.title(f'Algorithm Comparison Ratios for BP={bp_param} (Avg={avg_value})', fontsize=14)
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
        plt.yticks(np.arange(0.0, 2.1, 0.2))  # Set y-ticks every 0.2
        
        # Set appropriate x-ticks based on data range
        x_values = specific_data['arrival_rate'].dropna().unique()
        if len(x_values) > 0:
            min_x = max(min(x_values), 0)
            max_x = max(x_values)
            
            # Calculate appropriate step size
            step = max(1, (max_x - min_x) / 10)
            plt.xticks(np.arange(min_x, max_x + step, step))
        
        # Adjust layout and save
        plt.tight_layout()
        filename = f'{output_dir}/BP_{bp_param_str}_Algorithm_Comparison_avg{avg_value}.pdf'
        plt.savefig(filename)
        print(f"Created plot: {filename}")
        plt.close()

# Function to create RDY variant comparison plots - focusing on sqrt comparisons
def create_rdynamic_comparison_plots(data, bp_parameter, output_dir, avg_value):
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
    
    # Get unique bp_parameters
    if 'bp_parameter' in data.columns:
        unique_bp_params = data['bp_parameter'].unique()
        try:
            unique_bp_params = sorted(unique_bp_params, key=lambda x: get_bp_index(x, bp_parameter))
        except Exception as e:
            print(f"Error sorting bp_parameters: {e}")
    else:
        print("Warning: 'bp_parameter' column not found in data")
        return
    
    # Create a separate plot for each BP parameter
    for bp_param in unique_bp_params:
        plt.figure(figsize=(14, 10))
        specific_data = data[data['bp_parameter'] == bp_param]
        
        if specific_data.empty:
            plt.close()
            continue
        
        # Plot each comparison column
        marker_idx = 0
        for col in available_columns:
            # Remove debug prints in final version
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
            valid_data = specific_data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
            
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
        
        # Format title and filename
        bp_param_str = str(bp_param).replace("=", "_").replace(" ", "_").replace(".", "p")
        
        # Add titles, labels, and legend
        plt.title(f'RDY Variant Comparisons - BP={bp_param} (Avg={avg_value})', fontsize=14)
        plt.xlabel('Mean Interarrival Time', fontsize=12)
        plt.ylabel('Ratio', fontsize=12)
        plt.legend(title='Comparison', loc='best', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Set fixed y-axis limits from 0.0 to 2.0 as requested
        plt.ylim(0.0, 2.0)
        plt.yticks(np.arange(0.0, 2.1, 0.2))  # Set y-ticks every 0.2
        
        # Set appropriate x-ticks
        x_values = specific_data['arrival_rate'].dropna().unique()
        if len(x_values) > 0:
            min_x = max(min(x_values), 0)
            max_x = max(x_values)
            step = max(1, (max_x - min_x) / 10)
            plt.xticks(np.arange(min_x, max_x + step, step))
        
        # Save plot
        plt.tight_layout()
        filename = f'{output_dir}/BP_{bp_param_str}_RDY_Variant_Comparison_avg{avg_value}.pdf'
        plt.savefig(filename)
        print(f"Created plot: {filename}")
        plt.close()

# Function to create plots comparing algorithm vs benchmark for each variant
def create_algorithm_variant_plots(data, bp_parameter, output_dir, avg_value):
    # Define variants to analyze (keeping the original names for data access)
    variants = ["Rdynamic_sqrt_2", "Rdynamic_sqrt_6", "Rdynamic_sqrt_8", "Rdynamic_sqrt_10", "Dynamic"]
    
    # Display names will be used in the plot labels
    
    # Define benchmarks to compare against
    benchmarks = ["RR", "SRPT", "SETF", "FCFS", "RMLF", "Dynamic"]
    
    # Get unique bp_parameters
    if 'bp_parameter' not in data.columns:
        print("Warning: 'bp_parameter' column not found in data")
        return
        
    unique_bp_params = data['bp_parameter'].unique()
    try:
        unique_bp_params = sorted(unique_bp_params, key=lambda x: get_bp_index(x, bp_parameter))
    except Exception as e:
        print(f"Error sorting bp_parameters: {e}")
    
    # For each variant, create plots comparing it against benchmarks
    for variant in variants:
        for bp_param in unique_bp_params:
            plt.figure(figsize=(14, 10))
            specific_data = data[data['bp_parameter'] == bp_param]
            
            if specific_data.empty:
                plt.close()
                continue
            
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
                valid_data = specific_data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
                
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
            
            # Format for display and filename
            bp_param_str = str(bp_param).replace("=", "_").replace(" ", "_").replace(".", "p")
            variant_str = get_rdy_display_name(variant)
            
            # Add titles and labels
            plt.title(f'{variant_str} vs Benchmarks - BP={bp_param} (Avg={avg_value})', fontsize=14)
            plt.xlabel('Mean Interarrival Time', fontsize=12)
            plt.ylabel('Ratio (Lower is Better)', fontsize=12)
            plt.legend(title='Comparison', loc='best', fontsize=10)
            plt.grid(True, alpha=0.3)
            
            # Set fixed y-axis limits from 0.0 to 2.0 as requested
            plt.ylim(0.0, 2.0)
            plt.yticks(np.arange(0.0, 2.1, 0.2))  # Set y-ticks every 0.2
            
            # Set x-ticks
            x_values = specific_data['arrival_rate'].dropna().unique()
            if len(x_values) > 0:
                min_x = max(min(x_values), 0)
                max_x = max(x_values)
                step = max(1, (max_x - min_x) / 10)
                plt.xticks(np.arange(min_x, max_x + step, step))
            
            # Save plot
            plt.tight_layout()
            # Use short name for filename if available
            variant_short = get_rdy_display_name(variant)
            variant_filename = variant_short.replace('/', '_').replace(' ', '_')
            filename = f'{output_dir}/BP_{bp_param_str}_{variant_filename}_vs_Benchmarks_avg{avg_value}.pdf'
            plt.savefig(filename)
            print(f"Created plot: {filename}")
            plt.close()

# Process each avg value (30, 60, 90)
for avg_value in ["30", "60", "90"]:
    # Get the corresponding bp_parameter list
    bp_parameter = bp_parameter_map[avg_value]
    
    # Define the file path
    file_path = f'compare_avg_{avg_value}/all_result_avg_{avg_value}_cp60.csv'
    
    # Create directory for output files
    output_dir = f"{plots_dir}/avg_{avg_value}"
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
            
            # Debug: Print column names and sample of bp_parameter values
            print(f"File: {file_path}")
            print(f"Columns: {data.columns.tolist()}")
            
            if 'bp_parameter' not in data.columns:
                print(f"Error: 'bp_parameter' column not found in {file_path}")
                continue
                
            print(f"BP parameters: {data['bp_parameter'].unique()}")
            
            # Clean data - ensure all required columns exist
            # Check numerical columns and fix any non-numeric values
            for col in data.columns:
                if col != 'bp_parameter' and col != 'arrival_rate':
                    if data[col].dtype == object:  # String type
                        try:
                            data[col] = pd.to_numeric(data[col], errors='coerce')
                            print(f"Converted column {col} to numeric")
                        except Exception as e:
                            print(f"Error converting {col} to numeric: {e}")
            
            # Drop rows with NaN in key columns
            data = data.dropna(subset=['arrival_rate', 'bp_parameter'])
            
            # Create individual BP parameter plots with all comparison columns
            create_individual_bp_plots(data, bp_parameter, output_dir, avg_value)
            
            # Create RDY variant comparison plots for each BP parameter
            create_rdynamic_comparison_plots(data, bp_parameter, output_dir, avg_value)
            
            # Create algorithm variant vs benchmark plots
            create_algorithm_variant_plots(data, bp_parameter, output_dir, avg_value)
            
            print(f"Created all plots for avg_{avg_value}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")