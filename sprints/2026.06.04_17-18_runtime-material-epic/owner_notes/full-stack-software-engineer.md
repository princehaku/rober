# Full-Stack Owner Note: O7 PC/operator 8787 Runtime Smoke

## 角色与范围

- owner: User Touchpoint Full-Stack Engineer
- sprint: `sprints/2026.06.04_17-18_runtime-material-epic`
- 目标: 验证 PC/operator workflow 是否能访问真实上位机 `8787` 的非运动状态接口，并形成 O7 evidence/ref 或明确 blocker。
- 本轮未改 PC 产品代码、未改公开 API、未改底盘参数、未下发底盘运动命令。

## 用户旅程变化和触点收益

- PC operator 入口现在有真实上位机证据可引用：`ssh root@192.168.1.11 -p 37878` 可达，`127.0.0.1:8787` 返回 `status/map/radar/base` 等非运动状态。
- PC 同源代理可把真实 8787 status 与 map/list 转换成浏览器可消费的 fail-closed 摘要，operator 能看到 camera ready、radar/map/localize/not_proven、ACK/T1001 缺口，而不是看一张 mock UI。
- operator report 当前被真实上位机 `405 Method Not Allowed` 阻断；PC 侧保留 `upper_http_405`，不会把报告写入失败包装成成功。

## 实际动作

1. 阅读 `AGENTS.md`、`OKR.md`、本轮 `pre_start.md/prd.md/tech-plan.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_direct_upper_pc_api.md` 和 `pc-tools/workstation` 现有实现/测试。
2. 执行 CEO 指定 SSH/API 非运动检查：
   - `ssh root@192.168.1.11 -p 37878 'hostname; date; curl -fsS http://127.0.0.1:8787/api/status || true; curl -fsS http://127.0.0.1:8787/api/operator/report || true'`
3. 追加执行上位机只读 GET 摘要，覆盖 health/status/radar/map/localize/nav2/elevator/base/report。
4. 执行 PC package 现有测试：`cd pc-tools/workstation && npm test -- --run`。
5. 临时启动 PC workstation API 做同源代理 smoke：
   - 首次 `PORT=18787 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 因 `tsx` 在 `/mnt/c/.../Temp` 创建 IPC socket 失败。
   - 改用 `TMPDIR=/tmp PORT=18787 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 成功启动，监听 `http://127.0.0.1:18787`。
   - 调用 `/api/o7/direct-upper/status`、`/api/o7/direct-upper/map/list`、`/api/o7/direct-upper/operator-report`。
   - smoke 后已停止本地 `PORT=18787` API 进程。

## 关键验证结果

### SSH/API 非运动检查

```text
hostname: op-z3-b6.home
date: Thu Jun  4 05:19:18 PM CST 2026
/api/status: HTTP 200, schema=trashbot.upper_robot_api.v1.status
/api/operator/report: curl: (22) The requested URL returned error: 405
```

`/api/status` 关键字段摘录：

```json
{
  "camera": "ready",
  "radar_scan_status": "not_proven",
  "radar_raw_packet_status": "raw_packets_parsed",
  "map_status": "not_proven",
  "localization_status": "not_proven",
  "nav2_status": "not_proven",
  "elevator_status": "not_proven",
  "base_write_control_available": true,
  "base_t1001_observed": false,
  "safe_to_control": false,
  "robot_control_executed": false
}
```

### 上位机只读 GET 摘要

```text
/health: HTTP 200, schema=trashbot.upper_robot_api.v1.health, status=ready
/api/status: HTTP 200, camera=ready, radar_raw_packet_status=raw_packets_parsed, radar_scan_status=not_proven
/api/radar/status: HTTP 200, blocked_reasons=["ros2_lidar_scan_not_connected","scan_continuity_not_observed"]
/api/map/list: HTTP 200, schema=trashbot.upper_robot_api.v1.map_list_result, status=not_proven
/api/map/proof/latest: HTTP 404 Not Found
/api/localize/proof/latest: HTTP 404 Not Found
/api/nav2/status: HTTP 200, status=not_proven
/api/elevator/status: HTTP 200, status=not_proven
/api/base/status: HTTP 200, safe_to_control=false, robot_control_executed=false
/api/operator/report: HTTP 405 Method Not Allowed
```

### PC package 测试

```text
RUN  v4.1.7 /mnt/e/rober/pc-tools/workstation
Test Files  3 passed (3)
Tests  97 passed (97)
Duration  24.81s
```

### PC 同源代理 smoke

