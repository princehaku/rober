# Tech Plan: Runtime Material Deploy Refresh

## sprint_type

sprint_type: epic

## 文件范围和职责

### Robot Software Engineer

- 允许改动：`onboard/scripts/upper_robot_api.py`、`onboard/scripts/o1_lidar_scan_proof_collector.py`、相关 upper API 测试、`docs/interfaces/o7_upper_robot_api.md`、`docs/interfaces/lidar_ros2_closed_loop.md`、本 sprint owner note。
- 只读/运行范围：上位机 `192.168.1.11:8787` 的 service、进程、部署目录、health/status/radar refresh/latest 端点。
- 任务：
  1. 确认实际 8787 启动路径、service 名称、部署目录、reload/restart 命令和回滚方式。
  2. 比对本地与上位机 `upper_robot_api.py` / collector 版本，找出导致 HTTP 405 的部署差异。
  3. 在确认安全 reload 路径后部署 refresh route。
  4. 验证 live `POST /api/radar/scan-proof/refresh` 和 `GET /api/radar/scan-proof/latest`。
- 禁止：调用 `/api/base/manual`、发布 `/cmd_vel`、发送底盘 `T=1/T=13/T=130/T=131`、做 HIL 或修改硬件配置。

### User Touchpoint Full-Stack Engineer

- 允许改动：`pc-tools/workstation/` 中 direct-upper server/client/UI/test 的必要文件、`docs/interfaces/o7_direct_upper_pc_api.md`、`docs/product/pc_tools_workstation.md`、本 sprint owner note。
- 任务：
  1. 确认 PC runtime/adapter 指向部署后的 `192.168.1.11:8787`。
  2. 通过 PC 同源 `POST /api/o7/direct-upper/radar/scan-proof/refresh` 触发 refresh。
  3. 记录 operator 可读结果、adapter version、artifact freshness 和 blocker 文案。
- 禁止：新增与本轮无关的 UI 大改，不绕过 upper API 直连 ROS graph。

### Hardware Infra Engineer

- 文件范围：只读咨询优先；如必须改文档，仅限 `docs/hardware/o1_wave_rover_serial_feedback_probe.md`、`docs/hardware/o1_pc_manual_lidar_hil_boundary.md`、`docs/interfaces/lidar_ros2_closed_loop.md` 小段和本 sprint owner note。
- 任务：
  1. 复核 deploy refresh 不触碰底盘 `/dev/ttyS5`、运动指令或 HIL。
  2. 检查结果材料是否持续标注 `safe_to_control=false`、`robot_control_executed=false`。
  3. 若发现 deploy/reload 会影响底盘控制服务，要求暂停并升级 Product/CEO。
- 禁止：低速 pulse、manual control、turn smoke、急停演练或把 `T=1001` 写成 robot ACK。

### Product Manager / OKR Owner

- 文件范围：本轮已允许的 `pre_start.md`、`prd.md`、`tech-plan.md`、`owner_notes/product-okr-owner.md`；IC 返回前不得改 `OKR.md`、`tech-done.md`、`side2side_check.md`、`final.md`。
- 任务：定义验收口径、Evidence Type Gate、最近 2 轮 blocker scan、OKR 最低优先级核对和后续涨分规则。

## 执行步骤

1. Robot Software 先运行只读定位：
   ```bash
   curl -sS http://192.168.1.11:8787/health
   curl -sS http://192.168.1.11:8787/api/radar/status
   curl -i -X POST http://192.168.1.11:8787/api/radar/scan-proof/refresh
   ```
   预期：确认当前仍是 405 或已部署；若非 405，继续 latest 回读。
2. Robot Software 确认 reload/service：
   ```bash
   ssh <upper-host> 'ps -ef | grep -E "upper_robot_api|8787" | grep -v grep || true'
   ssh <upper-host> 'systemctl --user list-units --type=service --all | grep -E "trashbot|upper|robot|8787" || true'
   ssh <upper-host> 'systemctl list-units --type=service --all | grep -E "trashbot|upper|robot|8787" || true'
   ```
   预期：拿到实际服务或进程路径；若没有 service，必须写清启动命令和回滚方案再部署。
3. Robot Software 同步文件前做版本 diff：
   ```bash
   ssh <upper-host> 'python3 --version && ls -l <upper-api-dir>'
   ```
   预期：确认上位机代码目录；不确定目录时停止，不盲写。
4. 部署后验证 upper route：
   ```bash
   curl -sS -X POST http://192.168.1.11:8787/api/radar/scan-proof/refresh | tee /tmp/scan-proof-refresh.json
   curl -sS http://192.168.1.11:8787/api/radar/scan-proof/latest | tee /tmp/scan-proof-latest.json
   ```
   预期：refresh 返回 JSON，latest artifact 与本次时间戳/evidence_ref 对齐。
5. Full-Stack 验证 PC 同源：
   ```bash
   curl -sS -X POST http://localhost:<pc-port>/api/o7/direct-upper/radar/scan-proof/refresh | tee /tmp/pc-scan-proof-refresh.json
   ```
   预期：PC proxy 调到同一个 upper refresh route，并在 UI/API 里展示 freshness/blocker。
