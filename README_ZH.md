# 固定到達率實驗 - 系統負載對排程演算法效能影響研究

**最後更新**: 2025-12-18
**版本**: 2.0 (重構版)

---

## 📋 目錄

1. [研究背景](#研究背景)
2. [核心發現](#核心發現)
3. [實驗設計](#實驗設計)
4. [理論基礎](#理論基礎)
5. [快速開始](#快速開始)
6. [詳細使用說明](#詳細使用說明)
7. [結果解讀](#結果解讀)
8. [程式碼架構](#程式碼架構)
9. [常見問題](#常見問題)

---

## 🎯 研究背景

### 問題起源

在之前的實驗中，我們觀察到一個令人困惑的現象：

**當 `coherence_time` 增加時，系統的 L2-norm flow time 顯著上升。**

最初我們認為可能的原因是：
- 工作大小分佈的變化（Bounded Pareto 的 H 引數）
- 分佈型別的差異（BP vs Normal）
- 引數切換頻率的影響

### 關鍵洞察 💡

透過深入分析，我們發現了真正的根本原因：

**系統負載 (ρ = E[job_size] / mean_inter_arrival_time) 才是決定性因素！**

#### 原始實驗的問題

在之前的設計中：
```python
inter_arrival_time = [20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]  # 11 個值
```

假設平均工作大小 E[X] = 30，計算系統負載：

| Mean Arrival Time | 到達率 λ | 服務率 μ | 利用率 ρ = λ/μ | 系統狀態 |
|-------------------|---------|---------|----------------|----------|
| 20 秒 | 0.050 | 0.033 | **1.50** | ⚠️ **過載** (unstable) |
| 22 秒 | 0.045 | 0.033 | **1.36** | ⚠️ **過載** |
| 24 秒 | 0.042 | 0.033 | **1.25** | ⚠️ **過載** |
| 26 秒 | 0.038 | 0.033 | **1.15** | ⚠️ **過載** |
| 28 秒 | 0.036 | 0.033 | **1.07** | ⚠️ **過載** |
| 30 秒 | 0.033 | 0.033 | **1.00** | ⚡ **臨界** |
| 32 秒 | 0.031 | 0.033 | **0.94** | ✅ **穩定** |
| 34 秒 | 0.029 | 0.033 | **0.88** | ✅ **穩定** |
| 36 秒 | 0.028 | 0.033 | **0.83** | ✅ **穩定** |
| 38 秒 | 0.026 | 0.033 | **0.79** | ✅ **穩定** |
| 40 秒 | 0.025 | 0.033 | **0.75** | ✅ **穩定** |

**問題所在**：
- 區間 [20, 40] 包含：
  - **6 個過載值** (20-28)：ρ > 1，佇列會無限增長
  - **1 個臨界值** (30)：ρ = 1
  - **4 個穩定值** (32-40)：ρ < 1

**當 `coherence_time` 高時**：
- 系統會長時間停留在**過載狀態** (ρ > 1)
- 佇列持續增長，無法清空
- 導致某些工作的 flow time 極長
- L2-norm 對異常值敏感，因此數值爆炸性增長

### 因此我們需要新的實驗設計 🔬

**核心思想**：**隔離變數，單獨測試系統負載的影響。**

---

## 🔍 核心發現

### 1. 系統負載 ρ 是決定性因素

**定義**：
```
ρ = E[job_size] / mean_inter_arrival_time
```

**物理意義**：
- ρ < 1：系統可以處理到達的工作，佇列可以清空
- ρ = 1：臨界狀態，系統處於邊緣
- ρ > 1：系統過載，佇列無限增長

### 2. Coherence Time 的作用

- **低 coherence_time**（如 2, 4秒）：
  - 引數頻繁切換
  - 系統在不同負載間快速切換
  - 過載期間較短，佇列可以在低負載期間恢復
  - L2-norm 相對較低

- **高 coherence_time**（如 32768, 65536秒）：
  - 引數長時間不變
  - 若 ρ > 1，佇列持續增長
  - 即使後續切換到 ρ < 1，積累的佇列需要很長時間清空
  - 部分工作的 flow time 極長，導致 L2-norm 爆炸

### 3. 分佈型別的影響是次要的

無論是 Bounded Pareto 還是 Normal 分佈：
- 只要 E[X] = 30，在相同的 mean_inter_arrival_time 下
- 系統負載 ρ 相同
- 效能表現應該類似

---

## 🧪 實驗設計

### 實驗目標

**驗證假設**：系統負載 ρ 是影響效能的主要因素。

### 實驗方案：固定到達率實驗

#### 核心原理

**固定 mean inter-arrival time**，只改變工作大小分佈引數。

#### 三個負載場景

| 場景 | Mean Arrival Time | 理論 ρ | 系統狀態 | 預期表現 |
|------|------------------|--------|----------|----------|
| **過載** | 20 | 1.5 | 佇列無限增長 | L2-norm 極高 |
| **臨界** | 30 | 1.0 | 邊緣穩定 | L2-norm 中等，敏感 |
| **穩定** | 40 | 0.75 | 系統可處理 | L2-norm 低 |

#### 測試引數

**Bounded Pareto 引數**（5個）：
```python
BP_PARAMETERS = [
    {"L": 16.772, "H": 64},       # E[X] = 30
    {"L": 7.918, "H": 512},       # E[X] = 30
    {"L": 5.649, "H": 4096},      # E[X] = 30
    {"L": 4.639, "H": 32768},     # E[X] = 30
    {"L": 4.073, "H": 262144}     # E[X] = 30
]
```

**Normal 分佈引數**（5個）：
```python
NORMAL_PARAMETERS = [
    {"mean": 30, "std": 6},   # 緊湊分佈
    {"mean": 30, "std": 9},   # 中等方差
    {"mean": 30, "std": 12},  # 較寬分佈
    {"mean": 30, "std": 15},  # 更寬分佈
    {"mean": 30, "std": 18}   # 最寬分佈
]
```

**Coherence Times**（16個）：
```python
[2^1, 2^2, 2^3, ..., 2^16] = [2, 4, 8, ..., 65536]
```

#### 實驗規模

```
總資料集數量 = 3 (負載) × 10 (引數) × 16 (coherence) × 10 (重複) = 4,800 個
```

---

## 📐 理論基礎

### M/G/1 佇列理論

我們的系統可以建模為 M/G/1 佇列：
- **M** (Markovian)：泊松到達過程
- **G** (General)：通用服務時間分佈
- **1**：單一伺服器

#### 關鍵公式

**平均佇列長度** (Pollaczek-Khinchine 公式)：
```
E[L] = ρ + (ρ² + λ² Var[S]) / (2(1-ρ))

其中：
- ρ：系統負載
- λ：到達率
- Var[S]：服務時間方差
```

**觀察**：
- 當 ρ → 1 時，E[L] → ∞
- 當 ρ > 1 時，佇列不穩定，無限增長

### Flow Time 的定義

```
Flow Time = Completion Time - Arrival Time
```

對於每個工作 i：
```
F_i = C_i - A_i
```

### L2-Norm Flow Time

```
L2-norm = sqrt(Σ(F_i²))
```

**特性**：
- 對異常值（極大的 flow time）非常敏感
- 平方操作放大了大值的影響
- 適合檢測系統過載情況

---

## 🚀 快速開始

### 前置要求

```bash
# Python 依賴
pip install numpy pandas matplotlib tqdm

# C++ 編譯器
# macOS: 確保安裝了 Xcode Command Line Tools
xcode-select --install
```

### 步驟 1：測試配置

```bash
cd /Users/melowu/Desktop/ultimus/experiments
python3 config.py
```

**預期輸出**：
```
======================================================================
實驗配置摘要
======================================================================
固定到達率: [20, 30, 40]
  - 過載 (ρ=1.5): mean_arrival = 20
  - 臨界 (ρ=1.0): mean_arrival = 30
  - 穩定 (ρ=0.75): mean_arrival = 40

Coherence Times: 16 個 (2^1 到 2^16)
BP 引數: 5 個
Normal 引數: 5 個
總引數組合: 10 個

每個配置生成 10000 個工作
每個配置重複 10 次

總實驗數: 3 × 10 × 16 × 10
         = 4800 個資料集
======================================================================
```

### 步驟 2：生成測試資料

```bash
cd /Users/melowu/Desktop/ultimus/experiments
python3 fixed_arrival_experiment.py --test
```

這將生成小規模測試資料集（約18個檔案）用於驗證流程。

### 步驟 3：執行演算法（單個演算法測試）

```bash
cd /Users/melowu/Desktop/ultimus/Cpp_Optimization/algorithms/SRPT
make clean && make
./SRPT
```

### 步驟 4：生成圖表

```bash
cd /Users/melowu/Desktop/ultimus/plotting
python3 plot_fixed_arrival.py
```

檢視結果：
```bash
open /Users/melowu/Desktop/ultimus/plots_output/fixed_arrival_overload_BP_H512_clairvoyant.png
```

---

## 📚 詳細使用說明

### 完整實驗流程

#### 1. 生成完整資料集

```bash
cd /Users/melowu/Desktop/ultimus/experiments
python3 fixed_arrival_experiment.py --full
```

⚠️ **注意**：完整資料集生成需要較長時間（約1-2小時）。

**進度提示**：
```
【重複 1/10】

  負載條件: overload (arrival=20, ρ=1.50)
  引數: 100%|██████████| 10/10 [05:23<00:00, 32.35s/it]

  負載條件: critical (arrival=30, ρ=1.00)
  引數: 100%|██████████| 10/10 [05:15<00:00, 31.58s/it]

  負載條件: stable (arrival=40, ρ=0.75)
  引數: 100%|██████████| 10/10 [05:08<00:00, 30.82s/it]
```

**生成的資料結構**：
```
data/
├── fixed_arrival_overload_1/
│   ├── param_BP_H64/
│   │   ├── coherence_2/
│   │   │   └── fixed_arrival_overload_BP_H64_ct2.csv
│   │   ├── coherence_4/
│   │   └── ...
│   ├── param_BP_H512/
│   ├── param_Normal_std6/
│   └── ...
├── fixed_arrival_critical_1/
├── fixed_arrival_stable_1/
├── fixed_arrival_overload_2/
└── ... (重複 2-10)
```

#### 2. 更新演算法 C++ 程式碼

對於每個演算法，新增新的實驗處理：

**示例：SRPT.cpp**

```cpp
// 在檔案開頭新增 include
#include "process_fixed_arrival_experiment.h"

// 在 main() 函式末尾，其他實驗之後新增：

std::cout << "\n========================================\n";
std::cout << "Processing Fixed Arrival Experiment...\n";
std::cout << "========================================\n";
process_fixed_arrival_experiment(SRPT, "SRPT", data_dir, output_dir);
```

**需要更新的演算法**：
- SRPT
- Dynamic
- Dynamic_BAL
- RFDynamic
- BAL
- FCFS
- SETF
- RMLF

#### 3. 編譯並執行演算法

**方法 A：單獨編譯執行**

```bash
# SRPT
cd /Users/melowu/Desktop/ultimus/Cpp_Optimization/algorithms/SRPT
make clean && make
./SRPT

# Dynamic
cd /Users/melowu/Desktop/ultimus/Cpp_Optimization/algorithms/Dynamic
make clean && make
./Dynamic

# ... 依此類推
```

**方法 B：使用批處理指令碼**（推薦）

```bash
cd /Users/melowu/Desktop/ultimus
./run_all_algorithms.sh
```

**預期輸出**（每個演算法）：
```
======================================================================
處理固定到達率實驗: SRPT
======================================================================

負載條件: overload, 重複 1
  引數: BP_H64
    ct=2, L2=1234.56, MaxFlow=5678.90
    ct=4, L2=1345.67, MaxFlow=6789.01
    ...
  引數: BP_H512
    ...

----------------------------------------------------------------------
儲存結果...
✓ 完成！儲存了 480 個結果檔案
======================================================================
```

#### 4. 生成所有圖表

```bash
cd /Users/melowu/Desktop/ultimus/plotting
python3 plot_fixed_arrival.py
```

**生成的圖表**（60張）：
```
plots_output/
├── fixed_arrival_overload_BP_H64_clairvoyant.png
├── fixed_arrival_overload_BP_H64_non_clairvoyant.png
├── fixed_arrival_overload_BP_H512_clairvoyant.png
├── fixed_arrival_overload_BP_H512_non_clairvoyant.png
├── ...
├── fixed_arrival_stable_Normal_std18_clairvoyant.png
└── fixed_arrival_stable_Normal_std18_non_clairvoyant.png
```

---

## 📊 結果解讀

### 檢視圖表

```bash
# 過載場景
open plots_output/fixed_arrival_overload_*_clairvoyant.png

# 臨界場景
open plots_output/fixed_arrival_critical_*_clairvoyant.png

# 穩定場景
open plots_output/fixed_arrival_stable_*_clairvoyant.png
```

### 預期觀察結果

#### 場景 1：過載 (ρ=1.5)

**預期**：
- ✅ L2-norm **極高**（可能達到數十萬）
- ✅ 隨 coherence_time 增加而**顯著上升**
- ✅ 所有參數列現類似（因為都是 ρ=1.5）

**原因**：
- 系統始終過載
- 佇列持續增長
- Coherence time 越長，積累的佇列越多

**圖表特徵**：
```
L2-norm
  ↑
  |        ________/
  |      _/
  |    _/
  |  _/
  | /
  |________________→ Coherence Time
   2   8   32  128  ...
```

#### 場景 2：臨界 (ρ=1.0)

**預期**：
- ✅ L2-norm **中等**（數千到數萬）
- ✅ 對 coherence_time **敏感**
- ✅ 不同引數可能有差異（方差影響）

**原因**：
- 系統處於邊緣
- 微小波動可能導致暫時過載或恢復
- Coherence time 影響系統調整能力

**圖表特徵**：
```
L2-norm
  ↑
  |          ___/
  |        _/
  |      _/
  |    _/
  |  _/
  |________________→ Coherence Time
```

#### 場景 3：穩定 (ρ=0.75)

**預期**：
- ✅ L2-norm **低**（數百到數千）
- ✅ 相對**平坦**，對 coherence_time 不敏感
- ✅ 演算法間差異較小

**原因**：
- 系統有餘量處理工作
- 佇列可以清空
- Coherence time 影響較小

**圖表特徵**：
```
L2-norm
  ↑
  |  _____________
  | /
  |/
  |________________→ Coherence Time
```

### 跨場景比較

**關鍵問題**：
1. L2-norm 是否滿足：**過載 > 臨界 > 穩定**？
2. Coherence time 的影響是否：**過載 > 臨界 > 穩定**？
3. 不同分佈型別（BP vs Normal）在相同負載下表現是否類似？

**如果答案都是"是"**，則驗證了我們的假設：**系統負載 ρ 是決定性因素。**

### 演算法效能評估

**問題**：
- 在**過載**場景下，哪個演算法表現最好？
- 在**穩定**場景下，演算法間差異是否縮小？
- Clairvoyant 演算法是否在所有場景下都優於 Non-clairvoyant？

---

## 🏗️ 程式碼架構

### 目錄結構

```
ultimus/
├── experiments/                     # 實驗模組
│   ├── config.py                    # 配置（引數定義）
│   ├── data_generator.py           # 資料生成核心函式
│   └── fixed_arrival_experiment.py # 固定到達率實驗
│
├── Cpp_Optimization/                # C++ 演算法
│   └── function_tools/
│       └── process_fixed_arrival_experiment.h  # 統一處理標頭檔案
│
├── plotting/                        # 繪圖模組
│   └── plot_fixed_arrival.py       # 固定到達率繪圖
│
├── data/                            # 生成的資料
│   └── fixed_arrival_*/
│
├── algorithm_result/                # 演算法結果
│   └── {Algorithm}_result/
│       └── fixed_arrival_experiment_result/
│
├── plots_output/                    # 生成的圖表
│
├── README_ZH.md                     # 本文件
└── Write_csv.py                     # CSV 寫入工具
```

### 模組說明

#### `experiments/config.py`
- 集中定義所有實驗引數
- 負載場景定義
- Bounded Pareto 和 Normal 引數
- Coherence times
- 演算法分類

#### `experiments/data_generator.py`
- 核心資料生成函式
- 分佈生成（BP, Normal）
- 工作序列生成
- 統計分析函式

#### `experiments/fixed_arrival_experiment.py`
- 固定到達率實驗的主邏輯
- 遍歷所有配置生成資料
- 支援完整執行和測試模式

#### `Cpp_Optimization/function_tools/process_fixed_arrival_experiment.h`
- C++ 統一實驗處理模板
- 自動遍歷資料目錄
- 呼叫演算法並儲存結果

#### `plotting/plot_fixed_arrival.py`
- 生成所有視覺化圖表
- 自動檢測引數配置
- Clairvoyant / Non-clairvoyant 分類

---

## ❓ 常見問題

### Q1: 為什麼要重複 10 次？

**答**：增加統計可靠性。
- 隨機性：到達時間和工作大小都是隨機生成的
- 平均值更穩定：10 次重複的平均值可以減少隨機波動
- 標準差：可以觀察結果的分散程度

### Q2: 為什麼選擇這三個負載值？

**答**：代表三種典型系統狀態。
- **ρ=1.5**：明顯過載，驗證極端情況
- **ρ=1.0**：臨界點，最有趣的區域
- **ρ=0.75**：穩定狀態，作為基線

### Q3: 所有 BP 引數的 E[X] 真的都是 30 嗎？

**答**：是的。Bounded Pareto 的期望值公式：
```
E[X] = α/(α-1) * (L - H*(L/H)^α) / (1 - (L/H)^α)

其中 α = 1.1
```
我們精心選擇 L 值，使得對於不同的 H，E[X] 始終等於 30。

### Q4: 如果我只想測試特定演算法怎麼辦？

**答**：
```bash
# 只編譯和執行 SRPT
cd Cpp_Optimization/algorithms/SRPT
make clean && make
./SRPT

# 只繪製 SRPT 的圖表
# 修改 plotting/plot_fixed_arrival.py
# 將 CLAIRVOYANT_ALGORITHMS = ['SRPT']
```

### Q5: 資料檔案太大，如何清理？

**答**：
```bash
# 刪除所有生成的資料（保留程式碼）
rm -rf data/fixed_arrival_*

# 刪除演算法結果
rm -rf algorithm_result/*/fixed_arrival_experiment_result

# 刪除圖表
rm -rf plots_output/fixed_arrival_*
```

### Q6: 為什麼 L2-norm 比平均 flow time 更敏感？

**答**：數學性質不同。
```
平均 flow time = (F1 + F2 + ... + Fn) / n
L2-norm = sqrt((F1² + F2² + ... + Fn²) / n)
```

如果有一個極大的 flow time，比如 F1 = 100000：
- 對平均值的影響：+100000/n
- 對 L2-norm 的影響：+sqrt(10000000000/n)

平方操作放大了異常值的貢獻。

### Q7: 我可以增加更多負載場景嗎？

**答**：可以！修改 `experiments/config.py`：
```python
FIXED_ARRIVAL_RATES = {
    "extreme_overload": 15,  # ρ = 2.0
    "overload": 20,          # ρ = 1.5
    "critical": 30,          # ρ = 1.0
    "stable": 40,            # ρ = 0.75
    "light": 50             # ρ = 0.6
}
```

---

## 🎓 研究意義

### 學術貢獻

1. **量化了系統負載的影響**
   - 明確了 ρ 與效能指標的關係
   - 驗證了佇列理論的預測

2. **揭示了 Coherence Time 的作用機制**
   - 不是引數本身，而是引數切換頻率影響系統恢復能力

3. **比較了不同排程演算法在不同負載下的表現**
   - Clairvoyant vs Non-clairvoyant
   - Overload vs Stable 場景

### 實踐價值

1. **系統設計指導**
   - 應該控制系統負載 ρ < 1
   - 即使是短暫的過載也可能導致長期影響

2. **引數配置建議**
   - 頻繁調整引數（低 coherence time）可以緩解過載影響
   - 但也增加了系統複雜度

3. **演算法選擇依據**
   - 不同負載場景下，演算法效能排名可能不同
   - 應根據預期負載選擇合適的排程策略

---

## 📞 聯絡與支援

如有問題或建議，請：
1. 檢視本文件的"常見問題"部分
2. 檢查日誌檔案：`logs/`
3. 驗證配置：`python3 experiments/config.py`

