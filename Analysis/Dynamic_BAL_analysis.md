# Dynamic_BAL 演算法分析文件

## 一、演算法概述

Dynamic_BAL 是一種**混合式排程演算法**，透過動態切換 BAL (Balanced Algorithm) 和 FCFS (First Come, First Served) 兩種策略。BAL 演算法特別設計用於**防止工作飢餓**，同時維持良好的平均 flow time。

### 核心特點
- **防飢餓機制**：BAL 使用飢餓閾值來確保大工作不會無限期等待
- **動態切換**：根據歷史工作負載動態選擇最適合的排程策略
- **L2 Norm 最佳化**：使用 L2 範數作為效能指標

### 與 Dynamic 的主要差異
| 特性 | Dynamic | Dynamic_BAL |
|------|---------|-------------|
| 主要策略 | SRPT | BAL |
| 飢餓防護 | 無 | 有 (閾值機制) |
| 適用場景 | 工作大小變異小 | 工作大小變異大 |

---

## 二、演算法原理

### 2.1 BAL 演算法核心

BAL (Balanced Algorithm) 的核心概念是在 **最佳化 flow time** 和 **防止飢餓** 之間取得平衡。

#### 飢餓閾值計算
```
starvation_threshold = N^(2/3)
```
其中 N 是總工作數量。

#### 工作選擇邏輯
1. 優先選擇 **飢餓中的工作** (等待時間超過閾值)
2. 若無飢餓工作，選擇 **剩餘時間最短的工作**

### 2.2 決策機制

```
工作選擇優先順序:
1. 檢查是否有工作的等待時間 > starvation_threshold
   ├── 有 → 選擇等待最久的飢餓工作
   └── 無 → 選擇剩餘處理時間最短的工作 (類似 SRPT)
```

### 2.3 FCFS 對比

| 特性 | BAL | FCFS |
|------|-----|------|
| 選擇依據 | 飢餓優先 + SRPT | 到達順序 |
| 搶佔式 | 是 | 否 |
| 公平性 | 中等 | 高 |
| Flow Time | 良好 | 一般 |

---

## 三、虛擬碼 (Pseudo Code)

```
演算法: Dynamic_BAL (混合式 BAL/FCFS 排程)
輸入: jobs[] - 工作列表
      nJobsPerRound - 每輪到達工作數
      mode - 歷史回顧模式 (1-6)
輸出: avg_flow_time, l2_norm, max_flow_time

初始化:
    total_jobs ← jobs.size()
    starvation_threshold ← total_jobs^(2/3)    // 關鍵：飢餓閾值
    current_time ← 0
    active_jobs ← 空隊列
    completed_jobs ← 空列表
    round_history ← 空列表
    is_bal_better ← true
    current_round ← 1
    currently_executing ← null

    FOR each job in jobs:
        job.remaining_time ← job.job_size
        job.starving_time ← -1              // BAL 特有欄位
        job.waiting_time_ratio ← 0.0        // BAL 特有欄位

主迴圈: WHILE (未完成工作數 < 總工作數)

    // 步驟 1: 接收到達的工作
    WHILE (有工作在 current_time 或之前到達)
        將工作加入 active_jobs
        記錄到 jobs_in_current_round
        n_arrival_jobs++

    // 步驟 2: 檢查點邏輯
    WHILE (n_arrival_jobs >= nJobsPerRound)
        儲存當前輪次工作到 round_history

        IF (currently_executing 不為空)
            暫停執行中的工作
            放回 active_jobs

        IF (current_round == 1)
            is_bal_better ← true
            記錄 "BAL" 到 algorithm_history
        ELSE
            // 決定有效模式
            effective_mode ← 根據 mode 和 current_round 決定

            // 收集歷史工作進行模擬
            jobs_to_simulate ← 收集最近 N 輪的工作

            // 運行模擬
            bal_l2 ← 模擬_BAL(jobs_to_simulate, starvation_threshold)
            fcfs_l2 ← 模擬_FCFS(jobs_to_simulate)

            is_bal_better ← (bal_l2 <= fcfs_l2)
            記錄選擇結果

        current_round++
        更新 jobs_in_current_round

    // 步驟 3: 選擇下一個執行的工作
    IF (currently_executing 為空 AND active_jobs 非空)
        IF (is_bal_better)
            currently_executing ← BAL選擇(active_jobs, current_time, starvation_threshold)
        ELSE
            currently_executing ← FCFS選擇(active_jobs)

        設定 start_time

    // 步驟 4: 執行工作 (與 Dynamic 相同)
    ...

// 計算最終指標
RETURN (avg_flow_time, l2_norm, max_flow_time)
```

