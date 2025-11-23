#!/usr/bin/env bash
set -euo pipefail

# ======== Configuration ========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/melowu/Work/ultimus"
VENV_PATH="${PROJECT_ROOT}/.venv"
JOB_INIT_SCRIPT="${PROJECT_ROOT}/Job_init.py"
PLOTTER_SCRIPT="${PROJECT_ROOT}/_plotter.py"

# Result directories
RESULT_BASE_DIR="${PROJECT_ROOT}"
ALGORITHM_RESULT_DIR="${RESULT_BASE_DIR}/algorithm_result"

# Algorithm executables with CPU allocation and optional parameters
# Format: "NAME:PATH:CPU_LIST:FLAGS:PARAMETERS"

# Priority algorithms (run first with all 16 cores)
PRIORITY_ALGORITHMS=(
  "Dynamic:${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic/build/Dynamic:0,1,2,3,4,5:MULTITHREAD:100 1,2,3,4,5,6"
  "Dynamic_BAL:${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic_BAL/build/Dynamic_BAL:6,7,8,9,10:MULTITHREAD:100 1,2,3,4,5,6"
  "RFDynamic:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RFDynamic/build/RFDynamic:11,12,13,14,15:MULTITHREAD:100 1,2,3,4,5,6"
)

# Regular algorithms (run after priority algorithms complete)
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

# Combined list for other functions (stop, status, etc.)
ALGORITHMS=("${PRIORITY_ALGORITHMS[@]}" "${REGULAR_ALGORITHMS[@]}")

LOG_DIR="${PROJECT_ROOT}/logs"
UNIT_PREFIX="sched"
STEP_DELAY=5  # 5 seconds between steps
# ==========================

need_tools() {
  command -v systemctl >/dev/null || { echo "systemctl not found, ensure systemd is installed"; exit 1; }
  command -v systemd-run >/dev/null || { echo "systemd-run not found"; exit 1; }
}

ensure_env() {
  # Create directories first
  mkdir -p "$LOG_DIR"
  mkdir -p "$ALGORITHM_RESULT_DIR"

  # Check Python virtual environment
  if [[ ! -d "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it with: python3 -m venv $VENV_PATH"
    exit 1
  fi

  # Check for systemd user instance
  if ! systemctl --user is-system-running >/dev/null 2>&1; then
    echo "Error: The systemd user manager is not running for user '$(whoami)'." >&2
    echo "This is required for running algorithms persistently via 'systemd-run --user'." >&2
    echo "To fix this, enable lingering for your user with the command:" >&2
    echo "    sudo loginctl enable-linger $(whoami)" >&2
    echo "After running this command, you may need to reboot for it to take full effect." >&2
    exit 1
  fi

  local cores
  cores="$(nproc || echo 1)"
  echo "System has $cores CPU cores available"

  if (( cores < 16 )); then
    echo "Warning: System has only $cores cores, but script expects 16"
    echo "Consider reducing the number of concurrent processes"
  fi
}

unit_name_for() {
  local name="$1"
  echo "${UNIT_PREFIX}-${name}"
}

check_executable() {
  local cmd="$1" name="$2"

  if [[ ! -f "$cmd" ]]; then
    echo "Warning: ${cmd} not found for ${name}"
    return 1
  fi

  if [[ ! -x "$cmd" ]]; then
    echo "Warning: ${cmd} is not executable for ${name}"
    echo "  Trying to fix with: chmod +x ${cmd}"
    chmod +x "$cmd" 2>/dev/null || {
      echo "  Failed to make executable. Please run: sudo chmod +x ${cmd}"
      return 1
    }
  fi

  return 0
}

get_cmd_info() {
  local search_name="$1"
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    if [[ "${name,,}" == "${search_name,,}" ]]; then
      echo "$item"
      return 0
    fi
  done
  return 1
}

move_analysis_folders() {
  echo ""
  echo "=========================================="
  echo "Moving Analysis Folders"
  echo "=========================================="
  
  local analysis_dest_dir="${PROJECT_ROOT}/Analysis"
  mkdir -p "$analysis_dest_dir"
  
  local moved_count=0
  local total_count=0
  
  # Move Dynamic_analysis
  if [[ -d "${PROJECT_ROOT}/Dynamic_analysis" ]]; then
    ((total_count++))
    echo -n "Moving Dynamic_analysis... "
    
    local dest_path="${analysis_dest_dir}/Dynamic_analysis"
    
    if [[ -d "$dest_path" ]]; then
      local timestamp=$(date +%Y%m%d_%H%M%S)
      dest_path="${analysis_dest_dir}/Dynamic_analysis_${timestamp}"
      echo -n "(exists, adding timestamp) "
    fi
    
    if mv "${PROJECT_ROOT}/Dynamic_analysis" "$dest_path" 2>/dev/null; then
      echo "✓ → ${dest_path}"
      ((moved_count++))
    else
      echo "✗ Failed"
    fi
  fi
  
  # Move Dynamic_BAL_analysis
  if [[ -d "${PROJECT_ROOT}/Dynamic_BAL_analysis" ]]; then
    ((total_count++))
    echo -n "Moving Dynamic_BAL_analysis... "
    
    local dest_path="${analysis_dest_dir}/Dynamic_BAL_analysis"
    
    if [[ -d "$dest_path" ]]; then
      local timestamp=$(date +%Y%m%d_%H%M%S)
      dest_path="${analysis_dest_dir}/Dynamic_BAL_analysis_${timestamp}"
      echo -n "(exists, adding timestamp) "
    fi
    
    if mv "${PROJECT_ROOT}/Dynamic_BAL_analysis" "$dest_path" 2>/dev/null; then
      echo "✓ → ${dest_path}"
      ((moved_count++))
    else
      echo "✗ Failed"
    fi
  fi
   # Move RFDynamic_analysis
  if [[ -d "${PROJECT_ROOT}/RFDynamic_analysis" ]]; then
    ((total_count++))
    echo -n "Moving RFDynamic_analysis... "
    
    local dest_path="${analysis_dest_dir}/RFDynamic_analysis"
    
    if [[ -d "$dest_path" ]]; then
      local timestamp=$(date +%Y%m%d_%H%M%S)
      dest_path="${analysis_dest_dir}/RFDynamic_analysis_${timestamp}"
      echo -n "(exists, adding timestamp) "
    fi
    
    if mv "${PROJECT_ROOT}/RFDynamic_analysis" "$dest_path" 2>/dev/null; then
      echo "✓ → ${dest_path}"
      ((moved_count++))
    else
      echo "✗ Failed"
    fi
  fi
  
  echo ""
  if [[ $total_count -eq 0 ]]; then
    echo "Summary: No analysis folders found to move"
  else
    echo "Summary: Moved ${moved_count}/${total_count} analysis folders"
  fi
  
  return 0
}

move_result_folders() {
  local dest_dir="$1"
  local label="$2"
  local filter="${3:-all}"  # 'all', 'exclude_dynamic', or 'only_dynamic'

  echo ""
  echo "=========================================="
  echo "Moving Result Folders to ${label}"
  echo "=========================================="

  # Ensure destination directory exists with full permissions
  mkdir -p "$dest_dir"
  chmod 755 "$dest_dir" 2>/dev/null || true

  local moved_count=0
  local total_count=0
  local failed_folders=()

  while IFS= read -r -d '' result_folder; do
    local folder_name=$(basename "$result_folder")
    
    # Skip destination directories
    if [[ "$folder_name" == "algorithm_result" || "$folder_name" == "Analysis" ]]; then
      continue
    fi
    
    # Apply filter for Dynamic folders
    if [[ "$filter" == "exclude_dynamic" ]]; then
      if [[ "$folder_name" == "Dynamic_result" || "$folder_name" == "Dynamic_BAL_result" ]]; then
        continue
      fi
    elif [[ "$filter" == "only_dynamic" ]]; then
      if [[ "$folder_name" != "Dynamic_result" && "$folder_name" != "Dynamic_BAL_result" ]]; then
        continue
      fi
    fi
    
    ((total_count++))
    local dest_path="${dest_dir}/${folder_name}"

    echo -n "Moving ${folder_name}... "

    # Check if source exists and is accessible
    if [[ ! -d "$result_folder" ]]; then
      echo "✗ Source not found"
      failed_folders+=("${folder_name} (not found)")
      continue
    fi

    # If destination exists, add timestamp
    if [[ -d "$dest_path" ]]; then
      local timestamp=$(date +%Y%m%d_%H%M%S)
      dest_path="${dest_dir}/${folder_name}_${timestamp}"
      echo -n "(exists, adding timestamp) "
    fi

    # Try to move with detailed error reporting
    local move_error
    if move_error=$(mv "$result_folder" "$dest_path" 2>&1); then
      echo "✓ → ${dest_path}"
      ((moved_count++))
    else
      echo "✗ Failed: ${move_error}"
      failed_folders+=("${folder_name}")
      
      # Try alternative: copy then remove
      echo -n "  Attempting copy+remove... "
      if cp -r "$result_folder" "$dest_path" 2>/dev/null && rm -rf "$result_folder" 2>/dev/null; then
        echo "✓"
        ((moved_count++))
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
    if [[ ${#failed_folders[@]} -gt 0 ]]; then
      echo "Failed: ${failed_folders[*]}"
    fi
  fi

  return 0
}

run_job_init() {
  echo "=========================================="
  echo "Step 1: Running Job Initialization"
  echo "=========================================="

  if [[ ! -f "$JOB_INIT_SCRIPT" ]]; then
    echo "Error: Job_init.py not found at $JOB_INIT_SCRIPT"
    return 1
  fi

  local logf="${LOG_DIR}/job_init.log"
  echo "Running Job_init.py..."
  echo "Log: $logf"

  if "${VENV_PATH}/bin/python" "$JOB_INIT_SCRIPT" > "$logf" 2>&1; then
    echo "✓ Job initialization completed successfully"
    return 0
  else
    echo "✗ Job initialization failed. Check log: $logf"
    tail -n 20 "$logf"
    return 1
  fi
}

update_cpu_affinity() {
  local name="$1"
  local new_cpu_list="$2"
  local unit; unit="$(unit_name_for "$name")"

  if ! systemctl --user is-active "$unit" >/dev/null 2>&1; then
    return 1
  fi

  echo "  Updating $name to use CPUs: $new_cpu_list"
  if systemctl --user set-property "$unit" CPUAffinity="$new_cpu_list" 2>/dev/null; then
    return 0
  else
    echo "  ⚠ Warning: Failed to update CPU affinity for $name"
    return 1
  fi
}

start_one() {
  local name="$1" cmd="$2" cpu_list="$3" extra="${4:-}" params="${5:-}"
  local unit; unit="$(unit_name_for "$name")"
  local logf="${LOG_DIR}/${name}.log"

  # Ensure log directory exists
  mkdir -p "$LOG_DIR"

  # Check if already running
  if systemctl --user is-active "$unit" >/dev/null 2>&1; then
    local pid
    pid="$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo "?")"

    # Create log file if it doesn't exist
    if [[ ! -f "$logf" ]]; then
      touch "$logf"
      echo "[$(date)] Log file created for already-running process" > "$logf"
    fi

    # Get actual CPU affinity
    local actual_cpu_affinity
    actual_cpu_affinity="$(systemctl --user show -p CPUAffinity --value "$unit" 2>/dev/null || echo "")"

    if [[ "$extra" == "MULTITHREAD" ]]; then
      echo -n "[already running] ${name} (unit=${unit}, PID=${pid})"
      if [[ -n "$actual_cpu_affinity" ]]; then
        echo " with CPUs: ${actual_cpu_affinity} (multi-threaded)"
      else
        echo " with CPUs: ${cpu_list} (multi-threaded)"
      fi
      if [[ -n "$params" ]]; then
        echo "                  Parameters: $params"
      fi
      echo "                  Log: ${logf}"
    else
      echo -n "[already running] ${name} (unit=${unit}, PID=${pid})"
      if [[ -n "$actual_cpu_affinity" ]]; then
        echo " with CPU: ${actual_cpu_affinity}"
      else
        echo " with CPU: ${cpu_list}"
      fi
      echo "                  Log: ${logf}"
    fi
    return 0
  fi

  if ! check_executable "$cmd" "$name"; then
    echo "[failed] Could not start ${name} - executable issue"
    return 1
  fi

  local systemd_cmd=(
    systemd-run
    --user
    --unit="${unit}"
    --working-directory="$PROJECT_ROOT"
    --collect
    --property=Restart=no
    --property=Type=simple
    --property=RemainAfterExit=no
    --property=CPUAffinity="${cpu_list}"
    --property=OOMPolicy=continue
    --property=OOMScoreAdjust=-900
    --property=TasksMax=infinity
    --property=IOSchedulingClass=best-effort
    --property=IOSchedulingPriority=4
    --property=Nice=5
    --property=StandardOutput=append:"${logf}"
    --property=StandardError=append:"${logf}"
    --property=KillSignal=SIGTERM
    --property=TimeoutStopSec=60s
    --property=KillMode=mixed
  )

  if [[ "$extra" == "MULTITHREAD" ]]; then
    echo "[starting] ${name} with CPUs: ${cpu_list} (multi-threaded)"
    if [[ -n "$params" ]]; then
      echo "           Parameters: $params"
    fi
  else
    echo "[starting] ${name} with CPU: ${cpu_list}"
  fi

  local stderr_output
  local full_command=("$cmd")
  if [[ -n "$params" ]]; then
    read -ra params_array <<< "$params"
    full_command+=("${params_array[@]}")
  fi

  if stderr_output=$("${systemd_cmd[@]}" "${full_command[@]}" 2>&1); then
    sleep 0.5
    local pid
    pid="$(systemctl --user show -p MainPID --value "${unit}" 2>/dev/null || echo "?")"
    echo "[started] ${name} (unit=${unit}, PID=${pid}) → ${logf}"
    return 0
  else
    echo "[failed] Could not start ${name}"
    echo "         Error: ${stderr_output}"
    return 1
  fi
}

run_priority_algorithms() {
  echo ""
  echo "=========================================="
  echo "Step 2a: Running PRIORITY Algorithms First"
  echo "=========================================="
  echo "These algorithms use all 16 CPU cores:"
  echo "  - Dynamic (cores 0-5)"
  echo "  - Dynamic_BAL (cores 6-10)"
  echo "  - RFDynamic (cores 11-15)"
  echo "CPU resources will be redistributed as algorithms complete"
  echo "=========================================="

  need_tools

  local total=0
  local succeeded=0
  local failed=0
  local failed_list=()
  local started_units=()

  # Track algorithm names for dynamic CPU reallocation
  declare -A algo_names

  for item in "${PRIORITY_ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    ((total++))

    if start_one "$name" "$cmd" "$cpu_list" "$extra" "$params"; then
      ((succeeded++))
      local unit="$(unit_name_for "$name")"
      started_units+=("$unit")
      algo_names["$unit"]="$name"
    else
      ((failed++))
      failed_list+=("$name")
    fi
  done

  echo ""
  echo "Started: ${succeeded}/${total} priority algorithms"

  if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "Failed to start: ${failed_list[*]}"
    echo "⚠ Warning: Some priority algorithms failed to start"
    return 1
  fi

  if [[ ${#started_units[@]} -eq 0 ]]; then
    echo "✗ No priority algorithms were started successfully"
    return 1
  fi

  echo ""
  echo "Waiting for ${#started_units[@]} priority algorithm(s) to complete..."
  echo "This may take a long time..."

  local check_interval=10
  local last_status_time=0
  local status_interval=60  # Print detailed status every 60 seconds
  local last_running_count=${#started_units[@]}

  while true; do
    local running=0
    local completed=0
    local current_time=$(date +%s)
    local running_units=()

    # Count running units and track which ones are still running
    for unit in "${started_units[@]}"; do
      if systemctl --user is-active "$unit" >/dev/null 2>&1; then
        ((running++))
        running_units+=("$unit")
      else
        ((completed++))
      fi
    done

    # Check if number of running algorithms changed - need to redistribute CPUs
    if [[ $running -ne $last_running_count ]] && [[ $running -gt 0 ]]; then
      echo ""
      echo "=========================================="
      echo "⚡ Algorithm completed! Redistributing CPU resources..."
      echo "Running algorithms: $running, Completed: $completed"
      echo "=========================================="

      # Redistribute CPUs based on number of running algorithms
      if [[ $running -eq 3 ]]; then
        # All 3 running - original allocation
        # Dynamic: 0-5, Dynamic_BAL: 6-10, RFDynamic: 11-15
        :  # Do nothing, already set correctly
      elif [[ $running -eq 2 ]]; then
        # 2 algorithms running - split 16 cores evenly (8 cores each)
        local cpu_sets=("0,1,2,3,4,5,6,7" "8,9,10,11,12,13,14,15")
        local idx=0
        for unit in "${running_units[@]}"; do
          update_cpu_affinity "${algo_names[$unit]}" "${cpu_sets[$idx]}"
          ((idx++))
        done
        echo "✓ Redistributed: Each algorithm now uses 8 cores"
      elif [[ $running -eq 1 ]]; then
        # 1 algorithm running - use all 16 cores
        for unit in "${running_units[@]}"; do
          update_cpu_affinity "${algo_names[$unit]}" "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"
        done
        echo "✓ Redistributed: Remaining algorithm now uses all 16 cores"
      fi
      echo "=========================================="
      echo ""

      last_running_count=$running
    fi

    # Print basic status
    echo "[$(date +%H:%M:%S)] Priority Algorithms - Running: $running, Completed: $completed / ${#started_units[@]}"

    # Print detailed status periodically
    if (( current_time - last_status_time >= status_interval )); then
      echo ""
      echo "  Detailed status:"
      for unit in "${started_units[@]}"; do
        local name="${algo_names[$unit]}"
        if systemctl --user is-active "$unit" >/dev/null 2>&1; then
          local pid="$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo "?")"
          local cpu_affinity="$(systemctl --user show -p CPUAffinity --value "$unit" 2>/dev/null || echo "?")"
          echo "    ✓ $name (PID: $pid, CPUs: $cpu_affinity) - Still running"
        else
          echo "    ✓ $name - Completed"
        fi
      done
      echo ""
      last_status_time=$current_time
    fi

    if [[ $running -eq 0 ]]; then
      echo ""
      echo "✓ All priority algorithms completed!"
      echo ""
      break
    fi

    sleep $check_interval
  done

  return 0
}

run_regular_algorithms() {
  echo ""
  echo "=========================================="
  echo "Step 2b: Running REGULAR Algorithms"
  echo "=========================================="
  echo "Running remaining algorithms in parallel..."
  echo "=========================================="

  need_tools

  local total=0
  local succeeded=0
  local failed=0
  local failed_list=()
  local started_units=()

  for item in "${REGULAR_ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list extra params <<< "$item"
    ((total++))

    if start_one "$name" "$cmd" "$cpu_list" "$extra" "$params"; then
      ((succeeded++))
      started_units+=("$(unit_name_for "$name")")
    else
      ((failed++))
      failed_list+=("$name")
    fi
  done

  echo ""
  echo "Started: ${succeeded}/${total} regular algorithms"

  if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "Failed to start: ${failed_list[*]}"
    echo "⚠ Warning: Some algorithms failed to start"
  fi

  if [[ ${#started_units[@]} -eq 0 ]]; then
    echo "✗ No regular algorithms were started successfully"
    return 1
  fi

  echo ""
  echo "Waiting for ${#started_units[@]} regular algorithm(s) to complete..."

  local check_interval=5

  while true; do
    local running=0
    local completed=0

    for unit in "${started_units[@]}"; do
      if systemctl --user is-active "$unit" >/dev/null 2>&1; then
        ((running++))
      else
        ((completed++))
      fi
    done

    echo "[$(date +%H:%M:%S)] Regular Algorithms - Running: $running, Completed: $completed / ${#started_units[@]}"

    if [[ $running -eq 0 ]]; then
      echo ""
      echo "✓ All regular algorithms completed!"
      break
    fi

    sleep $check_interval
  done

  return 0
}

# Legacy function for backwards compatibility (now runs algorithms in two phases)
run_all_algorithms() {
  # Phase 1: Run priority algorithms first
  if ! run_priority_algorithms; then
    echo "✗ Priority algorithms phase failed"
    return 1
  fi

  echo ""
  echo "=========================================="
  echo "Priority Phase Complete!"
  echo "Starting Regular Algorithms Phase..."
  echo "=========================================="
  echo ""
  sleep 5

  # Phase 2: Run regular algorithms
  if ! run_regular_algorithms; then
    echo "✗ Regular algorithms phase failed"
    return 1
  fi

  return 0
}


run_plotter() {
  echo ""
  echo "=========================================="
  echo "Step 6: Running Comparison Plotter"
  echo "=========================================="

  if [[ ! -f "$PLOTTER_SCRIPT" ]]; then
    echo "Error: Plotter script not found at $PLOTTER_SCRIPT"
    return 1
  fi

  local logf="${LOG_DIR}/_plotter.log"
  echo "Running _plotter.py..."
  echo "Log: $logf"

  if "${VENV_PATH}/bin/python" "$PLOTTER_SCRIPT" > "$logf" 2>&1; then
    echo "✓ Plotting completed successfully"
    return 0
  else
    echo "✗ Plotting failed. Check log: $logf"
    tail -n 20 "$logf"
    return 1
  fi
}
stop_one() {
  local name="$1"
  local unit; unit="$(unit_name_for "$name")"
  echo -n "Stopping ${name}... "
  if systemctl --user is-active "$unit" >/dev/null 2>&1; then
    if systemctl --user stop "$unit" 2>/dev/null; then
      echo "done"
      return 0
    else
      echo "failed"
      return 1
    fi
  else
    echo "not running"
    return 0
  fi
}

stop_processes() {
  if [[ $# -eq 0 ]]; then
    echo "Error: No process names specified"
    return 1
  fi
  for proc_name in "$@"; do
    stop_one "$proc_name"
  done
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
    unit="$(unit_name_for "$name")"
    if systemctl --user is-active "$unit" >/dev/null 2>&1; then
      pid="$(systemctl --user show -p MainPID --value "$unit" 2>/dev/null || echo "?")"
      actual_cpu="$(systemctl --user show -p CPUAffinity --value "$unit" 2>/dev/null || echo "$cpu_list")"
      logf="${LOG_DIR}/${name}.log"
      
      if [[ "$extra" == "MULTITHREAD" ]]; then
        echo "[active] $name (PID: $pid, CPUs: $actual_cpu, multi-threaded)"
        [[ -n "$params" ]] && echo "         Parameters: $params"
        echo "         Log: $logf"
      else
        echo "[active] $name (PID: $pid, CPU: $actual_cpu)"
        echo "         Log: $logf"
      fi
    else
      echo "[stopped] $name"
    fi
  done
}

logs_one() {
  local name="$1"
  local lines="${2:-200}"
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

# Add this function to verify results exist before moving
verify_result_folders() {
  local folder_pattern="$1"
  local label="$2"
  
  echo "Verifying ${label} folders..."
  local found=0
  
  while IFS= read -r -d '' result_folder; do
    local folder_name=$(basename "$result_folder")
    
    # Count files in the folder (recursively)
    local file_count=$(find "$result_folder" -type f 2>/dev/null | wc -l)
    
    if [[ $file_count -gt 0 ]]; then
      echo "  ✓ ${folder_name}: ${file_count} files"
      ((found++))
    else
      echo "  ⚠ ${folder_name}: EMPTY (0 files)"
    fi
  done < <(find "$RESULT_BASE_DIR" -maxdepth 1 -type d -name "${folder_pattern}" -print0 2>/dev/null)
  
  if [[ $found -eq 0 ]]; then
    echo "  ✗ No non-empty ${label} folders found!"
    return 1
  fi
  
  echo "  Found $found non-empty folder(s)"
  return 0
}

run_pipeline() {
  ensure_env

  local start_time=$(date +%s)
  echo "========================================"
  echo "Starting Full Pipeline"
  echo "========================================"
  echo "Start time: $(date)"
  echo ""

  # Step 1: Job initialization
  if ! run_job_init; then
    echo "✗ Pipeline failed at Job Initialization"
    return 1
  fi

  echo ""
  echo "Waiting ${STEP_DELAY} seconds before next step..."
  sleep $STEP_DELAY

  # Step 2: Run all algorithms in parallel
  if ! run_all_algorithms; then
    echo "✗ Pipeline failed at Algorithm Execution"
    return 1
  fi

  echo ""
  echo "Waiting ${STEP_DELAY} seconds before moving results..."
  sleep $STEP_DELAY

  # Step 3: Verify and move ALL results to algorithm_result
  echo ""
  if ! verify_result_folders "*_result" "algorithm"; then
    echo "⚠ Warning: Some result folders are empty, but continuing..."
  fi
  
  if ! move_result_folders "$ALGORITHM_RESULT_DIR" "Algorithm Results" "all"; then
    echo "✗ Failed to move algorithm results"
    return 1
  fi

  echo ""
  echo "Waiting ${STEP_DELAY} seconds before moving analysis..."
  sleep $STEP_DELAY

  # Step 4: Move analysis folders to Analysis directory
  if ! move_analysis_folders; then
    echo "✗ Failed to move analysis folders"
    return 1
  fi

  # # Step 5: Run plotter
  # echo ""
  # echo "Waiting ${STEP_DELAY} seconds before plotting..."
  # sleep $STEP_DELAY
  # if ! run_plotter; then
  #   echo "✗ Pipeline failed at Plotting"
  #   return 1
  # fi

  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  local hours=$((duration / 3600))
  local minutes=$(((duration % 3600) / 60))
  local seconds=$((duration % 60))

  echo ""
  echo "========================================"
  echo "✓ Full Pipeline Completed Successfully"
  echo "========================================"
  echo "End time: $(date)"
  printf "Total duration: %dh %dm %ds\n" "$hours" "$minutes" "$seconds"
  echo ""
  echo "Results organized in:"
  echo "  - Algorithm runs: ${ALGORITHM_RESULT_DIR}/"
  echo "  - Analysis:       ${PROJECT_ROOT}/Analysis/"
  echo "  - Logs:           ${LOG_DIR}/"
  
  # Final verification
  echo ""
  echo "Final file counts:"
  local algorithm_count=$(find "$ALGORITHM_RESULT_DIR" -type f 2>/dev/null | wc -l)
  echo "  - Algorithm results: $algorithm_count files"
}

usage() {
  cat <<'EOF'
Pipeline Management Script
=========================
Usage: $0 {run|stop-all|stop NAME|status|logs NAME [lines]|check|help}

Before first run:
  sudo loginctl enable-linger $(whoami)

Commands:
  run     - Run full pipeline (no timeout - will wait indefinitely)
  status  - Show process status
  stop    - Stop processes
  logs    - View logs
  check   - Check executables
EOF
}

main() {
  case "${1:-help}" in
    run) run_pipeline ;;
    stop-all) stop_all ;;
    stop) shift; stop_processes "$@" ;;
    status) status_all ;;
    logs) shift; logs_one "$@" ;;
    check) check_all_executables ;;
    *) usage ;;
  esac
}

main "$@"