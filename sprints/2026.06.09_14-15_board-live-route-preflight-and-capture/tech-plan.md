# Board Live Route Preflight and Capture Tech Plan

## 责任 Engineer

主责 owner：`robot-algorithm-engineer`。  
本 sprint 仅为产品侧设计与执行计划：允许的交付范围是 `pre_start.md`、`prd.md`、`tech-plan.md` 三份文档。  
涉及硬件协议/串口细节的技术细节，不在本轮改动作业范围。

## 文件范围

可改动文件：

- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/pre_start.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/prd.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md`

默认不改动：

- 代码、测试、launch、硬件配置、上位机凭证、其他 sprint、`OKR.md`、`docs/product`。

## 接口边界

- SSH 入口必须使用：`ssh root@192.168.1.11 -p 37878`。
- 真实上位机目标环境：优先 `onboard` 上的 ROS2 Humble。  
- 关键 topic：`/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`。
- 关键产物：`map.yaml`、`route.csv`、`fixed route yaml`、keyframe、`rosbag`、replay JSONL。

## 设计原则

- 第一优先级是重试真实上位机执行。  
- 第二优先级是即使失败也要沉淀可复用 runbook，避免再次重入无效状态。  
- 第三优先级是把输出路径标准化到 sprint 级别，便于下次直接复跑和审计。

## 执行方案：两条并行状态流

### A. 正常路径（SSH 可达）

1. 本机前置检查：`git status --short` 确认工作区清爽。  
2. SSH 连接：按给定入口登录上位机。  
3. 上位机环境探测：确认 `ros2`、`setup.bash`、`ros2 pkg` 可用。  
4. 主题探测：输出 `/scan` 等 topic 列表与短周期 `hz`。  
5. 启动采集：带时间戳的 run 目录执行建图+路线录制。  
6. 保存地图与导出路线：执行 save_map 与 route 转换，并做 fixed-route dry-run。  
7. 如有可能补录 rosbag；如无法补录，记录原因（空间/权限/设备不足）。  
8. 记录所有命令输出到 `tech-done`，并输出证据路径。

### B. 失败路径（SSH 不可达/上位机ROS缺失）

1. 不得直接收口 blocked。  
2. 立即使用本地 runbook（见下）完成统一预检与复现记录。  
3. 将失败原因、建议修复动作（网关、AP、路由、防火墙、VPN、端口）写入本 sprint 产物。  
4. 标注 runbook 的下一次复测清单，允许第二次执行同一入口。

## 统一预检与采集 runbook（本 sprint 交付项）

以下文本可直接保存为本地脚本（本 sprint 以文档形式交付）：

```bash
#!/usr/bin/env bash
set -euo pipefail

# === 配置 ===
TARGET_HOST="${TRASHBOT_TARGET_HOST:-192.168.1.11}"
TARGET_PORT="${TRASHBOT_TARGET_PORT:-37878}"
LOCAL_LOG_DIR="${HOME}/.ros/trashbot_live_preflight"
mkdir -p "$LOCAL_LOG_DIR"
RUN_ID="preflight_$(date +%Y%m%d_%H%M%S)"
RUN_LOG="$LOCAL_LOG_DIR/${RUN_ID}.log"

log() { echo "[$(date +%F_%T)] $*" | tee -a "$RUN_LOG"; }
run() { log "$*"; eval "$*" >>"$RUN_LOG" 2>&1; }

log "开始：preflight + capture check"
run "git -C /Users/m1/apps/rober status --short"
run "ping -c 2 192.168.1.1 || true"
run "nc -vz -w 3 \"$TARGET_HOST\" \"$TARGET_PORT\" || true"
run "ssh -p \"$TARGET_PORT\" \"root@$TARGET_HOST\" 'echo preflight_ssh_ok' || true"

log "开始远端最小环境探测"
ssh -p "$TARGET_PORT" "root@$TARGET_HOST" bash -lc '
  set -e
  hostname
  date
  command -v ros2 || true
  echo "==== setup candidates ===="
  for f in /opt/ros/humble/setup.bash /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do
    [ -f "$f" ] && echo "FOUND:$f"
  done
  source /opt/ros/humble/setup.bash
  command -v ros2 || true
  ros2 pkg list | egrep "ros2_trashbot_(bringup|nav|hardware|behavior)" || true
  ros2 topic list | egrep "/scan|/camera/image_raw|/odom|/tf|/map" || true
'

run "ssh -p \"$TARGET_PORT\" \"root@$TARGET_HOST\" \"bash -lc \"
  source /opt/ros/humble/setup.bash
  if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
  ros2 topic list | egrep '/scan|/camera/image_raw|/odom|/tf|/map' || true
\""

log "runbook 完成。详细输出在: $RUN_LOG"
```

> 说明：`ssh` 登录成功后，可在工程执行时在同一命令通道补充后续 `learn.launch.py`、`save_map`、`route_csv_to_yaml`、`fixed_route_autonomy` 与 rosbag 命令；本 sprint 仅交付 runbook 文本，不直接修改实现代码。

## 验收命令

### 必要命令（本轮结束后必须报告）

```bash
git status --short
test -f sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/pre_start.md && test -f sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/prd.md && test -f sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md
rg -n "sprint_type: epic|ssh root@192.168.1.11 -p 37878|OKR 最低优先级核对|验收命令|文件范围|preflight|route.csv|map.yaml|rosbag|replay JSONL" sprints/2026.06.09_14-15_board-live-route-preflight-and-capture
```

### 执行建议（工程复核）

- SSH 成功时按上一段 A 路径继续 `learn.launch.py` 路由采集。  
- SSH/网络失败时按 B 路径完成 runbook 与失败复核。  

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低完成度条目是 **O7（约 12%）**。  
本 sprint 的目标不直接修改 O7 现有软件能力，而是响应 CEO 实际网络/现场条件，优先补齐真实上位机路线证据（O3 现场 lane）。  
理由：  
1. O3 归档模块虽软件侧已基本完成，但现场 map/route/replay 空白阻断了后续 O2 与 O7 的真实执行价值。  
2. O7 的复用价值（PC 路线回放、PC 视觉回看）依赖本轮 route/map 材料。  
3. 因此本 sprint 通过真实证据优先权重进行方向微偏置，属于 O6/O5 健全性之外的现场 unblock。

## 成功标准与边界

成功标准（之一满足）：

- `map.yaml`、`route.csv`、keyframe/replay/rosbag 至少一类成功写出；
- 或记录下详细失败原因 + 可复用 runbook + 下一次执行清单；
- 并在 sprint 文档保留证据路径与证据边界。

边界：

- 本轮不改变上位机系统配置，不承担云端部署与 WAVE ROVER 串口协议变更；
- 未执行命令的场景下不得宣称 delivery success 或任务闭环。

## 风险与对冲

1. 目标主机端口依旧不可达（高概率）：通过 runbook 落地重试路径。  
2. topic 不齐全（可见性不足）：记录缺失清单，优先回退到本地复测而非空收口。  
3. 产物路径无权限：先降级到 `route preflight` 与命令输出归档，不把缺权限误判为整体失败。  
