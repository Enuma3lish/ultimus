#!/usr/bin/env python3
"""
測試工作生成函數的工具腳本
提供多種測試選項來驗證工作大小和抵達時間的分布特性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import Job_init
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict

def plot_job_size_distribution(job_list: List[Dict], title: str = "Job Size Distribution"):
    """繪製工作大小分布圖"""
    job_sizes = [job["job_size"] for job in job_list]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(title, fontsize=16)
    
    # 直方圖
    axes[0, 0].hist(job_sizes, bins=50, edgecolor='black', alpha=0.7)
    axes[0, 0].set_xlabel('Job Size')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Histogram')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Box plot
    axes[0, 1].boxplot(job_sizes)
    axes[0, 1].set_ylabel('Job Size')
    axes[0, 1].set_title('Box Plot')
    axes[0, 1].grid(True, alpha=0.3)
    
    # CDF
    sorted_sizes = np.sort(job_sizes)
    cdf = np.arange(1, len(sorted_sizes) + 1) / len(sorted_sizes)
    axes[1, 0].plot(sorted_sizes, cdf)
    axes[1, 0].set_xlabel('Job Size')
    axes[1, 0].set_ylabel('CDF')
    axes[1, 0].set_title('Cumulative Distribution')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 統計信息文本
    stats_text = f"""Statistics:
Mean: {np.mean(job_sizes):.2f}
Std: {np.std(job_sizes):.2f}
Min: {np.min(job_sizes):.0f}
Max: {np.max(job_sizes):.0f}
Median: {np.median(job_sizes):.2f}
Q25: {np.percentile(job_sizes, 25):.2f}
Q75: {np.percentile(job_sizes, 75):.2f}
Count: {len(job_sizes)}"""
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=12, family='monospace',
                    verticalalignment='center')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    return fig

def plot_arrival_time_distribution(job_list: List[Dict], title: str = "Arrival Time Distribution"):
    """繪製抵達時間分布圖"""
    arrival_times = [job["arrival_time"] for job in job_list]
    
    # 計算抵達間隔
    inter_arrivals = []
    for i in range(1, len(arrival_times)):
        inter_arrivals.append(arrival_times[i] - arrival_times[i-1])
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(title, fontsize=16)
    
    # 抵達時間序列
    axes[0, 0].plot(range(len(arrival_times)), arrival_times, alpha=0.7)
    axes[0, 0].set_xlabel('Job Index')
    axes[0, 0].set_ylabel('Arrival Time')
    axes[0, 0].set_title('Arrival Time Series')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 抵達間隔直方圖
    axes[0, 1].hist(inter_arrivals, bins=50, edgecolor='black', alpha=0.7)
    axes[0, 1].set_xlabel('Inter-Arrival Time')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Inter-Arrival Distribution')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 抵達間隔序列
    axes[1, 0].plot(range(len(inter_arrivals)), inter_arrivals, alpha=0.7)
    axes[1, 0].set_xlabel('Job Index')
    axes[1, 0].set_ylabel('Inter-Arrival Time')
    axes[1, 0].set_title('Inter-Arrival Time Series')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 統計信息
    stats_text = f"""Inter-Arrival Statistics:
Mean: {np.mean(inter_arrivals):.2f}
Std: {np.std(inter_arrivals):.2f}
Min: {np.min(inter_arrivals):.0f}
Max: {np.max(inter_arrivals):.0f}
Median: {np.median(inter_arrivals):.2f}

