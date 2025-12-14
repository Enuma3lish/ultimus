#!/usr/bin/env python3
"""
簡單的範例腳本，展示如何使用重構後的 Job_init.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import Job_init
import matplotlib.pyplot as plt

def example_1_basic_analysis():
    """範例 1: 基本工作生成和分析"""
    print("="*60)
    print("範例 1: 基本工作生成和分析")
    print("="*60)
    
    # 選擇一個 Bounded Pareto 參數
    param = Job_init.bp_parameter_30[0]
    print(f"\n使用參數: L={param['L']}, H={param['H']}")
    
    # 生成 5000 個工作
    job_list = Job_init.job_init(5000, 30, param)
    print(f"生成了 {len(job_list)} 個工作")
    
    # 分析統計特性
    stats = Job_init.analyze_jobs(job_list)
    
    print("\n工作大小統計:")
    print(f"  平均: {stats['job_size_mean']:.2f}")
    print(f"  標準差: {stats['job_size_std']:.2f}")
    print(f"  範圍: [{stats['job_size_min']}, {stats['job_size_max']}]")
    
    print("\n抵達時間統計:")
    print(f"  平均間隔: {stats['inter_arrival_mean']:.2f}")
    print(f"  間隔標準差: {stats['inter_arrival_std']:.2f}")
    print(f"  總持續時間: {stats['total_duration']:.0f}")

def example_2_compare_distributions():
    """範例 2: 比較不同分布"""
    print("\n" + "="*60)
    print("範例 2: 比較 Bounded Pareto 和 Normal 分布")
    print("="*60)
    
    num_jobs = 3000
    
    # BP 參數
    bp_param = Job_init.bp_parameter_30[2]
    bp_jobs = Job_init.job_init(num_jobs, 30, bp_param)
    bp_stats = Job_init.analyze_jobs(bp_jobs)
    
    # Normal 參數
    normal_param = Job_init.normal_parameter_30[2]
    normal_jobs = Job_init.job_init(num_jobs, 30, normal_param)
    normal_stats = Job_init.analyze_jobs(normal_jobs)
    
    print(f"\nBounded Pareto (L={bp_param['L']}, H={bp_param['H']}):")
    print(f"  平均工作大小: {bp_stats['job_size_mean']:.2f}")
    print(f"  標準差: {bp_stats['job_size_std']:.2f}")
    
    print(f"\nNormal (mean={normal_param['mean']}, std={normal_param['std']}):")
    print(f"  平均工作大小: {normal_stats['job_size_mean']:.2f}")
    print(f"  標準差: {normal_stats['job_size_std']:.2f}")

def example_3_test_random_modes():
    """範例 3: 測試不同的隨機模式"""
    print("\n" + "="*60)
    print("範例 3: 測試隨機和軟隨機模式")
    print("="*60)
    
    num_jobs = 5000
    coherence_time = 128
    
    # Random 模式
    bp_random = Job_init.bounded_pareto_random_job_init(num_jobs, coherence_time)
    random_stats = Job_init.analyze_jobs(bp_random)
    
    # Soft Random 模式
    bp_softrandom = Job_init.bounded_pareto_soft_random_job_init(num_jobs, coherence_time)
    softrandom_stats = Job_init.analyze_jobs(bp_softrandom)
    
    print(f"\nBP Random (coherence_time={coherence_time}):")
    print(f"  平均工作大小: {random_stats['job_size_mean']:.2f}")
    print(f"  標準差: {random_stats['job_size_std']:.2f}")
    
    print(f"\nBP Soft Random (coherence_time={coherence_time}):")
    print(f"  平均工作大小: {softrandom_stats['job_size_mean']:.2f}")
    print(f"  標準差: {softrandom_stats['job_size_std']:.2f}")

def example_4_coherence_time_sensitivity():
    """範例 4: Coherence time 敏感度分析"""
    print("\n" + "="*60)
    print("範例 4: Coherence Time 敏感度分析")
    print("="*60)
    
    num_jobs = 5000
    coherence_times = [2, 8, 32, 128, 512, 2048, 8192]
    
    results = []
    for ct in coherence_times:
        job_list = Job_init.bounded_pareto_random_job_init(num_jobs, coherence_time=ct)
        stats = Job_init.analyze_jobs(job_list)
        results.append({
            'ct': ct,
            'mean': stats['job_size_mean'],
            'std': stats['job_size_std']
        })
    
    print("\nCoherence Time | 平均工作大小 | 標準差")
    print("-" * 50)
    for r in results:
        print(f"{r['ct']:14d} | {r['mean']:12.2f} | {r['std']:10.2f}")

def example_5_export_results():
    """範例 5: 導出測試結果"""
    print("\n" + "="*60)
    print("範例 5: 運行完整測試並導出結果")
    print("="*60)
    
    # 運行測試（簡化版，較少工作數量）
    print("\n正在運行測試...")
    results = Job_init.test_job_generation(num_jobs=1000, verbose=False)
    
    # 導出結果
    os.makedirs('test_output', exist_ok=True)
    output_file = 'test_output/example_results.csv'
    Job_init.export_test_results_to_csv(results, output_file)
    
    print(f"\n測試完成！結果已保存到: {output_file}")
    print(f"共測試了 {len(results)} 個配置")

def example_6_visualize_distribution():
    """範例 6: 視覺化工作大小分布"""
    print("\n" + "="*60)
    print("範例 6: 視覺化工作大小分布")
    print("="*60)
    
    num_jobs = 5000
    
    # 生成三種不同的工作列表
    bp_param = Job_init.bp_parameter_30[1]
    normal_param = Job_init.normal_parameter_30[1]
    
    bp_jobs = Job_init.job_init(num_jobs, 30, bp_param)
    normal_jobs = Job_init.job_init(num_jobs, 30, normal_param)
    random_jobs = Job_init.bounded_pareto_random_job_init(num_jobs, 128)
    
    # 提取工作大小
    bp_sizes = [job['job_size'] for job in bp_jobs]
    normal_sizes = [job['job_size'] for job in normal_jobs]
    random_sizes = [job['job_size'] for job in random_jobs]
    
    # 創建圖表
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    axes[0].hist(bp_sizes, bins=50, edgecolor='black', alpha=0.7)
    axes[0].set_title(f'BP Distribution\nL={bp_param["L"]:.2f}, H={bp_param["H"]:.0f}')
    axes[0].set_xlabel('Job Size')
    axes[0].set_ylabel('Frequency')
    
    axes[1].hist(normal_sizes, bins=50, edgecolor='black', alpha=0.7, color='green')
    axes[1].set_title(f'Normal Distribution\nmean={normal_param["mean"]}, std={normal_param["std"]}')
    axes[1].set_xlabel('Job Size')
    axes[1].set_ylabel('Frequency')
    
    axes[2].hist(random_sizes, bins=50, edgecolor='black', alpha=0.7, color='red')
    axes[2].set_title('BP Random (CT=128)')
    axes[2].set_xlabel('Job Size')
    axes[2].set_ylabel('Frequency')
    
    plt.tight_layout()
    
    # 保存圖表
    os.makedirs('test_output', exist_ok=True)
    output_file = 'test_output/example_distributions.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n圖表已保存到: {output_file}")
    
    # 也顯示圖表（如果有顯示器）
    try:
        plt.show()
    except:
        print("無法顯示圖表（可能沒有圖形界面）")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='工作生成測試範例')
    parser.add_argument('--example', type=int, default=0,
                       help='運行特定範例 (1-6)，0 表示運行所有範例')
    
    args = parser.parse_args()
    
    examples = {
        1: example_1_basic_analysis,
        2: example_2_compare_distributions,
        3: example_3_test_random_modes,
        4: example_4_coherence_time_sensitivity,
        5: example_5_export_results,
        6: example_6_visualize_distribution
    }
    
    if args.example == 0:
        # 運行所有範例
        for i in range(1, 7):
            examples[i]()
            print()  # 空行分隔
    elif args.example in examples:
        examples[args.example]()
    else:
        print(f"錯誤: 範例 {args.example} 不存在")
        print("請選擇 0-6 之間的數字")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("所有範例執行完畢！")
    print("="*60)
