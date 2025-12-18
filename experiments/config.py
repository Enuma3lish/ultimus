"""
实验配置模块
定义所有实验参数和分布设置
"""

import numpy as np

# ============================================================================
# 核心参数：固定到达率
# ============================================================================
# 这些是我们要测试的三个关键负载场景
FIXED_ARRIVAL_RATES = {
    "overload": 20,      # ρ = 30/20 = 1.5 (过载，队列无限增长)
    "critical": 30,      # ρ = 30/30 = 1.0 (临界，边缘稳定)
    "stable": 40         # ρ = 30/40 = 0.75 (稳定，系统可处理)
}

# ============================================================================
# Coherence Time 设置
# ============================================================================
# 从 2^1 到 2^16，测试参数切换频率对性能的影响
COHERENCE_TIMES = [2**i for i in range(1, 17)]

# ============================================================================
# Bounded Pareto 参数 (avg_30)
# ============================================================================
# 所有参数的期望值 E[X] = 30
BP_PARAMETERS = [
    {"L": 16.772, "H": 64, "type": "BP", "name": "BP_H64"},
    {"L": 7.918, "H": 512, "type": "BP", "name": "BP_H512"},
    {"L": 5.649, "H": 4096, "type": "BP", "name": "BP_H4096"},
    {"L": 4.639, "H": 32768, "type": "BP", "name": "BP_H32768"},
    {"L": 4.073, "H": 262144, "type": "BP", "name": "BP_H262144"}
]

# ============================================================================
# Normal 分布参数 (avg_30)
# ============================================================================
# 所有参数的平均值 = 30，不同标准差
NORMAL_PARAMETERS = [
    {"mean": 30, "std": 6, "type": "Normal", "name": "Normal_std6"},
    {"mean": 30, "std": 9, "type": "Normal", "name": "Normal_std9"},
    {"mean": 30, "std": 12, "type": "Normal", "name": "Normal_std12"},
    {"mean": 30, "std": 15, "type": "Normal", "name": "Normal_std15"},
    {"mean": 30, "std": 18, "type": "Normal", "name": "Normal_std18"}
]

# ============================================================================
# 组合所有参数
# ============================================================================
ALL_PARAMETERS = BP_PARAMETERS + NORMAL_PARAMETERS

# ============================================================================
# 实验设置
# ============================================================================
NUM_JOBS = 10000  # 每个实验生成的工作数量
NUM_REPLICATIONS = 10  # 每个配置的重复次数（用于统计可靠性）

# ============================================================================
# 算法分类
# ============================================================================
CLAIRVOYANT_ALGORITHMS = ['SRPT', 'Dynamic', 'Dynamic_BAL', 'BAL', 'FCFS']
NON_CLAIRVOYANT_ALGORITHMS = ['RFDynamic', 'SETF', 'RMLF', 'FCFS']

# ============================================================================
# 路径配置
# ============================================================================
import os

BASE_DIR = "/Users/melowu/Desktop/ultimus"
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULT_DIR = os.path.join(BASE_DIR, "algorithm_result")
PLOT_DIR = os.path.join(BASE_DIR, "plots_output")

# ============================================================================
# 辅助函数
# ============================================================================
def get_load_factor(mean_service_time, mean_arrival_time):
    """
    计算系统负载因子 ρ = λ/μ = mean_service_time / mean_arrival_time

    Parameters:
    - mean_service_time: 平均服务时间 (期望工作大小)
    - mean_arrival_time: 平均到达时间间隔

    Returns:
    - ρ: 系统负载因子
    """
    return mean_service_time / mean_arrival_time

def get_parameter_info(param):
    """
    获取参数的详细信息字符串

    Parameters:
    - param: 参数字典

    Returns:
    - info: 参数信息字符串
    """
    if param["type"] == "BP":
        return f"BP(L={param['L']:.3f}, H={int(param['H'])})"
    else:
        return f"Normal(μ={param['mean']}, σ={param['std']})"

def print_experiment_summary():
    """打印实验配置摘要"""
    print("=" * 70)
    print("实验配置摘要")
    print("=" * 70)
    print(f"固定到达率: {list(FIXED_ARRIVAL_RATES.values())}")
    print(f"  - 过载 (ρ=1.5): mean_arrival = {FIXED_ARRIVAL_RATES['overload']}")
    print(f"  - 临界 (ρ=1.0): mean_arrival = {FIXED_ARRIVAL_RATES['critical']}")
    print(f"  - 稳定 (ρ=0.75): mean_arrival = {FIXED_ARRIVAL_RATES['stable']}")
    print(f"\nCoherence Times: {len(COHERENCE_TIMES)} 个 (2^1 到 2^16)")
    print(f"BP 参数: {len(BP_PARAMETERS)} 个")
    print(f"Normal 参数: {len(NORMAL_PARAMETERS)} 个")
    print(f"总参数组合: {len(ALL_PARAMETERS)} 个")
    print(f"\n每个配置生成 {NUM_JOBS} 个工作")
    print(f"每个配置重复 {NUM_REPLICATIONS} 次")
    print(f"\n总实验数: {len(FIXED_ARRIVAL_RATES)} × {len(ALL_PARAMETERS)} × {len(COHERENCE_TIMES)} × {NUM_REPLICATIONS}")
    print(f"         = {len(FIXED_ARRIVAL_RATES) * len(ALL_PARAMETERS) * len(COHERENCE_TIMES) * NUM_REPLICATIONS} 个数据集")
    print("=" * 70)

if __name__ == "__main__":
    print_experiment_summary()

    print("\n详细参数列表:")
    print("\nBounded Pareto 参数:")
    for i, p in enumerate(BP_PARAMETERS, 1):
        print(f"  {i}. {get_parameter_info(p)}")

    print("\nNormal 分布参数:")
    for i, p in enumerate(NORMAL_PARAMETERS, 1):
        print(f"  {i}. {get_parameter_info(p)}")
