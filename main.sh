#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
VENV_PATH="${PROJECT_ROOT}/.venv"
JOB_INIT_SCRIPT="${PROJECT_ROOT}/Job_init.py"
PLOTTER_SCRIPT="${PROJECT_ROOT}/compare_plotter.py"

# Result directories
RESULT_BASE_DIR="${PROJECT_ROOT}"
ALGORITHM_RESULT_DIR="${RESULT_BASE_DIR}/algorithm_result"

# ======== Batch parameters (user-configurable) ========
BATCH_SIZES="${BATCH_SIZES:-25,50,100,200,500}"
K_VALUES="${K_VALUES:-1,2,4,8,16,0}"

# Algorithm executables with CPU allocation
DYNAMIC_BIN="${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic/build/Dynamic"
DYNAMIC_BAL_BIN="${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic_BAL/build/Dynamic_BAL"
RFDYNAMIC_BIN="${PROJECT_ROOT}/Cpp_Optimization/algorithms/RFDynamic/build/RFDynamic"

build_priority_algorithms() {
  local B="$1"
  PRIORITY_ALGORITHMS=(
    "Dynamic:${DYNAMIC_BIN}:0,1,2,3,4,5:MULTITHREAD:${B} ${K_VALUES}"
    "Dynamic_BAL:${DYNAMIC_BAL_BIN}:6,7,8,9,10:MULTITHREAD:${B} ${K_VALUES}"
    "RFDynamic:${RFDYNAMIC_BIN}:11,12,13,14,15:MULTITHREAD:${B} ${K_VALUES}"
  )
  ALGORITHMS=("${PRIORITY_ALGORITHMS[@]}" "${REGULAR_ALGORITHMS[@]}")
}

PRIORITY_ALGORITHMS=(
  "Dynamic:${DYNAMIC_BIN}:0,1,2,3,4,5:MULTITHREAD:"
  "Dynamic_BAL:${DYNAMIC_BAL_BIN}:6,7,8,9,10:MULTITHREAD:"
  "RFDynamic:${RFDYNAMIC_BIN}:11,12,13,14,15:MULTITHREAD:"
)

REGULAR_ALGORITHMS=(
  "BAL:${PROJECT_ROOT}/Cpp_Optimization/algorithms/BAL/build/BAL:0::"
  "SRPT:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SRPT/build/SRPT:1::"
  "FCFS:${PROJECT_ROOT}/Cpp_Optimization/algorithms/FCFS/build/FCFS:2::"
  "RR:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RR/build/RR:3::"
  "SETF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SETF/build/SETF:4::"
  "SJF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SJF/build/SJF:5::"
  "RMLF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RMLF/build/RMLF:6::"
  "MLFQ:${PROJECT_ROOT}/Cpp_Optimization/algorithms/MLFQ/build/MLFQ:7::"
)

ALGORITHMS=("${PRIORITY_ALGORITHMS[@]}" "${REGULAR_ALGORITHMS[@]}")

LOG_DIR="${PROJECT_ROOT}/logs"
UNIT_PREFIX="sched"
STEP_DELAY=5

# =============================================================================
# Utility functions
# =============================================================================

need_tools() {
  command -v systemctl >/dev/null || { echo "systemctl not found"; exit 1; }
  command -v systemd-run >/dev/null || { echo "systemd-run not found"; exit 1; }
}

