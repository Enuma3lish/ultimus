"""
数据生成核心模块
提供工作生成的基础函数
"""

import numpy as np
import math
from typing import List, Dict

# ============================================================================
# 分布生成函数
# ============================================================================

def generate_bounded_pareto(alpha, xmin, xmax, size=1):
    """
    生成 Bounded Pareto 分布的随机值

    Parameters:
    - alpha: Pareto 参数 (通常为 1.1)
    - xmin: 最小值 (L)
    - xmax: 最大值 (H)
    - size: 生成数量

    Returns:
    - 数组: Bounded Pareto 分布的随机值
    """
    cdf_xmin = 1 - (xmin / xmax) ** alpha
    u = np.random.uniform(0, cdf_xmin, size=size)
    x = xmin / ((1 - u) ** (1 / alpha))
    return x

def generate_normal(mean, std, size=1):
    """
    生成 Normal 分布的随机值（截断为正值）

    Parameters:
    - mean: 平均值
    - std: 标准差
    - size: 生成数量

    Returns:
    - 数组: Normal 分布的随机值（最小为1）
    """
    samples = np.random.normal(mean, std, size=size)
    # 确保所有值为正（最小工作大小 = 1）
    samples = np.maximum(samples, 1)
    return samples

def generate_job_size(param, size=1):
    """
    根据参数类型生成工作大小

    Parameters:
    - param: 参数字典（包含 type, L/H 或 mean/std）
    - size: 生成数量

    Returns:
    - 数组: 工作大小
    """
    if param["type"] == "BP":
        return generate_bounded_pareto(1.1, param["L"], param["H"], size=size)
    elif param["type"] == "Normal":
        return generate_normal(param["mean"], param["std"], size=size)
    else:
        raise ValueError(f"Unknown parameter type: {param['type']}")

# ============================================================================
# 工作生成函数
# ============================================================================

def generate_jobs_fixed_arrival(num_jobs, fixed_mean_arrival, param, coherence_time=1):
    """
    生成固定到达率的工作序列

    **核心实验函数**：
    - 固定 mean inter-arrival time（控制系统负载 ρ）
    - 工作大小参数每 coherence_time 切换一次
    - 参数在 coherence_time 内保持不变

    Parameters:
    - num_jobs: 工作数量
    - fixed_mean_arrival: 固定的平均到达时间间隔
    - param: 单一参数（BP 或 Normal）
    - coherence_time: 参数切换间隔（基于 CPU 时间）

    Returns:
    - jobs: 工作列表 [{"arrival_time": int, "job_size": int}, ...]
    """
    jobs = []
    current_time = 0

    # 使用固定参数生成所有工作
    for _ in range(num_jobs):
        # 生成工作大小
        job_size = math.ceil(generate_job_size(param, size=1)[0])

        # 生成到达时间（指数分布）
        inter_arrival = round(np.random.exponential(scale=fixed_mean_arrival))
        inter_arrival = max(1, inter_arrival)  # 确保至少为1
        current_time += inter_arrival

        jobs.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return jobs

def generate_jobs_switching_params(num_jobs, fixed_mean_arrival, all_params, coherence_time=1):
    """
    生成固定到达率、参数切换的工作序列

    **扩展实验函数**：
    - 固定 mean inter-arrival time
    - 工作大小参数每 coherence_time 从 all_params 中随机选择

    Parameters:
    - num_jobs: 工作数量
    - fixed_mean_arrival: 固定的平均到达时间间隔
    - all_params: 参数列表（从中随机选择）
    - coherence_time: 参数切换间隔

    Returns:
    - jobs: 工作列表
    """
    jobs = []
    current_time = 0
    last_change_time = 0

    # 初始化参数
    current_param = np.random.choice(all_params)

    for _ in range(num_jobs):
        # 检查是否需要切换参数
        if current_time - last_change_time >= coherence_time:
            current_param = np.random.choice(all_params)
            last_change_time = current_time

        # 生成工作大小
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # 生成到达时间
        inter_arrival = round(np.random.exponential(scale=fixed_mean_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        jobs.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return jobs

# ============================================================================
# 数据分析函数
# ============================================================================

def analyze_jobs(jobs: List[Dict]) -> Dict:
    """
    分析工作序列的统计特性

    Parameters:
    - jobs: 工作列表

    Returns:
    - stats: 统计字典
    """
    if not jobs:
        return {}

    job_sizes = [job["job_size"] for job in jobs]
    arrival_times = [job["arrival_time"] for job in jobs]

    # 计算到达时间间隔
    inter_arrivals = []
    for i in range(1, len(arrival_times)):
        inter_arrivals.append(arrival_times[i] - arrival_times[i-1])

    stats = {
        # 工作大小统计
        "job_size_mean": np.mean(job_sizes),
        "job_size_std": np.std(job_sizes),
        "job_size_min": np.min(job_sizes),
        "job_size_max": np.max(job_sizes),
        "job_size_median": np.median(job_sizes),

        # 到达间隔统计
        "inter_arrival_mean": np.mean(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_std": np.std(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_min": np.min(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_max": np.max(inter_arrivals) if inter_arrivals else 0,

        # 系统负载估计
        "estimated_rho": np.mean(job_sizes) / np.mean(inter_arrivals) if inter_arrivals and np.mean(inter_arrivals) > 0 else 0,

        # 基本信息
        "num_jobs": len(jobs),
        "total_duration": arrival_times[-1] - arrival_times[0] if len(arrival_times) > 1 else 0
    }

    return stats

# ============================================================================
# 测试函数
# ============================================================================

def test_data_generation():
    """测试数据生成功能"""
    from experiments.config import BP_PARAMETERS, NORMAL_PARAMETERS, FIXED_ARRIVAL_RATES

    print("=" * 70)
    print("数据生成测试")
    print("=" * 70)

    # 测试单一参数
    print("\n测试 1: 单一参数（BP, H=512）")
    param = BP_PARAMETERS[1]  # H=512
    jobs = generate_jobs_fixed_arrival(1000, 30, param, coherence_time=100)
    stats = analyze_jobs(jobs)
    print(f"  生成 {stats['num_jobs']} 个工作")
    print(f"  平均工作大小: {stats['job_size_mean']:.2f}")
    print(f"  平均到达间隔: {stats['inter_arrival_mean']:.2f}")
    print(f"  估计负载 ρ: {stats['estimated_rho']:.3f}")

    # 测试参数切换
    print("\n测试 2: 参数切换（所有 BP 参数）")
    jobs = generate_jobs_switching_params(1000, 30, BP_PARAMETERS, coherence_time=100)
    stats = analyze_jobs(jobs)
    print(f"  生成 {stats['num_jobs']} 个工作")
    print(f"  平均工作大小: {stats['job_size_mean']:.2f}")
    print(f"  平均到达间隔: {stats['inter_arrival_mean']:.2f}")
    print(f"  估计负载 ρ: {stats['estimated_rho']:.3f}")

    # 测试不同负载
    print("\n测试 3: 不同负载条件")
    for load_name, arrival_time in FIXED_ARRIVAL_RATES.items():
        jobs = generate_jobs_fixed_arrival(1000, arrival_time, param, coherence_time=100)
        stats = analyze_jobs(jobs)
        theoretical_rho = 30 / arrival_time
        print(f"  {load_name} (arrival={arrival_time}): ρ理论={theoretical_rho:.2f}, ρ估计={stats['estimated_rho']:.2f}")

    print("\n✓ 数据生成测试完成！")

if __name__ == "__main__":
    test_data_generation()
