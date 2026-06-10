# 2026-06-11 00:55 PC Manual Motion Evidence Capture

## sprint_type

micro

## owner

`full-stack-software-engineer`

## 目标

在上一轮 `4406984 Add PC manual motion HIL gate` 基础上，给 PC workstation 的 `POST /api/robot-control/base/manual?baseUrl=...` 与 `POST /api/robot-control/base/stop?baseUrl=...` 增加运动证据自动采集 V1。

本轮继续保持普通用户 PC 首页简易风格：首屏只显示一句最近证据状态，高级诊断才展示 before/after endpoint 摘要。没有现场物理安全确认时，不发送 `forward/back/left/right` 非零运动。

## 硬件事实来源

本轮没有直接开串口，也没有修改 onboard、硬件配置、launch 或 vendor 文件。涉及 WAVE ROVER 和上位机边界时采用本地资料：

- `docs/vendor/VENDOR_INDEX.md`

采用事实边界：

- WAVE ROVER UART 是 newline-delimited JSON。
- 当前项目实测链路是 `/dev/ttyS5 @ 115200`。
- 速度控制参考 `T=1`。
- 反馈请求参考 `T=130`。
- workstation 只消费上位机 HTTP API，不直接操作 UART。

## 实际改动

- 更新 `pc-tools/workstation/src/shared/contracts.ts`：
  - 给 `RobotControlBaseCommandProxyResponse` 增加 `evidence_capture_status`、`evidence_capture_endpoints`、`evidence_capture_blocked_reasons`、`before_readback`、`after_readback`、`motion_evidence_summary`。
  - 固定状态枚举为 `captured | partial | blocked`。
- 更新 `pc-tools/workstation/src/server/index.ts`：
  - manual/stop 代理在 before 和 after 两个阶段自动采集固定 GET-only endpoint：
    - `/api/base/status`
    - `/api/base/feedback-samples/latest`
    - `/api/radar/status`
    - `/api/radar/scan-proof/latest`
  - 本地 reject、远端失败、远端成功都返回同一套 evidence capture 字段。
  - endpoint 失败不会改变 manual/stop 主请求规则，只会把 evidence 状态降级为 `partial` 或 `blocked`。
  - 仍固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - `移动/导航` 首屏新增一句普通用户可读的最近证据状态。
  - 高级诊断新增 evidence capture status、endpoint、blocked reason、before/after readback 摘要。
- 更新 `pc-tools/workstation/test/App.test.ts` 与 `pc-tools/workstation/test/catalog.test.ts`：
  - 覆盖首页最近证据简洁文案。
  - 覆盖 local checklist reject 也采集 before/after 固定 GET evidence，并确认不发送 `/api/base/manual` POST。
- 更新 `docs/product/pc_tools_workstation.md`：
  - 同步 manual/stop evidence capture 合同、固定 GET endpoint、首页/高级诊断展示边界。
- 新增 artifacts：
  - `sprints/2026.06.11_00-55_pc_manual_motion_evidence_capture/artifacts/local_manual_reject_evidence_response.json`
  - `sprints/2026.06.11_00-55_pc_manual_motion_evidence_capture/artifacts/remote_stop_evidence_response.json`

## 接口影响

`POST /api/robot-control/base/manual?baseUrl=<robot-api-base-url>` 与 `POST /api/robot-control/base/stop?baseUrl=<robot-api-base-url>` 响应新增字段：

- `evidence_capture_status`
- `evidence_capture_endpoints`
- `evidence_capture_blocked_reasons`
- `before_readback`
- `after_readback`
- `motion_evidence_summary`

证据采集只使用固定 GET endpoint，不新增任意代理，不接受前端传入 endpoint/method/body。

## 验证结果

运行时间：2026-06-11 00:57:37 CST。

主节点复核时间：2026-06-11 00:59:54 CST。复核重点是固定 endpoint、首页简洁风格、真实上位机 stop-only 边界和 artifact 内容。

```bash
cd pc-tools/workstation && npm run build
```

通过。关键输出：`33 modules transformed`、`built in 1.11s`。

主节点复跑通过。关键输出：`33 modules transformed`、`built in 1.45s`。

```bash
cd pc-tools/workstation && npm run test
```

通过。关键输出：`Test Files  2 passed (2)`、`Tests  69 passed (69)`。

主节点复跑通过。关键输出：`Test Files  2 passed (2)`、`Tests  69 passed (69)`。

```bash
cd pc-tools/workstation && npm run lint
```

通过，无 error/warning。

主节点复跑通过，无 error/warning。

```bash
git diff --check
```

通过，无 whitespace error。

主节点复跑通过，无 whitespace error。

