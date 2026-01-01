# RFDynamic 演算法分析文件

## 一、演算法概述

RFDynamic (RMLF/FCFS Dynamic) 是一種**非透視 (Non-Clairvoyant) 混合式排程演算法**，透過動態切換 RMLF (Randomized Multi-Level Feedback) 和 FCFS (First Come, First Served) 策略。

### 核心特點
- **非透視性**：不需要事先知道工作的處理時間
- **兩階段設計**：Phase 1 建立工作池，Phase 2 動態切換
- **工作池機制**：透過歷史完成工作來估計未來工作特性
- **RMLF 策略**：使用量子 (quantum) 基礎的多層級回饋排程

### 與其他演算法比較

| 特性 | Dynamic | Dynamic_BAL | RFDynamic |
|------|---------|-------------|-----------|
| 需要知道工作大小 | 是 | 是 | **否** |
| 主要策略 | SRPT | BAL | RMLF |
| 適用場景 | 透視排程 | 防飢餓 | 非透視排程 |
| 兩階段設計 | 否 | 否 | **是** |

---

## 二、演算法原理

### 2.1 RMLF 演算法核心

RMLF (Randomized Multi-Level Feedback) 是一種**非透視排程演算法**，無需事先知道工作大小。

#### 基本運作方式
1. **量子 (Quantum)**：每個工作在當前級別獲得固定的 CPU 時間
2. **多層級**：工作用完量子後降級到下一層
3. **隨機化**：在同級別中隨機選擇工作

```
級別 0: 量子 = 1    (最高優先)
級別 1: 量子 = 2
級別 2: 量子 = 4
級別 3: 量子 = 8
...
級別 k: 量子 = 2^k
```

### 2.2 兩階段設計

#### Phase 1: 初始化 (FCFS 前 100 個完成)

```
目的: 建立初始工作池，收集工作大小分布資訊

執行:
1. 使用 FCFS 處理所有工作
2. 收集前 100 個完成的工作
3. 記錄這些工作的 job_size 到工作池
4. 這些資料作為後續模擬的基礎
```

#### Phase 2: 動態切換 (每 nJobsPerRound 個到達)

```
重複執行:
1. 等待 nJobsPerRound 個新工作到達
2. 從工作池取樣，模擬 RMLF 和 FCFS
3. 選擇 L2 Norm 較低的策略
4. 執行選定策略直到下一個檢查點
5. 更新工作池 (加入新完成的工作)
```

### 2.3 工作池 (JobSizePool)

工作池是 RFDynamic 的核心資料結構，用於追蹤歷史工作完成情況。

```
JobSizePool:
├── pool[] - 所有完成工作的大小記錄
├── add_job_size(size) - 加入新完成工作
├── sample_random(n) - 隨機取樣 n 個工作大小
└── get_simulation_set(target, recent) - 取得模擬用資料集
    ├── 優先使用 recent completions
    └── 不足時從 pool 隨機補足
```

---

## 三、虛擬碼 (Pseudo Code)

### 3.1 主演算法

