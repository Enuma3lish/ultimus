"""
固定到达率实验绘图脚本
生成清晰的可视化图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import logging
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from experiments.config import (
    CLAIRVOYANT_ALGORITHMS,
    NON_CLAIRVOYANT_ALGORITHMS,
    RESULT_DIR,
    PLOT_DIR
)

# ============================================================================
# 日志设置
# ============================================================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 颜色和标记方案
# ============================================================================
ALGORITHM_COLORS = {
    'SRPT': '#ff7f0e',
    'Dynamic': '#8c564b',
    'Dynamic_BAL': '#e377c2',
    'RFDynamic': '#17becf',
    'BAL': '#9467bd',
    'FCFS': '#d62728',
    'SETF': '#2ca02c',
    'RMLF': '#404040',
}

ALGORITHM_MARKERS = {
    'SRPT': 's',
    'Dynamic': 'x',
    'Dynamic_BAL': 'P',
    'RFDynamic': 'h',
    'BAL': 'D',
    'FCFS': 'v',
    'SETF': '^',
    'RMLF': '*',
}

# ============================================================================
# 绘图样式设置
# ============================================================================
def setup_plot_style():
    """设置 matplotlib 样式"""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (12, 7),
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'legend.fontsize': 11,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'lines.linewidth': 2.5,
        'lines.markersize': 10,
        'grid.alpha': 0.3,
        'legend.framealpha': 0.9,
    })

# ============================================================================
# 核心绘图函数
# ============================================================================
def plot_fixed_arrival_single(arrival_name, param_name, algorithms, title, output_filename):
    """
    为单一负载条件和参数绘制图表

    Parameters:
    - arrival_name: 负载名称 ("overload", "critical", "stable")
    - param_name: 参数名称 (如 "BP_H512")
    - algorithms: 算法列表
    - title: 图表标题
    - output_filename: 输出文件名
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 7))

    plotted_count = 0

    for algorithm in algorithms:
        # 查找结果文件
        pattern = os.path.join(
            RESULT_DIR,
            f"{algorithm}_result",
            "fixed_arrival_experiment_result",
            f"fixed_arrival_{arrival_name}_{param_name}_result_{algorithm}_*.csv"
        )
        files = glob.glob(pattern)

        if not files:
            continue

        # 读取所有重复实验的数据
        all_data = []
        for file in files:
            try:
                df = pd.read_csv(file)
                l2_col = f"{algorithm}_L2_norm_flow_time"

                if 'coherence_time' not in df.columns or l2_col not in df.columns:
                    continue

                df = df.sort_values('coherence_time')
                all_data.append(df)
            except Exception as e:
                logger.error(f"  错误读取 {file}: {e}")
                continue

        if not all_data:
            continue

        # 计算平均值和标准差
        combined_df = pd.concat(all_data)
        grouped = combined_df.groupby('coherence_time').agg({
            f"{algorithm}_L2_norm_flow_time": ['mean', 'std']
        }).reset_index()

        grouped.columns = ['coherence_time', 'mean_l2', 'std_l2']

        # 绘制曲线
        ax.plot(grouped['coherence_time'], grouped['mean_l2'],
               marker=ALGORITHM_MARKERS.get(algorithm, 'o'),
               color=ALGORITHM_COLORS.get(algorithm, 'black'),
               linestyle='-',
               linewidth=2.5,
               markersize=10,
               markeredgewidth=1.5,
               markeredgecolor='white',
               markerfacecolor=ALGORITHM_COLORS.get(algorithm, 'black'),
               label=algorithm)

        # 添加误差带（可选）
        # ax.fill_between(grouped['coherence_time'],
        #                 grouped['mean_l2'] - grouped['std_l2'],
        #                 grouped['mean_l2'] + grouped['std_l2'],
        #                 color=ALGORITHM_COLORS.get(algorithm, 'black'),
        #                 alpha=0.2)

        plotted_count += 1

    if plotted_count == 0:
        logger.warning(f"  没有数据绘制：{arrival_name}_{param_name}")
        plt.close()
        return

    # 配置图表
    ax.set_xlabel('Coherence Time (对数刻度)', fontsize=14, fontweight='bold')
    ax.set_ylabel('L2-Norm Flow Time', fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xscale('log', base=2)

    # 设置 x 轴刻度
    x_ticks = [2**i for i in range(1, 17)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f'2^{int(np.log2(x))}' for x in x_ticks], rotation=45, ha='right')

    ax.legend(loc='best', framealpha=0.9, fontsize=11)
    ax.grid(True, alpha=0.3, which='both', linestyle='--')

    # 保存图表
    output_file = os.path.join(PLOT_DIR, output_filename)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"  ✓ 已保存: {output_file}")

