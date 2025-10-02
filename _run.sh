#!/usr/bin/env bash
set -uo pipefail

# ======== Configuration ========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/melowu/Work/ultimus"
VENV_PATH="${PROJECT_ROOT}/.venv"
JOB_INIT_SCRIPT="${PROJECT_ROOT}/Job_init.py"
PLOTTER_SCRIPT="${PROJECT_ROOT}/algorithm_comparison_plotter.py"

# Algorithm executables with CPU allocation
# In run.sh, change this line:
ALGORITHMS=(
  "BAL:${PROJECT_ROOT}/Cpp_Optimization/algorithms/BAL/build/BAL:0"
  "SRPT:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SRPT/build/SRPT:1"
  "Dynamic:${PROJECT_ROOT}/Cpp_Optimization/algorithms/Dynamic/build/Dynamic:2"  
  "FCFS:${PROJECT_ROOT}/Cpp_Optimization/algorithms/FCFS/build/FCFS:3"
  "RR:${PROJECT_ROOT}/Cpp_Optimization/algorithms/RR/build/RR:4"
  "SETF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SETF/build/SETF:5"
  "SJF:${PROJECT_ROOT}/Cpp_Optimization/algorithms/SJF/build/SJF:6"
)

LOG_DIR="${PROJECT_ROOT}/logs"
UNIT_PREFIX="sched"
# ==========================

need_tools() {
  command -v systemctl >/dev/null || { echo "systemctl not found, ensure systemd is installed"; exit 1; }
  command -v systemd-run >/dev/null || { echo "systemd-run not found"; exit 1; }
}

