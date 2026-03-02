#!/bin/bash
# ResearchOps-24x7 Scheduler
# Asia/Shanghai timezone

WORKSPACE="/root/openclaw-workspace/research_hub"
OPS_DIR="$WORKSPACE/ops"
LOCK_FILE="$OPS_DIR/scheduler.lock"
LOG_FILE="$OPS_DIR/scheduler.log"

# 防止重复运行
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date)] Scheduler already running (PID: $PID)" >> "$LOG_FILE"
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== ResearchOps-24x7 Scheduler Started ==="

# 任务执行函数
run_task() {
    local task_name=$1
    local task_cmd=$2
    log "Starting: $task_name"
    
    if eval "$task_cmd" >> "$LOG_FILE" 2>&1; then
        log "Completed: $task_name"
    else
        log "FAILED: $task_name (exit code: $?)"
    fi
}

# 主循环
while true; do
    HOUR=$(date +%H)
    MIN=$(date +%M)
    TIME_VAL="${HOUR}${MIN}"
    
    case $TIME_VAL in
        0005)
            run_task "T1-GatewayWatchdog" "cd $WORKSPACE && python3 ops/task1_gateway_watchdog.py"
            sleep 60
            ;;
        0020)
            run_task "T2-ModelPerfBaseline" "cd $WORKSPACE && python3 ops/task2_model_perf.py"
            sleep 60
            ;;
        0007|0307|0607|0907|1207|1507|1807|2107)
            run_task "T3-LiteratureCollection" "cd $WORKSPACE && python3 ops/task3_literature_collect.py"
            sleep 60
            ;;
        0930)
            run_task "T4-RepoTracking" "cd $WORKSPACE && python3 ops/task4_repo_tracking.py"
            sleep 60
            ;;
        1240)
            run_task "T5-DatasetHealthCheck" "cd $WORKSPACE && python3 ops/task5_dataset_health.py"
            sleep 60
            ;;
        1550)
            run_task "T6-ReproPreCheck" "cd $WORKSPACE && python3 ops/task6_repro_precheck.py"
            sleep 60
            ;;
        1840)
            run_task "T7-DedupAndIndex" "cd $WORKSPACE && python3 ops/task7_dedup_index.py"
            sleep 60
            ;;
        2355)
            run_task "T8-DailyFinalReport" "cd $WORKSPACE && python3 ops/task8_daily_report.py"
            sleep 60
            ;;
    esac
    
    # 每分钟检查一次
    sleep 30
done