```
演算法: RFDynamic (RMLF/FCFS 動態切換)
輸入: jobs[] - 工作列表
      nJobsPerRound - 每輪到達工作數
      mode - 歷史回顧模式 (1-6)
輸出: avg_flow_time, l2_norm, max_flow_time

常數:
    INITIAL_FCFS_COUNT = 100  // Phase 1 目標完成數

初始化:
    job_pool ← 新的 JobSizePool
    algorithm_history ← 空列表
    round_completions_history ← 空列表
    completion_count ← 0
    current_round ← 0

// ========== PHASE 1: FCFS 初始化 ==========
PHASE_1:
    輸出 "Phase 1: 使用 FCFS 完成前 100 個工作"

    // 執行完整 FCFS
    phase1_jobs ← 複製 jobs
    執行 FCFS(phase1_jobs)

    // 收集前 100 個完成的工作
    completed_with_time ← 按完成時間排序的工作列表

    FOR i = 0 TO INITIAL_FCFS_COUNT - 1:
        job ← completed_with_time[i]
        更新 job_pool_tracking[job.index]
        job_pool.add_job_size(job.job_size)
        completed_sizes_this_round.append(job.job_size)
        completion_count++

    // 儲存 Phase 1 完成記錄
    round_completions_history.append(completed_sizes_this_round)
    algorithm_history.append("FCFS")
    current_round ← 1

// ========== PHASE 2: 動態切換 ==========
PHASE_2:
    輸出 "Phase 2: 動態切換，每 nJobsPerRound 個到達觸發"
    next_job_idx ← 第一個未處理工作的索引
    use_fcfs ← true

    WHILE (next_job_idx < jobs.size()):
        current_round++
        completed_sizes_this_round ← 空列表

        // 確定這一輪要處理的工作範圍
        batch_end ← min(next_job_idx + nJobsPerRound, jobs.size())

        // 決定有效模式
        effective_mode ← 根據 mode 和 current_round 決定

        // 計算需要的歷史輪數
        rounds_needed ← 根據 effective_mode 決定

        // 收集最近完成的工作
        recent_completions ← 收集最近 rounds_needed 輪的完成工作

        // 取得模擬資料集
        simulation_set ← job_pool.get_simulation_set(
            target_size = rounds_needed * nJobsPerRound,
            recent_completions
        )

        // 模擬比較
        IF simulation_set 非空:
            fcfs_l2 ← simulate_fcfs_l2(simulation_set)
            rmlf_l2 ← simulate_rmlf_l2(simulation_set)
            use_fcfs ← (fcfs_l2 <= rmlf_l2)
        ELSE:
            use_fcfs ← true  // 預設

        algorithm_history.append(use_fcfs ? "FCFS" : "RMLF")

        // 執行選定策略
        accumulated_jobs ← jobs[0:batch_end]
        IF use_fcfs:
            執行 FCFS(accumulated_jobs)
        ELSE:
            執行 RMLF(accumulated_jobs)

        // 收集新完成的工作
        FOR each job in accumulated_jobs:
            IF job 新完成:
                更新 job_pool_tracking
                job_pool.add_job_size(job.job_size)
                completed_sizes_this_round.append(job.job_size)
                completion_count++

        // 儲存這輪的完成記錄
        round_completions_history.append(completed_sizes_this_round)
        next_job_idx ← batch_end

// 計算最終指標
FOR each job in job_pool_tracking:
    IF job 完成:
        flow_time ← completion_time - arrival_time
        累加統計

RETURN (avg_flow_time, l2_norm, max_flow_time)
```

### 3.2 RMLF 模擬

```
演算法: simulate_rmlf_l2 (模擬 RMLF 排程)
輸入: job_sizes[] - 工作大小列表
輸出: l2_norm - L2 範數

函數 simulate_rmlf_l2(job_sizes):
    // 建立模擬工作
    sim_jobs ← 空列表
    FOR i, size in enumerate(job_sizes):
        job ← 新工作(arrival_time=0, job_size=size, index=i)
        sim_jobs.append(job)

    // 執行 RMLF 排程
    result ← RMLF_algorithm(sim_jobs)

    RETURN result.l2_norm_flow_time
```

---

## 四、模式 (Mode) 說明

RFDynamic 的模式決定了用於模擬的歷史資料量。

| 模式 | 回顧輪數 | 啟用條件 | 目標大小計算 |
|------|----------|----------|--------------|
| 1 | 1 輪 | 始終可用 | 1 × nJobsPerRound |
| 2 | 2 輪 | round >= 3 | 2 × nJobsPerRound |
| 3 | 4 輪 | round >= 5 | 4 × nJobsPerRound |
| 4 | 8 輪 | round >= 9 | 8 × nJobsPerRound |
| 5 | 16 輪 | round >= 17 | 16 × nJobsPerRound |
| 6 | 全部 | 始終可用 | job_pool.size() |

### 模式選擇的影響

```
模擬資料集組成:
1. 優先使用 recent_completions (最近 N 輪)
2. 不足時從 pool 隨機取樣補足

較大 mode → 更多歷史資料 → 更穩定但可能過時
較小 mode → 較少歷史資料 → 更靈敏但可能過擬合
```

---

## 五、分析輸出格式

### 5.1 CSV 檔案結構

```csv
arrival_rate,bp_L,bp_H,FCFS_percentage,RMLF_percentage,total_rounds
22.00,4.64,32768,15.40,84.60,500
40.00,16.77,64,78.20,21.80,500
```

### 5.2 欄位說明

| 欄位名稱 | 說明 | 範例 |
|----------|------|------|
| arrival_rate | 工作到達率 | 22.00 |
| bp_L | Bounded Pareto 分布的 L 參數 | 4.64 |
| bp_H | Bounded Pareto 分布的 H 參數 | 32768 |
| FCFS_percentage | 選擇 FCFS 的輪次百分比 | 15.40 |
| RMLF_percentage | 選擇 RMLF 的輪次百分比 | 84.60 |
| total_rounds | 總輪次數 | 500 |

### 5.3 輸出目錄結構

```
Analysis/RFDynamic_analysis/
├── avg_30/
│   ├── mode_1/
│   │   └── RFDynamic_avg_30_nJobsPerRound_100_mode_1_round_1.csv
│   ├── mode_2/
│   └── ...
├── Random/
└── Softrandom/
```

---

## 六、效能特性

### 6.1 時間複雜度

