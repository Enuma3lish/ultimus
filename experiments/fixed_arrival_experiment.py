"""
固定到达率实验
核心实验：测试固定 mean inter-arrival time 对系统性能的影响
"""

import os
import sys
import tqdm
import pandas as pd
from typing import Dict, List

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from experiments.config import (
    FIXED_ARRIVAL_RATES,
    COHERENCE_TIMES,
    BP_PARAMETERS,
    NORMAL_PARAMETERS,
    ALL_PARAMETERS,
    NUM_JOBS,
    NUM_REPLICATIONS,
    DATA_DIR
)
from experiments.data_generator import generate_jobs_fixed_arrival, analyze_jobs
import Write_csv

# ============================================================================
# 实验生成函数
# ============================================================================

def generate_fixed_arrival_experiment(arrival_rate_name, arrival_rate_value,
                                      param, coherence_time, replication_id):
    """
    生成单个固定到达率实验数据

    Parameters:
    - arrival_rate_name: 负载名称 ("overload", "critical", "stable")
    - arrival_rate_value: 平均到达时间间隔
    - param: 分布参数字典
    - coherence_time: coherence time 值
    - replication_id: 重复实验编号 (1-10)

    Returns:
    - jobs: 工作列表
    - filename: 保存的文件路径
    """
    # 创建输出目录
    exp_dir = os.path.join(
        DATA_DIR,
        f"fixed_arrival_{arrival_rate_name}_{replication_id}",
        f"param_{param['name']}",
        f"coherence_{coherence_time}"
    )
    os.makedirs(exp_dir, exist_ok=True)

    # 生成工作
    jobs = generate_jobs_fixed_arrival(
        num_jobs=NUM_JOBS,
        fixed_mean_arrival=arrival_rate_value,
        param=param,
        coherence_time=coherence_time
    )

    # 保存文件
    filename = os.path.join(
        exp_dir,
        f"fixed_arrival_{arrival_rate_name}_{param['name']}_ct{coherence_time}.csv"
    )
    Write_csv.Write_raw(filename, jobs)

    return jobs, filename

def generate_all_experiments():
    """
    生成所有固定到达率实验的数据

    实验结构：
    - 3 个负载条件 (overload, critical, stable)
    - 10 个参数 (5 BP + 5 Normal)
    - 16 个 coherence times (2^1 to 2^16)
    - 10 次重复
    - 总计：3 × 10 × 16 × 10 = 4,800 个数据集
    """
    print("=" * 70)
    print("固定到达率实验 - 数据生成")
    print("=" * 70)
    print(f"负载条件: {len(FIXED_ARRIVAL_RATES)} 个")
    print(f"分布参数: {len(ALL_PARAMETERS)} 个")
    print(f"Coherence Times: {len(COHERENCE_TIMES)} 个")
    print(f"重复次数: {NUM_REPLICATIONS} 次")
    print(f"总数据集: {len(FIXED_ARRIVAL_RATES) * len(ALL_PARAMETERS) * len(COHERENCE_TIMES) * NUM_REPLICATIONS}")
    print("=" * 70)

    # 统计信息
    total_generated = 0
    stats_summary = []

    # 遍历所有配置
    for rep_id in range(1, NUM_REPLICATIONS + 1):
        print(f"\n【重复 {rep_id}/{NUM_REPLICATIONS}】")

        for arrival_name, arrival_value in FIXED_ARRIVAL_RATES.items():
            theoretical_rho = 30 / arrival_value
            print(f"\n  负载条件: {arrival_name} (arrival={arrival_value}, ρ={theoretical_rho:.2f})")

            for param in tqdm.tqdm(ALL_PARAMETERS, desc=f"  参数"):
                for ct in COHERENCE_TIMES:
                    try:
                        jobs, filename = generate_fixed_arrival_experiment(
                            arrival_rate_name=arrival_name,
                            arrival_rate_value=arrival_value,
                            param=param,
                            coherence_time=ct,
                            replication_id=rep_id
                        )

                        # 分析统计
                        stats = analyze_jobs(jobs)
                        stats_summary.append({
                            "replication": rep_id,
                            "arrival_name": arrival_name,
                            "arrival_value": arrival_value,
                            "param_name": param["name"],
                            "param_type": param["type"],
                            "coherence_time": ct,
                            "theoretical_rho": theoretical_rho,
                            "estimated_rho": stats["estimated_rho"],
                            "mean_job_size": stats["job_size_mean"],
                            "mean_inter_arrival": stats["inter_arrival_mean"],
                            "num_jobs": stats["num_jobs"],
                            "filename": filename
                        })

                        total_generated += 1

                    except Exception as e:
                        print(f"\n    错误：{param['name']}, ct={ct}: {e}")
                        continue

    # 保存统计摘要
    summary_file = os.path.join(DATA_DIR, "experiment_generation_summary.csv")
    df_summary = pd.DataFrame(stats_summary)
    df_summary.to_csv(summary_file, index=False)

    print("\n" + "=" * 70)
    print(f"✓ 数据生成完成！")
    print(f"  成功生成: {total_generated} 个数据集")
    print(f"  统计摘要: {summary_file}")
    print("=" * 70)

    return df_summary

# ============================================================================
# 快速测试函数
# ============================================================================

def generate_test_subset():
    """
    生成小规模测试数据集
    用于快速验证实验流程
    """
    print("=" * 70)
    print("生成测试数据集（小规模）")
    print("=" * 70)

    # 只生成一次重复，每个负载条件选择一个参数
    test_params = [BP_PARAMETERS[0], NORMAL_PARAMETERS[0]]  # 选两个参数
    test_coherence_times = [2, 128, 16384]  # 选三个 coherence time

    total = 0
    for arrival_name, arrival_value in FIXED_ARRIVAL_RATES.items():
        print(f"\n负载: {arrival_name}")
        for param in test_params:
            for ct in test_coherence_times:
                jobs, filename = generate_fixed_arrival_experiment(
                    arrival_rate_name=arrival_name,
                    arrival_rate_value=arrival_value,
                    param=param,
                    coherence_time=ct,
                    replication_id=1
                )
                total += 1
                print(f"  ✓ {param['name']}, ct={ct}")

    print(f"\n✓ 测试数据集生成完成：{total} 个文件")
    print("=" * 70)

# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='固定到达率实验 - 数据生成')
    parser.add_argument('--test', action='store_true',
                       help='生成小规模测试数据集')
    parser.add_argument('--full', action='store_true',
                       help='生成完整数据集')

    args = parser.parse_args()

    if args.test:
        generate_test_subset()
    elif args.full:
        generate_all_experiments()
    else:
        print("请指定运行模式：")
        print("  --test  : 生成测试数据集")
        print("  --full  : 生成完整数据集")

if __name__ == "__main__":
    main()