```text
/api/o7/direct-upper/status:
  HTTP 200
  schema=trashbot.pc_tools_workstation.o7_direct_upper_status.v1
  status=ready
  upper_api_base_url_source=env
  adapter_version=2026-06-04.field-default-radar-v2
  camera_status=ready
  radar_raw_packet_status=raw_packets_parsed
  radar_scan_status=not_proven
  map_lifecycle_status=not_proven
  localization_status=not_proven
  robot_ack_connected=false
  t1001_observed=false
  safe_to_control=false
  robot_control_executed=false

/api/o7/direct-upper/map/list?evidence_ref=o7_runtime_material_20260604_full_stack:
  HTTP 200
  schema=trashbot.pc_tools_workstation.o7_direct_upper_map_list.v1
  accepted_by_workstation=true
  upper_request.executed=true
  upper_request.path=/api/map/list
  upper_request.ok=true
  blocked_reasons=["robot_ack_not_connected","t1001_feedback_not_observed","field_evidence_not_proven"]
  safe_to_control=false
  robot_control_executed=false

/api/o7/direct-upper/operator-report:
  HTTP 502 from PC fail-closed wrapper
  upper_request.executed=true
  upper_request.path=/api/operator/report
  upper_request.http_status=405
  failure_reason=upper_http_405
  accepted_by_workstation=false
  safe_to_control=false
  robot_control_executed=false
```

## 失败定位

- root cause: 真实上位机 `8787` 当前拒绝 `/api/operator/report`，GET 和 PC 代理 POST 均返回 `405 Method Not Allowed`。
- 影响: PC operator workflow 不能在真实上位机写入/获取 operator report evidence；本轮 O7 只能证明 status 与 map/list 只读路径可达，不能证明完整 operator report 闭环。
- 归属判断: 8787 runtime report route 的方法/实现缺口更偏 Robot Software upper API owner；Full-Stack PC 侧已经正确 fail-closed 并暴露 `upper_http_405`，本轮不在 PC 侧伪造 report。
- 本地工具环境次要问题: `npm run api` 在默认 TMPDIR 下因 `tsx` IPC socket 位于 `/mnt/c/.../Temp` 报 `listen ENOTSUP`；设置 `TMPDIR=/tmp` 后可启动。这不影响 PC contract，但后续 runbook 可提示 WSL/mac 混合环境设置 `TMPDIR=/tmp`。

## 证据类型

- `robot_runtime_material`: SSH 到真实上位机成功，8787 `/health`、`/api/status`、`/api/radar/status`、`/api/map/list`、`/api/nav2/status`、`/api/elevator/status`、`/api/base/status` 返回真实 runtime/fail-closed 状态。
- `software_guard`: PC workstation 97 个测试通过；PC 同源代理 status/map/list 能转发真实 8787 并保持 `safe_to_control=false`、`robot_control_executed=false`。
- `blocked_with_root_cause`: `/api/operator/report` 在真实上位机返回 HTTP 405，operator report 闭环未完成。

## not_proven 与剩余风险

- 未证明真实 PC WASD 控车、底盘运动、急停演练、robot ACK、同场新鲜 `T=1001`、真实 `/scan` continuity、SLAM map artifact、AMCL 定位恢复、Nav2 消费 `/scan+map`、真实电梯状态链或 delivery success。
- `/api/status` 中 `base_write_control_available=true` 只说明上位机看到了可写底盘入口，不等于安全准入或 HIL pass。
- LiDAR raw packet 证据显示 `raw_packets_parsed`，但 `/scan` continuity 仍 `not_proven`，且 raw packet artifact freshness 为 stale；O7 不能据此宣称实时雷达可用。
- map/localize proof latest 为 404，说明当前仍缺 map lifecycle 与 localization runtime artifact。
- operator report 需要 Robot Software 对齐 8787 API：实现/启用 `POST /api/operator/report`，或明确提供只读 report endpoint 与 schema；Full-Stack 可随后复测 PC 同源代理和 UI 展示。

## 改动文件和接口影响

- 改动文件: `sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/full-stack-software-engineer.md`
- 接口影响: 无代码接口变更；本轮只记录真实 8787 contract 现状与 blocker。
- 需要机器人侧配合: 修复或澄清上位机 `/api/operator/report` method contract，并产出 operator report evidence ref 后再由 PC 复测。

## 2026-06-04 18:12 CST 复跑补充

### 用户旅程变化和触点收益

- PC operator 从“能打开页面”推进到“能通过 PC 同源代理读取真实上位机 8787 状态”：`direct-upper/status` 可看到 camera ready、radar raw packet parsed、map/localization not_proven、ACK/T1001 缺口和安全锁。
- PC 不把 8787 的 HTTP 可达包装成可控车；`safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false` 在真实 proxy 响应中保持固定。
- operator report 仍被上位机 405 阻断，PC 侧以 `upper_http_405` fail-closed 返回，operator 能看到失败原因，不会误以为 evidence 已写入。

### 复跑动作