ensure_env() {
  mkdir -p "$LOG_DIR"
  mkdir -p "$ALGORITHM_RESULT_DIR"

  if [[ ! -d "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it with: python3 -m venv $VENV_PATH"
    exit 1
  fi

  if ! systemctl --user is-system-running >/dev/null 2>&1; then
    echo "Error: The systemd user manager is not running for user '$(whoami)'." >&2
    echo "To fix: sudo loginctl enable-linger $(whoami)" >&2
    exit 1
  fi

  local cores
  cores="$(nproc || echo 1)"
  echo "System has $cores CPU cores available"
  if (( cores < 16 )); then
    echo "Warning: System has only $cores cores, script expects 16"
  fi
}

unit_name_for() { echo "${UNIT_PREFIX}-${1}"; }

check_executable() {
  local cmd="$1" name="$2"
  if [[ ! -f "$cmd" ]]; then
    echo "Warning: ${cmd} not found for ${name}"; return 1
  fi
  if [[ ! -x "$cmd" ]]; then
    echo "Warning: ${cmd} is not executable for ${name}"
    chmod +x "$cmd" 2>/dev/null || { echo "  Failed to fix"; return 1; }
  fi
  return 0
}

get_cmd_info() {
  local search_name="$1"
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    if [[ "${name,,}" == "${search_name,,}" ]]; then
      echo "$item"; return 0
    fi
  done
  return 1
}

# =============================================================================
# Analysis / result folder management
# =============================================================================

move_analysis_folders() {
  echo ""
  echo "=========================================="
  echo "Moving Analysis Folders"
  echo "=========================================="

  local analysis_dest_dir="${PROJECT_ROOT}/Analysis"
  mkdir -p "$analysis_dest_dir"
  local moved_count=0 total_count=0

  for folder_name in Dynamic_analysis Dynamic_BAL_analysis RFDynamic_analysis; do
    if [[ -d "${PROJECT_ROOT}/${folder_name}" ]]; then
      ((total_count++))
      echo -n "Moving ${folder_name}... "
      local dest_path="${analysis_dest_dir}/${folder_name}"
      if [[ -d "$dest_path" ]]; then
        dest_path="${analysis_dest_dir}/${folder_name}_$(date +%Y%m%d_%H%M%S)"
        echo -n "(exists, adding timestamp) "
      fi
      if mv "${PROJECT_ROOT}/${folder_name}" "$dest_path" 2>/dev/null; then
        echo "✓ → ${dest_path}"; ((moved_count++))
      else
        echo "✗ Failed"
      fi
    fi
  done

  echo ""
  if [[ $total_count -eq 0 ]]; then
    echo "Summary: No analysis folders found to move"
  else
    echo "Summary: Moved ${moved_count}/${total_count} analysis folders"
  fi
  return 0
}

move_result_folders() {
  local dest_dir="$1" label="$2" filter="${3:-all}"

  echo ""
  echo "=========================================="
  echo "Moving Result Folders to ${label}"
  echo "=========================================="

  mkdir -p "$dest_dir"
  chmod 755 "$dest_dir" 2>/dev/null || true

  local moved_count=0 total_count=0 failed_folders=()

  while IFS= read -r -d '' result_folder; do
    local folder_name
    folder_name=$(basename "$result_folder")
    [[ "$folder_name" == "algorithm_result" || "$folder_name" == "Analysis" ]] && continue

    if [[ "$filter" == "exclude_dynamic" ]]; then
      [[ "$folder_name" == "Dynamic_result" || "$folder_name" == "Dynamic_BAL_result" ]] && continue
    elif [[ "$filter" == "only_dynamic" ]]; then
      [[ "$folder_name" != "Dynamic_result" && "$folder_name" != "Dynamic_BAL_result" ]] && continue
    fi

    ((total_count++))
    local dest_path="${dest_dir}/${folder_name}"
    echo -n "Moving ${folder_name}... "

    if [[ ! -d "$result_folder" ]]; then
      echo "✗ Source not found"; failed_folders+=("${folder_name}"); continue
    fi
    if [[ -d "$dest_path" ]]; then
      dest_path="${dest_dir}/${folder_name}_$(date +%Y%m%d_%H%M%S)"
      echo -n "(exists, adding timestamp) "
    fi

    if mv "$result_folder" "$dest_path" 2>/dev/null; then
      echo "✓ → ${dest_path}"; ((moved_count++))
    else
      echo "✗ Failed"; failed_folders+=("${folder_name}")
      echo -n "  Attempting copy+remove... "
      if cp -r "$result_folder" "$dest_path" 2>/dev/null && rm -rf "$result_folder" 2>/dev/null; then
        echo "✓"; ((moved_count++))
      else
        echo "✗"
      fi
    fi
  done < <(find "$RESULT_BASE_DIR" -maxdepth 1 -type d \( -name "*result" -o -name "*_result" \) -print0 2>/dev/null)

  echo ""
  if [[ $total_count -eq 0 ]]; then
    echo "Summary: No result folders found to move"
  else
    echo "Summary: Moved ${moved_count}/${total_count} result folders"
    [[ ${#failed_folders[@]} -gt 0 ]] && echo "Failed: ${failed_folders[*]}"
  fi
  return 0
}

verify_result_folders() {
  local folder_pattern="$1" label="$2"
  echo "Verifying ${label} folders..."
  local found=0

  while IFS= read -r -d '' result_folder; do
    local folder_name file_count
    folder_name=$(basename "$result_folder")
    file_count=$(find "$result_folder" -type f 2>/dev/null | wc -l)
    if [[ $file_count -gt 0 ]]; then
      echo "  ✓ ${folder_name}: ${file_count} files"; ((found++))
    else
      echo "  ⚠ ${folder_name}: EMPTY"
    fi
  done < <(find "$RESULT_BASE_DIR" -maxdepth 1 -type d -name "${folder_pattern}" -print0 2>/dev/null)

  if [[ $found -eq 0 ]]; then
    echo "  ✗ No non-empty ${label} folders found!"; return 1
  fi
  echo "  Found $found non-empty folder(s)"
  return 0
}

# =============================================================================
# Systemd process management
# =============================================================================

start_one() {
  local name="$1" cmd="$2" cpu_list="$3" extra="${4:-}" params="${5:-}"
  local unit logf
  unit="$(unit_name_for "$name")"
  logf="${LOG_DIR}/${name}.log"
  mkdir -p "$LOG_DIR"

  if systemctl --user is-active "$unit" >/dev/null 2>&1; then
    local pid
    pid="$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo "?")"
    [[ ! -f "$logf" ]] && { touch "$logf"; echo "[$(date)] Log created for running process" > "$logf"; }
    local actual_cpu
    actual_cpu="$(systemctl --user show -p CPUAffinity --value "$unit" 2>/dev/null || echo "")"

    if [[ "$extra" == "MULTITHREAD" ]]; then
      echo -n "[already running] ${name} (unit=${unit}, PID=${pid})"
      echo " with CPUs: ${actual_cpu:-$cpu_list} (multi-threaded)"
      [[ -n "$params" ]] && echo "                  Parameters: $params"
    else
      echo "[already running] ${name} (unit=${unit}, PID=${pid}) with CPU: ${actual_cpu:-$cpu_list}"
    fi
    echo "                  Log: ${logf}"
    return 0
  fi

  check_executable "$cmd" "$name" || { echo "[failed] Could not start ${name}"; return 1; }

  local systemd_cmd=(
    systemd-run --user --unit="${unit}" --working-directory="$PROJECT_ROOT"
    --collect --property=Restart=no --property=Type=simple
    --property=RemainAfterExit=no --property=CPUAffinity="${cpu_list}"
    --property=OOMPolicy=continue --property=OOMScoreAdjust=-900
    --property=TasksMax=infinity --property=IOSchedulingClass=best-effort
    --property=IOSchedulingPriority=4 --property=Nice=5
    --property=StandardOutput=append:"${logf}"
    --property=StandardError=append:"${logf}"
    --property=KillSignal=SIGTERM --property=TimeoutStopSec=60s
    --property=KillMode=mixed
  )

  if [[ "$extra" == "MULTITHREAD" ]]; then
    echo "[starting] ${name} with CPUs: ${cpu_list} (multi-threaded)"
    [[ -n "$params" ]] && echo "           Parameters: $params"
  else
    echo "[starting] ${name} with CPU: ${cpu_list}"
  fi

  local full_command=("$cmd")
  if [[ -n "$params" ]]; then
    read -ra params_array <<< "$params"
    full_command+=("${params_array[@]}")
  fi

  local stderr_output
  if stderr_output=$("${systemd_cmd[@]}" "${full_command[@]}" 2>&1); then
    sleep 0.5
    local pid
    pid="$(systemctl --user show -p MainPID --value "${unit}" 2>/dev/null || echo "?")"
    echo "[started] ${name} (unit=${unit}, PID=${pid}) → ${logf}"
    return 0
  else
    echo "[failed] Could not start ${name}: ${stderr_output}"
    return 1
  fi
}

update_cpu_affinity() {
  local name="$1" new_cpu_list="$2"
  local unit; unit="$(unit_name_for "$name")"
  if ! systemctl --user is-active "$unit" >/dev/null 2>&1; then return 1; fi
  echo "  Updating $name to use CPUs: $new_cpu_list"
  systemctl --user set-property "$unit" CPUAffinity="$new_cpu_list" 2>/dev/null || {
    echo "  ⚠ Warning: Failed to update CPU affinity for $name"; return 1
  }
}

stop_one() {
  local name="$1"
  local unit; unit="$(unit_name_for "$name")"
  echo -n "Stopping ${name}... "
  if systemctl --user is-active "$unit" >/dev/null 2>&1; then
    systemctl --user stop "$unit" 2>/dev/null && echo "done" || echo "failed"
  else
    echo "not running"
  fi
}

stop_all() {
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name _ _ _ _ <<< "$item"
    stop_one "$name"
  done
}

status_all() {
  echo "Algorithm Status:"
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    local unit; unit="$(unit_name_for "$name")"
    if systemctl --user is-active "$unit" >/dev/null 2>&1; then
      local pid actual_cpu logf
      pid="$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo "?")"
      actual_cpu="$(systemctl --user show -p CPUAffinity --value "$unit" 2>/dev/null || echo "$cpu_list")"
      logf="${LOG_DIR}/${name}.log"
      if [[ "$extra" == "MULTITHREAD" ]]; then
        echo "[active] $name (PID: $pid, CPUs: $actual_cpu, multi-threaded)"
        [[ -n "$params" ]] && echo "         Parameters: $params"
      else
        echo "[active] $name (PID: $pid, CPU: $actual_cpu)"
      fi
      echo "         Log: $logf"
    else
      echo "[stopped] $name"
    fi
  done
}

logs_one() {
  local name="$1" lines="${2:-200}"
  local logf="${LOG_DIR}/${name}.log"
  [[ -f "$logf" ]] && tail -n "$lines" "$logf" || echo "Log not found: $logf"
}

check_all_executables() {
  echo "Checking executables..."
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd _ _ _ <<< "$item"
    [[ -x "$cmd" ]] && echo "✓ $name" || echo "✗ $name (not executable)"
  done
}

# =============================================================================
# Algorithm experiments (§4.1–§4.5)
# =============================================================================

run_job_init() {
  echo "=========================================="
  echo "Step 1: Running Job Initialization"
  echo "=========================================="
  if [[ ! -f "$JOB_INIT_SCRIPT" ]]; then
    echo "Error: Job_init.py not found at $JOB_INIT_SCRIPT"; return 1
  fi
  local logf="${LOG_DIR}/job_init.log"
  echo "Running Job_init.py..."
  echo "Log: $logf"
  if "${VENV_PATH}/bin/python" "$JOB_INIT_SCRIPT" > "$logf" 2>&1; then
    echo "✓ Job initialization completed"; return 0
  else
    echo "✗ Job initialization failed. Check log: $logf"
    tail -n 20 "$logf"; return 1
  fi
}

run_priority_algorithms() {
  echo ""
  echo "=========================================="
  echo "Step 2a: Running PRIORITY Algorithms"
  echo "=========================================="
  echo "  - Dynamic (cores 0-5)"
  echo "  - Dynamic_BAL (cores 6-10)"
  echo "  - RFDynamic (cores 11-15)"
  echo "Batch sizes (B): ${BATCH_SIZES}"
  echo "Lookback values (k): ${K_VALUES}"
  echo "=========================================="

  need_tools

  local total=0 succeeded=0 failed=0 failed_list=() started_units=()
  declare -A algo_names

  for item in "${PRIORITY_ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    ((total++))
    if start_one "$name" "$cmd" "$cpu_list" "$extra" "$params"; then
      ((succeeded++))
      local unit="$(unit_name_for "$name")"
      started_units+=("$unit"); algo_names["$unit"]="$name"
    else
      ((failed++)); failed_list+=("$name")
    fi
  done

  echo ""
  echo "Started: ${succeeded}/${total} priority algorithms"
  if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "Failed to start: ${failed_list[*]}"; return 1
  fi
  [[ ${#started_units[@]} -eq 0 ]] && { echo "✗ No priority algorithms started"; return 1; }

  echo ""
  echo "Waiting for ${#started_units[@]} priority algorithm(s) to complete..."

  local check_interval=10 last_status_time=0 status_interval=60
  local last_running_count=${#started_units[@]}

  while true; do
    local running=0 completed=0 running_units=()
    local current_time; current_time=$(date +%s)

    for unit in "${started_units[@]}"; do
      if systemctl --user is-active "$unit" >/dev/null 2>&1; then
        ((running++)); running_units+=("$unit")
      else
        ((completed++))
      fi
    done

    # Redistribute CPUs when an algorithm completes
    if [[ $running -ne $last_running_count ]] && [[ $running -gt 0 ]]; then
      echo ""
      echo "⚡ Algorithm completed! Redistributing CPUs... (Running: $running, Completed: $completed)"
      if [[ $running -eq 2 ]]; then
        local cpu_sets=("0,1,2,3,4,5,6,7" "8,9,10,11,12,13,14,15")
        local idx=0
        for unit in "${running_units[@]}"; do
          update_cpu_affinity "${algo_names[$unit]}" "${cpu_sets[$idx]}"; ((idx++))
        done
        echo "✓ Each algorithm now uses 8 cores"
      elif [[ $running -eq 1 ]]; then
        for unit in "${running_units[@]}"; do
          update_cpu_affinity "${algo_names[$unit]}" "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"
        done
        echo "✓ Remaining algorithm now uses all 16 cores"
      fi
      last_running_count=$running
    fi

    echo "[$(date +%H:%M:%S)] Priority — Running: $running, Completed: $completed / ${#started_units[@]}"

    if (( current_time - last_status_time >= status_interval )); then
      for unit in "${started_units[@]}"; do
        local name="${algo_names[$unit]}"
        if systemctl --user is-active "$unit" >/dev/null 2>&1; then
          local pid cpu_aff
          pid="$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo "?")"
          cpu_aff="$(systemctl --user show -p CPUAffinity --value "$unit" 2>/dev/null || echo "?")"
          echo "    ✓ $name (PID: $pid, CPUs: $cpu_aff) - Running"
        else
          echo "    ✓ $name - Completed"
        fi
      done
      last_status_time=$current_time
    fi

    [[ $running -eq 0 ]] && { echo ""; echo "✓ All priority algorithms completed!"; break; }
    sleep $check_interval
  done
  return 0
}

run_regular_algorithms() {
  echo ""
  echo "=========================================="
  echo "Step 2b: Running REGULAR Algorithms"
  echo "=========================================="

  need_tools
  local total=0 succeeded=0 failed=0 failed_list=() started_units=()

  for item in "${REGULAR_ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    ((total++))
    if start_one "$name" "$cmd" "$cpu_list" "$extra" "$params"; then
      ((succeeded++)); started_units+=("$(unit_name_for "$name")")
    else
      ((failed++)); failed_list+=("$name")
    fi
  done

  echo ""
  echo "Started: ${succeeded}/${total} regular algorithms"
  [[ ${#failed_list[@]} -gt 0 ]] && echo "Failed: ${failed_list[*]}"
  [[ ${#started_units[@]} -eq 0 ]] && { echo "✗ No regular algorithms started"; return 1; }

  echo "Waiting for ${#started_units[@]} regular algorithm(s) to complete..."
  while true; do
    local running=0 completed=0
    for unit in "${started_units[@]}"; do
      systemctl --user is-active "$unit" >/dev/null 2>&1 && ((running++)) || ((completed++))
    done
    echo "[$(date +%H:%M:%S)] Regular — Running: $running, Completed: $completed / ${#started_units[@]}"
    [[ $running -eq 0 ]] && { echo ""; echo "✓ All regular algorithms completed!"; break; }
    sleep 5
  done
  return 0
}

run_algorithm_pipeline() {
  ensure_env
  local start_time; start_time=$(date +%s)

  echo "========================================"
  echo "Algorithm Experiments (§4.1–§4.5)"
  echo "========================================"
  echo "Start time: $(date)"
  echo "Batch sizes (B): ${BATCH_SIZES}"
  echo "Lookback values (k): ${K_VALUES}"
  echo ""

  # Step 1: Job initialization
  run_job_init || { echo "✗ Pipeline failed at Job Initialization"; return 1; }

  echo ""; sleep $STEP_DELAY

  # Step 2: For each batch size, run priority + regular algorithms
  IFS=',' read -ra BATCH_SIZE_ARRAY <<< "$BATCH_SIZES"
  local batch_count=${#BATCH_SIZE_ARRAY[@]} batch_idx=0

  for B in "${BATCH_SIZE_ARRAY[@]}"; do
    ((batch_idx++)) || true
    echo ""
    echo "########################################################"
    echo "  Batch size B=${B}  (${batch_idx}/${batch_count})"
    echo "  Lookback k=${K_VALUES}"
    echo "########################################################"

    build_priority_algorithms "$B"
    run_priority_algorithms || { echo "✗ Failed at Priority Algorithms (B=${B})"; return 1; }

    echo ""
    sleep 5

    # Baselines only run once (first batch size)
    if [[ $batch_idx -eq 1 ]]; then
      run_regular_algorithms || { echo "✗ Failed at Regular Algorithms"; return 1; }
    else
      echo "(Skipping baselines — already run with first batch size)"
    fi

    sleep $STEP_DELAY
    verify_result_folders "*_result" "algorithm" || echo "⚠ Some result folders empty, continuing..."
    move_result_folders "$ALGORITHM_RESULT_DIR" "Algorithm Results (B=${B})" "all" || return 1

    sleep $STEP_DELAY
    move_analysis_folders || return 1

    echo "✓ Completed batch size B=${B} (${batch_idx}/${batch_count})"
  done

  local end_time duration hours minutes seconds
  end_time=$(date +%s); duration=$((end_time - start_time))
  hours=$((duration / 3600)); minutes=$(((duration % 3600) / 60)); seconds=$((duration % 60))

  echo ""
  echo "========================================"
  echo "✓ Algorithm Experiments Complete"
  echo "========================================"
  printf "Duration: %dh %dm %ds\n" "$hours" "$minutes" "$seconds"
  echo "Results: ${ALGORITHM_RESULT_DIR}/"
  echo "Analysis: ${PROJECT_ROOT}/Analysis/"
}

# =============================================================================
# §4.6 Distribution Shift Experiment
# =============================================================================

run_distribution_shift() {
  local start_time; start_time=$(date +%s)
  local EXP_DIR="Cpp_Optimization/experiments/distribution_shift"
  local BINARY="./${EXP_DIR}/build/DistributionShift"
  local BASE_OUT="./algorithm_result/distribution_shift_result"
  local SEEDS=(1 2 3 4 5 6 7 8 9 10)
  local B=100

  cd "$PROJECT_ROOT"

  echo ""
  echo "============================================================"
  echo " §4.6 Distribution Shift Experiment"
  echo "  Seeds: ${SEEDS[*]}"
  echo "  B=${B}  k=16  eval_window=100"
  echo "============================================================"
  echo ""

  # Generate seed 10 data if missing
  if [ ! -f "./data/distribution_shift_10/shift_H64_H262144.csv" ]; then
    echo ">>> Generating seed 10 data..."
    python -c "
import sys; sys.path.insert(0, '.')
from Job_init import distribution_shift_job_init
import Write_csv, os
os.makedirs('data/distribution_shift_10', exist_ok=True)
samples = distribution_shift_job_init(num_jobs=10000, avg_inter_arrival_time=30)
Write_csv.Write_raw('data/distribution_shift_10/shift_H64_H262144.csv', samples)
print('  Generated distribution_shift_10 data')
"
    echo ""
  fi

  # Build
  echo ">>> Building DistributionShift..."
  cd "${EXP_DIR}"
  mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -1
  make -j"$(nproc)" 2>&1 | tail -1
  cd "$PROJECT_ROOT"
  echo "  Build complete."
  echo ""

  # Run baselines (once per seed, parallel)
  echo ">>> Running baselines for ${#SEEDS[@]} seeds..."
  local pids=()
  for seed in "${SEEDS[@]}"; do
    local DATA="./data/distribution_shift_${seed}/shift_H64_H262144.csv"
    local OUT_DIR="${BASE_OUT}/seed_${seed}/baselines"
    mkdir -p "$OUT_DIR"
    "$BINARY" "$DATA" "$B" baselines "$OUT_DIR" > "${OUT_DIR}/run.log" 2>&1 &
    pids+=($!)
  done
  for pid in "${pids[@]}"; do
    wait "$pid" || { echo "ERROR: baseline process $pid failed"; return 1; }
  done
  echo "  Baselines complete."
  echo ""

  # Run framework algorithms (per seed, parallel)
  echo ">>> Running framework algorithms (${#SEEDS[@]} seeds × B=${B})..."
  pids=()
  for seed in "${SEEDS[@]}"; do
    local DATA="./data/distribution_shift_${seed}/shift_H64_H262144.csv"
    local OUT_DIR="${BASE_OUT}/seed_${seed}/B_${B}"
    mkdir -p "$OUT_DIR"
    "$BINARY" "$DATA" "$B" framework "$OUT_DIR" > "${OUT_DIR}/run.log" 2>&1 &
    pids+=($!)
  done
  for pid in "${pids[@]}"; do
    wait "$pid" || { echo "ERROR: framework process $pid failed"; return 1; }
  done
  echo "  Framework runs complete."
  echo ""

  # Generate plots
  echo ">>> Generating distribution shift plots..."
  python compare_plotter.py --distribution-shift
  echo ""

  local end_time duration hours minutes seconds
  end_time=$(date +%s); duration=$((end_time - start_time))
  hours=$((duration / 3600)); minutes=$(((duration % 3600) / 60)); seconds=$((duration % 60))

  echo "============================================================"
  echo " §4.6 Distribution Shift COMPLETE"
  printf " Duration: %dh %dm %ds\n" "$hours" "$minutes" "$seconds"
  echo " Results: ${BASE_OUT}/"
  echo " Figures: figures/sec4_timevarying/"
  echo "============================================================"
}

# =============================================================================
# Plotting
# =============================================================================

run_plotter() {
  echo ""
  echo "=========================================="
  echo "Generating All Plots"
  echo "=========================================="

  if [[ ! -f "$PLOTTER_SCRIPT" ]]; then
    echo "Error: Plotter script not found at $PLOTTER_SCRIPT"; return 1
  fi

  local logf="${LOG_DIR}/compare_plotter.log"
  echo "Running compare_plotter.py..."
  echo "Log: $logf"

  if python "$PLOTTER_SCRIPT" > "$logf" 2>&1; then
    echo "✓ Plotting completed"
  else
    echo "✗ Plotting failed. Check log: $logf"
    tail -n 20 "$logf"; return 1
  fi
}

# =============================================================================
# Full pipeline
# =============================================================================

run_full_pipeline() {
  local start_time; start_time=$(date +%s)

  echo "================================================================"
  echo " Full Pipeline: Algorithm Experiments + Distribution Shift"
  echo "================================================================"
  echo "Start time: $(date)"
  echo ""

  # Phase 1: Algorithm experiments (§4.1–§4.5)
  run_algorithm_pipeline || { echo "✗ Algorithm pipeline failed"; return 1; }

  echo ""
  sleep $STEP_DELAY

  # Phase 2: Distribution shift (§4.6)
  run_distribution_shift || { echo "✗ Distribution shift failed"; return 1; }

  # Phase 3: Generate all plots
  echo ""
  run_plotter || echo "⚠ Plotting failed (results still available)"

  local end_time duration hours minutes seconds
  end_time=$(date +%s); duration=$((end_time - start_time))
  hours=$((duration / 3600)); minutes=$(((duration % 3600) / 60)); seconds=$((duration % 60))

  echo ""
  echo "================================================================"
  echo "✓ Full Pipeline Complete"
  echo "================================================================"
  printf "Total duration: %dh %dm %ds\n" "$hours" "$minutes" "$seconds"
  echo "Algorithm results: ${ALGORITHM_RESULT_DIR}/"
  echo "Analysis:          ${PROJECT_ROOT}/Analysis/"
  echo "Figures:           ${PROJECT_ROOT}/figures/"
}

# =============================================================================
# CLI
# =============================================================================

usage() {
  cat <<'EOF'
main.sh — Unified Pipeline
===========================

Usage: ./main.sh COMMAND [args...]

Commands:
  run [B] [k]      Full pipeline (algorithms §4.1-4.5 + distribution shift §4.6 + plots)
                     B = batch sizes, comma-separated (default: 25,50,100,200,500)
                     k = lookback values, comma-separated (default: 1,2,4,8,16,0)
  algorithms [B] [k]  Algorithm experiments only (§4.1–§4.5)
  distshift          Distribution shift experiment only (§4.6)
  plot               Generate all plots
  status             Show process status
  stop NAME          Stop specific process
  stop-all           Stop all processes
  logs NAME [lines]  View logs for a process
  check              Check all executables

Examples:
  ./main.sh run                             # Full pipeline, default params
  ./main.sh run 100 8                       # B=100, k=8
  ./main.sh run 25,50,100,200,500 8         # §4.5 Batch Size Sensitivity
  ./main.sh algorithms 100 1,2,4,8,16,0    # §4.4 Lookback Sensitivity
  ./main.sh distshift                       # §4.6 only
  ./main.sh plot                            # Regenerate all figures
  ./main.sh status                          # Check running processes
EOF
}

main() {
  local cmd="${1:-run}"

  case "$cmd" in
    run)
      [[ -n "${2:-}" ]] && BATCH_SIZES="$2"
      [[ -n "${3:-}" ]] && K_VALUES="$3"
      run_full_pipeline
      ;;
    algorithms)
      [[ -n "${2:-}" ]] && BATCH_SIZES="$2"
      [[ -n "${3:-}" ]] && K_VALUES="$3"
      run_algorithm_pipeline
      ;;
    distshift)
      run_distribution_shift
      ;;
    plot)
      run_plotter
      ;;
    stop-all)  stop_all ;;
    stop)      shift; stop_one "$@" ;;
    status)    status_all ;;
    logs)      shift; logs_one "$@" ;;
    check)     check_all_executables ;;
    help|*)    usage ;;
  esac
}

main "$@"