---

## 四、BAL 工作選擇虛擬碼

```
演算法: BAL_SELECT (BAL 工作選擇)
輸入: active_jobs - 待處理工作列表
      current_time - 當前時間
      threshold - 飢餓閾值
輸出: selected_job - 選中的工作

函數 BAL_SELECT(active_jobs, current_time, threshold):

    // 步驟 1: 更新所有工作的等待資訊
    FOR each job in active_jobs:
        waiting_time ← current_time - job.arrival_time
        job.waiting_time_ratio ← waiting_time / job.job_size

    // 步驟 2: 找出飢餓的工作
    starving_jobs ← 空列表
    FOR each job in active_jobs:
        IF job.waiting_time_ratio > threshold:
            加入 starving_jobs

    // 步驟 3: 選擇工作
    IF starving_jobs 非空:
        // 優先處理等待比例最高的飢餓工作
        RETURN max(starving_jobs, key=waiting_time_ratio)
    ELSE:
        // 無飢餓工作，使用 SRPT 策略
        RETURN min(active_jobs, key=remaining_time)
```

---

## 五、模式 (Mode) 說明

與 Dynamic 相同的模式設定：

| 模式 | 回顧輪數 | 啟用條件 | 說明 |
|------|----------|----------|------|
| 1 | 1 輪 | 始終可用 | 僅使用上一輪資料 |
| 2 | 2 輪 | round >= 3 | 使用最近 2 輪資料 |
| 3 | 4 輪 | round >= 5 | 使用最近 4 輪資料 |
| 4 | 8 輪 | round >= 9 | 使用最近 8 輪資料 |
| 5 | 16 輪 | round >= 17 | 使用最近 16 輪資料 |
| 6 | 全部 | 始終可用 | 使用所有歷史資料 |

---

## 六、分析輸出格式

### 6.1 CSV 檔案結構

```csv
arrival_rate,bp_L,bp_H,FCFS_percentage,BAL_percentage,total_rounds
22.00,4.64,32768,5.20,94.80,500
40.00,16.77,64,88.40,11.60,500
```

### 6.2 欄位說明

| 欄位名稱 | 說明 | 範例 |
|----------|------|------|
| arrival_rate | 工作到達率 | 22.00 |
| bp_L | Bounded Pareto 分布的 L 參數 | 4.64 |
| bp_H | Bounded Pareto 分布的 H 參數 | 32768 |
| FCFS_percentage | 選擇 FCFS 的輪次百分比 | 5.20 |
| BAL_percentage | 選擇 BAL 的輪次百分比 | 94.80 |
| total_rounds | 總輪次數 | 500 |

### 6.3 輸出目錄結構

```
Analysis/Dynamic_BAL_analysis/
├── avg_30/
│   ├── mode_1/
│   │   └── Dynamic_BAL_avg_30_nJobsPerRound_100_mode_1_round_1.csv
│   ├── mode_2/
│   └── ...
├── Random/
└── Softrandom/
```

---

## 七、飢餓閾值分析

### 7.1 閾值公式推導

```
starvation_threshold = N^(2/3)
```

