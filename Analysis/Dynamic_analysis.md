# Dynamic 演算法分析文件

## 一、演算法概述

Dynamic 是一種**混合式排程演算法**，透過動態切換 SRPT (Shortest Remaining Processing Time) 和 FCFS (First Come, First Served) 兩種策略，以達到最佳化工作流程時間 (Flow Time) 的目標。

### 核心特點
- **自適應切換**：根據歷史工作負載動態選擇最適合的排程策略
- **檢查點機制**：每當 `nJobsPerRound` 個工作到達時觸發決策點
- **L2 Norm 最佳化**：使用 L2 範數作為效能指標，強調極端值的影響

---

## 二、演算法原理

### 2.1 基本概念

Dynamic 演算法的核心思想是：**不同的工作負載特性適合不同的排程策略**。

- **SRPT**：優先處理剩餘處理時間最短的工作
  - 優點：最小化平均 flow time
  - 缺點：可能導致大工作飢餓 (starvation)

- **FCFS**：按到達順序處理工作
  - 優點：公平性高，無飢餓問題
  - 缺點：無法優化 flow time

### 2.2 決策機制

在每個檢查點，演算法：
1. 收集歷史工作資訊
2. 模擬 SRPT 和 FCFS 的表現
3. 選擇 L2 範數較低的策略

---

## 三、虛擬碼 (Pseudo Code)

```
演算法: Dynamic (混合式 SRPT/FCFS 排程)
輸入: jobs[] - 工作列表
      nJobsPerRound - 每輪到達工作數
      mode - 歷史回顧模式 (1-6)
輸出: avg_flow_time, l2_norm, max_flow_time

初始化:
    current_time ← 0
    active_jobs ← 空隊列
    completed_jobs ← 空列表
    round_history ← 空列表
    is_srpt_better ← true
    current_round ← 1
    currently_executing ← null

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
            is_srpt_better ← true
            記錄 "SRPT" 到 algorithm_history
        ELSE
            // 決定有效模式
            effective_mode ← 根據 mode 和 current_round 決定

            // 收集歷史工作進行模擬
            jobs_to_simulate ← 收集最近 N 輪的工作

            // 運行模擬
            srpt_l2 ← 模擬_SRPT(jobs_to_simulate)
            fcfs_l2 ← 模擬_FCFS(jobs_to_simulate)

            is_srpt_better ← (srpt_l2 <= fcfs_l2)
            記錄選擇結果

        current_round++
        更新 jobs_in_current_round

    // 步驟 3: 選擇下一個執行的工作
    IF (currently_executing 為空 AND active_jobs 非空)
        IF (is_srpt_better)
            currently_executing ← SRPT選擇(active_jobs)
        ELSE
            currently_executing ← FCFS選擇(active_jobs)

        設定 start_time

    // 步驟 4: 執行工作
    IF (currently_executing 不為空)
        計算執行時間 delta:
            - SRPT模式: 執行到下次到達或完成
            - FCFS模式: 執行到完成

        current_time += delta
        remaining_time -= delta

        IF (remaining_time == 0)
            設定 completion_time
            加入 completed_jobs
            currently_executing ← null
    ELSE
        // 空閒，跳到下一個到達時間
        current_time ← 下一個工作到達時間

// 計算最終指標
FOR each job in completed_jobs:
    flow_time ← completion_time - arrival_time
    累加 sum_flow, sum_sq
    更新 max_flow

RETURN (sum_flow / n, sqrt(sum_sq), max_flow)
```

---

## 四、模式 (Mode) 說明

| 模式 | 回顧輪數 | 啟用條件 | 說明 |
|------|----------|----------|------|
| 1 | 1 輪 | 始終可用 | 僅使用上一輪資料 |
| 2 | 2 輪 | round >= 3 | 使用最近 2 輪資料 |
| 3 | 4 輪 | round >= 5 | 使用最近 4 輪資料 |
| 4 | 8 輪 | round >= 9 | 使用最近 8 輪資料 |
| 5 | 16 輪 | round >= 17 | 使用最近 16 輪資料 |
| 6 | 全部 | 始終可用 | 使用所有歷史資料 |

### 模式選擇建議
- **短期負載變化大**：使用較小的 mode (1-2)
- **長期負載穩定**：使用較大的 mode (5-6)
- **一般情況**：mode 3 或 4 是較好的平衡點

