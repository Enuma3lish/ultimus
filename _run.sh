#!/usr/bin/env bash
set -uo pipefail  # Removed -e to prevent early exit

# ======== Configuration ========
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Commands with CPU allocation
# Dynamic needs 4 CPUs (1 main + 3 worker processes)
# Others are single-threaded
CMDS=(
  "FCFS:${BIN_DIR}/FCFS:0"
  "SRPT:${BIN_DIR}/SRPT:1"
  "Dynamic:${BIN_DIR}/Dynamic:2,3,4,5"  # 4 CPUs for multiprocessing
  "RR:${BIN_DIR}/RR:6"
  "BAL:${BIN_DIR}/BAL:7"
  "SETF:${BIN_DIR}/SETF:8"
  "SJF:${BIN_DIR}/SJF:9"
)

LOG_DIR="${BIN_DIR}/logs"
UNIT_PREFIX="sched"
# ==========================

need_tools() {
  command -v systemctl >/dev/null || { echo "systemctl not found, ensure systemd is installed"; exit 1; }
  command -v systemd-run >/dev/null || { echo "systemd-run not found"; exit 1; }
}

ensure_env() {
  mkdir -p "$LOG_DIR"
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

# Check if executable exists and is executable
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

# Get command info by name
get_cmd_info() {
  local search_name="$1"
  for item in "${CMDS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    if [[ "${name,,}" == "${search_name,,}" ]]; then  # Case-insensitive comparison
      echo "$item"
      return 0
    fi
  done
  return 1
}

# Start single process
start_one() {
  local name="$1" cmd="$2" cpu_list="$3"
  local unit; unit="$(unit_name_for "$name")"
  local logf="${LOG_DIR}/${name}.log"

  # Check if already running
  if systemctl is-active "$unit" >/dev/null 2>&1; then
    echo "[already running] ${name} (unit=${unit})"
    return 0
  fi

  # Check if executable exists and is runnable
  if ! check_executable "$cmd" "$name"; then
    echo "[failed] Could not start ${name} - executable issue"
    return 1
  fi

  # Build systemd-run command
  local systemd_cmd=(
    systemd-run
    --unit="${unit}"
    --same-dir
    --collect
    --property=Restart=on-failure
    --property=RestartSec=5s
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
    --property=Environment=PYTHONUNBUFFERED=1
    --property=Environment=PYTHONHASHSEED=0
  )

  # For Dynamic, set multiprocessing-specific environment
  if [[ "$name" == "Dynamic" ]]; then
    systemd_cmd+=("--property=Environment=OMP_NUM_THREADS=4")
    echo "[starting] ${name} with CPUs: ${cpu_list} (multiprocessing enabled)"
  else
    echo "[starting] ${name} with CPU: ${cpu_list}"
  fi

  # Start the process
  if "${systemd_cmd[@]}" "$cmd" >/dev/null 2>&1; then
    sleep 0.3
    local pid
    pid="$(systemctl show -p MainPID --value "${unit}" 2>/dev/null || echo "?")"
    echo "[started] ${name} (unit=${unit}, PID=${pid}) → ${logf}"
    return 0
  else
    echo "[failed] Could not start ${name} - systemd-run failed"
    return 1
  fi
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

# Start all processes - with error resilience
start_all() {
  need_tools
  ensure_env

  echo "Starting all processes..."
  echo "------------------------"
  
  local total=0
  local succeeded=0
  local failed=0
  local already_running=0
  local failed_list=()
  
  for item in "${CMDS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    ((total++))
    
    if start_one "$name" "$cmd" "$cpu_list"; then
      # Check if it was already running or newly started
      if systemctl is-active "$(unit_name_for "$name")" >/dev/null 2>&1; then
        local output=$(systemctl show -p ActiveEnterTimestamp --value "$(unit_name_for "$name")")
        if [[ -n "$output" ]]; then
          ((succeeded++))
        fi
      fi
    else
      ((failed++))
      failed_list+=("$name")
    fi
  done

  echo ""
  echo "Summary:"
  echo "  Total processes: ${total}"
  echo "  Successfully started: ${succeeded}"
  echo "  Failed to start: ${failed}"
  
  if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "  Failed processes: ${failed_list[*]}"
    echo ""
    echo "To debug failures, check:"
    echo "  1. Executables exist: ls -la ${BIN_DIR}/"
    echo "  2. Executables are runnable: file ${BIN_DIR}/*"
    echo "  3. View logs: $0 logs <process_name>"
  fi
  
  echo ""
  echo "Commands:"
  echo "  $0 status           - Check status of all processes"
  echo "  $0 stop-all         - Stop all processes"
  echo "  $0 stop <names>     - Stop specific processes"
  echo "  $0 logs <name>      - View logs for specific process"
}

# Start multiple processes by name
start_processes() {
  if [[ $# -eq 0 ]]; then
    echo "Error: No process names specified"
    echo "Usage: $0 start <name1> [name2] ..."
    echo "Available processes: FCFS, SRPT, Dynamic, RR, BAL, SETF, SJF"
    return 1
  fi
  
  local succeeded=0
  local failed=0
  local failed_list=()
  
  for proc_name in "$@"; do
    if cmd_info=$(get_cmd_info "$proc_name"); then
      IFS=":" read -r name cmd cpu_list <<< "$cmd_info"
      if start_one "$name" "$cmd" "$cpu_list"; then
        ((succeeded++))
      else
        ((failed++))
        failed_list+=("$name")
      fi
    else
      echo "Error: Unknown process '${proc_name}'"
      echo "Available processes: FCFS, SRPT, Dynamic, RR, BAL, SETF, SJF"
      ((failed++))
      failed_list+=("${proc_name}")
    fi
  done
  
  echo ""
  echo "Summary: Started ${succeeded}, Failed ${failed}"
  if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "Failed: ${failed_list[*]}"
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
  echo "Stopping all processes..."
  echo "------------------------"
  
  local total=0
  local stopped=0
  
  for item in "${CMDS[@]}"; do
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
  echo "Process Status Summary:"
  echo "----------------------"
  
  local running=0
  local stopped=0
  
  for item in "${CMDS[@]}"; do
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
      
      # Format memory display
      if [[ "$mem" != "[not set]" ]] && [[ "$mem" =~ ^[0-9]+$ ]]; then
        mem_mb=$((mem / 1024 / 1024))
        mem_str="Mem: ${mem_mb}MB"
      else
        mem_str=""
      fi
      
      # Special notation for Dynamic (multiprocessing)
      if [[ "$name" == "Dynamic" ]]; then
        cpu_info="CPUs: ${cpu_list} (multiproc)"
      else
        cpu_info="CPU: ${cpu_list}"
      fi
      
      # Executable check
      if [[ ! -x "$cmd" ]]; then
        exec_status=" [!exec]"
      else
        exec_status=""
      fi
      
      printf "[%-8s] %-8s PID: %-6s %-20s %s%s\n" \
        "${act}/${sub}" "$name" "${pid}" "${cpu_info}" "${mem_str}" "${exec_status}"
    else
      ((stopped++))
      # Check if executable exists
      if [[ ! -f "$cmd" ]]; then
        exec_status=" [not found: $cmd]"
      elif [[ ! -x "$cmd" ]]; then
        exec_status=" [not executable: $cmd]"
      else
        exec_status=""
      fi
      printf "[%-8s] %-8s %s\n" "stopped" "$name" "${exec_status}"
    fi
  done
  
  echo ""
  echo "Total: ${running} running, ${stopped} stopped"
}

# Restart specific processes
restart_processes() {
  if [[ $# -eq 0 ]]; then
    # Restart all if no arguments
    echo "Restarting all processes..."
    stop_all
    echo ""
    start_all
  else
    echo "Restarting processes: $*"
    stop_processes "$@"
    echo ""
    start_processes "$@"
  fi
}

logs_one() {
  local name="$1"
  local lines="${2:-200}"
  local logf="${LOG_DIR}/${name}.log"
  
  # Case-insensitive name lookup
  for item in "${CMDS[@]}"; do
    IFS=":" read -r cmd_name cmd cpu_list <<< "$item"
    if [[ "${cmd_name,,}" == "${name,,}" ]]; then
      name="$cmd_name"
      logf="${LOG_DIR}/${cmd_name}.log"
      break
    fi
  done
  
  if [[ -f "$logf" ]]; then
    echo "=== Last ${lines} lines of ${name} log ==="
    tail -n "${lines}" "$logf"
  else
    echo "Log file not found: $logf"
    echo "Note: Logs are created when process starts. If ${name} never started, no log exists."
  fi
}

monitor_all() {
  echo "Monitoring all processes (Ctrl+C to stop)..."
  trap 'echo ""; echo "Monitoring stopped"; return 0' INT
  
  while true; do
    clear
    echo "=== Process Monitor - $(date) ==="
    echo ""
    status_all
    echo ""
    echo "Press Ctrl+C to exit monitoring"
    sleep 5
  done
}

# Debug function to check all executables
check_all_executables() {
  echo "Checking all executables..."
  echo "------------------------"
  
  for item in "${CMDS[@]}"; do
    IFS=":" read -r name cmd cpu_list <<< "$item"
    echo -n "$name: "
    
    if [[ ! -f "$cmd" ]]; then
      echo "NOT FOUND at $cmd"
    elif [[ ! -x "$cmd" ]]; then
      echo "EXISTS but NOT EXECUTABLE at $cmd"
      ls -l "$cmd" | awk '{print "  Permissions: " $1 " Owner: " $3}'
    else
      echo "OK"
      file "$cmd" | sed 's/^/  /'
    fi
  done
}

usage() {
  cat <<EOF
Dynamic Scheduler Management Script
====================================

Usage:
  $0 start-all                    # Start all processes
  $0 start <name1> [name2] ...    # Start specific process(es)
  $0 stop-all                     # Stop all processes
  $0 stop <name1> [name2] ...     # Stop specific process(es)
  $0 restart-all                  # Restart all processes
  $0 restart <name1> [name2] ...  # Restart specific process(es)
  $0 status                       # Show status of all processes
  $0 check                        # Check all executables
  $0 logs <name> [lines]          # View last N lines of logs (default: 200)
  $0 monitor                      # Continuously monitor all processes
  $0 help                         # Show this help message

Available Processes:
  FCFS, SRPT, Dynamic, RR, BAL, SETF, SJF

Examples:
  $0 start-all                    # Start all schedulers
  $0 start Dynamic SRPT           # Start only Dynamic and SRPT
  $0 stop FCFS RR                 # Stop FCFS and RR
  $0 restart Dynamic              # Restart only Dynamic
  $0 logs Dynamic 500             # View last 500 lines of Dynamic logs
  $0 check                        # Verify all executables exist
  $0 monitor                      # Watch real-time status

Process Configuration:
  - FCFS, SRPT, RR, BAL, SETF, SJF: Single-threaded (1 CPU each)
  - Dynamic: Multi-threaded with 3 worker processes (4 CPUs total)

CPU Allocation:
  - CPUs 0-1: FCFS, SRPT
  - CPUs 2-5: Dynamic (multiprocessing)
  - CPUs 6-9: RR, BAL, SETF, SJF

Logs Location: ${LOG_DIR}/

Troubleshooting:
  If processes fail to start:
  1. Check executables exist: $0 check
  2. Make executables runnable: chmod +x ${BIN_DIR}/*
  3. Check logs: $0 logs <process_name>
  4. Check systemd status: systemctl status sched-<process_name>

Notes:
  - Process names are case-insensitive
  - Dynamic uses Python multiprocessing with Pool(processes=3)
  - Each process is managed as a systemd transient service
  - Processes auto-restart on failure (RestartSec=5s)
EOF
}

# Main command dispatcher
case "${1:-}" in
  start-all)
    start_all
    ;;
  start)
    shift || true
    if [[ $# -eq 0 ]]; then
      echo "No processes specified, starting all..."
      start_all
    else
      start_processes "$@"
    fi
    ;;
  stop-all)
    stop_all
    ;;
  stop)
    shift || true
    if [[ $# -eq 0 ]]; then
      echo "No processes specified, stopping all..."
      stop_all
    else
      stop_processes "$@"
    fi
    ;;
  restart-all)
    stop_all
    echo ""
    start_all
    ;;
  restart)
    shift || true
    restart_processes "$@"
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
      echo "Error: Please provide process name"
      echo "Available: FCFS, SRPT, Dynamic, RR, BAL, SETF, SJF"
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