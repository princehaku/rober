# Board Live Full Stack Evidence Tech Plan

## sprint_type: epic

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 最低当前 Objective：O7（约 12%），其次 O6（约 30%）。
- 本 sprint 是否针对最低 Objective：间接针对 O7/O6，直接推进 `OKR.md` 第 5 节最高优先级的现场 O3 验证 lane。
- 理由：O7 的真实地图、历史路线回放、标注和 O6 的真实机器人数据都依赖上游真实路线/传感器材料。SSH 已恢复，本轮应优先产出真实上车 evidence，而不是继续扩展 PC mock surface。

## Vendor 资料来源

- 入口：`docs/vendor/VENDOR_INDEX.md`
- 本轮硬件事实采用：
  - Orange Pi Zero 3：`docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf` 与 `OrangePi-ZERO3_电路图.pdf`（仅在涉及引脚/电压/串口路径时需要进一步打开）。
  - WAVE ROVER：`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`uart_ctrl.h`、`movtion_module.h`、`ugv_rpi/base_ctrl.py`、`ugv_rpi/config.yaml`。
- 本轮默认只做 ROS2/topic/设备观测和低速 smoke，不新增引脚、电压、接线或固件假设。

## 文件范围

主节点只更新 sprint 文档。子 agent 执行阶段默认不改产品代码。

允许写入：

- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/tech-done.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/side2side_check.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/final.md`
- 如需复制/保存本地证据，可写入 `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/`

条件允许改动（仅当既有脚本阻塞证据归档，且必须由 `robot-software-engineer` 单独说明原因）：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/scripts/board_live_route_preflight.sh`
- 对应 tests 与 `docs/navigation/`

## 远端与本地目录约定

- SSH：`root@192.168.1.11 -p 37878`
- 远端 run root：`/root/.ros/trashbot_live_runs`
- 本轮 run id：`field_full_stack_$(date +%Y%m%d_%H%M%S)`
- 本地 sprint artifact root：`sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/`

## 派工

### A. robot-hardware-engineer

目标：确认真实硬件 runtime、设备、串口/底盘安全边界，并在安全 gate 通过时执行低速 motion smoke。

必须先读：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
```

执行要求：

- 不改硬件配置。
- 不改 launch 参数。
- 不直接使用 vendor JSON 指令绕过 ROS2，除非 ROS2 硬件层不可用且只做只读反馈探测。
- 运动 smoke 必须低速、短时、立即 stop。

建议命令：

```bash
ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new -p 37878 root@192.168.1.11 'hostname; date; uname -a; ls -l /dev/tty* /dev/video* 2>/dev/null | head -80'
ssh -p 37878 root@192.168.1.11 'source /opt/ros/humble/setup.bash; for f in /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do [ -f "$f" ] && source "$f"; done; ros2 topic list; ros2 node list || true'
ssh -p 37878 root@192.168.1.11 'source /opt/ros/humble/setup.bash; for f in /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do [ -f "$f" ] && source "$f"; done; timeout 5s ros2 topic echo /battery --once || true; timeout 5s ros2 topic echo /odom --once || true'
```

运动 smoke 仅在现场安全前提满足时执行：

```bash
ssh -p 37878 root@192.168.1.11 'source /opt/ros/humble/setup.bash; for f in /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do [ -f "$f" ] && source "$f"; done; timeout 1s ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.03, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" --rate 2 || true; ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"'
```

### B. robot-algorithm-engineer

目标：雷达、摄像头、SLAM/建图、rosbag 和 route evidence。

执行要求：

- 优先只读 topic smoke。
- 若 topic 不存在，尝试定位 launch/package，不盲目启动长时间进程。
- rosbag 最多 30 秒。
- 若 learn.launch 可安全启动，记录命令和输出；否则写明阻断 gate。

建议命令：

```bash
ssh -p 37878 root@192.168.1.11 'source /opt/ros/humble/setup.bash; for f in /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do [ -f "$f" ] && source "$f"; done; ros2 pkg list | egrep "ros2_trashbot_(bringup|nav|hardware|vision|behavior)" || true; ros2 topic list | sort'
ssh -p 37878 root@192.168.1.11 'source /opt/ros/humble/setup.bash; for f in /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do [ -f "$f" ] && source "$f"; done; timeout 8s ros2 topic hz /scan --window 5 || true; timeout 8s ros2 topic hz /camera/image_raw --window 5 || true; timeout 8s ros2 topic hz /odom --window 5 || true; timeout 5s ros2 topic echo /tf --once || true'
ssh -p 37878 root@192.168.1.11 'RUN_ID=field_full_stack_$(date +%Y%m%d_%H%M%S); OUT=/root/.ros/trashbot_live_runs/$RUN_ID; mkdir -p "$OUT"; source /opt/ros/humble/setup.bash; for f in /ws/install/setup.bash ~/rober/onboard/install/setup.bash ~/apps/rober/onboard/install/setup.bash; do [ -f "$f" ] && source "$f"; done; timeout 30s ros2 bag record -o "$OUT/route_bag" /scan /camera/image_raw /odom /tf /map; find "$OUT" -maxdepth 4 -type f -o -type d | sort'
```

### C. robot-software-engineer

目标：把真实材料归档到本地 sprint artifact，生成 manifest，并更新 tech-done / side2side / final。

执行要求：

- 复用 `field_route_evidence_preflight.py` 和 `field_route_evidence_manifest.py`。
- 如远端产物路径存在，使用 `scp -P 37878 -r` 拉取到本地 sprint artifacts。
- manifest 必须保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`，除非另有完整真实送达证据。

建议命令：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/preflight_ssh.json
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --input sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/<pulled_run_dir> --preflight-json sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/preflight_ssh.json --output sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/field_evidence_manifest.json
python3 -m json.tool sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/field_evidence_manifest.json >/tmp/field_evidence_manifest.pretty.json
git diff --check
```

## 验收命令

各子 agent 必须至少返回：

```bash
git status --short --branch
ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new -p 37878 root@192.168.1.11 'hostname; date; uname -a'
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/preflight_ssh.json
rg -n "雷达|摄像头|建图|运动|/scan|/camera/image_raw|/odom|/tf|map.yaml|route.csv|rosbag|field_evidence_manifest|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" sprints/2026.06.09_23-00_board-live-full-stack-evidence
git diff --check
```

## 成功退出条件

完成必须证明：

- 雷达 gate：通过或明确失败原因。
- 摄像头 gate：通过或明确失败原因。
- 建图 gate：通过或明确失败原因。
- 运动 gate：通过或明确安全/runtime 阻断原因。
- manifest gate：通过或明确 artifact 缺失。

如果本轮只完成 SSH 探针，不算成功。

## 风险

- 真实运动有物理风险；低速 smoke 也必须先确认安全边界。
- ROS graph 可能未启动，传感器 topic 可能不存在；这不是失败终点，而是下一步 bringup 事实。
- `map.yaml` / `route.csv` 可能需要人工驾驶或另开终端；如果本轮不能安全移动，必须留下可复跑命令。