6. Hardware 复核非运动边界：
   ```bash
   curl -sS http://192.168.1.11:8787/api/status
   curl -sS http://192.168.1.11:8787/api/base/status
   ```
   预期：材料中 `safe_to_control=false`，且没有本轮触发 base/manual 或 movement command。

## 验收命令

Robot Software Engineer 必须返回：

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
python3 -m compileall -q onboard/scripts
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o7_upper_robot_api.md docs/interfaces/lidar_ros2_closed_loop.md
```

User Touchpoint Full-Stack Engineer 必须返回：

```bash
cd pc-tools/workstation && npm test -- --run
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation docs/interfaces/o7_direct_upper_pc_api.md docs/product/pc_tools_workstation.md
```

Hardware Infra Engineer 必须返回：

```bash
git diff --check -- docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/hardware/o1_pc_manual_lidar_hil_boundary.md docs/interfaces/lidar_ros2_closed_loop.md
```

现场/material 验收必须包含：

```bash
curl -i -X POST http://192.168.1.11:8787/api/radar/scan-proof/refresh
curl -sS http://192.168.1.11:8787/api/radar/scan-proof/latest
```

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O8 约 43%；产品主线最低为 O2 约 72%，其次 O3 约 73%。
- 本 sprint 是否针对该 Objective：是。O8 通过 Epic 留档、Evidence Type Gate 和 blocker scan 继续推进；产品抓手针对 O3/O7 的 runtime material 前置条件。
- 为什么不直接做 O2：最近两轮已经确认 O2 blocker 是缺真实/受控电梯图片 manifest，本轮没有新图片来源；继续围绕 O2 写文档或 fixture 会重复消费 blocker。
- final.md 收口时需复核：如果 refresh route 部署成功并取得 fresh `/scan` proof，下一轮必须从 O3 进入 SLAM `/map`、map save/load、AMCL 或 Nav2 消费；如果部署失败，必须标记 root cause，避免第三轮重复消费。

## 最近 2 轮 blocker 核对

- `20-21_runtime-material-followup`：O3 blocked 在 live hooks 仍是 dry-run/no-command，O2 blocked 在无真实/受控 elevator image manifest。
- `21-22_runtime-material-runtime-hooks`：O3/O7 blocked 在 live 8787 未部署 refresh route，`POST /api/radar/scan-proof/refresh` 返回 405。
- 本轮处理策略：只攻 `upper_refresh_route_not_deployed_http_405`；O2/O1/O5/O6 均作为风险/下一步，不进入本轮实现。

## Evidence Type Gate

| Evidence type | 本轮可否涨分 | 判定 |
| --- | --- | --- |
| `software_guard` | 否 | 本地 unittest、PC tests/build/lint、接口文档只能证明护栏。 |
| `blocked_with_root_cause` | 否 | HTTP 405、service unknown、no `/scan` topic 等只能收敛 blocker。 |
| `robot_runtime_material` | 可小幅支撑 O3/O7 | live deployed route 成功、fresh `/scan` proof、latest artifact 与 evidence_ref 对齐、PC 同源触发通过。 |
| `field_hil_material` | 本轮不采集 | 低速 pulse、ACK/T=1001 同场、急停、视频等属于 O1/O7 下一步。 |
| `user_acceptance_material` | 本轮不采集 | 普通用户任务验收、送达成功、跨楼层流程不在本轮。 |
| `production_live_material` | 本轮不采集 | O5/O6 production cloud/4G/DB/OSS 不在本轮。 |

## OKR 涨分规则

- O3 可涨：live 8787 部署 refresh route，fresh `/scan` once/hz artifact 回读成功，材料标注为 `robot_runtime_material`；若同时证明 `/lidar/raw_packet`、TF 或 ROS2 topic freshness，可作为下一轮 SLAM/AMCL/Nav2 的前置证据。
- O7 可涨：PC 同源入口触发 deployed upper refresh route，UI/API 展示 fresh/stale/blocker 并保留 operator evidence；只有 upper curl 成功但 PC 未触发时，O7 不涨。
- O8 可涨：本轮完整按 Epic 留档、blocker root cause 清晰、IC owner notes 和 final 复核 evidence gate；但 O8 涨分不能替代 O3/O7 产品涨分。
- 不涨：本地测试、route 代码存在、旧 artifact readback、HTTP 405、service 路径未知、无 `/scan` topic、仅 SSH 手工命令、仅 UI 文案。

## 风险、阻塞和证据链缺口

- `upper_8787_reload_path_unknown`：需要 service/进程/部署目录/回滚证据。
- `upper_refresh_route_not_deployed_http_405`：上一轮已确认，本轮必须部署或进一步定位。
- `ros2_scan_topic_absent_or_stale`：route 部署后仍可能无 fresh `/scan`。
- `pc_adapter_runtime_stale`：PC 可能仍未加载新 adapter 或指向旧 upper base URL。
- `o2_image_manifest_missing`：电梯图片 manifest 缺口保留为下一步。
- `o1_hil_safety_not_ready`：底盘低速 pulse 和 stop-first HIL 保留为下一步，不在本轮执行。
