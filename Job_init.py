import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math
import os
import random
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # For non-GUI environments
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from collections import defaultdict

# Define inter-arrival times
inter_arrival_time = [i for i in range(20, 41, 2)]

# High load threshold: inter_arrival <= 25 means high load (H)
HIGH_LOAD_THRESHOLD = 25

# Bounded Pareto parameters
bp_parameter_60 = [
    {"L": 56.300, "H": pow(2, 6), "type": "BP"},
    {"L": 18.900, "H": pow(2, 9), "type": "BP"},
    {"L": 12.400, "H": pow(2, 12), "type": "BP"},
    {"L": 9.800, "H": pow(2, 15), "type": "BP"},
    {"L": 8.500, "H": pow(2, 18), "type": "BP"}
]
bp_parameter_90 = [
    {"L": 32.300, "H": pow(2, 9), "type": "BP"},
    {"L": 19.700, "H": pow(2, 12), "type": "BP"},
    {"L": 15.300, "H": pow(2, 15), "type": "BP"},
    {"L": 13.000, "H": pow(2, 18), "type": "BP"}
]
bp_parameter_30 = [
    {"L": 16.772, "H": pow(2, 6), "type": "BP"},
    {"L": 7.918, "H": pow(2, 9), "type": "BP"},
    {"L": 5.649, "H": pow(2, 12), "type": "BP"},
    {"L": 4.639, "H": pow(2, 15), "type": "BP"},
    {"L": 4.073, "H": pow(2, 18), "type": "BP"}
]

# Normal distribution parameters
normal_parameter_30 = [
    {"mean": 30, "std": 6, "type": "Normal"},
    {"mean": 30, "std": 9, "type": "Normal"},
    {"mean": 30, "std": 12, "type": "Normal"},
    {"mean": 30, "std": 15, "type": "Normal"},
    {"mean": 30, "std": 18, "type": "Normal"}
]

normal_parameter_60 = [
    {"mean": 60, "std": 12, "type": "Normal"},
    {"mean": 60, "std": 18, "type": "Normal"},
    {"mean": 60, "std": 24, "type": "Normal"}
]

normal_parameter_90 = [
    {"mean": 90, "std": 18, "type": "Normal"},
    {"mean": 90, "std": 27, "type": "Normal"},
    {"mean": 90, "std": 36, "type": "Normal"}
]

# Create parameter sets
parameter_sets = {
    "avg_30": bp_parameter_30 + normal_parameter_30,
    "avg_60": bp_parameter_60 + normal_parameter_60,
    "avg_90": bp_parameter_90 + normal_parameter_90
}

normal_parameter_sets = {
    "avg_30": normal_parameter_30,
    "avg_60": normal_parameter_60,
    "avg_90": normal_parameter_90
}

bp_parameter_sets = {
    "avg_30": bp_parameter_30,
    "avg_60": bp_parameter_60,
    "avg_90": bp_parameter_90
}


# =============================================================================
# Basic Generation Functions
# =============================================================================

def generate_bounded_pareto(alpha, xmin, xmax, size=1):
    """Generate bounded Pareto distributed random values."""
    cdf_xmin = 1 - (xmin / xmax) ** alpha
    u = np.random.uniform(0, cdf_xmin, size=size)
    x = xmin / ((1 - u) ** (1 / alpha))
    return x


def generate_normal_job_size(mean, std, size=1):
    """Generate job sizes from normal distribution."""
    samples = np.random.normal(mean, std, size=size)
    samples = np.maximum(samples, 1)
    return samples


def generate_job_size(param, size=1):
    """Generate job size based on parameter type."""
    if param["type"] == "BP":
        return generate_bounded_pareto(1.1, param["L"], param["H"], size=size)
    elif param["type"] == "Normal":
        return generate_normal_job_size(param["mean"], param["std"], size=size)
    else:
        raise ValueError(f"Unknown parameter type: {param['type']}")


def job_init(num_jobs, avg_inter_arrival_time, param):
    """Create jobs with either bounded Pareto or Normal distribution."""
    samples = []
    job_sizes = [math.ceil(size) for size in generate_job_size(param, size=num_jobs)]
    
    current_time = 0
    arrival_times = []
    for _ in range(num_jobs):
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        arrival_times.append(current_time)
    
    for k in range(num_jobs):
        samples.append({"arrival_time": arrival_times[k], "job_size": job_sizes[k]})
    return samples


# =============================================================================
# Analysis Functions
# =============================================================================

def is_high_load(inter_arrival_setting: int, threshold: int = HIGH_LOAD_THRESHOLD) -> bool:
    """Determine if an inter-arrival setting represents high load."""
    return inter_arrival_setting <= threshold