```bash
python3 -m json.tool /Users/m1/apps/rober/sprints/2026.06.11_00-55_pc_manual_motion_evidence_capture/artifacts/local_manual_reject_evidence_response.json >/dev/null
python3 -m json.tool /Users/m1/apps/rober/sprints/2026.06.11_00-55_pc_manual_motion_evidence_capture/artifacts/remote_stop_evidence_response.json >/dev/null
```

通过，两个 JSON artifact 均可格式化。

主节点复核 artifact 摘要：
- `local_manual_reject_evidence_response.json`：`proxy_status=command_rejected`、`evidence_capture_status=blocked`、`evidence_capture_endpoints=8`、所有 evidence endpoint `method=GET`、`robot_control_executed=false`。
- `remote_stop_evidence_response.json`：`proxy_status=command_forwarded`、`remote_http_status=200`、`requested_direction=stop`、`applied_direction=stop`、`evidence_capture_status=captured`、`evidence_capture_endpoints=8`、所有 evidence endpoint `method=GET`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## Smoke 结果

本地 workstation API 使用空闲端口 `127.0.0.1:8790` 启动。

```bash
curl -sS -X POST 'http://127.0.0.1:8790/api/robot-control/base/manual?baseUrl=http%3A%2F%2F127.0.0.1%3A8790' \
  -H 'Content-Type: application/json' \
  --data '{"direction":"forward","speed":0.08,"duration_ms":500,"confirm_hil_checklist":false}'
```

结果：

- HTTP `400`
- `proxy_status=command_rejected`
- `failure_reason=confirm_hil_checklist_required`
- `evidence_capture_status=blocked`
- `evidence_capture_endpoints` 数量为 `8`
- `before_readback` / `after_readback` 都包含 4 个固定 endpoint key
- `robot_control_executed=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

说明：本地 reject smoke 的 `baseUrl` 指向 workstation 自身，不是真实 Robot API，因此固定 GET evidence endpoint 不存在，证据状态按预期为 `blocked`，但字段完整。

```bash
curl -sS -X POST 'http://127.0.0.1:8790/api/robot-control/base/stop?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' \
  -H 'Content-Type: application/json' \
  --data '{}'
```

结果：

- HTTP `200`
- `command_kind=stop`
- `proxy_status=command_forwarded`
- `remote_http_status=200`
- `status=stopped`
- `evidence_capture_status=captured`
- `evidence_capture_endpoints` 数量为 `8`
- `before_readback` / `after_readback` 都包含：
  - `base_status`
  - `base_feedback_samples_latest`
  - `radar_status`
  - `radar_scan_proof_latest`
- `requested_direction=stop`
- `applied_direction=stop`
- `robot_control_executed=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

浏览器验收：
- 打开 `http://127.0.0.1:8791/` 后默认仍是 `Rober 小车控制台` / `机器人` 页。
- 第一屏仍只展示 `小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航` 五块简易卡片。
- `移动/导航` 卡片只新增 `最近证据：还没有请求。` 一句普通用户摘要；endpoint 列表和 before/after readback 留在 `高级诊断`。
- 浏览器 console warning/error 为空。
- 截图 artifact：[`/Users/m1/apps/rober/sprints/2026.06.11_00-55_pc_manual_motion_evidence_capture/artifacts/browser_motion_evidence_first_screen.png`](</Users/m1/apps/rober/sprints/2026.06.11_00-55_pc_manual_motion_evidence_capture/artifacts/browser_motion_evidence_first_screen.png>)。

## 非零运动边界

本轮真实上位机 smoke 只发送了 stop。没有向真实上位机发送 `forward/back/left/right` 非零运动命令。

## 用户旅程变化

普通用户仍停留在简洁 PC 首页：`移动/导航` 卡片只显示方向键、停止、现场 checklist、一次简短请求状态和一句“最近证据”。工程字段、endpoint 列表、before/after readback 和 blocked reason 均在高级诊断区。

收益是 operator 每次点动或 stop 后都能拿到自动采集的 base/radar/readback 前后快照摘要，便于后续上车 evidence capture，但不会被误读为 HIL pass。

## 剩余风险

- evidence capture 只证明 workstation 通过上位机 HTTP 固定 GET endpoint 读到了快照摘要，不证明真实底盘安全、HIL 通过、轮向正确、UART 反馈完整或送达成功。
- local reject smoke 的 evidence 状态为 `blocked`，因为它故意指向 workstation 本地服务，不是真实 Robot API。
- 真实上位机 smoke 只覆盖 stop，不覆盖非零 motion；非零 motion 仍需要现场物理安全确认、急停/扶控和 Hardware/Robot owner 的 HIL 口径。