1. 重新阅读 `AGENTS.md`、`OKR.md`、本 sprint `tech-plan.md`、本文件、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_direct_upper_pc_api.md` 和 `pc-tools/workstation` package/adapter 入口。
2. 直接访问真实上位机 `http://192.168.1.11:8787` 的只读或非运动 endpoint；没有调用 `/api/base/manual`，没有发底盘运动 POST。
3. 运行 PC package 测试、build、lint。
4. 用 `TMPDIR=/tmp PORT=18787 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 启动 PC 同源 API，复测 `direct-upper/status`、`direct-upper/map/list` 和非运动 `direct-upper/operator-report`；smoke 后已停止本地 `18787` API 进程。

### 8787 live HTTP smoke 摘要

```text
GET /health                  -> HTTP 200, schema=trashbot.upper_robot_api.v1.health, status=ready
GET /api/status              -> HTTP 200, schema=trashbot.upper_robot_api.v1.status
GET /api/radar/status        -> HTTP 200, blocked_reasons=["ros2_lidar_scan_not_connected","scan_continuity_not_observed"]
GET /api/map/list            -> HTTP 200, schema=trashbot.upper_robot_api.v1.map_list_result, status=not_proven
GET /api/map/proof/latest    -> HTTP 404, artifact_status=missing
GET /api/localize/proof/latest -> HTTP 404, artifact_status=missing
GET /api/nav2/status         -> HTTP 200, status=not_proven, artifact_status=missing
GET /api/elevator/status     -> HTTP 200, status=not_proven, artifact_status=missing
GET /api/base/status         -> HTTP 200, write_control_available=true, safe_to_control=false, robot_control_executed=false
GET /api/operator/report     -> HTTP 405, body="405: Method Not Allowed"
```

`GET /api/status` 关键安全字段：

```text
camera.status=ready
radar.scan_status=not_proven
radar.raw_packet_proof_latest.latest_proof_status=raw_packets_parsed
map.status=not_proven
localization.status=not_proven
nav2.status=not_proven
elevator.status=not_proven
base.write_control_available=true
base.feedback_ack.t1001_observed=false
base.feedback_ack.robot_ack_connected=false
base.safe_to_control=false
base.robot_control_executed=false
```

### PC 同源代理 smoke 摘要

```text
GET /api/o7/direct-upper/status
  -> HTTP 200
  status=ready
  upper_api_base_url_source=env
  adapter.version=2026-06-04.field-default-radar-v2
  health_request.ok=true, status_request.ok=true
  camera_status=ready
  radar_scan_status=not_proven
  radar_raw_packet_proof_latest_status=raw_packets_parsed
  map_lifecycle_status=not_proven
  localization_status=not_proven
  safe_to_control=false
  robot_control_executed=false

GET /api/o7/direct-upper/map/list?evidence_ref=o7_runtime_material_20260604_full_stack_rerun
  -> HTTP 200
  accepted_by_workstation=true
  upper_request.path=/api/map/list
  upper_request.ok=true
  blocked_reasons=["robot_ack_not_connected","t1001_feedback_not_observed","field_evidence_not_proven"]
  safe_to_control=false
  robot_control_executed=false

POST /api/o7/direct-upper/operator-report
  -> HTTP 502
  accepted_by_workstation=false
  upper_request.path=/api/operator/report
  upper_request.http_status=405
  failure_reason=upper_http_405
  blocked_reasons=["upper_http_405","robot_ack_not_connected","t1001_feedback_not_observed","field_evidence_not_proven"]
  safe_to_control=false
  robot_control_executed=false
```

### PC/package 验证

```text
cd pc-tools/workstation && npm test -- --run
Test Files  3 passed (3)
Tests  97 passed (97)
Duration  19.42s

cd pc-tools/workstation && npm run build
vite v7.3.3 building client environment for production...
✓ 14 modules transformed.
✓ built in 2.38s

cd pc-tools/workstation && npm run lint
exit code 0

git diff --check -- sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/full-stack-software-engineer.md pc-tools docs/product
exit code 0, no output
```

### 失败定位与剩余风险

- 真实 blocker 仍是上位机 8787 `/api/operator/report` 方法契约：GET 返回 405，PC proxy POST 也收到远端 HTTP 405，因此 O7 operator report evidence ref 不能闭环。
- 归属仍偏 Robot Software upper API owner；Full-Stack PC 层当前行为正确，已 fail-closed 暴露 `upper_http_405`，没有伪造 report 成功。
- `base.write_control_available=true` 只说明上位机能看到底盘写入口；本次没有现场看护/净空/急停证据，也没有调用底盘运动命令，不能证明 PC WASD 控车、HIL、robot ACK 或 `safe_to_control=true`。
- `/api/base/status` 的历史 `base_feedback_samples_latest` 已显示 T1001 样本文件存在但 freshness stale；本次没有新增同场新鲜 `T=1001` 证据，不能把它写成 ACK 闭环。
- `/api/map/proof/latest`、`/api/localize/proof/latest` 仍缺 artifact；O7 PC 能看见 not_proven，不等于 O3 map/localization runtime 已完成。