ensure_env() {
  mkdir -p "$LOG_DIR"
  
  # Check Python virtual environment
  if [[ ! -d "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create it with: python3 -m venv $VENV_PATH"
    exit 1
  fi
  
  local cores
  cores="$(nproc || echo 1)"
  echo "System has $cores CPU cores available"
  
  if (( cores < 10 )); then
    echo "Warning: System has only $cores cores, but script expects 10"
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
    IFS=":" read -r name cmd cpu_list <<< "$item"
    if [[ "${name,,}" == "${search_name,,}" ]]; then
      echo "$item"
      return 0
    fi
  done
  return 1
}

# Run Job_init.py in virtual environment
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

# Start single algorithm process
start_one() {
  local name="$1" cmd="$2" cpu_list="$3"
  local unit; unit="$(unit_name_for "$name")"
  local logf="${LOG_DIR}/${name}.log"

  if systemctl is-active "$unit" >/dev/null 2>&1; then
    echo "[already running] ${name} (unit=${unit})"
    return 0
  fi

  if ! check_executable "$cmd" "$name"; then
    echo "[failed] Could not start ${name} - executable issue"
    return 1
  fi

  local systemd_cmd=(
    systemd-run
    --unit="${unit}"
    --same-dir
    --collect
    --property=Restart=no
    --property=CPUAffinity="${cpu_list}"
    --property=OOMPolicy=continue
    --property=OOMScoreAdjust=-900
    --property=TasksMax=infinity
    --property=IOSchedulingClass=best-effort
    --property=IOSchedulingPriority=4
    --property=Nice=5
    --property=StandardOutput=append:"${logf}"
    --property=StandardError=append:"${logf}"
    --property=KillSignal=SIGINT
    --property=TimeoutStopSec=30s
  )

  echo "[starting] ${name} with CPU: ${cpu_list}"

  if "${systemd_cmd[@]}" "$cmd" >/dev/null 2>&1; then
    sleep 0.3
    local pid
    pid="$(systemctl show -p MainPID --value "${unit}" 2>/dev/null || echo "?")"
    echo "[started] ${name} (unit=${unit}, PID=${pid}) → ${logf}"
    return 0
  else
    echo "[failed] Could not start ${name}"
    return 1
  fi
}

# Run all algorithms in parallel
run_all_algorithms() {
  echo ""
  echo "=========================================="
  echo "Step 2: Running All Algorithms in Parallel"
  echo "=========================================="
  
  need_tools
  
  local total=0
  local succeeded=0
  local failed=0
  local failed_list=()
  
  # Start all algorithms
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    ((total++))
    
    if start_one "$name" "$cmd" "$cpu_list"; then
      ((succeeded++))
    else
      ((failed++))
      failed_list+=("$name")
    fi
  done

  echo ""
  echo "Started: ${succeeded}/${total} algorithms"
  
  if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "Failed to start: ${failed_list[*]}"
    return 1
  fi
  
  # Wait for all algorithms to complete
  echo ""
  echo "Waiting for all algorithms to complete..."
  local all_units=()
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    all_units+=("$(unit_name_for "$name")")
  done
  
  local check_interval=5
  local max_wait=7200  # 2 hours max
  local elapsed=0
  
  while true; do
    local running=0
    local completed=0
    
    for unit in "${all_units[@]}"; do
      if systemctl is-active "$unit" >/dev/null 2>&1; then
        ((running++))
      else
        ((completed++))
      fi
    done
    
    echo "[$(date +%H:%M:%S)] Running: $running, Completed: $completed / $total"
    
    if [[ $running -eq 0 ]]; then
      echo "✓ All algorithms completed"
      break
    fi
    
    if [[ $elapsed -ge $max_wait ]]; then
      echo "✗ Timeout: Some algorithms still running after ${max_wait}s"
      return 1
    fi
    
    sleep $check_interval
    ((elapsed += check_interval))
  done
  
  return 0
}

# Run plotter in virtual environment
run_plotter() {
  echo ""
  echo "=========================================="
  echo "Step 3: Running Comparison Plotter"
  echo "=========================================="
  
  if [[ ! -f "$PLOTTER_SCRIPT" ]]; then
    echo "Error: Plotter script not found at $PLOTTER_SCRIPT"
    return 1
  fi
  
  local logf="${LOG_DIR}/plotter.log"
  echo "Running algorithm_comparison_plotter.py..."
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

# Full pipeline execution
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
    echo ""
    echo "✗ Pipeline failed at Job Initialization"
    return 1
  fi
  
  # Step 2: Run all algorithms in parallel
  if ! run_all_algorithms; then
    echo ""
    echo "✗ Pipeline failed at Algorithm Execution"
    return 1
  fi
  
  # Step 3: Run plotter
  if ! run_plotter; then
    echo ""
    echo "✗ Pipeline failed at Plotting"
    return 1
  fi
  
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  local minutes=$((duration / 60))
  local seconds=$((duration % 60))
  
  echo ""
  echo "========================================"
  echo "✓ Full Pipeline Completed Successfully"
  echo "========================================"
  echo "End time: $(date)"
  echo "Total duration: ${minutes}m ${seconds}s"
  echo ""
  echo "Check logs at: $LOG_DIR/"
}

# Stop single process
stop_one() {
  local name="$1"
  local unit; unit="$(unit_name_for "$name")"
  
  echo -n "Stopping ${name}... "
  if systemctl is-active "$unit" >/dev/null 2>&1; then
    if systemctl stop "$unit" 2>/dev/null; then
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

# Stop multiple processes by name
stop_processes() {
  if [[ $# -eq 0 ]]; then
    echo "Error: No process names specified"
    echo "Usage: $0 stop <name1> [name2] ..."
    return 1
  fi
  
  local stopped=0
  local failed=0
  
  for proc_name in "$@"; do
    if cmd_info=$(get_cmd_info "$proc_name"); then
      IFS=":" read -r name cmd cpu_list <<< "$cmd_info"
      if stop_one "$name"; then
        ((stopped++))
      else
        ((failed++))
      fi
    else
      echo "Error: Unknown process '${proc_name}'"
      ((failed++))
    fi
  done
  
  echo ""
  echo "Summary: Stopped ${stopped}, Failed ${failed}"
}

stop_all() {
  echo "Stopping all algorithms..."
  echo "------------------------"
  
  local total=0
  local stopped=0
  
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    ((total++))
    if stop_one "$name"; then
      ((stopped++))
    fi
  done
  
  echo ""
  echo "Summary: Stopped ${stopped} out of ${total} processes"
}

status_all() {
  echo "Algorithm Status Summary:"
  echo "----------------------"
  
  local running=0
  local stopped=0
  
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    unit="$(unit_name_for "$name")"
    
    if systemctl status "$unit" >/dev/null 2>&1; then
      pid="$(systemctl show -p MainPID --value "$unit" 2>/dev/null || echo "?")"
      act="$(systemctl is-active "$unit" 2>/dev/null || echo "unknown")"
      
      if [[ "$act" == "active" ]]; then
        ((running++))
      else
        ((stopped++))
      fi
      
      sub="$(systemctl show -p SubState --value "$unit" 2>/dev/null || echo "unknown")"
      mem="$(systemctl show -p MemoryCurrent --value "$unit" 2>/dev/null || echo "[not set]")"
      
      if [[ "$mem" != "[not set]" ]] && [[ "$mem" =~ ^[0-9]+$ ]]; then
        mem_mb=$((mem / 1024 / 1024))
        mem_str="Mem: ${mem_mb}MB"
      else
        mem_str=""
      fi
      
      if [[ "$name" == "Dynamic" ]]; then
        cpu_info="CPUs: ${cpu_list} (multiproc)"
      else
        cpu_info="CPU: ${cpu_list}"
      fi
      
      if [[ ! -x "$cmd" ]]; then
        exec_status=" [!exec]"
      else
        exec_status=""
      fi
      
      printf "[%-8s] %-8s PID: %-6s %-20s %s%s\n" \
        "${act}/${sub}" "$name" "${pid}" "${cpu_info}" "${mem_str}" "${exec_status}"
    else
      ((stopped++))
      if [[ ! -f "$cmd" ]]; then
        exec_status=" [not found]"
      elif [[ ! -x "$cmd" ]]; then
        exec_status=" [not executable]"
      else
        exec_status=""
      fi
      printf "[%-8s] %-8s %s\n" "stopped" "$name" "${exec_status}"
    fi
  done
  
  echo ""
  echo "Total: ${running} running, ${stopped} stopped"
}

logs_one() {
  local name="$1"
  local lines="${2:-200}"
  
  # Special handling for job_init and plotter
  if [[ "${name,,}" == "job_init" ]]; then
    local logf="${LOG_DIR}/job_init.log"
  elif [[ "${name,,}" == "plotter" ]]; then
    local logf="${LOG_DIR}/plotter.log"
  else
    # Find algorithm name (case-insensitive)
    for item in "${ALGORITHMS[@]}"; do
      IFS=":" read -r cmd_name cmd cpu_list <<< "$item"
      if [[ "${cmd_name,,}" == "${name,,}" ]]; then
        name="$cmd_name"
        break
      fi
    done
    local logf="${LOG_DIR}/${name}.log"
  fi
  
  if [[ -f "$logf" ]]; then
    echo "=== Last ${lines} lines of ${name} log ==="
    tail -n "${lines}" "$logf"
  else
    echo "Log file not found: $logf"
  fi
}

monitor_all() {
  echo "Monitoring all processes (Ctrl+C to stop)..."
  trap 'echo ""; echo "Monitoring stopped"; return 0' INT
  
  while true; do
    clear
    echo "=== Algorithm Monitor - $(date) ==="
    echo ""
    status_all
    echo ""
    echo "Press Ctrl+C to exit monitoring"
    sleep 5
  done
}

check_all_executables() {
  echo "Checking all executables..."
  echo "------------------------"
  
  echo "Python Scripts:"
  for script in "$JOB_INIT_SCRIPT" "$PLOTTER_SCRIPT"; do
    local name=$(basename "$script")
    echo -n "  $name: "
    if [[ ! -f "$script" ]]; then
      echo "NOT FOUND at $script"
    else
      echo "OK"
    fi
  done
  
  echo ""
  echo "C++ Algorithms:"
  for item in "${ALGORITHMS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    echo -n "  $name: "
    
    if [[ ! -f "$cmd" ]]; then
      echo "NOT FOUND at $cmd"
    elif [[ ! -x "$cmd" ]]; then
      echo "EXISTS but NOT EXECUTABLE"
      ls -l "$cmd" | awk '{print "    Permissions: " $1 " Owner: " $3}'
    else
      echo "OK"
    fi
  done
}

usage() {
  cat <<EOF
Algorithm Pipeline Management Script
====================================

Usage:
  $0 run                          # Run full pipeline (init → algorithms → plot)
  $0 stop-all                     # Stop all running algorithms
  $0 stop <name1> [name2] ...     # Stop specific algorithm(s)
  $0 status                       # Show status of all algorithms
  $0 check                        # Check all executables and scripts
  $0 logs <name> [lines]          # View logs (default: 200 lines)
  $0 monitor                      # Continuously monitor all algorithms
  $0 help                         # Show this help message

Pipeline Steps:
  1. Job Initialization    → Runs Job_init.py in .venv
  2. Algorithm Execution   → Runs 7 algorithms in parallel
  3. Results Plotting      → Runs algorithm_comparison_plotter.py in .venv

Available Algorithms:
  BAL, SRPT, Dynamic, FCFS, RR, SETF, SJF

Log Names:
  job_init, plotter, BAL, SRPT, Dynamic, FCFS, RR, SETF, SJF

Examples:
  $0 run                          # Execute full pipeline
  $0 status                       # Check what's running
  $0 stop Dynamic SRPT            # Stop specific algorithms
  $0 logs Dynamic 500             # View last 500 lines
  $0 logs job_init                # View initialization logs
  $0 logs plotter                 # View plotting logs
  $0 check                        # Verify all files exist
  $0 monitor                      # Real-time monitoring

CPU Allocation:
  - CPUs 0-1: BAL, SRPT
  - CPUs 2-5: Dynamic (multiprocessing with 4 CPUs)
  - CPUs 6-9: FCFS, RR, SETF, SJF

Logs Location: ${LOG_DIR}/

Troubleshooting:
  1. Check all files: $0 check
  2. Make executables: chmod +x ${PROJECT_ROOT}/Cpp_Optimization/algorithms/*/build/*
  3. View logs: $0 logs <name>
  4. Check systemd: systemctl status sched-<name>

Notes:
  - Virtual environment required at ${VENV_PATH}
  - All algorithms run in parallel on separate CPUs
  - Pipeline waits for all algorithms to complete before plotting
  - Maximum wait time: 2 hours per pipeline
EOF
}

# Main command dispatcher
case "${1:-}" in
  run|pipeline)
    run_pipeline
    ;;
  stop-all)
    stop_all
    ;;
  stop)
    shift || true
    stop_processes "$@"
    ;;
  status)
    status_all
    ;;
  check)
    check_all_executables
    ;;
  logs)
    shift || true
    if [[ -z "${1:-}" ]]; then
      echo "Error: Please provide log name"
      echo "Available: job_init, plotter, BAL, SRPT, Dynamic, FCFS, RR, SETF, SJF"
      exit 1
    fi
    logs_one "$1" "${2:-200}"
    ;;
  monitor)
    monitor_all
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac