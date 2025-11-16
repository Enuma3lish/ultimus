# Plotter and Column Name Update Summary

## Changes Completed ✅

### 1. Column Name Fixes

**Changed:** `arrival_rate` → `Mean_inter_arrival_time`

**Files Modified:**
- ✅ `/Cpp_Optimization/function_tools/process_avg_folders.h`
- ✅ `_plotter.py`
- ✅ `distribution_based_plotter.py`

**Why:** The column was named "arrival_rate" but actually represents the **mean inter-arrival time** between jobs. The new name is more accurate.

### 2. Combined Plotter Created

**New File:** `plotter.py`

Combines functionality from:
- `_plotter.py` - Original averaging and plotting
- `distribution_based_plotter.py` - Distribution-specific plotting

**New Features:**

#### A. Distribution-Based Grouping

**Bounded Pareto Distributions (L ≤ H):**
- Creates ONE graph per (L, H) parameter pair
- Example: L=4.073, H=262144 gets its own graph
- Title: "Clairvoyant - Bounded Pareto Distribution (L=4.073, H=262144)"

**Normal Distributions (L > H):**
- Groups by std (H value)
- Creates ONE graph per std value
- Title: "Clairvoyant - Result in normal: std=6"
- Example: All Normal(30,6), Normal(60,6), Normal(90,6) on same graph

#### B. Correct Axis Labels

**For avg30/avg60/avg90 cases:**
- X-axis: "Mean Inter-Arrival Time"
- Y-axis: "L2-Norm Flow Time"

**For random/softrandom cases:**
- X-axis: "Coherence Time (CPU Time)"
- Y-axis: "L2-Norm Flow Time"
- Title includes: "Distribution: Mixed Distributions"

### 3. Coherence Time Definition - VERIFIED ✅

**Correct Implementation in Job_init.py:**

```python
# Line 170
if current_time - last_change_time >= coherence_time:
    current_param = random.choice(all_parameters)
    last_change_time = current_time
```

**Definition:**
- Coherence time = **CPU time period** to change dataset
- NOT based on number of jobs generated
- If coherence_time=10000, change happens after 10000 CPU time units

**Example:**
- Current time = 0, using bp_L=4.073
- At CPU time = 10000, might switch to bp_L=6.639
- The switch is based on `current_time`, which accumulates inter-arrival times

### 4. Normal Distribution Detection

**Logic:**
```python
def is_normal_distribution(bp_L, bp_H):
    return bp_L > bp_H
```

**Why:**
- Bounded Pareto: L < H (e.g., L=4.073, H=262144)
- Normal: mean, std where mean > std (e.g., mean=30, std=6)

---

## How to Use

### Step 1: Rebuild C++ Algorithms

The column name change in C++ requires rebuilding:

```bash
cd /Users/melowu/Desktop/ultimus/Cpp_Optimization/algorithms/

# For each algorithm (SRPT, MLFQ, etc.)
cd ALGORITHM_NAME
cd build
cmake ..
make
./ALGORITHM_NAME

# This regenerates result files with "Mean_inter_arrival_time" column
```

### Step 2: Run New Plotter

```bash
cd /Users/melowu/Desktop/ultimus
python3 plotter.py
```

**Output:**
- Plots saved to: `/Users/melowu/Desktop/ultimus/plots_output/`

**Expected Plots:**

For each avg type (avg30, avg60, avg90):
- Multiple Bounded Pareto plots (one per L,H pair)
- Multiple Normal plots (one per std value)
- For both Clairvoyant and Non-Clairvoyant groups

For random/softrandom:
- Clairvoyant comparison
- Non-clairvoyant comparison
- X-axis: Coherence time (log scale)

---

## File Structure

