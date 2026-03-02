#!/usr/bin/env python3
"""
Task 1: Gateway & Channel Watchdog
Timeout: 8s, retry: 1
"""
import subprocess
import json
from datetime import datetime
import time

def run_cmd(cmd, timeout=8):
    """执行命令，8秒超时，1次重试"""
    for attempt in range(2):
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:500],
                "stderr": result.stderr[:200],
                "attempt": attempt + 1
            }
        except subprocess.TimeoutExpired:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"success": False, "error": "Timeout", "attempt": attempt + 1}
        except Exception as e:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"success": False, "error": str(e)[:50], "attempt": attempt + 1}
    return {"success": False, "error": "Max retries", "attempt": 2}

def main():
    timestamp = datetime.now().isoformat()
    log_entry = {"timestamp": timestamp, "checks": {}}
    
    # Check 1: Gateway Health
    print("[T1] Checking gateway health...")
    r1 = run_cmd("openclaw gateway health")
    log_entry["checks"]["gateway_health"] = r1
    status1 = "✅" if r1["success"] else "❌"
    print(f"  {status1} Gateway: {r1.get('stdout', r1.get('error', 'FAIL'))[:50]}")
    
    # Check 2: Channels Status
    print("[T1] Checking channels...")
    r2 = run_cmd("openclaw channels status --probe")
    log_entry["checks"]["channels_status"] = r2
    status2 = "✅" if r2["success"] else "❌"
    print(f"  {status2} Channels: {'OK' if r2['success'] else r2.get('error', 'FAIL')}")
    
    # Check 3: Hooks List
    print("[T1] Checking hooks...")
    r3 = run_cmd("openclaw hooks list")
    log_entry["checks"]["hooks_list"] = r3
    status3 = "✅" if r3["success"] else "❌"
    print(f"  {status3} Hooks: {'OK' if r3['success'] else r3.get('error', 'FAIL')}")
    
    # Recovery action if needed
    needs_restart = not (r1["success"] and r2["success"])
    if needs_restart:
        print("[T1] ⚠️ Issues detected, attempting recovery...")
        restart = run_cmd("systemctl restart openclaw-gateway.service", timeout=15)
        log_entry["recovery_action"] = restart
        print(f"  Restart: {'✅' if restart['success'] else '❌'}")
        
        # Re-check after restart
        time.sleep(3)
        recheck = run_cmd("openclaw gateway health")
        log_entry["post_recovery_check"] = recheck
        print(f"  Post-restart: {'✅' if recheck['success'] else '❌'}")
    
    # Write log
    with open("/root/openclaw-workspace/research_hub/ops/watchdog.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    overall = "OK" if all(c["success"] for c in log_entry["checks"].values()) else "NEEDS_ATTENTION"
    print(f"[T1] Completed: {overall}")

if __name__ == "__main__":
    main()
