#!/usr/bin/env bash
set -euo pipefail

# ======== Configuration ========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/melowu/Desktop/ultimus"
VENV_PATH="${PROJECT_ROOT}/.venv"
JOB_INIT_SCRIPT="${PROJECT_ROOT}/Job_init.py"
PLOTTER_SCRIPT="${PROJECT_ROOT}/_plotter.py"

# Result directories
RESULT_BASE_DIR="${PROJECT_ROOT}"
ALGORITHM_RESULT_DIR="${RESULT_BASE_DIR}/algorithm_result"
HISTORY_RESULT_DIR="${PROJECT_ROOT}/History_result"
RANDOM_SOFTRANDOM_DEST="${PROJECT_ROOT}/random_softrandom_results"

# Algorithm executables with process management
# Format: "NAME:PATH:PARAMETERS"
# Note: macOS doesn't support CPU affinity like Linux, so we manage via process priority

# Priority algorithms (run first)
PRIORITY_ALGORITHMS=(
  "Dynamic:${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic/build/Dynamic:100 1,2,3,4,5,6"
  "Dynamic_BAL:${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic_BAL/build/Dynamic_BAL:100 1,2,3,4,5,6"
  "RFDynamic:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RFDynamic/build/RFDynamic:100 1,2,3,4,5,6"
)

# Regular algorithms (run after priority algorithms complete)
REGULAR_ALGORITHMS=(
  "BAL:${PROJECT_ROOT}/Cpp_Optimization/algorithms/BAL/build/BAL:"
  "SRPT:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SRPT/build/SRPT:"
  "FCFS:${PROJECT_ROOT}/Cpp_Optimization/algorithms/FCFS/build/FCFS:"
  "RR:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RR/build/RR:"
  "SETF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SETF/build/SETF:"
  "SJF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SJF/build/SJF:"
  "RMLF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RMLF/build/RMLF:"
  "MLFQ:${PROJECT_ROOT}/Cpp_Optimization/algorithms/MLFQ/build/MLFQ:"
)

# Combined list for other functions (stop, status, etc.)
ALGORITHMS=("${PRIORITY_ALGORITHMS[@]}" "${REGULAR_ALGORITHMS[@]}")

LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/pids"
STEP_DELAY=5  # 5 seconds between steps
# ==========================

