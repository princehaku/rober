# Board Live Route Preflight and Capture Sprint Tech Done

## sprint_type: epic

## 自主能力目标和本轮抓手

目标：优先尝试真实上位机 live preflight；若 SSH 不可达，也要交付一键复用的本地 runbook（含命令检查、日志路径、capture 模板）作为下一次可复跑入口。

本轮实际抓手落地为：

- 新增 `onboard/scripts/board_live_route_preflight.sh`，统一做本机预检、网络探测、SSH/ROS2 topic smoke 与 capture 模板输出。
- 更新 `docs/navigation/fixed_route_workflow.md`，将现场上位机预检作为固定工作流入口写入导航文档。
- 将本轮执行结果、失败原因、日志路径与下一步 owner 建到 `side2side_check.md` / `final.md`。

## 改动文件和接口影响

实际改动文件：

- `onboard/scripts/board_live_route_preflight.sh`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-done.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/side2side_check.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/final.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md`（同步验收命令与执行范围）

接口影响：

- 未改 `hardware/WAVE ROVER/UART`、`launch`、`docs/product`、`OKR.md`、`pre_start.md`、`prd.md`。
- 未增加任何底盘运动命令；`collect_capture_commands` 仅输出模板命令，不下发 `ros2` action 或电机相关动作。

## 验收命令结果（关键片段）

### 预检脚本语法与帮助

- `bash -n onboard/scripts/board_live_route_preflight.sh`：通过。
- `bash onboard/scripts/board_live_route_preflight.sh --help`：返回脚本用法和 `--help` 参数说明。
- `bash onboard/scripts/board_live_route_preflight.sh --dry-run --local-only`：返回 0，产生日志，包含 `git status`、网关/ping/nc 检查和 capture 模板记录。

### 网络可达与 blocker

- `ssh -o ConnectTimeout=5 -o BatchMode=yes root@192.168.1.11 -p 37878 'echo board_live_ssh_ok'`：
  - 结果：`No route to host`，退出码 `255`（最新一次复测）  
- `bash onboard/scripts/board_live_route_preflight.sh --skip-capture`：
  - 结果：`preflight` 写入日志并明确失败；最终退出码 `2`
  - 最近一次日志：`/Users/m1/.ros/trashbot_live_preflight/20260609_153658_80389.log`
  - 前序样例日志：`/Users/m1/.ros/trashbot_live_preflight/20260609_153653_80241.log`

### 关键预检日志字段（已确认落地）

- `git status --short`
- `default_gateway=192.168.1.1`
- `ping 192.168.1.11 exit=2`（允许继续）
- `nc 192.168.1.11:37878 exit=1`（允许继续）
- `ssh 192.168.1.11:37878 exit=255`（remote handshake 未达）

## 数据、样本或调试输出变化

- 产物产出：`map.yaml`、`route.csv`、`keyframe`、`replay JSONL`、`rosbag`：本轮全部未产出（SSH 不达）。
- 产出新证据：  
  - `~/.ros/trashbot_live_preflight/20260609_153658_80389.log`（阻塞样例）
  - `~/.ros/trashbot_live_preflight/20260609_153653_80241.log`（dry-run/local-only 样例）
  - `~/.ros/trashbot_live_preflight/20260609_153440_75519.log`（历史复测样例）

## 失败定位

- 首要失败：主机网络链路不可达（`192.168.1.11:37878`）。
- `ping` 与 `nc` 已按要求记录失败，且脚本按设计继续执行 `ssh` 与后续步骤；`ssh` 回退仍失败退出码 255。
- 未触及 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` 的远端 topic smoke 成功路径（因 SSH 不达）。

## 剩余风险与下一步建议

- 风险：若网络/上位机 IP/端口仍未恢复，无法产出 O3 的现场 route/map 证据。
- 建议：恢复上位机网络与端口连通后，执行  
  - `bash onboard/scripts/board_live_route_preflight.sh --skip-capture=false`  
  - 或直接使用日志中输出的 capture 模板进行 `learn.launch.py` + `/trashbot/save_map` + `route_csv_to_yaml` + `fixed_route_autonomy --ros-args ... dry_run:=true` 的真实闭环复测。