Total Duration: {arrival_times[-1]:.0f}
Num Jobs: {len(job_list)}"""
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=12, family='monospace',
                    verticalalignment='center')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    return fig

def test_single_distribution(param: Dict, num_jobs: int = 5000, avg_inter_arrival: int = 30):
    """測試單個分布參數"""
    print(f"\n{'='*60}")
    print(f"測試參數: {param}")
    print(f"工作數量: {num_jobs}, 平均抵達間隔: {avg_inter_arrival}")
    print('='*60)
    
    # 生成工作
    job_list = Job_init.job_init(num_jobs, avg_inter_arrival, param)
    
    # 分析
    stats = Job_init.analyze_jobs(job_list)
    
    # 打印統計信息
    print("\n工作大小統計:")
    print(f"  平均值: {stats['job_size_mean']:.2f}")
    print(f"  標準差: {stats['job_size_std']:.2f}")
    print(f"  範圍: [{stats['job_size_min']}, {stats['job_size_max']}]")
    print(f"  中位數: {stats['job_size_median']:.2f}")
    print(f"  四分位數: [{stats['job_size_q25']:.2f}, {stats['job_size_q75']:.2f}]")
    
    print("\n抵達時間統計:")
    print(f"  平均間隔: {stats['inter_arrival_mean']:.2f}")
    print(f"  間隔標準差: {stats['inter_arrival_std']:.2f}")
    print(f"  間隔範圍: [{stats['inter_arrival_min']}, {stats['inter_arrival_max']}]")
    print(f"  總持續時間: {stats['total_duration']:.0f}")
    
    # 繪圖
    fig1 = plot_job_size_distribution(job_list, 
                                      f"Job Size Distribution - {param['type']}")
    fig2 = plot_arrival_time_distribution(job_list,
                                          f"Arrival Time Distribution - {param['type']}")
    
    return job_list, stats, fig1, fig2

def compare_bp_vs_normal():
    """比較 Bounded Pareto 和 Normal 分布"""
    print("\n" + "="*60)
    print("比較 Bounded Pareto vs Normal 分布")
    print("="*60)
    
    num_jobs = 5000
    results = []
    
    # 測試 BP 參數
    print("\nBounded Pareto 參數:")
    for i, param in enumerate(Job_init.bp_parameter_30):
        job_list = Job_init.job_init(num_jobs, 30, param)
        stats = Job_init.analyze_jobs(job_list)
        results.append({
            'Type': 'BP',
            'Index': i,
            'L/Mean': param['L'],
            'H/Std': param['H'],
            'Job_Size_Mean': stats['job_size_mean'],
            'Job_Size_Std': stats['job_size_std'],
            'Job_Size_Min': stats['job_size_min'],
            'Job_Size_Max': stats['job_size_max'],
            'Inter_Arrival_Mean': stats['inter_arrival_mean']
        })
        print(f"  {i}: L={param['L']:.2f}, H={param['H']:.0f} -> "
              f"Mean={stats['job_size_mean']:.2f}, Std={stats['job_size_std']:.2f}")
    
    # 測試 Normal 參數
    print("\nNormal 參數:")
    for i, param in enumerate(Job_init.normal_parameter_30):
        job_list = Job_init.job_init(num_jobs, 30, param)
        stats = Job_init.analyze_jobs(job_list)
        results.append({
            'Type': 'Normal',
            'Index': i,
            'L/Mean': param['mean'],
            'H/Std': param['std'],
            'Job_Size_Mean': stats['job_size_mean'],
            'Job_Size_Std': stats['job_size_std'],
            'Job_Size_Min': stats['job_size_min'],
            'Job_Size_Max': stats['job_size_max'],
            'Inter_Arrival_Mean': stats['inter_arrival_mean']
        })
        print(f"  {i}: Mean={param['mean']}, Std={param['std']} -> "
              f"Mean={stats['job_size_mean']:.2f}, Std={stats['job_size_std']:.2f}")
    
    df = pd.DataFrame(results)
    print("\n完整比較表:")
    print(df.to_string(index=False))
    
    return df

def test_coherence_time_effect():
    """測試 coherence time 對工作分布的影響"""
    print("\n" + "="*60)
    print("測試 Coherence Time 效果")
    print("="*60)
    
    num_jobs = 10000
    coherence_times = [2, 8, 32, 128, 512, 2048, 8192, 16384]
    
    results = []
    
    for ct in coherence_times:
        # BP random
        job_list = Job_init.bounded_pareto_random_job_init(num_jobs, coherence_time=ct)
        stats = Job_init.analyze_jobs(job_list)
        results.append({
            'Type': 'BP_Random',
            'Coherence_Time': ct,
            'Job_Size_Mean': stats['job_size_mean'],
            'Job_Size_Std': stats['job_size_std'],
            'Inter_Arrival_Mean': stats['inter_arrival_mean']
        })
        
        # Normal random
        job_list = Job_init.normal_random_job_init(num_jobs, coherence_time=ct)
        stats = Job_init.analyze_jobs(job_list)
        results.append({
            'Type': 'Normal_Random',
            'Coherence_Time': ct,
            'Job_Size_Mean': stats['job_size_mean'],
            'Job_Size_Std': stats['job_size_std'],
            'Inter_Arrival_Mean': stats['inter_arrival_mean']
        })
    
    df = pd.DataFrame(results)
    print("\nCoherence Time 影響:")
    print(df.to_string(index=False))
    
    # 繪圖
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    bp_data = df[df['Type'] == 'BP_Random']
    normal_data = df[df['Type'] == 'Normal_Random']
    
    axes[0].plot(bp_data['Coherence_Time'], bp_data['Job_Size_Mean'], 
                 'o-', label='BP Random')
    axes[0].plot(normal_data['Coherence_Time'], normal_data['Job_Size_Mean'],
                 's-', label='Normal Random')
    axes[0].set_xscale('log', base=2)
    axes[0].set_xlabel('Coherence Time')
    axes[0].set_ylabel('Mean Job Size')
    axes[0].set_title('Mean Job Size vs Coherence Time')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(bp_data['Coherence_Time'], bp_data['Job_Size_Std'],
                 'o-', label='BP Random')
    axes[1].plot(normal_data['Coherence_Time'], normal_data['Job_Size_Std'],
                 's-', label='Normal Random')
    axes[1].set_xscale('log', base=2)
    axes[1].set_xlabel('Coherence Time')
    axes[1].set_ylabel('Job Size Std Dev')
    axes[1].set_title('Job Size Std Dev vs Coherence Time')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    return df, fig

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='測試工作生成函數')
    parser.add_argument('--test', type=str, default='all',
                       choices=['all', 'bp', 'normal', 'compare', 'coherence', 'single'],
                       help='測試類型')
    parser.add_argument('--num-jobs', type=int, default=5000,
                       help='生成的工作數量')
    parser.add_argument('--save-plots', action='store_true',
                       help='保存圖表到文件')
    parser.add_argument('--param-index', type=int, default=0,
                       help='單個測試時的參數索引')
    
    args = parser.parse_args()
    
    os.makedirs('test_output', exist_ok=True)
    
    if args.test == 'all' or args.test == 'compare':
        df = compare_bp_vs_normal()
        df.to_csv('test_output/distribution_comparison.csv', index=False)
        print("\n結果已保存到: test_output/distribution_comparison.csv")
    
    if args.test == 'all' or args.test == 'coherence':
        df, fig = test_coherence_time_effect()
        df.to_csv('test_output/coherence_time_analysis.csv', index=False)
        if args.save_plots:
            fig.savefig('test_output/coherence_time_plot.png', dpi=150, bbox_inches='tight')
        print("\n結果已保存到: test_output/coherence_time_analysis.csv")
    
    if args.test == 'bp' or args.test == 'single':
        param = Job_init.bp_parameter_30[args.param_index]
        job_list, stats, fig1, fig2 = test_single_distribution(param, args.num_jobs)
        if args.save_plots:
            fig1.savefig(f'test_output/bp_jobsize_{args.param_index}.png', dpi=150, bbox_inches='tight')
            fig2.savefig(f'test_output/bp_arrival_{args.param_index}.png', dpi=150, bbox_inches='tight')
    
    if args.test == 'normal' or (args.test == 'single' and args.param_index < len(Job_init.normal_parameter_30)):
        param = Job_init.normal_parameter_30[min(args.param_index, len(Job_init.normal_parameter_30)-1)]
        job_list, stats, fig1, fig2 = test_single_distribution(param, args.num_jobs)
        if args.save_plots:
            fig1.savefig(f'test_output/normal_jobsize_{args.param_index}.png', dpi=150, bbox_inches='tight')
            fig2.savefig(f'test_output/normal_arrival_{args.param_index}.png', dpi=150, bbox_inches='tight')
    
    if not args.save_plots:
        plt.show()
    
    print("\n測試完成！")
