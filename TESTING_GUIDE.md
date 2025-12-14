# Job Generation Testing Guide

## 重構內容

已對 `Job_init.py` 進行重構，新增以下功能：

### 新增函數

1. **`analyze_jobs(job_list)`**
   - 分析工作列表的統計特性
   - 返回工作大小和抵達時間的詳細統計信息

2. **`test_job_generation(num_jobs, verbose)`**
   - 測試所有工作生成函數
   - 可選擇性打印詳細統計信息

3. **`export_test_results_to_csv(results, filename)`**
   - 將測試結果導出為 CSV 文件

4. **`compare_distributions(num_jobs)`**
   - 比較不同分布的工作大小特性
   - 返回 pandas DataFrame

### 命令行使用

#### 1. 生成原始數據（默認模式）
```bash
python Job_init.py --mode generate
```

#### 2. 運行測試
```bash
# 基本測試（生成 1000 個工作）
python Job_init.py --mode test

# 指定工作數量
python Job_init.py --mode test --num-jobs 5000

# 指定輸出文件
python Job_init.py --mode test --num-jobs 5000 --output my_test.csv
```

#### 3. 比較分布
```bash
# 比較不同分布特性
python Job_init.py --mode compare

# 指定工作數量和輸出文件
python Job_init.py --mode compare --num-jobs 10000 --output comparison.csv
```

## 測試腳本使用

`test_job_generation.py` 提供更詳細的測試和視覺化功能。

### 基本使用

#### 1. 運行所有測試
```bash
python test_job_generation.py --test all
```

#### 2. 比較 BP 和 Normal 分布
```bash
python test_job_generation.py --test compare
```

#### 3. 測試 Coherence Time 效果
```bash
python test_job_generation.py --test coherence
```

#### 4. 測試單個 BP 參數
```bash
# 測試第 0 個 BP 參數
python test_job_generation.py --test bp --param-index 0

# 測試第 2 個 BP 參數，生成 10000 個工作
python test_job_generation.py --test bp --param-index 2 --num-jobs 10000
```

#### 5. 測試單個 Normal 參數
```bash
python test_job_generation.py --test normal --param-index 1 --num-jobs 5000
```

### 保存圖表
```bash
# 運行測試並保存所有圖表到 test_output 目錄
python test_job_generation.py --test all --save-plots

# 比較分布並保存
python test_job_generation.py --test compare --save-plots
```

## 輸出文件

測試結果會保存在以下位置：

- `test_output/distribution_comparison.csv` - 分布比較結果
- `test_output/coherence_time_analysis.csv` - Coherence time 分析結果
- `test_output/*.png` - 各種圖表（如果使用 --save-plots）

## Python API 使用示例

```python
import Job_init

# 1. 生成工作並分析
param = Job_init.bp_parameter_30[0]
job_list = Job_init.job_init(5000, 30, param)
stats = Job_init.analyze_jobs(job_list)

print(f"平均工作大小: {stats['job_size_mean']:.2f}")
print(f"平均抵達間隔: {stats['inter_arrival_mean']:.2f}")

# 2. 運行完整測試
results = Job_init.test_job_generation(num_jobs=1000, verbose=True)

# 3. 導出結果
Job_init.export_test_results_to_csv(results, "my_results.csv")

# 4. 比較分布
df = Job_init.compare_distributions(num_jobs=5000)
print(df)
```

## 測試項目

### 工作大小統計
- 平均值 (mean)
- 標準差 (std)
- 最小值/最大值 (min/max)
- 中位數 (median)
- 四分位數 (Q25/Q75)

### 抵達時間統計
- 平均抵達間隔
- 抵達間隔標準差
- 最小/最大間隔
- 總持續時間
- 工作數量

### 測試的分布類型
1. **Bounded Pareto (avg_30)**
   - 5 個不同的 L, H 參數組合

2. **Normal (avg_30)**
   - 5 個不同的 mean, std 參數組合

3. **Random 模式**
   - Bounded Pareto random
   - Normal random
   - 多個 coherence time 值

4. **Soft Random 模式**
   - Bounded Pareto soft random
   - Normal soft random
   - 多個 coherence time 值

## 視覺化圖表

測試腳本會生成以下圖表：

1. **工作大小分布圖**
   - 直方圖
   - Box plot
   - 累積分布函數 (CDF)
   - 統計摘要

2. **抵達時間分布圖**
   - 抵達時間序列
   - 抵達間隔直方圖
   - 抵達間隔序列
   - 統計摘要

3. **Coherence Time 效果圖**
   - 平均工作大小 vs coherence time
   - 工作大小標準差 vs coherence time

## 建議的測試流程

1. **快速驗證**
   ```bash
   python test_job_generation.py --test compare --num-jobs 1000
   ```

2. **詳細分析**
   ```bash
   python test_job_generation.py --test all --num-jobs 5000 --save-plots
   ```

3. **特定參數測試**
   ```bash
   python test_job_generation.py --test bp --param-index 0 --num-jobs 10000 --save-plots
   ```

4. **Coherence time 敏感度分析**
   ```bash
   python test_job_generation.py --test coherence --num-jobs 10000 --save-plots
   ```

## 注意事項

- 測試會在 `test_output/` 目錄中創建輸出文件
- 較大的 `num-jobs` 值會提供更準確的統計結果，但需要更長的執行時間
- 圖表需要 X11 或圖形界面（如果不使用 --save-plots）
- 所有測試都使用相同的隨機種子以確保可重複性