```
/Users/melowu/Desktop/ultimus/
├── plotter.py                          # NEW: Combined plotter
├── _plotter.py                         # OLD: Original (still works)
├── distribution_based_plotter.py       # OLD: Distribution-based (still works)
├── fix_column_names.py                 # Utility script
│
├── plots_output/                       # Output directory
│   ├── bounded_pareto_Clairvoyant_avg30_L_4.073_H_262144.png
│   ├── normal_Clairvoyant_avg30_std_6.png
│   ├── clairvoyant_random_comparison.png
│   └── ...
│
└── Cpp_Optimization/function_tools/
    └── process_avg_folders.h           # MODIFIED: Column name changed
```

---

## Verification Checklist

### Before Running New Plotter

- [x] Column names fixed in C++ code
- [x] Coherence time verified (CPU time-based)
- [x] plotter.py created
- [ ] **TODO:** Rebuild C++ algorithms
- [ ] **TODO:** Verify result files have "Mean_inter_arrival_time" column

### After Rebuilding

Run this to check:

```bash
# Check a sample result file
head -2 /Users/melowu/Desktop/ultimus/algorithm_result/MLFQ_result/avg30_result/20_MLFQ_1_result.csv

# Expected output:
# Mean_inter_arrival_time,bp_parameter_L,bp_parameter_H,MLFQ_L2_norm_flow_time
# 20,4.073000,262144,6542434.551435
```

If it still shows "arrival_rate", you need to rebuild that algorithm.

---

## Distribution Examples

### Example 1: Bounded Pareto

**Parameters:** L=4.073, H=262144

**Graph:**
- Title: "Clairvoyant - Bounded Pareto Distribution (L=4.073, H=262144)"
- X-axis: Mean Inter-Arrival Time (20, 22, 24, ..., 40)
- Y-axis: L2-Norm Flow Time
- Lines: SRPT, SJF, BAL, RR, FCFS, Dynamic

### Example 2: Normal Distribution

**Parameters:** std=6 (H=6)

**Graph:**
- Title: "Clairvoyant - Result in normal: std=6"
- X-axis: Mean Inter-Arrival Time (20, 22, 24, ..., 40)
- Y-axis: L2-Norm Flow Time
- Lines: All algorithms with Normal(mean, 6) parameters

### Example 3: Random/Softrandom

**Graph:**
- Title: "Clairvoyant - Random\nDistribution: Mixed Distributions"
- X-axis: Coherence Time (CPU Time) - logarithmic scale (2^1, 2^2, ..., 2^16)
- Y-axis: L2-Norm Flow Time
- Lines: SRPT, SJF, BAL, RR, FCFS, Dynamic

---

## Advanced Features in plotter.py

### 1. Automatic Mode Selection for Dynamic Algorithms

- **RFDynamic:** Uses mode that wins most frequently in random case
- **Dynamic/Dynamic_BAL:** Uses mode closest to mode 6

### 2. Data Grouping

- Averages across all trial runs (1-10)
- Groups by (Mean_inter_arrival_time, bp_L, bp_H)
- Separate handling for each distribution type

### 3. Plot Styling

- High-contrast colors
- Distinct markers for each algorithm
- Grid for readability
- Bold labels
- Legend with algorithm names (and mode info for Dynamic)

---

## Troubleshooting

### Problem: "KeyError: 'arrival_rate'"

**Solution:** Old result files still use old column name. Rebuild algorithms.

### Problem: "No plots generated"

**Solution:** Check that:
1. Result files exist in `algorithm_result/*/avg30_result/`
2. Files have correct column names
3. At least one algorithm has complete data

### Problem: "Empty plots"

**Solution:**
1. Check log output for which algorithms were loaded
2. Verify CSV files have data
3. Check for NaN values in L2_norm_flow_time column

---

## Next Steps

1. ✅ Column names fixed
2. ✅ plotter.py created
3. ✅ Coherence time verified
4. ⚠️ **REQUIRED:** Rebuild all C++ algorithms
5. ⚠️ **REQUIRED:** Run `python3 plotter.py`
6. ⚠️ **OPTIONAL:** Fix SRPT bug (see SRPT_FIXED.cpp)

---

**Generated:** 2025-11-16
**Status:** READY FOR USE (after rebuilding C++ algorithms)
