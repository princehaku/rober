# Board Live Route Preflight and Capture Tech Plan

## 责任 Engineer

主责 owner：`robot-algorithm-engineer`（本轮闭环主责）。
本 plan 为可执行计划：本轮目标是把现场 lane 从“阻塞记录”转为“可复用执行入口 + 可复盘证据”。

## 文件范围

执行阶段允许改动以下文件：

- `onboard/scripts/board_live_route_preflight.sh`（新增或更新脚本入口，必须放在 `onboard/scripts`）
- `docs/navigation/fixed_route_workflow.md`（补现场 preflight/capture 入口说明）
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-done.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/side2side_check.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/final.md`
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md`（本文件可按执行结果同步补充）

明确约束（不得改动）：

- 不改 launch/行为编排配置
- 不改硬件配置参数
- 不改 WAVE ROVER / UART / 串口协议
- 不向根 `scripts/` 新增上车强耦合脚本（与 `scripts/README.md` 对齐）
- 不改 OKR 或 `docs/product`（本轮仅处理执行链路闭环）

## 接口边界

- SSH 首选入口：`ssh root@192.168.1.11 -p 37878`（第一优先级，首次必试）
- 目标 topic：`/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`
- 目标产物：`map.yaml`、`route.csv`、`keyframe`、`replay JSONL`/`rosbag`（任一存在可作为现场证据）
- 现场文档入口：统一参考 `docs/navigation/fixed_route_workflow.md`

## 设计原则

- 第一优先级：真实 SSH 重试，必须先尝试真实上位机链路。
- 第二优先级：SSH 不可达时，必须保留可复用本地 preflight/capture 入口，不得直接 `blocked` 收口。
- 第三优先级：产物路径、失败原因、复测动作固定写入 `tech-done.md`/`side2side_check.md`/`final.md`。

## 执行步骤

### A. 现场优先路径（首选）

1. 本地先跑一次安全预检：
   - `bash onboard/scripts/board_live_route_preflight.sh --help`
   - `bash onboard/scripts/board_live_route_preflight.sh --dry-run`
2. 立即尝试真实 SSH 链路（必试）：
   - `ssh root@192.168.1.11 -p 37878`
3. 若连通成功，执行脚本采集链路（或等价命令）：
   - ROS2 环境检查（`command -v ros2`、`setup.bash`）
   - `ros2 topic list` 与 `/scan` 等关键 topic 采样
   - 真实路线采集（`learn`/`map`/`route`/固定路线转换）
   - dry-run 与本地复核命令输出归档
4. 成功产物写入 `tech-done.md`：时间戳 run 目录、产物清单、路径、可复现命令。

### B. SSH 不可达或远端不可采集时（兜底）

1. 必须在 `docs/navigation/fixed_route_workflow.md` 中保留可复用替代入口（非阻塞）：
   - SSH 失败原因分桶（网关/端口/密钥/权限）
   - 下次复试清单（网络修复、上位机服务复位、权限验证）
2. 产出“下一次可直接复跑”的本地预检与采集序列（脚本 + 文档同步）。
3. `tech-done.md` 必须写明失败边界与下一步建议，不允许以未复用的 blocker 直接结束。
4. 将复核痕迹同步到 `side2side_check.md` 和 `final.md`，明确“为什么没到现场采集 + 下次重试路径”。

### C. 文档同步约束

- `onboard/scripts/board_live_route_preflight.sh` 为入口脚本，文档里不得再重复散落不可复用命令片段。
- `docs/navigation/fixed_route_workflow.md` 只保留当前 sprint 生效的执行口径和路径命名，避免和历史命令冲突。

## 验收命令

本 sprint 结束前必须执行并上报以下命令输出：

```bash
bash -n onboard/scripts/board_live_route_preflight.sh
bash onboard/scripts/board_live_route_preflight.sh --help
bash onboard/scripts/board_live_route_preflight.sh --dry-run
git status --short
rg -n "onboard/scripts/board_live_route_preflight.sh|docs/navigation/fixed_route_workflow.md|tech-done.md|side2side_check.md|final.md|bash -n|ssh root@192.168.1.11 -p 37878|不要改硬件配置|WAVE ROVER" sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md
git diff --check -- sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md
```

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低完成度条目是 **O7（约 12%）**。
本 sprint 与 CEO 指令一致，优先级偏置到 O3 现场材料恢复：
1) 用真实 SSH 重试恢复现场材料采集能力；
2) 不可达时保留 runbook 复跑能力，避免同类阻塞反复；
3) 这样对齐 O2 与 O7 的后续交付前置条件，属于可验证的现场 unblock。

## 成功标准与边界

成功标准（满足其一）：

- 在 `map.yaml` / `route.csv` / keyframe / replay / rosbag 中至少产出一类现场证据；
- 或产出可复用 runbook + 明确下一次执行步骤与恢复动作；
- 且同步完成 `tech-done.md` + `side2side_check.md` + `final.md`。

边界：

- `不要改硬件配置`
- `不要改 launch`
- `不要改 WAVE ROVER` 协议相关参数与串口细节
- 未实际命令执行时不得宣告“现场 lane 已完成”

## 风险与对冲

1. 目标主机端口依旧不可达：通过 runbook 与本地 dry-run 保持可复跑闭环。
2. topic 列表缺失或速率异常：在 `tech-done.md` 记录缺失项并同步修复动作，不做空收口。
3. 产物目录缺权限：退化为预检日志/证据路径记录，避免“无证据失败”。
