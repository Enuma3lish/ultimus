import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define specific comparison sets for each avg value
comparison_sets = {
    "30": [
        "Rdynamic_sqrt_6/RR_ratio",
        "Rdynamic_sqrt_6/SRPT_ratio",
        "Rdynamic_sqrt_6/SETF_ratio",
        "Rdynamic_sqrt_6/FCFS_ratio",
        "Rdynamic_sqrt_6/RMLF_ratio",
        "Rdynamic_sqrt_6/Dynamic_ratio",
        "Dynamic/SRPT_ratio",
        "Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio",
        "Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio"
    ],
    "60": [
        "Rdynamic_sqrt_8/RR_ratio",
        "Rdynamic_sqrt_8/SRPT_ratio",
        "Rdynamic_sqrt_8/SETF_ratio",
        "Rdynamic_sqrt_8/FCFS_ratio",
        "Rdynamic_sqrt_8/RMLF_ratio",
        "Rdynamic_sqrt_8/Dynamic_ratio",
        "Dynamic/SRPT_ratio",
        "Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio"
    ],
    "90": [
        "Rdynamic_sqrt_10/RR_ratio",
        "Rdynamic_sqrt_10/SRPT_ratio",
        "Rdynamic_sqrt_10/SETF_ratio",
        "Rdynamic_sqrt_10/FCFS_ratio",
        "Rdynamic_sqrt_10/RMLF_ratio",
        "Rdynamic_sqrt_10/Dynamic_ratio"
    ]
}

# Load the parameters
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
bp_parameter_30 = [
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)}
]

# Map the avg values to their respective bp_parameter lists
bp_parameter_map = {
    "30": bp_parameter_30,
    "60": bp_parameter_60,
    "90": bp_parameter_90
}

# Define markers and line styles
markers = [
    {'marker': '^', 'size': 10},  # Large upward triangle
    {'marker': '^', 'size': 6},   # Small upward triangle
    {'marker': 'o', 'size': 8},   # Circle
    {'marker': 'v', 'size': 6},   # Small downward triangle
    {'marker': 'v', 'size': 10}   # Large downward triangle
]

