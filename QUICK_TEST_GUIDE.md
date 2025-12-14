# 快速測試指南

## 🚀 快速開始

### 1. 運行範例程式
```bash
# 運行所有範例
python examples.py

# 運行特定範例 (1-6)
python examples.py --example 1
```

### 2. 快速比較測試
```bash
# 比較 BP 和 Normal 分布
python test_job_generation.py --test compare --num-jobs 1000
```

### 3. 完整測試套件
```bash
# 運行所有測試並保存圖表
python test_job_generation.py --test all --num-jobs 5000 --save-plots
```

## 📊 範例說明

### 範例 1: 基本分析
```bash
python examples.py --example 1
```
- 生成 5000 個工作
- 分析工作大小和抵達時間統計

### 範例 2: 比較分布
```bash
python examples.py --example 2
```
- 比較 Bounded Pareto 和 Normal 分布
- 展示平均值和標準差差異

### 範例 3: 隨機模式
```bash
python examples.py --example 3
```
- 測試 Random 和 Soft Random 模式
- 比較兩種模式的統計特性

### 範例 4: Coherence Time
```bash
python examples.py --example 4
```
- 分析 coherence time 對工作分布的影響
- 測試多個 coherence time 值

### 範例 5: 導出結果
```bash
python examples.py --example 5
```
- 運行完整測試
- 將結果導出為 CSV 文件

### 範例 6: 視覺化
```bash
python examples.py --example 6
```
- 生成三種分布的直方圖
- 保存圖表到文件

## 📝 Python API 使用

### 基本用法
```python
import Job_init

# 生成工作
param = Job_init.bp_parameter_30[0]
jobs = Job_init.job_init(1000, 30, param)

# 分析統計
stats = Job_init.analyze_jobs(jobs)
print(f"平均工作大小: {stats['job_size_mean']:.2f}")
```

### 測試不同分布
```python
# Bounded Pareto
bp_jobs = Job_init.job_init(1000, 30, Job_init.bp_parameter_30[0])

# Normal
normal_jobs = Job_init.job_init(1000, 30, Job_init.normal_parameter_30[0])

# Random
random_jobs = Job_init.bounded_pareto_random_job_init(1000, coherence_time=128)

# Soft Random
soft_jobs = Job_init.bounded_pareto_soft_random_job_init(1000, coherence_time=128)
```

### 完整測試
```python
# 運行測試
results = Job_init.test_job_generation(num_jobs=1000, verbose=True)

# 導出結果
Job_init.export_test_results_to_csv(results, "results.csv")

# 比較分布
df = Job_init.compare_distributions(num_jobs=5000)
print(df)
```

## 📁 輸出文件位置

所有測試結果保存在 `test_output/` 目錄：

```
test_output/
├── distribution_comparison.csv       # 分布比較
├── coherence_time_analysis.csv      # Coherence time 分析
├── example_results.csv               # 範例測試結果
├── example_distributions.png         # 分布圖表
├── bp_jobsize_*.png                 # BP 工作大小圖
├── bp_arrival_*.png                 # BP 抵達時間圖
├── normal_jobsize_*.png             # Normal 工作大小圖
└── normal_arrival_*.png             # Normal 抵達時間圖
```

## 🔍 關鍵統計指標

### 工作大小統計
- `job_size_mean` - 平均工作大小
- `job_size_std` - 標準差
- `job_size_min/max` - 最小/最大值
- `job_size_median` - 中位數
- `job_size_q25/q75` - 四分位數

### 抵達時間統計
- `inter_arrival_mean` - 平均抵達間隔
- `inter_arrival_std` - 抵達間隔標準差
- `inter_arrival_min/max` - 間隔最小/最大值
- `total_duration` - 總持續時間
- `num_jobs` - 工作總數

## 💡 使用建議

1. **快速驗證**: 先用小樣本 (1000 jobs) 測試
2. **詳細分析**: 使用 5000-10000 jobs 獲得更準確的統計
3. **視覺化**: 使用 `--save-plots` 保存圖表供後續分析
4. **批量測試**: 使用 `--test all` 運行完整測試套件

## ⚡ 常見使用場景

### 場景 1: 驗證新參數
```bash
# 修改 Job_init.py 中的參數後
python examples.py --example 1
```

### 場景 2: 比較兩種分布
```bash
python test_job_generation.py --test compare --num-jobs 5000
```

### 場景 3: 調整 Coherence Time
```bash
python examples.py --example 4
```

### 場景 4: 生成報告
```bash
# 生成完整的測試報告
python test_job_generation.py --test all --num-jobs 10000 --save-plots
```

## 📚 更多信息

詳細文檔請參閱 `TESTING_GUIDE.md`