def plot_all_fixed_arrival_experiments():
    """
    生成所有固定到达率实验的图表

    生成结构：
    - 3 个负载条件 × 10 个参数 = 30 组图表
    - 每组图表分为 clairvoyant 和 non-clairvoyant
    - 总计：60 张图表
    """
    logger.info("\n" + "=" * 70)
    logger.info("固定到达率实验 - 绘图")
    logger.info("=" * 70)

    os.makedirs(PLOT_DIR, exist_ok=True)

    # 负载条件
    arrival_conditions = {
        "overload": "过载 (ρ=1.5)",
        "critical": "临界 (ρ=1.0)",
        "stable": "稳定 (ρ=0.75)"
    }

    # 获取所有参数名称
    # 从结果文件中自动提取
    result_dir = os.path.join(RESULT_DIR, "SRPT_result", "fixed_arrival_experiment_result")
    if not os.path.exists(result_dir):
        logger.error(f"结果目录不存在: {result_dir}")
        return

    all_files = glob.glob(os.path.join(result_dir, "fixed_arrival_*.csv"))
    param_names = set()

    for file in all_files:
        basename = os.path.basename(file)
        # 格式：fixed_arrival_{arrival_name}_{param_name}_result_SRPT_{rep}.csv
        parts = basename.split('_')
        if len(parts) >= 6:
            # 提取参数名称（可能包含下划线）
            arrival_idx = 2
            result_idx = parts.index("result")
            param_name = "_".join(parts[arrival_idx + 1:result_idx])
            param_names.add(param_name)

    logger.info(f"发现 {len(param_names)} 个参数配置")

    total_plots = 0

    for arrival_name, arrival_desc in arrival_conditions.items():
        logger.info(f"\n负载条件: {arrival_name} {arrival_desc}")

        for param_name in sorted(param_names):
            logger.info(f"  参数: {param_name}")

            # Clairvoyant 图表
            plot_fixed_arrival_single(
                arrival_name=arrival_name,
                param_name=param_name,
                algorithms=CLAIRVOYANT_ALGORITHMS,
                title=f"固定到达率 {arrival_desc} - {param_name} (Clairvoyant)",
                output_filename=f"fixed_arrival_{arrival_name}_{param_name}_clairvoyant.png"
            )
            total_plots += 1

            # Non-clairvoyant 图表
            plot_fixed_arrival_single(
                arrival_name=arrival_name,
                param_name=param_name,
                algorithms=NON_CLAIRVOYANT_ALGORITHMS,
                title=f"固定到达率 {arrival_desc} - {param_name} (Non-Clairvoyant)",
                output_filename=f"fixed_arrival_{arrival_name}_{param_name}_non_clairvoyant.png"
            )
            total_plots += 1

    logger.info("\n" + "=" * 70)
    logger.info(f"✓ 绘图完成！生成了 {total_plots} 张图表")
    logger.info(f"  输出目录: {PLOT_DIR}")
    logger.info("=" * 70)

# ============================================================================
# 主函数
# ============================================================================
def main():
    """主函数"""
    plot_all_fixed_arrival_experiments()

if __name__ == "__main__":
    main()