# Define colors for different algorithms
algorithm_colors = {
    'RR': 'red',
    'SRPT': 'blue',
    'SETF': 'green',
    'FCFS': 'purple',
    'RMLF': 'orange',
    'Dynamic': 'brown'
}

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
def create_individual_bp_plots(data, bp_parameter, output_dir, avg_value, cp_value):
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
    
    # Create a separate plot for each BP parameter
    for bp_param in unique_bp_params:
        plt.figure(figsize=(14, 10))
        specific_data = data[data['bp_parameter'] == bp_param]
        
        if specific_data.empty:
            print(f"No data for BP parameter {bp_param}")
            plt.close()
            continue
        
        # Define line styles based on ratio type
        line_styles = {
            'RR': {'style': '-', 'color': algorithm_colors['RR']},
            'SRPT': {'style': '-', 'color': algorithm_colors['SRPT']},
            'SETF': {'style': '-', 'color': algorithm_colors['SETF']},
            'FCFS': {'style': '-', 'color': algorithm_colors['FCFS']},
            'RMLF': {'style': '-', 'color': algorithm_colors['RMLF']},
            'Dynamic': {'style': '-', 'color': algorithm_colors['Dynamic']},
            'Rdynamic_sqrt_8': {'style': '--', 'color': 'blue'},
            'Rdynamic_sqrt_10': {'style': ':', 'color': 'green'}
        }
        
        # Plot each ratio column
        for col in ratio_columns:
            # Skip if column doesn't exist
            if col not in specific_data.columns:
                continue
            
            # Parse the ratio column to determine style and label
            parts = col.split('/')
            numerator = parts[0]
            denominator = parts[1].split('_')[0] if '_ratio' in parts[1] else parts[1]
            
            # Determine color and style
            if denominator in algorithm_colors:
                color = algorithm_colors[denominator]
                style_key = denominator
            elif numerator == 'Dynamic' and denominator == 'SRPT':
                color = 'black'  # Special case for Dynamic/SRPT
                style_key = 'SRPT'
            else:
                color = 'black'  # Default
                style_key = 'RR'
            
            linestyle = line_styles.get(style_key, {}).get('style', '-')
            
            # Format label
            if 'Rdynamic' in numerator and 'Rdynamic' in denominator:
                label = f"{numerator.replace('Rdynamic_', '')} vs {denominator.replace('Rdynamic_', '')}"
            elif numerator == 'Dynamic' and denominator == 'SRPT':
                label = 'Dynamic vs SRPT'
            else:
                label = f"{numerator} vs {denominator}"
            
            # Sort and plot valid data
            valid_data = specific_data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
            
            if valid_data.empty:
                continue
            
            plt.plot(
                valid_data['arrival_rate'],
                valid_data[col],
                marker='o',
                markersize=6,
                linestyle=linestyle,
                label=label,
                color=color
            )
        
        # Add horizontal line at y=1 (indicates equal performance)
        plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
        
        # Format BP parameter for title and filename
        bp_param_str = str(bp_param).replace("=", "_").replace(" ", "_").replace(".", "p")
        
        # Add titles, labels, and legend
        plt.title(f'Algorithm Comparison Ratios for BP={bp_param} (Avg={avg_value}, CP={cp_value})', fontsize=14)
        plt.xlabel('Mean Interarrival Time', fontsize=12)
        plt.ylabel('Ratio (Lower is Better)', fontsize=12)
        plt.legend(title='Comparison', loc='best', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Set y-axis limits to focus on meaningful values
        y_values = []
        for line in plt.gca().get_lines():
            y_data = line.get_ydata()
            if len(y_data) > 0:
                valid_y = [y for y in y_data if not np.isnan(y) and np.isfinite(y) and y <= 2]
                y_values.extend(valid_y)
        
        if y_values:
            # Set y-limit based on actual data
            min_y = max(0.5, min(y_values) * 0.9)  # Give some margin below the minimum
            max_y = min(2.0, max(y_values) * 1.1)  # Cap at 2.0 to avoid extreme outliers
            plt.ylim(min_y, max_y)
            
            # Set appropriate y-ticks
            tick_step = (max_y - min_y) / 10
            plt.yticks(np.arange(min_y, max_y + tick_step, tick_step))
        else:
            # Default y-limits if no valid data
            plt.ylim(0.5, 1.5)
            plt.yticks(np.arange(0.5, 1.6, 0.1))
        
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
        filename = f'{output_dir}/BP_{bp_param_str}_Algorithm_Comparison_avg{avg_value}_cp{cp_value}.pdf'
        plt.savefig(filename)
        print(f"Created plot: {filename}")
        plt.close()

# Function to create Rdynamic variant comparison plots
def create_rdynamic_comparison_plots(data, bp_parameter, output_dir, avg_value, cp_value):
    # Define Rdynamic comparison ratio columns to analyze
    rdynamic_comparison_columns = [
        "Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio",
        "Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio",
        "Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio"
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
    
    # Create a single plot with all Rdynamic variant comparisons
    plt.figure(figsize=(14, 10))
    
    # Plot each comparison for each BP parameter
    for bp_param in unique_bp_params:
        specific_data = data[data['bp_parameter'] == bp_param]
        
        if specific_data.empty:
            continue
            
        bp_index = np.where(unique_bp_params == bp_param)[0][0]
        marker_style = markers[bp_index % len(markers)]['marker']
        marker_size = markers[bp_index % len(markers)]['size']
        
        for col in available_columns:
            # Extract the variants being compared
            parts = col.split('/')
            variant1 = parts[0]
            variant2 = parts[1].split('_')[0]
            
            # Pick a distinct color for each comparison
            if "sqrt_6" in variant1 and "sqrt_8" in variant2:
                color = 'blue'
                label = "sqrt_6 vs sqrt_8"
            elif "sqrt_6" in variant1 and "sqrt_10" in variant2:
                color = 'green'
                label = "sqrt_6 vs sqrt_10"
            elif "sqrt_8" in variant1 and "sqrt_10" in variant2:
                color = 'red'
                label = "sqrt_8 vs sqrt_10"
            else:
                color = 'purple'
                label = col.replace('_ratio', '')
            
            # Sort by arrival_rate and plot
            valid_data = specific_data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
            
            if not valid_data.empty:
                plt.plot(
                    valid_data['arrival_rate'],
                    valid_data[col],
                    marker=marker_style,
                    markersize=marker_size,
                    linestyle='-',
                    label=f'{label} (BP={bp_param})',
                    color=color
                )
    
    # Add horizontal line at y=1 (indicates equal performance)
    plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
    
    # Add titles, labels, and legend
    plt.title(f'Rdynamic Variant Comparisons (Avg={avg_value}, CP={cp_value})', fontsize=14)
    plt.xlabel('Mean Interarrival Time', fontsize=12)
    plt.ylabel('Ratio', fontsize=12)
    
    # Handle legend - limit number of items to avoid overcrowding
    handles, labels = plt.gca().get_legend_handles_labels()
    if len(handles) > 12:
        plt.legend(handles[:12], labels[:12], title='Comparison', loc='best', fontsize=8)
    else:
        plt.legend(title='Comparison', loc='best', fontsize=9)
    
    plt.grid(True, alpha=0.3)
    
    # Set y-axis limits
    plt.ylim(0.8, 1.2)  # Focus on values around 1.0
    plt.yticks(np.arange(0.8, 1.21, 0.05))
    
    # Set appropriate x-axis ticks
    x_values = data['arrival_rate'].dropna().unique()
    if len(x_values) > 0:
        min_x = max(min(x_values), 0)
        max_x = max(x_values)
        step = max(1, (max_x - min_x) / 10)
        plt.xticks(np.arange(min_x, max_x + step, step))
    
    # Adjust layout and save
    plt.tight_layout()
    filename = f'{output_dir}/Rdynamic_Variant_Comparison_avg{avg_value}_cp{cp_value}.pdf'
    plt.savefig(filename)
    print(f"Created plot: {filename}")
    plt.close()

# Function to create comprehensive algorithm comparison plots (similar to original)
def create_algorithm_comparison_plots(data, bp_parameter, output_dir, avg_value, cp_value):
    # Create separate plots for different Rdynamic variants
    variants = ["Rdynamic_sqrt_6", "Rdynamic_sqrt_8", "Rdynamic_sqrt_10"]
    
    for variant in variants:
        # Find all ratio columns for this variant
        ratio_columns = [col for col in data.columns if col.startswith(f"{variant}/") and col.endswith("_ratio")]
        
        if not ratio_columns:
            print(f"No ratio columns found for {variant}")
            continue
            
        plt.figure(figsize=(14, 10))
        
        # Get unique bp_parameters and sort them
        unique_bp_params = data['bp_parameter'].unique()
        try:
            unique_bp_params = sorted(unique_bp_params, key=lambda x: get_bp_index(x, bp_parameter))
        except Exception as e:
            print(f"Error sorting bp_parameters: {e}")
        
        # Plot each algorithm comparison for each BP parameter
        for col in ratio_columns:
            # Extract algorithm name from column name
            algo = col.split('/')[1].split('_')[0]
            color = algorithm_colors.get(algo, 'black')
            
            for bp_param in unique_bp_params:
                specific_data = data[data['bp_parameter'] == bp_param]
                
                if specific_data.empty:
                    continue
                    
                bp_index = list(unique_bp_params).index(bp_param)
                marker_style = markers[bp_index % len(markers)]['marker']
                marker_size = markers[bp_index % len(markers)]['size']
                
                # Sort by arrival_rate and plot
                valid_data = specific_data.dropna(subset=[col, 'arrival_rate']).sort_values('arrival_rate')
                
                if not valid_data.empty:
                    plt.plot(
                        valid_data['arrival_rate'],
                        valid_data[col],
                        marker=marker_style,
                        markersize=marker_size,
                        linestyle='-',
                        label=f'{algo} (BP={bp_param})',
                        color=color
                    )
        
        # Add horizontal line at y=1
        plt.axhline(y=1, color='black', linestyle='-', alpha=0.3)
        
        # Clean up variant name for display
        display_variant = variant.replace('_', ' ').title()
        
        # Add titles and labels
        plt.title(f'{display_variant} vs Various Algorithms (Avg={avg_value}, CP={cp_value})', fontsize=14)
        plt.xlabel('Mean Interarrival Time', fontsize=12)
        plt.ylabel('Ratio (Lower is Better)', fontsize=12)
        
        # Handle legend
        handles, labels = plt.gca().get_legend_handles_labels()
        if len(handles) > 12:
            plt.legend(handles[:12], labels[:12], title='Algorithm and BP Parameter', loc='best', fontsize=8)
        else:
            plt.legend(title='Algorithm and BP Parameter', loc='best', fontsize=9)
        
        plt.grid(True, alpha=0.3)
        
        # Set y-limits
        y_values = []
        for line in plt.gca().get_lines():
            y_data = line.get_ydata()
            if len(y_data) > 0:
                valid_y = [y for y in y_data if not np.isnan(y) and np.isfinite(y) and y <= 2]
                y_values.extend(valid_y)
        
        if y_values:
            if any(y <= 2 for y in y_values):
                plt.ylim(0, 2)
                plt.yticks(np.arange(0, 2.1, 0.1))
            else:
                max_y = min(max(y_values), 5)
                plt.ylim(0, max_y)
                plt.yticks(np.arange(0, max_y + 0.1, max_y / 10))
        else:
            plt.ylim(0.5, 1.5)
            plt.yticks(np.arange(0.5, 1.6, 0.1))
        
        # Set x-ticks
        x_values = data['arrival_rate'].dropna().unique()
        if len(x_values) > 0:
            min_x = max(min(x_values), 0)
            max_x = max(x_values)
            step = max(1, (max_x - min_x) / 10)
            plt.xticks(np.arange(min_x, max_x + step, step))
        
        # Save the plot
        plt.tight_layout()
        variant_str = variant.replace('/', '_').replace(' ', '_')
        filename = f'{output_dir}/{variant_str}_Comparison_avg{avg_value}_cp{cp_value}.pdf'
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
            
            # Extract CP value from the file name (hardcoded to 60 based on filenames)
            cp_value = "60"
            
            # Generate program name based on the directory
            program_name = f"avg{avg_value}_cp{cp_value}"
            
            # Create individual BP parameter plots with specified comparison sets
            create_individual_bp_plots(data, bp_parameter, output_dir, avg_value, cp_value)
            
            print(f"Created plots for {program_name}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")