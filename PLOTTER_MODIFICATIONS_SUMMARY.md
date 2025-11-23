# Plotter.py Modifications Summary

## Date: November 23, 2025

## Major Changes

### 1. **Path Configuration Update**
- Changed `BASE_DATA_PATH` from `/Users/melowu/Desktop/ultimus` to `/home/melowu/Work/ultimus`
- This reflects the actual working directory on the Linux system

### 2. **Enhanced Color Contrast**
Modified color scheme for better visibility:
- **SRPT**: Changed from `#ff7f0e` (Orange) to `#FF0000` (Bright Red)
- **FCFS**: Changed from `#d62728` (Red) to `#FFD700` (Gold)
- **RMLF**: Changed from `#404040` (Dark Gray) to `#000000` (Black)

Updated markers for better distinction:
- SRPT: `s` → `D` (diamond)
- FCFS: `v` → `s` (square)
- BAL: `D` → `P` (plus filled)
- Dynamic_BAL: `P` → `p` (pentagon)
- MLFQ: `p` → `h` (hexagon)
- RFDynamic: `h` → `v` (triangle down)

### 3. **New Color Schemes for Mode Comparison**
Added dedicated color and marker schemes for mode comparison plots:
```python
MODE_COLORS = {
    1: '#e74c3c', 2: '#3498db', 3: '#2ecc71', 
    4: '#f39c12', 5: '#9b59b6', 6: '#1abc9c'
}

MODE_MARKERS = {
    1: 'o', 2: 's', 3: '^', 4: 'v', 5: 'D', 6: 'P'
}
```

### 4. **Improved Plot Styling**
Enhanced line and marker visibility:
- Line width: `2.5` → `3.0`
- Marker size: `10` → `12`
- Marker edge width: `1.5` → `2.0`

### 5. **New Benchmark Mode Selection (Excluding Mode 1 & 6)**

Replaced old benchmark selection with new function `find_benchmark_mode_exclude_1_6()`:
- Analyzes only modes 2-5 (excludes mode 1 and mode 6)
- Selects mode with highest frequency of best performance in random cases
- Works for all Dynamic algorithms (Dynamic, Dynamic_BAL, RFDynamic)
- Caches results to avoid redundant calculations

### 6. **Random/Softrandom Data Aggregation**

New function `aggregate_random_softrandom_data()`:
- Automatically processes individual result files
- Supports both distribution types:
  - `Bounded_Pareto_random_result/` and `Bounded_Pareto_softrandom_result/`
  - `normal_random_result/` and `normal_softrandom_result/`
- Groups by coherence_time and averages results
- Saves aggregated files as:
  - `{algorithm}_Bounded_Pareto_random_result.csv`
  - `{algorithm}_Bounded_Pareto_softrandom_result.csv`
  - `{algorithm}_normal_random_result.csv`
  - `{algorithm}_normal_softrandom_result.csv`

### 7. **Updated Random/Softrandom Plotting**

Modified `plot_random_or_softrandom()`:
- Now separates Bounded Pareto and Normal distributions
- Creates separate plots for each distribution type
- Automatically aggregates data before plotting
- Uses new benchmark mode selection
- Output filenames now include distribution type:
  - `{group}_Bounded_Pareto_{random/softrandom}_comparison.png`
  - `{group}_normal_{random/softrandom}_comparison.png`

### 8. **New Mode Comparison Functions**

#### `plot_mode_comparison_avg(algorithm, avg_type)`
Creates mode comparison plots for avg cases:
- One plot per (L, H) parameter combination
- X-axis: Mean Inter-Arrival Time
- Y-axis: L2-Norm Flow Time
- Shows all 6 modes with different colors and markers
- Separates Bounded Pareto and Normal distribution titles
- Output: `{algorithm}_mode_comparison_{avg_type}_BP_L_{L}_H_{H}.png`
- Output: `{algorithm}_mode_comparison_{avg_type}_normal_std_{H}.png`

#### `plot_mode_comparison_random(algorithm, distribution_type, random_type)`
Creates mode comparison plots for random/softrandom cases:
- X-axis: Coherence Time (log scale)
- Y-axis: L2-Norm Flow Time
- Shows all 6 modes with different colors and markers
- Separate plots for Bounded Pareto and Normal distributions
- Output: `{algorithm}_mode_comparison_{distribution_type}_{random_type}.png`

### 9. **Enhanced Main Execution Flow**

Updated `main()` function workflow:
1. Process avg30, avg60, avg90:
   - Algorithm comparison plots (existing)
   - **NEW**: Mode comparison plots for each Dynamic algorithm
   
2. Aggregate all random/softrandom data:
   - Process both Bounded_Pareto and normal distributions
   - For all algorithms (including Dynamic variants)
   
3. Create random/softrandom comparison plots:
   - Separate plots for Bounded_Pareto and Normal
   - For both clairvoyant and non-clairvoyant groups
   
4. **NEW**: Create mode comparison plots:
   - For each Dynamic algorithm
   - For both distribution types
   - For both random and softrandom cases

## Distribution Type Identification

Maintains the same rule for identifying distribution types:
- **Normal Distribution**: `bp_parameter_L > bp_parameter_H`
  - L represents mean, H represents std
- **Bounded Pareto**: `bp_parameter_L <= bp_parameter_H`
  - L and H are Pareto distribution parameters

## File Structure

### Input Files (per algorithm):
- `algorithm_result/{ALGO}_result/avg30_result/*.csv`
- `algorithm_result/{ALGO}_result/Bounded_Pareto_random_result/*.csv`
- `algorithm_result/{ALGO}_result/Bounded_Pareto_softrandom_result/*.csv`
- `algorithm_result/{ALGO}_result/normal_random_result/*.csv`
- `algorithm_result/{ALGO}_result/normal_softrandom_result/*.csv`

### Generated Aggregate Files:
- `algorithm_result/{ALGO}_result/{ALGO}_Bounded_Pareto_random_result.csv`
- `algorithm_result/{ALGO}_result/{ALGO}_Bounded_Pareto_softrandom_result.csv`
- `algorithm_result/{ALGO}_result/{ALGO}_normal_random_result.csv`
- `algorithm_result/{ALGO}_result/{ALGO}_normal_softrandom_result.csv`

### Output Plots:
- Algorithm comparisons (existing)
- **NEW**: Mode comparisons for avg cases
- **NEW**: Mode comparisons for random/softrandom cases
- Updated random/softrandom comparisons with distribution separation

## Benefits

1. **Better Benchmark Selection**: Excludes extreme modes (1 & 6), focuses on practical modes
2. **Automatic Data Processing**: No need for pre-aggregated files
3. **Comprehensive Visualization**: Can now compare all modes visually
4. **Distribution Separation**: Clear separation between Bounded Pareto and Normal cases
5. **Improved Readability**: Higher contrast colors and larger markers
6. **Flexibility**: Handles both distribution types automatically

## Usage

Simply run:
```bash
python3 plotter.py
```

The script will:
1. Aggregate all necessary data
2. Generate all comparison plots
3. Generate all mode comparison plots
4. Save everything to `plots_output/` directory