| 操作 | 複雜度 | 說明 |
|------|--------|------|
| Phase 1 FCFS | O(n log n) | 初始化階段 |
| RMLF 執行 | O(n log n) | 每輪 |
| 模擬 | O(m log m) | m = 模擬集大小 |
| 工作池取樣 | O(k) | k = 取樣數量 |
| 整體 | O(n^2 log n) | 最壞情況 |

### 6.2 空間複雜度

| 項目 | 複雜度 |
|------|--------|
| 工作池 | O(n) |
| 輪次歷史 | O(n) |
| 模擬資料 | O(m) |

---

## 七、使用範例

### 7.1 命令列執行

```bash
# 使用預設參數
./RFDynamic

# 指定參數
./RFDynamic 100 "1,2,3"
```

### 7.2 程式碼整合

```cpp
#include "RFDynamic.h"

// 簡單呼叫
DynamicRFResult result = RFDynamic(jobs);

// 完整參數
DynamicRFResult result = DYNAMIC_RF(jobs, 100, 3, "path/to/input.csv");
```

---

## 八、實驗觀察

### 8.1 RMLF 選擇傾向

| 場景 | RMLF 選擇率 | 說明 |
|------|-------------|------|
| 高 H 值 (大變異) | 較高 | RMLF 對大工作更公平 |
| 低 H 值 (小變異) | 較低 | FCFS 表現足夠 |
| 高負載 | 較高 | RMLF 的量子機制更有效 |

### 8.2 與透視演算法比較

| 指標 | Dynamic (透視) | RFDynamic (非透視) |
|------|----------------|-------------------|
| 資訊需求 | 需要工作大小 | 不需要 |
| Flow Time | 較優 | 略差 |
| 適用性 | 受限 | 更廣泛 |
| 實現複雜度 | 中等 | 較高 |

---

## 九、RMLF 多層級結構

### 9.1 層級設計

```
Level 0: quantum = 1    ← 新到達工作開始於此
         ↓
Level 1: quantum = 2    ← 用完 Level 0 量子後降級
         ↓
Level 2: quantum = 4
         ↓
Level 3: quantum = 8
         ↓
...
Level k: quantum = 2^k  ← 大工作最終會落到這裡
```

### 9.2 優先順序

```
處理優先順序: Level 0 > Level 1 > Level 2 > ...

同層級內: 隨機選擇 (Randomized)

降級條件: 用完當前層級的 quantum 但未完成
```

---

## 十、參考文獻

1. RMLF (Randomized Multi-Level Feedback) 理論分析
2. 非透視排程演算法競爭比證明
3. 工作池取樣理論

---

## 十一、附錄：關鍵程式碼片段

### A. JobSizePool 類別

```cpp
class JobSizePool {
private:
    std::vector<int> pool;
    std::mt19937 rng;

public:
    void add_job_size(int size) {
        pool.push_back(size);
    }

    std::vector<int> sample_random(int n) {
        std::vector<int> samples;
        std::uniform_int_distribution<size_t> dist(0, pool.size() - 1);

        for (int i = 0; i < n; i++) {
            samples.push_back(pool[dist(rng)]);
        }
        return samples;
    }

    std::vector<int> get_simulation_set(int target_size,
                                        const std::vector<int>& recent) {
        std::vector<int> result;

        // 1. 優先使用 recent completions
        int take = std::min((int)recent.size(), target_size);
        result.insert(result.end(), recent.begin(), recent.begin() + take);

        // 2. 不足時從 pool 隨機補足
        int needed = target_size - result.size();
        if (needed > 0 && !pool.empty()) {
            auto samples = sample_random(needed);
            result.insert(result.end(), samples.begin(), samples.end());
        }

        return result;
    }
};
```

### B. RMLF 模擬

```cpp
inline double simulate_rmlf_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;

    std::vector<Job> sim_jobs;
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j;
        j.arrival_time = 0;
        j.job_size = job_sizes[i];
        j.job_index = i;
        j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }

    return RMLF_algorithm(sim_jobs).l2_norm_flow_time;
}
```

### C. Phase 1 初始化

```cpp
// Phase 1: FCFS for first 100 completions
std::vector<Job> phase1_jobs = jobs;
Fcfs_Optimized(phase1_jobs);

std::vector<std::pair<long long, size_t>> completed_with_time;
for (size_t i = 0; i < phase1_jobs.size(); i++) {
    if (phase1_jobs[i].completion_time > 0) {
        completed_with_time.push_back({
            phase1_jobs[i].completion_time, i
        });
    }
}

std::sort(completed_with_time.begin(), completed_with_time.end());

for (size_t i = 0; i < INITIAL_FCFS_COUNT; i++) {
    Job& job = phase1_jobs[completed_with_time[i].second];
    job_pool.add_job_size(job.job_size);
    completion_count++;
}
```