這個公式的設計考量：
- **N^(1/2)**：過於激進，可能導致過多的飢餓介入
- **N^(2/3)**：平衡點，在合理時間內處理大工作
- **N^(1)**：過於保守，大工作可能等待過久

### 7.2 不同 N 值的閾值

| 總工作數 N | 飢餓閾值 |
|------------|----------|
| 100 | 21.5 |
| 1,000 | 100.0 |
| 10,000 | 464.2 |
| 50,000 | 1,357.2 |

---

## 八、效能特性

### 8.1 時間複雜度

| 操作 | 複雜度 |
|------|--------|
| BAL 工作選擇 | O(n) |
| FCFS 工作選擇 | O(n) |
| 模擬執行 (BAL) | O(n^2) 最壞 |
| 整體排程 | O(n^2) |

### 8.2 空間複雜度

| 項目 | 複雜度 |
|------|--------|
| 工作隊列 | O(n) |
| 飢餓追蹤資料 | O(n) |
| 歷史記錄 | O(n) |

---

## 九、使用範例

### 9.1 命令列執行

```bash
# 使用預設參數
./Dynamic_BAL

# 指定 nJobsPerRound
./Dynamic_BAL 50

# 指定 nJobsPerRound 和 modes
./Dynamic_BAL 100 "1,2,3,4"
```

### 9.2 程式碼整合

```cpp
#include "Dynamic_BAL.h"

// 簡單呼叫
DynamicResult result = Dynamic_BAL(jobs);

// 完整參數
DynamicResult result = DYNAMIC_BAL(jobs, 100, 3, "path/to/input.csv");
```

---

## 十、實驗觀察

### 10.1 BAL vs SRPT 選擇傾向

| 場景 | BAL 選擇率 | 說明 |
|------|------------|------|
| 高 H 值 (大變異) | 較高 | BAL 的防飢餓機制更有效 |
| 低 H 值 (小變異) | 較低 | FCFS 表現相當 |
| 高負載 | 較高 | 飢餓問題更嚴重 |
| 低負載 | 相當 | 兩者差異不大 |

### 10.2 與 Dynamic (SRPT) 比較

| 指標 | Dynamic | Dynamic_BAL |
|------|---------|-------------|
| 平均 Flow Time | 較低 | 略高 |
| 最大 Flow Time | 可能很高 | 有界 |
| 公平性 | 低 | 較高 |
| 飢餓風險 | 高 | 低 |

---

## 十一、參考文獻

1. Balanced Algorithm 防飢餓機制設計
2. N^(2/3) 閾值公式理論推導
3. 線上排程演算法競爭比分析

---

## 十二、附錄：關鍵程式碼片段

### A. 飢餓閾值計算

```cpp
double starvation_threshold = std::pow(total_jobs, 2.0/3.0);
```

### B. BAL 工作選擇

```cpp
Job* bal_select_next_job_fast(std::vector<Job*>& active_jobs,
                               long long current_time,
                               double threshold) {
    // 更新等待時間資訊
    for (Job* job : active_jobs) {
        long long wait = current_time - job->arrival_time;
        job->waiting_time_ratio = (double)wait / job->job_size;
    }

    // 尋找飢餓工作
    Job* starving = nullptr;
    double max_ratio = 0;

    for (Job* job : active_jobs) {
        if (job->waiting_time_ratio > threshold &&
            job->waiting_time_ratio > max_ratio) {
            starving = job;
            max_ratio = job->waiting_time_ratio;
        }
    }

    if (starving) return starving;

    // 無飢餓，使用 SRPT
    return *std::min_element(active_jobs.begin(), active_jobs.end(),
        [](const Job* a, const Job* b) {
            return a->remaining_time < b->remaining_time;
        });
}
```

### C. Job 結構 (BAL 擴充)

```cpp
struct Job {
    int arrival_time;
    int job_size;
    int job_index;
    int remaining_time;
    long long start_time;
    long long completion_time;
    long long starving_time;      // BAL 專用
    double waiting_time_ratio;     // BAL 專用
};
```