---

## 五、分析輸出格式

### 5.1 CSV 檔案結構

```csv
arrival_rate,bp_L,bp_H,FCFS_percentage,SRPT_percentage,total_rounds
22.00,4.64,32768,0.40,99.60,500
40.00,16.77,64,93.80,6.20,500
```

### 5.2 欄位說明

| 欄位名稱 | 說明 | 範例 |
|----------|------|------|
| arrival_rate | 工作到達率 (平均間隔時間) | 22.00 |
| bp_L | Bounded Pareto 分布的 L 參數 | 4.64 |
| bp_H | Bounded Pareto 分布的 H 參數 | 32768 |
| FCFS_percentage | 選擇 FCFS 的輪次百分比 | 0.40 |
| SRPT_percentage | 選擇 SRPT 的輪次百分比 | 99.60 |
| total_rounds | 總輪次數 | 500 |

### 5.3 輸出目錄結構

```
Analysis/Dynamic_analysis/
├── avg_30/
│   ├── mode_1/
│   │   └── Dynamic_avg_30_nJobsPerRound_100_mode_1_round_1.csv
│   ├── mode_2/
│   ├── mode_3/
│   ├── mode_4/
│   ├── mode_5/
│   └── mode_6/
├── Random/
│   └── ...
└── Softrandom/
    └── ...
```

---

## 六、效能特性

### 6.1 時間複雜度

| 操作 | 複雜度 |
|------|--------|
| 工作選擇 (SRPT) | O(n log n) |
| 工作選擇 (FCFS) | O(n) |
| 模擬執行 | O(n log n) |
| 整體排程 | O(n^2 log n) 最壞情況 |

### 6.2 空間複雜度

| 項目 | 複雜度 |
|------|--------|
| 工作隊列 | O(n) |
| 歷史記錄 | O(n) |
| 模擬資料 | O(n) |

---

## 七、使用範例

### 7.1 命令列執行

```bash
# 使用預設參數 (nJobsPerRound=100, mode=1-6)
./Dynamic

# 指定 nJobsPerRound
./Dynamic 50

# 指定 nJobsPerRound 和 modes
./Dynamic 100 "1,2,3"
```

### 7.2 程式碼整合

```cpp
#include "Dynamic.h"

// 簡單呼叫
DynamicResult result = Dynamic(jobs);

// 完整參數
DynamicResult result = DYNAMIC(jobs, 100, 3, "path/to/input.csv");
```

---

## 八、實驗觀察

### 8.1 SRPT 選擇傾向

根據分析資料觀察：
- **高 H 值 (大工作變異)**：SRPT 選擇率接近 100%
- **低 H 值 (小工作變異)**：FCFS 選擇率較高
- **低到達率**：兩者差異不大

### 8.2 效能比較

| 場景 | SRPT 優勢 | FCFS 優勢 |
|------|-----------|-----------|
| 高變異工作分布 | 明顯 | - |
| 均勻工作分布 | 輕微 | 相當 |
| 高負載 | 明顯 | - |
| 低負載 | 相當 | 相當 |

---

## 九、參考文獻

1. SRPT (Shortest Remaining Processing Time) 最佳化證明
2. Flow Time 分析與 L2 Norm 指標
3. 線上排程演算法競爭比分析

---

## 十、附錄：關鍵程式碼片段

### A. SRPT 工作選擇

```cpp
Job* srpt_select_next_job_fast(std::vector<Job*>& active_jobs) {
    return *std::min_element(active_jobs.begin(), active_jobs.end(),
        [](const Job* a, const Job* b) {
            if (a->remaining_time != b->remaining_time)
                return a->remaining_time < b->remaining_time;
            return a->arrival_time < b->arrival_time;
        });
}
```

### B. FCFS 工作選擇

```cpp
Job* fcfs_select_next_job_fast(std::vector<Job*>& active_jobs) {
    return *std::min_element(active_jobs.begin(), active_jobs.end(),
        [](const Job* a, const Job* b) {
            if (a->arrival_time != b->arrival_time)
                return a->arrival_time < b->arrival_time;
            return a->job_index < b->job_index;
        });
}
```

### C. L2 Norm 計算

```cpp
double l2_norm = std::sqrt((double)sum_sq);
// 其中 sum_sq = Σ(flow_time_i)^2
```
