#!/usr/bin/env bash
set -euo pipefail

# ======== 可調整區 ========
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CMDS=(
  "FCFS:${BIN_DIR}/FCFS"
  "SRPT:${BIN_DIR}/SRPT"
  "Dynamic:${BIN_DIR}/Dynamic"
  "RR:${BIN_DIR}/RR"
  "BAL:${BIN_DIR}/BAL"
  "SETF:${BIN_DIR}/SETF"
  "SJF:${BIN_DIR}/SJF"
)

CPU_LIST=(0 1 2 3 4 5 6 )   # 一個行程綁一顆 CPU
LOG_DIR="${BIN_DIR}/logs"  # 也可用 journald，但本腳本依需求輸出到檔案
UNIT_PREFIX="sched"        # transient unit name prefix
# ==========================

need_tools() {
  command -v systemctl >/dev/null || { echo "找不到 systemctl，請確認系統有 systemd"; exit 1; }
  command -v systemd-run >/dev/null || { echo "找不到 systemd-run"; exit 1; }
}

ensure_env() {
  mkdir -p "$LOG_DIR"
  local cores
  cores="$(nproc || echo 1)"
  if (( cores < ${#CPU_LIST[@]} )); then
    echo "警告：CPU 核心數 ($cores) 少於要綁定的 CPU 數 (${#CPU_LIST[@]}). 仍會嘗試執行。"
  fi
}

unit_name_for() {
  local name="$1"
  echo "${UNIT_PREFIX}-${name}"
}

# 啟動單一行程（systemd transient service）
start_one() {
  local name="$1" cpu="$2" cmd="$3"
  local unit; unit="$(unit_name_for "$name")"
  local logf="${LOG_DIR}/${name}.log"

  if [[ ! -x "$cmd" ]]; then
    echo "錯誤：${cmd} 不存在或不可執行（${name}）"
    exit 1
  fi

  # 備註：
  # - 使用 transient "service"（非 --scope），因此可設定 Restart=on-failure、自動重啟。
  # - CPUAffinity 綁定單一 CPU；OOMScoreAdjust 降低 OOM 殺機率；TasksMax 無上限。
  # - StandardOutput/StandardError 直接 append 到檔案，以滿足「每個行程各有 log」需求。
  # - Nice/IOScheduling 些微提高存活性（非必要，但有幫助）。
  systemd-run \
    --unit="${unit}" \
    --same-dir \
    --collect \
    --property=Restart=on-failure \
    --property=RestartSec=5s \
    --property=CPUAffinity="${cpu}" \
    --property=OOMPolicy=continue \
    --property=OOMScoreAdjust=-900 \
    --property=TasksMax=infinity \
    --property=IOSchedulingClass=best-effort \
    --property=IOSchedulingPriority=4 \
    --property=Nice=5 \
    --property=StandardOutput=append:"${logf}" \
    --property=StandardError=append:"${logf}" \
    --property=KillSignal=SIGINT \
    --property=TimeoutStopSec=15s \
    --property=Environment=PYTHONUNBUFFERED=1 \
    --property=Environment=PYTHONHASHSEED=0 \
    "$cmd" >/dev/null

  # 顯示 PID 與 CPU 綁定（MainPID 可能需要幾百毫秒才就緒）
  sleep 0.3
  local pid
  pid="$(systemctl show -p MainPID --value "${unit}" || true)"
  echo "[started][systemd] ${name} (unit=${unit}, PID=${pid:-?}, CPU=${cpu}) → ${logf}"
}

start_all() {
  need_tools
  ensure_env

  if ((${#CMDS[@]} != ${#CPU_LIST[@]})); then
    echo "行程數與 CPU 綁定數不符：${#CMDS[@]} vs ${#CPU_LIST[@]}"
    exit 1
  fi

  for i in "${!CMDS[@]}"; do
    IFS=":" read -r name cmd <<< "${CMDS[$i]}"
    cpu="${CPU_LIST[$i]}"
    start_one "$name" "$cpu" "$cmd"
  done

  echo "全部已送交 systemd（非阻塞）。可用：$0 status"
}

status_all() {
  for item in "${CMDS[@]}"; do
    IFS=":" read -r name cmd <<< "$item"
    unit="$(unit_name_for "$name")"
    if systemctl status "$unit" >/dev/null 2>&1; then
      pid="$(systemctl show -p MainPID --value "$unit")"
      act="$(systemctl is-active "$unit" || true)"
      sub="$(systemctl show -p SubState --value "$unit" || true)"
      echo "[${act}/${sub}] $name  unit=${unit}  PID=${pid}"
    else
      echo "[stopped] $name (unit=${unit})"
    fi
  done
}

stop_all() {
  echo "停止所有單位（優雅停止，逾時會由 systemd 強殺）..."
  for item in "${CMDS[@]}"; do
    IFS=":" read -r name cmd <<< "$item"
    unit="$(unit_name_for "$name")"
    systemctl stop "$unit" 2>/dev/null || true
  done
}

logs_one() {
  local name="$1"
  local logf="${LOG_DIR}/${name}.log"
  if [[ -f "$logf" ]]; then
    tail -n 200 "$logf"
  else
    echo "找不到 log：$logf"
  fi
}

usage() {
  cat <<EOF
用法：
  $0 start           # 以 systemd-run 啟動 7 個 transient services（各綁一顆 CPU），各自寫入 logs/*.log
  $0 status          # 顯示各 unit 狀態（active / failed 等）
  $0 stop            # 停止所有 unit
  $0 logs <NAME>     # 查看某一個程式的最近 200 行 log（NAME 例如 SRPT/FCFS/...）

說明：
- 單位名稱格式：sched-<NAME>（可改 UNIT_PREFIX）。
- 主要屬性：Restart=on-failure、CPUAffinity、OOMScoreAdjust=-900、TasksMax=infinity。
- log 在：${LOG_DIR}。若想用 journal，可把 StandardOutput/StandardError 改成 journal。
- 若可執行檔實際是 Python 腳本，將 CMDS 內對應改成：python3 your_script.py <args>
EOF
}

case "${1:-}" in
  start)  start_all ;;
  status) status_all ;;
  stop)   stop_all ;;
  logs)   shift || true; [[ "${1:-}" ]] || { echo "請提供 NAME，例如 SRPT"; exit 1; }; logs_one "$1" ;;
  *)      usage; exit 1 ;;
esac