def find_longest_contiguous_H(period_records: List[Dict]) -> Dict:
    """
    Find the longest contiguous high-load (H) period sequence.

    Returns:
        dict with longest H segment info including job indices
    """
    if not period_records:
        return {
            "longest_H_duration": 0,
            "longest_H_period_count": 0,
            "longest_H_job_count": 0,
            "longest_H_total_job_size": 0,
            "longest_H_avg_job_size": 0.0,
            "longest_H_start_time": 0,
            "longest_H_end_time": 0,
            "start_job_index": -1,
            "end_job_index": -1
        }

    max_segment = None
    max_duration = 0
    max_segment_start_period_idx = -1

    current_segment_start = None
    current_segment_periods = []
    current_segment_start_period_idx = -1

    for i, period in enumerate(period_records):
        if period["is_high_load"]:
            if current_segment_start is None:
                current_segment_start = i
                current_segment_periods = [period]
                current_segment_start_period_idx = i
            else:
                current_segment_periods.append(period)
        else:
            # End of H segment
            if current_segment_periods:
                duration = sum(p["period_duration"] for p in current_segment_periods)
                if duration > max_duration:
                    max_duration = duration
                    max_segment = current_segment_periods.copy()
                    max_segment_start_period_idx = current_segment_start_period_idx
            current_segment_start = None
            current_segment_periods = []
            current_segment_start_period_idx = -1

    # Check last segment
    if current_segment_periods:
        duration = sum(p["period_duration"] for p in current_segment_periods)
        if duration > max_duration:
            max_duration = duration
            max_segment = current_segment_periods.copy()
            max_segment_start_period_idx = current_segment_start_period_idx

    if max_segment is None or len(max_segment) == 0:
        return {
            "longest_H_duration": 0,
            "longest_H_period_count": 0,
            "longest_H_job_count": 0,
            "longest_H_total_job_size": 0,
            "longest_H_avg_job_size": 0.0,
            "longest_H_start_time": 0,
            "longest_H_end_time": 0,
            "start_job_index": -1,
            "end_job_index": -1
        }

    total_job_count = sum(p["job_count"] for p in max_segment)
    total_job_size = sum(p["total_job_size"] for p in max_segment)
    avg_job_size = total_job_size / total_job_count if total_job_count > 0 else 0.0

    # Calculate start_job_index: sum of job_count from all periods before max_segment
    start_job_index = sum(p["job_count"] for p in period_records[:max_segment_start_period_idx])
    end_job_index = start_job_index + total_job_count - 1

    return {
        "longest_H_duration": max_duration,
        "longest_H_period_count": len(max_segment),
        "longest_H_job_count": total_job_count,
        "longest_H_total_job_size": total_job_size,
        "longest_H_avg_job_size": avg_job_size,
        "longest_H_start_time": max_segment[0]["period_start_time"],
        "longest_H_end_time": max_segment[-1]["period_end_time"],
        "start_job_index": start_job_index,
        "end_job_index": end_job_index
    }


def analyze_single_instance(samples: List[Dict], period_records: List[Dict]) -> Dict:
    """
    Analyze a single instance and return key metrics.

    Returns:
        dict with longest H duration ratio (as percentage)
    """
    total_duration = sum(p["period_duration"] for p in period_records) if period_records else 0

    if not period_records:
        return {
            "longest_H_duration_ratio": 0.0
        }

    # Get longest H segment stats
    longest_H_stats = find_longest_contiguous_H(period_records)

    # 指標: 最長連續H時間片段佔總執行時間的百分比
    longest_H_duration_ratio = (longest_H_stats["longest_H_duration"] / total_duration * 100) if total_duration > 0 else 0.0

    result = {
        "longest_H_duration_ratio": longest_H_duration_ratio
    }

    return result


def aggregate_group_results(results: List[Dict]) -> Dict:
    """
    Aggregate results from multiple replications into mean, std, min, max.
    
    Args:
        results: List of result dicts from analyze_single_instance
        
    Returns:
        dict with aggregated statistics for each metric
    """
    if not results:
        return {}
    
    # Get all metric keys
    keys = results[0].keys()
    
    aggregated = {}
    for key in keys:
        values = [r[key] for r in results]
        aggregated[key] = {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values)
        }
    
    return aggregated