ensure_env() {
  # Create directories first
  mkdir -p "$LOG_DIR"
  mkdir -p "$PID_DIR"
  mkdir -p "$ALGORITHM_RESULT_DIR"
  mkdir -p "$HISTORY_RESULT_DIR"
  mkdir -p "$RANDOM_SOFTRANDOM_DEST"

  # Check Python virtual environment
  if [[ ! -d "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it with: python3 -m venv $VENV_PATH"
    exit 1
  fi

  local cores
  cores="$(sysctl -n hw.ncpu || echo 1)"
  echo "System has $cores CPU cores available"
}

pid_file_for() {
  local name="$1"
  echo "${PID_DIR}/${name}.pid"
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
      echo "  Failed to make executable. Please run: chmod +x ${cmd}"
      return 1
    }
  fi

  return 0
}

get_cmd_info() {
  local search_name="$1"
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd params <<< "$item"
    if [[ "${name,,}" == "${search_name,,}" ]]; then
      echo "$item"
      return 0
    fi
  done
  return 1
}

archive_existing_results() {
  echo ""
  echo "=========================================="
  echo "Checking for Existing Results to Archive"
  echo "=========================================="

  # Check if algorithm_result directory exists and is not empty
  if [[ ! -d "$ALGORITHM_RESULT_DIR" ]]; then
    echo "No algorithm_result directory found. Skipping archive."
    return 0
  fi

  # Count files in algorithm_result (recursively)
  local file_count=$(find "$ALGORITHM_RESULT_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
  
  if [[ $file_count -eq 0 ]]; then
    echo "algorithm_result directory is empty. Skipping archive."
    return 0
  fi

  echo "Found $file_count files in algorithm_result directory"
  echo "Creating archive with timestamp..."

  # Create History_result directory if it doesn't exist
  mkdir -p "$HISTORY_RESULT_DIR"
  chmod 755 "$HISTORY_RESULT_DIR" 2>/dev/null || true

  # Create timestamped archive folder
  local timestamp=$(date +%Y%m%d_%H%M%S)
  local archive_folder="${HISTORY_RESULT_DIR}/algorithm_result_${timestamp}"

  echo "Moving to: ${archive_folder}"

  # Move the entire algorithm_result directory
  if mv "$ALGORITHM_RESULT_DIR" "$archive_folder" 2>/dev/null; then
    echo "✓ Successfully archived existing results"
    echo "  → ${archive_folder}"
    
    # Recreate empty algorithm_result directory for new results
    mkdir -p "$ALGORITHM_RESULT_DIR"
    chmod 755 "$ALGORITHM_RESULT_DIR" 2>/dev/null || true
    echo "✓ Created fresh algorithm_result directory"
    return 0
  else
    echo "✗ Failed to move algorithm_result directory"
    echo "  Attempting copy + remove..."
    
    if cp -r "$ALGORITHM_RESULT_DIR" "$archive_folder" 2>/dev/null; then
      echo "✓ Copied to archive"
      
      # Remove old contents
      rm -rf "${ALGORITHM_RESULT_DIR:?}/"* 2>/dev/null
      echo "✓ Cleaned algorithm_result directory"
      return 0
    else
      echo "✗ Failed to archive existing results"
      echo "⚠ Warning: Proceeding anyway, but old results may be overwritten"
      return 1
    fi
  fi
}

copy_random_softrandom_results() {
  local dest_dir="$1"

  echo ""
  echo "=========================================="
  echo "Copying Random/Softrandom Results"
  echo "=========================================="

  # Ensure destination directory exists with full permissions
  mkdir -p "$dest_dir"
  chmod 755 "$dest_dir" 2>/dev/null || true

  local copied_count=0
  local total_count=0

  # Find all result folders
  while IFS= read -r -d '' result_folder; do
    local folder_name=$(basename "$result_folder")
    
    # Check if folder name contains "random" or "softrandom"
    if [[ "$folder_name" =~ random ]] || [[ "$folder_name" =~ softrandom ]]; then
      ((total_count++))
      local dest_path="${dest_dir}/${folder_name}"

      echo -n "Copying ${folder_name}... "

      # Check if source exists and is accessible
      if [[ ! -d "$result_folder" ]]; then
        echo "✗ Source not found"
        continue
      fi

      # If destination exists, remove it first (replace mode)
      if [[ -d "$dest_path" ]]; then
        echo -n "(replacing existing) "
        rm -rf "$dest_path" 2>/dev/null || {
          echo "✗ Failed to remove existing folder"
          continue
        }
      fi

      # Copy the folder
      if cp -r "$result_folder" "$dest_path" 2>/dev/null; then
        echo "✓ → ${dest_path}"
        ((copied_count++))
      else
        echo "✗ Failed to copy"
      fi
    fi
  done < <(find "$RESULT_BASE_DIR" -maxdepth 1 -type d \( -name "*random*" -o -name "*softrandom*" \) -print0 2>/dev/null)

  echo ""
  if [[ $total_count -eq 0 ]]; then
    echo "Summary: No random/softrandom folders found to copy"
  else
    echo "Summary: Copied ${copied_count}/${total_count} random/softrandom folders"
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
    if [[ "$folder_name" == "algorithm_result" || "$folder_name" == "Analysis" || "$folder_name" == "random_softrandom_results" ]]; then
      continue
    fi
    
    # Apply filter for Dynamic folders
    if [[ "$filter" == "exclude_dynamic" ]]; then
      if [[ "$folder_name" == "Dynamic_result" || "$folder_name" == "Dynamic_BAL_result" || "$folder_name" == "RFDynamic_result" ]]; then
        continue
      fi
    elif [[ "$filter" == "only_dynamic" ]]; then
      if [[ "$folder_name" != "Dynamic_result" && "$folder_name" != "Dynamic_BAL_result" && "$folder_name" != "RFDynamic_result" ]]; then
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

is_process_running() {
  local pid="$1"
  ps -p "$pid" >/dev/null 2>&1
}

start_one() {
  local name="$1" cmd="$2" params="${3:-}"
  local pidfile; pidfile="$(pid_file_for "$name")"
  local logf="${LOG_DIR}/${name}.log"

  # Ensure directories exist
  mkdir -p "$LOG_DIR"
  mkdir -p "$PID_DIR"

  # Check if already running
  if [[ -f "$pidfile" ]]; then
    local old_pid
    old_pid="$(cat "$pidfile")"
    if is_process_running "$old_pid"; then
      echo "[already running] ${name} (PID=${old_pid})"
      if [[ -n "$params" ]]; then
        echo "                  Parameters: $params"
      fi
      echo "                  Log: ${logf}"
      return 0
    else
      # Stale PID file, remove it
      rm -f "$pidfile"
    fi
  fi

  if ! check_executable "$cmd" "$name"; then
    echo "[failed] Could not start ${name} - executable issue"
    return 1
  fi

  echo "[starting] ${name}"
  if [[ -n "$params" ]]; then
    echo "           Parameters: $params"
  fi

  # Build command array
  local full_command=("$cmd")
  if [[ -n "$params" ]]; then
    read -ra params_array <<< "$params"
    full_command+=("${params_array[@]}")
  fi

  # Start process in background with nohup
  nohup "${full_command[@]}" > "$logf" 2>&1 &
  local pid=$!

  # Save PID
  echo "$pid" > "$pidfile"

  # Brief wait to check if process started successfully
  sleep 0.1
  if is_process_running "$pid"; then
    echo "[started] ${name} (PID=${pid}) → ${logf}"
    return 0
  else
    # Process might have completed already - check exit status via log
    # If the process finished quickly, that's actually success
    wait "$pid" 2>/dev/null
    local exit_code=$?
    if [[ $exit_code -eq 0 ]] || [[ ! -s "$logf" ]] || grep -q "completed successfully" "$logf" 2>/dev/null; then
      echo "[completed] ${name} (finished quickly) → ${logf}"
      # Keep PID file temporarily for tracking
      return 0
    else
      echo "[failed] ${name} - check log: ${logf}"
      rm -f "$pidfile"
      return 1
    fi
  fi
}

run_priority_algorithms() {
  echo ""
  echo "=========================================="
  echo "Step 2a: Running PRIORITY Algorithms First"
  echo "=========================================="
  echo "These algorithms will run in parallel:"
  echo "  - Dynamic"
  echo "  - Dynamic_BAL"
  echo "  - RFDynamic"
  echo "Note: macOS doesn't support CPU affinity binding like Linux"
  echo "=========================================="

  local total=0
  local succeeded=0
  local failed=0
  local failed_list=()
  local started_pids=()
  local started_names=()

  for item in "${PRIORITY_ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd params <<< "$item"
    ((total++))

    if start_one "$name" "$cmd" "$params"; then
      ((succeeded++))
      local pidfile; pidfile="$(pid_file_for "$name")"
      local pid; pid="$(cat "$pidfile")"
      started_pids+=("$pid")
      started_names+=("$name")
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

  if [[ ${#started_pids[@]} -eq 0 ]]; then
    echo "✗ No priority algorithms were started successfully"
    return 1
  fi

  echo ""
  echo "Waiting for ${#started_pids[@]} priority algorithm(s) to complete..."
  echo "This may take a long time..."

  local check_interval=10
  local last_status_time=0
  local status_interval=60  # Print detailed status every 60 seconds

  while true; do
    local running=0
    local completed=0
    local current_time=$(date +%s)

    # Count running processes
    for i in "${!started_pids[@]}"; do
      local pid="${started_pids[$i]}"
      if is_process_running "$pid"; then
        ((running++))
      else
        ((completed++))
      fi
    done

    # Print basic status
    echo "[$(date +%H:%M:%S)] Priority Algorithms - Running: $running, Completed: $completed / ${#started_pids[@]}"

    # Print detailed status periodically
    if (( current_time - last_status_time >= status_interval )); then
      echo ""
      echo "  Detailed status:"
      for i in "${!started_pids[@]}"; do
        local pid="${started_pids[$i]}"
        local name="${started_names[$i]}"
        if is_process_running "$pid"; then
          echo "    ✓ $name (PID: $pid) - Still running"
        else
          echo "    ✓ $name - Completed"
          # Clean up PID file
          rm -f "$(pid_file_for "$name")"
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

  local total=0
  local succeeded=0
  local failed=0
  local failed_list=()
  local started_pids=()
  local started_names=()

  for item in "${REGULAR_ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd params <<< "$item"
    ((total++))

    if start_one "$name" "$cmd" "$params"; then
      ((succeeded++))
      local pidfile; pidfile="$(pid_file_for "$name")"
      local pid; pid="$(cat "$pidfile")"
      started_pids+=("$pid")
      started_names+=("$name")
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

  if [[ ${#started_pids[@]} -eq 0 ]]; then
    echo "✗ No regular algorithms were started successfully"
    return 1
  fi

  echo ""
  echo "Waiting for ${#started_pids[@]} regular algorithm(s) to complete..."

  local check_interval=5

  while true; do
    local running=0
    local completed=0

    for i in "${!started_pids[@]}"; do
      local pid="${started_pids[$i]}"
      if is_process_running "$pid"; then
        ((running++))
      else
        ((completed++))
        # Clean up PID file
        local name="${started_names[$i]}"
        rm -f "$(pid_file_for "$name")"
      fi
    done

    echo "[$(date +%H:%M:%S)] Regular Algorithms - Running: $running, Completed: $completed / ${#started_pids[@]}"

    if [[ $running -eq 0 ]]; then
      echo ""
      echo "✓ All regular algorithms completed!"
      break
    fi

    sleep $check_interval
  done

  return 0
}

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
  local pidfile; pidfile="$(pid_file_for "$name")"
  
  echo -n "Stopping ${name}... "
  
  if [[ ! -f "$pidfile" ]]; then
    echo "not running (no PID file)"
    return 0
  fi

  local pid
  pid="$(cat "$pidfile")"

  if ! is_process_running "$pid"; then
    echo "not running (stale PID file)"
    rm -f "$pidfile"
    return 0
  fi

  # Try graceful shutdown first (SIGTERM)
  if kill -TERM "$pid" 2>/dev/null; then
    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while is_process_running "$pid" && [[ $count -lt 10 ]]; do
      sleep 1
      ((count++))
    done

    if ! is_process_running "$pid"; then
      rm -f "$pidfile"
      echo "done (graceful)"
      return 0
    fi

    # Force kill if still running
    echo -n "forcing... "
    if kill -KILL "$pid" 2>/dev/null; then
      sleep 1
      rm -f "$pidfile"
      echo "done (forced)"
      return 0
    fi
  fi

  echo "failed"
  return 1
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
    IFS=":" read -r name _ _ <<< "$item"
    stop_one "$name"
  done
}

status_all() {
  echo "Algorithm Status:"
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd params <<< "$item"
    pidfile="$(pid_file_for "$name")"
    logf="${LOG_DIR}/${name}.log"
    
    if [[ -f "$pidfile" ]]; then
      pid="$(cat "$pidfile")"
      if is_process_running "$pid"; then
        echo "[active] $name (PID: $pid)"
        [[ -n "$params" ]] && echo "         Parameters: $params"
        echo "         Log: $logf"
      else
        echo "[stopped] $name (stale PID file)"
        rm -f "$pidfile"
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
    IFS=":" read -r name cmd _ <<< "$item"
    [[ -x "$cmd" ]] && echo "✓ $name" || echo "✗ $name (not executable)"
  done
}

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
  echo "Starting Full Pipeline (macOS)"
  echo "========================================"
  echo "Start time: $(date)"
  echo ""

  # Step 0: Archive existing results if any
  if ! archive_existing_results; then
    echo "⚠ Warning: Archive step had issues, but continuing..."
  fi

  echo ""
  echo "Waiting ${STEP_DELAY} seconds before job initialization..."
  sleep $STEP_DELAY

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
  echo "Waiting ${STEP_DELAY} seconds before copying random/softrandom results..."
  sleep $STEP_DELAY

  # Step 3: Copy random/softrandom results to specified location
  echo ""
  if ! copy_random_softrandom_results "$RANDOM_SOFTRANDOM_DEST"; then
    echo "⚠ Warning: Failed to copy random/softrandom results, but continuing..."
  fi

  echo ""
  echo "Waiting ${STEP_DELAY} seconds before moving results..."
  sleep $STEP_DELAY

  # Step 4: Verify and move ALL results to algorithm_result
  echo ""
  if ! verify_result_folders "*_result" "algorithm"; then
    echo "⚠ Warning: Some result folders are empty, but continuing..."
  fi
  
  if ! move_result_folders "$ALGORITHM_RESULT_DIR" "Algorithm Results" "all"; then
    echo "✗ Failed to move algorithm results"
    return 1
  fi

  # Step 5: Run plotter (commented out by default)
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
  echo "  - Algorithm runs:         ${ALGORITHM_RESULT_DIR}/"
  echo "  - Random/Softrandom copy: ${RANDOM_SOFTRANDOM_DEST}/"
  echo "  - Archived results:       ${HISTORY_RESULT_DIR}/"
  echo "  - Logs:                   ${LOG_DIR}/"
  
  # Final verification
  echo ""
  echo "Final file counts:"
  local algorithm_count=$(find "$ALGORITHM_RESULT_DIR" -type f 2>/dev/null | wc -l)
  local random_count=$(find "$RANDOM_SOFTRANDOM_DEST" -type f 2>/dev/null | wc -l)
  echo "  - Algorithm results: $algorithm_count files"
  echo "  - Random/Softrandom: $random_count files"
}

usage() {
  cat <<EOF
Pipeline Management Script for macOS
=====================================
Usage: $(basename "$0") {run|stop-all|stop NAME|status|logs NAME [lines]|check|help}

Commands:
  run     - Run full pipeline (waits for all algorithms to complete)
  status  - Show process status
  stop    - Stop processes (stop-all or stop NAME)
  logs    - View logs (logs NAME [lines])
  check   - Check executables

Features:
  - Runs priority algorithms first (Dynamic, Dynamic_BAL, RFDynamic)
  - Then runs regular algorithms in parallel
  - Uses PID files for process management (no systemd on macOS)
  - Copies random/softrandom results to dedicated location
  - Organizes all results in algorithm_result folder

Note: macOS doesn't support CPU affinity like Linux. All processes
      run with normal scheduling priority.

Examples:
  ./$(basename "$0") run              # Run the full pipeline
  ./$(basename "$0") status           # Check algorithm status
  ./$(basename "$0") logs Dynamic 100 # View last 100 lines of Dynamic log
  ./$(basename "$0") stop Dynamic     # Stop the Dynamic algorithm
  ./$(basename "$0") stop-all         # Stop all algorithms
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