def save_analysis_csv(output_path: str, aggregated: Dict):
    """Save aggregated analysis results to CSV with simplified format."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Define metric descriptions - only duration ratio
    metric_descriptions = {
        "longest_H_duration_ratio": "最長連續H時間片段佔總時間百分比(%)"
    }

    rows = []
    for metric, stats in aggregated.items():
        if metric in metric_descriptions:
            desc = metric_descriptions.get(metric, metric)
            rows.append({
                "指標": desc,
                "平均值": round(stats["mean"], 2)
            })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')


def plot_metrics_by_coherence_time(all_group_results: Dict[str, List[Dict]], output_base: str = "analysis"):
    """
    Plot metrics vs coherence_time for each combination folder.

    Creates one plot per combination folder with duration ratio metric.
    X-axis: Coherence Time (log scale)
    Y-axis: Percentage (%)
    """
    # Set font support
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # Group results by combination folder (without freq)
    combination_data = defaultdict(lambda: defaultdict(list))

    for group_key, results in all_group_results.items():
        parts = group_key.split("/")
        if len(parts) >= 3 and parts[-1].startswith("freq_"):
            combination_folder = "/".join(parts[:-1])
            freq_str = parts[-1].replace("freq_", "")
            try:
                coherence_time = int(freq_str)
                combination_data[combination_folder][coherence_time].extend(results)
            except ValueError:
                continue

    # Single metric - only duration ratio
    metric_key = "longest_H_duration_ratio"
    metric_label = "Longest H Duration Ratio (%)"

    # Create plot for each combination folder
    for combination_folder, freq_data in tqdm.tqdm(combination_data.items(), desc="Generating plots"):
        fig, ax = plt.subplots(figsize=(10, 6))

        coherence_times = sorted(freq_data.keys())
        y_values = []

        for ct in coherence_times:
            results = freq_data[ct]
            if results:
                values = [r[metric_key] for r in results]
                mean_val = np.mean(values)
                y_values.append(mean_val)
            else:
                y_values.append(0)

        ax.plot(coherence_times, y_values, color="blue", marker="o",
               label=metric_label, linewidth=2, markersize=6)

        ax.set_xlabel("Coherence Time", fontsize=12)
        ax.set_ylabel("Percentage (%)", fontsize=12)
        ax.set_xscale('log', base=2)

        # Title using folder name
        folder_name = combination_folder.split("/")[-1] if "/" in combination_folder else combination_folder
        ax.set_title(f"Metrics vs Coherence Time\n{folder_name}", fontsize=13, fontweight='bold')

        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        plot_folder = os.path.join(output_base, combination_folder)
        os.makedirs(plot_folder, exist_ok=True)
        plot_path = os.path.join(plot_folder, "metrics_plot.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    print(f"Generated {len(combination_data)} plots")


def plot_comparison_conclusion(all_group_results: Dict[str, List[Dict]], output_base: str = "analysis"):
    """
    Create comparison plots for softrandom vs combination_softrandom.

    Creates two comparison images in analysis/conclusion/:
    1. Bounded_Pareto_combination_softrandom vs Bounded_Pareto_softrandom
    2. normal_combination_softrandom vs normal_softrandom

    Each image shows multiple lines with different colors and symbols.
    X-axis: Coherence Time (log scale)
    Y-axis: Percentage (%)
    """
    # Set font support
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # Create conclusion folder
    conclusion_folder = os.path.join(output_base, "conclusion")
    os.makedirs(conclusion_folder, exist_ok=True)

    # Group results by base type and coherence time
    bp_softrandom_data = defaultdict(list)  # {coherence_time: [results]}
    bp_combination_softrandom_data = defaultdict(lambda: defaultdict(list))  # {combo_name: {coherence_time: [results]}}
    normal_softrandom_data = defaultdict(list)
    normal_combination_softrandom_data = defaultdict(lambda: defaultdict(list))

    for group_key, results in all_group_results.items():
        parts = group_key.split("/")
        if len(parts) >= 2 and parts[-1].startswith("freq_"):
            freq_str = parts[-1].replace("freq_", "")
            try:
                coherence_time = int(freq_str)
            except ValueError:
                continue

            base_type = parts[0]

            if base_type == "Bounded_Pareto_softrandom":
                bp_softrandom_data[coherence_time].extend(results)
            elif base_type == "Bounded_Pareto_combination_softrandom":
                if len(parts) >= 2:
                    combo_name = parts[1] if len(parts) > 2 else "default"
                    bp_combination_softrandom_data[combo_name][coherence_time].extend(results)
            elif base_type == "normal_softrandom":
                normal_softrandom_data[coherence_time].extend(results)
            elif base_type == "normal_combination_softrandom":
                if len(parts) >= 2:
                    combo_name = parts[1] if len(parts) > 2 else "default"
                    normal_combination_softrandom_data[combo_name][coherence_time].extend(results)

    metric_key = "longest_H_duration_ratio"

    # Define colors and markers for different lines
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', 'h', '*']

    # =========================================================================
    # Plot 1: Bounded_Pareto comparison
    # =========================================================================
    fig, ax = plt.subplots(figsize=(12, 8))

    all_coherence_times = set()
    line_idx = 0

    # Plot Bounded_Pareto_softrandom
    if bp_softrandom_data:
        coherence_times = sorted(bp_softrandom_data.keys())
        all_coherence_times.update(coherence_times)
        y_values = []
        for ct in coherence_times:
            if bp_softrandom_data[ct]:
                values = [r[metric_key] for r in bp_softrandom_data[ct]]
                y_values.append(np.mean(values))
            else:
                y_values.append(0)

        ax.plot(coherence_times, y_values,
               color=colors[line_idx % len(colors)],
               marker=markers[line_idx % len(markers)],
               label="Bounded_Pareto_softrandom",
               linewidth=2, markersize=8)
        line_idx += 1

    # Plot each Bounded_Pareto_combination_softrandom variant
    for combo_name in sorted(bp_combination_softrandom_data.keys()):
        combo_data = bp_combination_softrandom_data[combo_name]
        coherence_times = sorted(combo_data.keys())
        all_coherence_times.update(coherence_times)
        y_values = []
        for ct in coherence_times:
            if combo_data[ct]:
                values = [r[metric_key] for r in combo_data[ct]]
                y_values.append(np.mean(values))
            else:
                y_values.append(0)

        label = f"BP_combination_{combo_name}"
        ax.plot(coherence_times, y_values,
               color=colors[line_idx % len(colors)],
               marker=markers[line_idx % len(markers)],
               label=label,
               linewidth=2, markersize=6)
        line_idx += 1

    ax.set_xlabel("Coherence Time", fontsize=12)
    ax.set_ylabel("Percentage (%)", fontsize=12)
    ax.set_xscale('log', base=2)
    ax.set_title("Bounded Pareto: Softrandom vs Combination Softrandom\nLongest H Duration Ratio (%)",
                fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(conclusion_folder, "Bounded_Pareto_comparison.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {plot_path}")

    # =========================================================================
    # Plot 2: Normal comparison
    # =========================================================================
    fig, ax = plt.subplots(figsize=(12, 8))

    all_coherence_times = set()
    line_idx = 0

    # Plot normal_softrandom
    if normal_softrandom_data:
        coherence_times = sorted(normal_softrandom_data.keys())
        all_coherence_times.update(coherence_times)
        y_values = []
        for ct in coherence_times:
            if normal_softrandom_data[ct]:
                values = [r[metric_key] for r in normal_softrandom_data[ct]]
                y_values.append(np.mean(values))
            else:
                y_values.append(0)

        ax.plot(coherence_times, y_values,
               color=colors[line_idx % len(colors)],
               marker=markers[line_idx % len(markers)],
               label="normal_softrandom",
               linewidth=2, markersize=8)
        line_idx += 1

    # Plot each normal_combination_softrandom variant
    for combo_name in sorted(normal_combination_softrandom_data.keys()):
        combo_data = normal_combination_softrandom_data[combo_name]
        coherence_times = sorted(combo_data.keys())
        all_coherence_times.update(coherence_times)
        y_values = []
        for ct in coherence_times:
            if combo_data[ct]:
                values = [r[metric_key] for r in combo_data[ct]]
                y_values.append(np.mean(values))
            else:
                y_values.append(0)

        label = f"normal_combination_{combo_name}"
        ax.plot(coherence_times, y_values,
               color=colors[line_idx % len(colors)],
               marker=markers[line_idx % len(markers)],
               label=label,
               linewidth=2, markersize=6)
        line_idx += 1

    ax.set_xlabel("Coherence Time", fontsize=12)
    ax.set_ylabel("Percentage (%)", fontsize=12)
    ax.set_xscale('log', base=2)
    ax.set_title("Normal: Softrandom vs Combination Softrandom\nLongest H Duration Ratio (%)",
                fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(conclusion_folder, "normal_comparison.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {plot_path}")

    print(f"Comparison plots saved to {conclusion_folder}/")


def get_group_key(folder_path: str) -> str:
    """
    Extract group key from folder path.
    
    Example:
        Input: data/Bounded_Pareto_combination_random_1/four_combination_H64_H512_H4096_H32768/freq_2_1
        Output: Bounded_Pareto_combination_random/four_combination_H64_H512_H4096_H32768/freq_2
    """
    parts = folder_path.replace("data/", "").split("/")
    
    # Remove replication suffix from each part
    cleaned_parts = []
    for part in parts:
        # Remove trailing _1, _2, ..., _10
        if "_" in part:
            # Check if last segment is a number
            segments = part.rsplit("_", 1)
            if len(segments) == 2 and segments[1].isdigit():
                cleaned_parts.append(segments[0])
            else:
                cleaned_parts.append(part)
        else:
            cleaned_parts.append(part)
    
    return "/".join(cleaned_parts)


# =============================================================================
# Job Generation Functions (with period_records)
# =============================================================================

def bounded_pareto_random_job_init(num_jobs, coherence_time=1) -> Tuple[List[Dict], List[Dict]]:
    """
    Create jobs with randomly selected Bounded Pareto parameters only from avg_30.
    
    Returns:
        tuple: (samples, period_records)
    """
    samples = []
    period_records = []
    
    all_bp_parameters = bp_parameter_30
    
    current_param = random.choice(all_bp_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0
    
    # Track current period
    period_start_time = 0
    period_job_indices = []
    period_total_job_size = 0
    
    for job_idx in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            # Save current period before switching
            if period_job_indices:
                period_records.append({
                    "period_start_time": period_start_time,
                    "period_end_time": current_time,
                    "period_duration": current_time - period_start_time,
                    "inter_arrival_setting": current_avg_inter_arrival,
                    "is_high_load": is_high_load(current_avg_inter_arrival),
                    "job_count": len(period_job_indices),
                    "total_job_size": period_total_job_size,
                    "param_info": current_param.copy()
                })
            
            # Switch parameters
            current_param = random.choice(all_bp_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
            
            # Start new period
            period_start_time = current_time
            period_job_indices = []
            period_total_job_size = 0
        
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
        period_job_indices.append(job_idx)
        period_total_job_size += job_size
    
    # Save last period
    if period_job_indices:
        period_records.append({
            "period_start_time": period_start_time,
            "period_end_time": current_time,
            "period_duration": current_time - period_start_time,
            "inter_arrival_setting": current_avg_inter_arrival,
            "is_high_load": is_high_load(current_avg_inter_arrival),
            "job_count": len(period_job_indices),
            "total_job_size": period_total_job_size,
            "param_info": current_param.copy()
        })
    
    return samples, period_records


def normal_random_job_init(num_jobs, coherence_time=1) -> Tuple[List[Dict], List[Dict]]:
    """
    Create jobs with randomly selected Normal distribution parameters only.
    
    Returns:
        tuple: (samples, period_records)
    """
    samples = []
    period_records = []
    
    all_normal_parameters = []
    for param_set in normal_parameter_sets.values():
        all_normal_parameters.extend(param_set)
    
    current_param = random.choice(all_normal_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0
    
    period_start_time = 0
    period_job_indices = []
    period_total_job_size = 0
    
    for job_idx in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            if period_job_indices:
                period_records.append({
                    "period_start_time": period_start_time,
                    "period_end_time": current_time,
                    "period_duration": current_time - period_start_time,
                    "inter_arrival_setting": current_avg_inter_arrival,
                    "is_high_load": is_high_load(current_avg_inter_arrival),
                    "job_count": len(period_job_indices),
                    "total_job_size": period_total_job_size,
                    "param_info": current_param.copy()
                })
            
            current_param = random.choice(all_normal_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
            
            period_start_time = current_time
            period_job_indices = []
            period_total_job_size = 0
        
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
        period_job_indices.append(job_idx)
        period_total_job_size += job_size
    
    if period_job_indices:
        period_records.append({
            "period_start_time": period_start_time,
            "period_end_time": current_time,
            "period_duration": current_time - period_start_time,
            "inter_arrival_setting": current_avg_inter_arrival,
            "is_high_load": is_high_load(current_avg_inter_arrival),
            "job_count": len(period_job_indices),
            "total_job_size": period_total_job_size,
            "param_info": current_param.copy()
        })
    
    return samples, period_records


def bounded_pareto_soft_random_job_init(num_jobs, coherence_time=1) -> Tuple[List[Dict], List[Dict]]:
    """
    Create jobs with soft randomness for Bounded Pareto parameters only from avg_30.
    
    Returns:
        tuple: (samples, period_records)
    """
    samples = []
    period_records = []
    
    current_param_set = bp_parameter_30
    current_param_index = random.randint(0, len(current_param_set) - 1)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    
    current_time = 0
    last_change_time = 0
    
    period_start_time = 0
    period_job_indices = []
    period_total_job_size = 0
    
    for job_idx in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            if period_job_indices:
                period_records.append({
                    "period_start_time": period_start_time,
                    "period_end_time": current_time,
                    "period_duration": current_time - period_start_time,
                    "inter_arrival_setting": current_avg_inter_arrival,
                    "is_high_load": is_high_load(current_avg_inter_arrival),
                    "job_count": len(period_job_indices),
                    "total_job_size": period_total_job_size,
                    "param_info": current_param_set[current_param_index].copy()
                })
            
            num_params = len(current_param_set)
            if current_param_index == 0:
                if random.random() < 0.5:
                    current_param_index = min(1, num_params - 1)
            elif current_param_index == num_params - 1:
                if random.random() < 0.5:
                    current_param_index = max(0, num_params - 2)
            else:
                choice = random.random()
                if choice < 1/3:
                    pass
                elif choice < 2/3:
                    current_param_index -= 1
                else:
                    current_param_index += 1
            
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
            
            period_start_time = current_time
            period_job_indices = []
            period_total_job_size = 0
        
        current_param = current_param_set[current_param_index]
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
        period_job_indices.append(job_idx)
        period_total_job_size += job_size
    
    if period_job_indices:
        period_records.append({
            "period_start_time": period_start_time,
            "period_end_time": current_time,
            "period_duration": current_time - period_start_time,
            "inter_arrival_setting": current_avg_inter_arrival,
            "is_high_load": is_high_load(current_avg_inter_arrival),
            "job_count": len(period_job_indices),
            "total_job_size": period_total_job_size,
            "param_info": current_param_set[current_param_index].copy()
        })
    
    return samples, period_records


def normal_soft_random_job_init(num_jobs, coherence_time=1) -> Tuple[List[Dict], List[Dict]]:
    """
    Create jobs with soft randomness for Normal distribution parameters only.
    
    Returns:
        tuple: (samples, period_records)
    """
    samples = []
    period_records = []
    
    normal_set_keys = list(normal_parameter_sets.keys())
    current_param_set_key = random.choice(normal_set_keys)
    current_param_set = normal_parameter_sets[current_param_set_key]
    current_param_index = random.randint(0, len(current_param_set) - 1)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    
    current_time = 0
    last_change_time = 0
    
    period_start_time = 0
    period_job_indices = []
    period_total_job_size = 0
    
    for job_idx in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            if period_job_indices:
                period_records.append({
                    "period_start_time": period_start_time,
                    "period_end_time": current_time,
                    "period_duration": current_time - period_start_time,
                    "inter_arrival_setting": current_avg_inter_arrival,
                    "is_high_load": is_high_load(current_avg_inter_arrival),
                    "job_count": len(period_job_indices),
                    "total_job_size": period_total_job_size,
                    "param_info": current_param_set[current_param_index].copy()
                })
            
            num_params = len(current_param_set)
            if current_param_index == 0:
                if random.random() < 0.5:
                    current_param_index = min(1, num_params - 1)
            elif current_param_index == num_params - 1:
                if random.random() < 0.5:
                    current_param_index = max(0, num_params - 2)
            else:
                choice = random.random()
                if choice < 1/3:
                    pass
                elif choice < 2/3:
                    current_param_index -= 1
                else:
                    current_param_index += 1
            
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
            
            period_start_time = current_time
            period_job_indices = []
            period_total_job_size = 0
        
        current_param = current_param_set[current_param_index]
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
        period_job_indices.append(job_idx)
        period_total_job_size += job_size
    
    if period_job_indices:
        period_records.append({
            "period_start_time": period_start_time,
            "period_end_time": current_time,
            "period_duration": current_time - period_start_time,
            "inter_arrival_setting": current_avg_inter_arrival,
            "is_high_load": is_high_load(current_avg_inter_arrival),
            "job_count": len(period_job_indices),
            "total_job_size": period_total_job_size,
            "param_info": current_param_set[current_param_index].copy()
        })
    
    return samples, period_records


def combination_random_job_init(num_jobs, param_set, coherence_time=1) -> Tuple[List[Dict], List[Dict]]:
    """
    Create jobs with random selection from a specific parameter set.
    
    Returns:
        tuple: (samples, period_records)
    """
    samples = []
    period_records = []
    
    current_param = random.choice(param_set)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0
    
    period_start_time = 0
    period_job_indices = []
    period_total_job_size = 0
    
    for job_idx in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            if period_job_indices:
                period_records.append({
                    "period_start_time": period_start_time,
                    "period_end_time": current_time,
                    "period_duration": current_time - period_start_time,
                    "inter_arrival_setting": current_avg_inter_arrival,
                    "is_high_load": is_high_load(current_avg_inter_arrival),
                    "job_count": len(period_job_indices),
                    "total_job_size": period_total_job_size,
                    "param_info": current_param.copy()
                })
            
            current_param = random.choice(param_set)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
            
            period_start_time = current_time
            period_job_indices = []
            period_total_job_size = 0
        
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
        period_job_indices.append(job_idx)
        period_total_job_size += job_size
    
    if period_job_indices:
        period_records.append({
            "period_start_time": period_start_time,
            "period_end_time": current_time,
            "period_duration": current_time - period_start_time,
            "inter_arrival_setting": current_avg_inter_arrival,
            "is_high_load": is_high_load(current_avg_inter_arrival),
            "job_count": len(period_job_indices),
            "total_job_size": period_total_job_size,
            "param_info": current_param.copy()
        })
    
    return samples, period_records


def combination_softrandom_job_init(num_jobs, param_set, coherence_time=1) -> Tuple[List[Dict], List[Dict]]:
    """
    Create jobs with soft randomness within a specific parameter set.
    
    Returns:
        tuple: (samples, period_records)
    """
    samples = []
    period_records = []
    
    current_param_index = random.randint(0, len(param_set) - 1)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    
    current_time = 0
    last_change_time = 0
    
    period_start_time = 0
    period_job_indices = []
    period_total_job_size = 0
    
    for job_idx in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            if period_job_indices:
                period_records.append({
                    "period_start_time": period_start_time,
                    "period_end_time": current_time,
                    "period_duration": current_time - period_start_time,
                    "inter_arrival_setting": current_avg_inter_arrival,
                    "is_high_load": is_high_load(current_avg_inter_arrival),
                    "job_count": len(period_job_indices),
                    "total_job_size": period_total_job_size,
                    "param_info": param_set[current_param_index].copy()
                })
            
            num_params = len(param_set)
            if num_params == 2:
                if random.random() < 0.5:
                    current_param_index = 1 - current_param_index
            else:
                if current_param_index == 0:
                    if random.random() < 0.5:
                        current_param_index = min(1, num_params - 1)
                elif current_param_index == num_params - 1:
                    if random.random() < 0.5:
                        current_param_index = max(0, num_params - 2)
                else:
                    choice = random.random()
                    if choice < 1/3:
                        pass
                    elif choice < 2/3:
                        current_param_index -= 1
                    else:
                        current_param_index += 1
            
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
            
            period_start_time = current_time
            period_job_indices = []
            period_total_job_size = 0
        
        current_param = param_set[current_param_index]
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
        period_job_indices.append(job_idx)
        period_total_job_size += job_size
    
    if period_job_indices:
        period_records.append({
            "period_start_time": period_start_time,
            "period_end_time": current_time,
            "period_duration": current_time - period_start_time,
            "inter_arrival_setting": current_avg_inter_arrival,
            "is_high_load": is_high_load(current_avg_inter_arrival),
            "job_count": len(period_job_indices),
            "total_job_size": period_total_job_size,
            "param_info": param_set[current_param_index].copy()
        })
    
    return samples, period_records


# =============================================================================
# Avg Job Generation (Fixed parameters per file)
# =============================================================================

def avg_job_init(num_jobs: int, avg_inter_arrival_time: int, param: Dict) -> List[Dict]:
    """
    Generate jobs with fixed inter-arrival time and fixed distribution parameters.
    This is the standard avg case generation for process_avg_folders.h

    Args:
        num_jobs: Number of jobs to generate
        avg_inter_arrival_time: Mean inter-arrival time (e.g., 20, 22, ..., 40)
        param: Distribution parameter dict with type "BP" or "Normal"

    Returns:
        List of job samples with arrival_time and job_size
    """
    samples = []

    # Generate job sizes based on distribution type
    job_sizes = [math.ceil(size) for size in generate_job_size(param, size=num_jobs)]

    # Generate arrival times using exponential distribution
    current_time = 0
    for k in range(num_jobs):
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        samples.append({
            "arrival_time": current_time,
            "job_size": job_sizes[k]
        })

    return samples


def get_avg_filename(avg_inter_arrival_time: int, param: Dict) -> str:
    """
    Generate filename for avg case in the format expected by parse_new_avg_filename.
    Format: avg_(arrival_rate,L_H).csv

    Args:
        avg_inter_arrival_time: Mean inter-arrival time
        param: Distribution parameter dict

    Returns:
        Filename string
    """
    if param["type"] == "BP":
        # Format: avg_(30,16.772_64).csv
        L = param["L"]
        H = int(param["H"])
        return f"avg_({avg_inter_arrival_time},{L}_{H}).csv"
    elif param["type"] == "Normal":
        # For Normal distribution, encode mean_std as L_H format
        # This allows reuse of existing parser
        mean = param["mean"]
        std = param["std"]
        return f"avg_({avg_inter_arrival_time},{mean}_{std}).csv"
    else:
        raise ValueError(f"Unknown parameter type: {param['type']}")


# =============================================================================
# Utility Functions
# =============================================================================

def save_longest_H_info(folder_path: str, period_records: List[Dict], total_jobs: int):
    """
    Save the longest H interval job index range to a CSV file.

    Args:
        folder_path: Directory where to save the file
        period_records: List of period records from job generation
        total_jobs: Total number of jobs generated
    """
    longest_H_stats = find_longest_contiguous_H(period_records)

    # Calculate total job size from all periods
    total_job_size = sum(p["total_job_size"] for p in period_records)

    # Calculate percentages
    job_count_pct = (longest_H_stats['longest_H_job_count'] / total_jobs * 100) if total_jobs > 0 else 0.0
    job_size_pct = (longest_H_stats['longest_H_total_job_size'] / total_job_size * 100) if total_job_size > 0 else 0.0

    info_file = os.path.join(folder_path, "longest_H_info.csv")
    with open(info_file, 'w') as f:
        f.write("start_job_index,end_job_index,job_count,total_jobs,job_count_percentage,longest_H_job_size,total_job_size,job_size_percentage\n")
        f.write(f"{longest_H_stats['start_job_index']},{longest_H_stats['end_job_index']},{longest_H_stats['longest_H_job_count']},{total_jobs},{job_count_pct:.4f},{longest_H_stats['longest_H_total_job_size']},{total_job_size},{job_size_pct:.4f}\n")


def get_combination_folder_name(param_set):
    """Generate descriptive folder name based on parameter set."""
    if param_set[0]["type"] == "BP":
        h_values = [str(int(p["H"])) for p in param_set]
        return "_".join([f"H{h}" for h in h_values])
    elif param_set[0]["type"] == "Normal":
        std_values = [str(int(p["std"])) for p in param_set]
        return "_".join([f"std{s}" for s in std_values])
    return "unknown"


# =============================================================================
# Save Functions with Analysis
# =============================================================================

def Save_file(num_jobs, i):
    """Save all job files and perform analysis."""
    os.makedirs("data", exist_ok=True)

    coherence_times = [pow(2, j) for j in range(1, 17, 1)]

    # Store results for group aggregation
    group_results = defaultdict(list)

    # ==========================================================================
    # Generate avg_30 jobs (fixed parameters per file)
    # ==========================================================================
    avg_30_folder = f"data/avg_30_{i}"
    os.makedirs(avg_30_folder, exist_ok=True)

    # All parameters for avg_30: both Bounded Pareto and Normal
    all_avg_30_params = bp_parameter_30 + normal_parameter_30

    total_files = len(inter_arrival_time) * len(all_avg_30_params)
    with tqdm.tqdm(total=total_files, desc=f"Processing avg_30 _{i}") as pbar:
        for avg_inter_arrival in inter_arrival_time:
            for param in all_avg_30_params:
                # Generate jobs
                samples = avg_job_init(num_jobs, avg_inter_arrival, param)

                # Generate filename
                filename = get_avg_filename(avg_inter_arrival, param)
                filepath = f"{avg_30_folder}/{filename}"

                # Write to CSV
                Write_csv.Write_raw(filepath, samples)

                pbar.update(1)

    print(f"  Generated {total_files} avg_30 files in {avg_30_folder}")

    # Generate Bounded_Pareto random jobs
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Bounded_Pareto random jobs _{i}"):
        bp_random_folder = f"data/Bounded_Pareto_random_{i}/freq_{ct}_{i}"
        os.makedirs(bp_random_folder, exist_ok=True)

        samples, period_records = bounded_pareto_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{bp_random_folder}/Bounded_Pareto_random_freq_{ct}.csv"
        Write_csv.Write_raw(filename, samples)

        # Save longest H info
        save_longest_H_info(bp_random_folder, period_records, num_jobs)

        # Analyze and collect
        result = analyze_single_instance(samples, period_records)
        group_key = get_group_key(bp_random_folder)
        group_results[group_key].append(result)

        # period_records goes to garbage
        del period_records
    
    # Generate normal random jobs
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing normal random jobs _{i}"):
        normal_random_folder = f"data/normal_random_{i}/freq_{ct}_{i}"
        os.makedirs(normal_random_folder, exist_ok=True)

        samples, period_records = normal_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{normal_random_folder}/normal_random_freq_{ct}.csv"
        Write_csv.Write_raw(filename, samples)

        # Save longest H info
        save_longest_H_info(normal_random_folder, period_records, num_jobs)

        result = analyze_single_instance(samples, period_records)
        group_key = get_group_key(normal_random_folder)
        group_results[group_key].append(result)

        del period_records
    
    # Generate Bounded_Pareto soft random jobs
    bp_softrandom_base = f"data/Bounded_Pareto_softrandom_{i}"
    os.makedirs(bp_softrandom_base, exist_ok=True)
    
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Bounded_Pareto soft random jobs _{i}"):
        bp_softrandom_folder = f"{bp_softrandom_base}/freq_{ct}_{i}"
        os.makedirs(bp_softrandom_folder, exist_ok=True)

        samples, period_records = bounded_pareto_soft_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{bp_softrandom_folder}/Bounded_Pareto_softrandom_freq_{ct}.csv"
        Write_csv.Write_raw(filename, samples)

        # Save longest H info
        save_longest_H_info(bp_softrandom_folder, period_records, num_jobs)

        result = analyze_single_instance(samples, period_records)
        group_key = get_group_key(bp_softrandom_folder)
        group_results[group_key].append(result)

        del period_records
    
    # Generate normal soft random jobs
    normal_softrandom_base = f"data/normal_softrandom_{i}"
    os.makedirs(normal_softrandom_base, exist_ok=True)
    
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing normal soft random jobs _{i}"):
        normal_softrandom_folder = f"{normal_softrandom_base}/freq_{ct}_{i}"
        os.makedirs(normal_softrandom_folder, exist_ok=True)

        samples, period_records = normal_soft_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{normal_softrandom_folder}/normal_softrandom_freq_{ct}.csv"
        Write_csv.Write_raw(filename, samples)

        # Save longest H info
        save_longest_H_info(normal_softrandom_folder, period_records, num_jobs)

        result = analyze_single_instance(samples, period_records)
        group_key = get_group_key(normal_softrandom_folder)
        group_results[group_key].append(result)

        del period_records
    
    # Define combination sets
    bp_two_combinations = [
        [bp_parameter_30[0], bp_parameter_30[1]],
        [bp_parameter_30[1], bp_parameter_30[2]],
        [bp_parameter_30[2], bp_parameter_30[3]],
        [bp_parameter_30[3], bp_parameter_30[4]]
    ]
    
    bp_three_combinations = [
        [bp_parameter_30[0], bp_parameter_30[1], bp_parameter_30[2]],
        [bp_parameter_30[1], bp_parameter_30[2], bp_parameter_30[3]],
        [bp_parameter_30[2], bp_parameter_30[3], bp_parameter_30[4]]
    ]
    
    bp_four_combinations = [
        [bp_parameter_30[0], bp_parameter_30[1], bp_parameter_30[2], bp_parameter_30[3]],
        [bp_parameter_30[1], bp_parameter_30[2], bp_parameter_30[3], bp_parameter_30[4]]
    ]
    
    normal_two_combinations = [
        [normal_parameter_30[0], normal_parameter_30[1]],
        [normal_parameter_30[1], normal_parameter_30[2]],
        [normal_parameter_30[2], normal_parameter_30[3]],
        [normal_parameter_30[3], normal_parameter_30[4]]
    ]
    
    normal_three_combinations = [
        [normal_parameter_30[0], normal_parameter_30[1], normal_parameter_30[2]],
        [normal_parameter_30[1], normal_parameter_30[2], normal_parameter_30[3]],
        [normal_parameter_30[2], normal_parameter_30[3], normal_parameter_30[4]]
    ]
    
    normal_four_combinations = [
        [normal_parameter_30[0], normal_parameter_30[1], normal_parameter_30[2], normal_parameter_30[3]],
        [normal_parameter_30[1], normal_parameter_30[2], normal_parameter_30[3], normal_parameter_30[4]]
    ]
    
    # Generate BP combination_random jobs
    bp_combination_random_base = f"data/Bounded_Pareto_combination_random_{i}"
    os.makedirs(bp_combination_random_base, exist_ok=True)
    
    for idx, param_set in enumerate(bp_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_two_comb_random_folder = f"{bp_combination_random_base}/two_combination_{combo_name}"
        os.makedirs(bp_two_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP two_combination_random {combo_name} _{i}"):
            freq_folder = f"{bp_two_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(bp_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_three_comb_random_folder = f"{bp_combination_random_base}/three_combination_{combo_name}"
        os.makedirs(bp_three_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP three_combination_random {combo_name} _{i}"):
            freq_folder = f"{bp_three_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(bp_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_four_comb_random_folder = f"{bp_combination_random_base}/four_combination_{combo_name}"
        os.makedirs(bp_four_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP four_combination_random {combo_name} _{i}"):
            freq_folder = f"{bp_four_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records

    # Generate Normal combination_random jobs
    normal_combination_random_base = f"data/normal_combination_random_{i}"
    os.makedirs(normal_combination_random_base, exist_ok=True)
    
    for idx, param_set in enumerate(normal_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_two_comb_random_folder = f"{normal_combination_random_base}/two_combination_{combo_name}"
        os.makedirs(normal_two_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal two_combination_random {combo_name} _{i}"):
            freq_folder = f"{normal_two_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(normal_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_three_comb_random_folder = f"{normal_combination_random_base}/three_combination_{combo_name}"
        os.makedirs(normal_three_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal three_combination_random {combo_name} _{i}"):
            freq_folder = f"{normal_three_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(normal_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_four_comb_random_folder = f"{normal_combination_random_base}/four_combination_{combo_name}"
        os.makedirs(normal_four_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal four_combination_random {combo_name} _{i}"):
            freq_folder = f"{normal_four_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records

    # Generate BP combination_softrandom jobs
    bp_combination_softrandom_base = f"data/Bounded_Pareto_combination_softrandom_{i}"
    os.makedirs(bp_combination_softrandom_base, exist_ok=True)
    
    for idx, param_set in enumerate(bp_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_two_comb_softrandom_folder = f"{bp_combination_softrandom_base}/two_combination_{combo_name}"
        os.makedirs(bp_two_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP two_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{bp_two_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(bp_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_three_comb_softrandom_folder = f"{bp_combination_softrandom_base}/three_combination_{combo_name}"
        os.makedirs(bp_three_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP three_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{bp_three_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(bp_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_four_comb_softrandom_folder = f"{bp_combination_softrandom_base}/four_combination_{combo_name}"
        os.makedirs(bp_four_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP four_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{bp_four_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records

    # Generate Normal combination_softrandom jobs
    normal_combination_softrandom_base = f"data/normal_combination_softrandom_{i}"
    os.makedirs(normal_combination_softrandom_base, exist_ok=True)
    
    for idx, param_set in enumerate(normal_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_two_comb_softrandom_folder = f"{normal_combination_softrandom_base}/two_combination_{combo_name}"
        os.makedirs(normal_two_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal two_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{normal_two_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(normal_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_three_comb_softrandom_folder = f"{normal_combination_softrandom_base}/three_combination_{combo_name}"
        os.makedirs(normal_three_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal three_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{normal_three_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records
    
    for idx, param_set in enumerate(normal_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_four_comb_softrandom_folder = f"{normal_combination_softrandom_base}/four_combination_{combo_name}"
        os.makedirs(normal_four_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal four_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{normal_four_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)

            samples, period_records = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, samples)

            # Save longest H info
            save_longest_H_info(freq_folder, period_records, num_jobs)

            result = analyze_single_instance(samples, period_records)
            group_key = get_group_key(freq_folder)
            group_results[group_key].append(result)

            del period_records

    return group_results


def save_all_group_analyses(all_group_results: Dict[str, List[Dict]], output_base: str = "analysis"):
    """
    Save aggregated analysis results for all groups and generate plots.

    Args:
        all_group_results: Dictionary mapping group_key to list of results
        output_base: Base directory for analysis output (default: 'analysis')
    """
    print("\n" + "=" * 80)
    print("Saving analysis results...")
    print("=" * 80)

    for group_key, results in tqdm.tqdm(all_group_results.items(), desc="Saving analysis"):
        if not results:
            continue

        aggregated = aggregate_group_results(results)
        output_path = os.path.join(output_base, group_key, "analysis.csv")
        save_analysis_csv(output_path, aggregated)

    print(f"Saved {len(all_group_results)} group analyses to {output_base}/")

    # Generate individual plots
    print("\n" + "=" * 80)
    print("Generating individual plots...")
    print("=" * 80)
    plot_metrics_by_coherence_time(all_group_results, output_base)

    # Generate comparison conclusion plots
    print("\n" + "=" * 80)
    print("Generating comparison conclusion plots...")
    print("=" * 80)
    plot_comparison_conclusion(all_group_results, output_base)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Job initialization with analysis')
    parser.add_argument('--mode', type=str, default='generate',
                       choices=['generate'],
                       help='Run mode: generate=generate data')
    parser.add_argument('--num-jobs', type=int, default=1000,
                       help='Number of jobs to generate')
    parser.add_argument('--analysis-output', type=str, default='analysis',
                       help='Analysis output directory (default: analysis)')

    args = parser.parse_args()

    if args.mode == 'generate':
        all_results = defaultdict(list)
        for i in range(1, 11):
            group_results = Save_file(args.num_jobs, i)
            # Merge results
            for key, results in group_results.items():
                all_results[key].extend(results)

        # Save all analyses and generate plots
        save_all_group_analyses(all_results, args.analysis_output)