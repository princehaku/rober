# 2026-06-11 00:35 PC Manual Motion HIL Gate

## sprint_type

micro

## owner

`full-stack-software-engineer`

## 产品 / 安全设计

### 目标

在不破坏 PC 首页普通用户简易风格的前提下，把 `移动/导航` 卡片从“未开放”升级成“受控点动（需现场确认）”。

本轮只做 WAVE ROVER 小车底盘的受控点动入口，不做自动导航、不做键盘连续控制、不做地图点击目标。

### 首页风格约束

- 默认首页仍然是 `Robot Control`。
- 第一屏只展示普通用户可理解的信息：方向键、停止、速度上限、时长上限、现场确认清单和简短失败解释。
- `source`、`proof_status`、`task_id`、raw proof、SDP、ICE、software_proof 等工程字段继续留在高级诊断，不回到首屏。

### 代理边界

- PC Node 端只新增两个固定代理：
  - `POST /api/robot-control/base/manual?baseUrl=...`
  - `POST /api/robot-control/base/stop?baseUrl=...`
- 这两个代理只允许分别转发到上位机：
  - `/api/base/manual`
  - `/api/base/stop`
- 不新增任意 POST 透传能力，不允许前端自定义远端路径。

### fail-closed 规则

- 所有 manual/stop 响应都必须继续固定：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- 非 `stop` 方向必须同时满足：
  - `confirm_hil_checklist=true`
  - 方向属于白名单
  - 速度、时长都通过本机 clamp
- 即使远端返回成功、ACK 或业务字段，也不能把页面解释成“已经安全可控”或“已通过 HIL”。

### HIL checklist 设计

前端只在用户勾选完完整 checklist 后，才允许发送非 stop 点动：

1. 现场有人扶控并准备急停。
2. 小车前后左右无人员和障碍。
3. 当前只做低速短时点动验证。
4. 已确认本轮不是自动导航。

未满足时按钮 disabled，并明确显示缺少的 checklist 原因。

### 速度 / 时长门槛

- 本轮前端和 Node 代理都显示并执行同一套上限。
- 代理必须对 `direction`、`speed`、`duration_ms` 做白名单与 clamp。
- 方向只允许：
  - `forward`
  - `back`
  - `left`
  - `right`
  - `stop`
- `stop` 允许在未勾 checklist 时执行，因为它是 fail-safe 动作。

### 真实联调边界

- 本轮允许对真实上位机 `http://192.168.1.11:8787` 做安全 smoke。
- 允许动作：
  - `POST /api/robot-control/base/stop?...`
  - 或 `direction=stop` 的手动停止请求
- 未做现场物理安全确认时，禁止发送 `forward/back/left/right` 的非零运动。

### 硬件事实来源

本轮涉及底盘控制边界时，只引用本地 vendor 资料，不猜测硬件细节：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

采用事实：

- 当前项目真实证据链使用 `/dev/ttyS5 @ 115200`
- WAVE ROVER UART 为 newline-delimited JSON
- `T=1` 为速度控制
- `T=130` 为反馈请求

这些事实只用于说明 HIL 边界和底盘控制来源，不代表本轮 workstation 直接操作 UART。

## 实际改动

- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/index.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/server/index.ts>)，新增固定代理：
  - `POST /api/robot-control/base/manual?baseUrl=...`
  - `POST /api/robot-control/base/stop?baseUrl=...`
- manual 代理只允许 `forward/back/left/right` 四个方向，并对 `speed`、`duration_ms` 做本机 clamp；stop 代理只允许固定转发到 `/api/base/stop`。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/robotControlSummary.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/server/robotControlSummary.ts>) 与 [`/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts>)，把受控点动 V1 的安全边界写入共享合同：`speed_limit_mps=0.12`、`duration_limit_ms=800`、允许方向白名单、HIL checklist、`/api/base/stop` 入口、`allowed_methods=["GET","POST"]`。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/client/workstationApi.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/client/workstationApi.ts>)，新增 `postRobotControlBaseManual()` 与 `postRobotControlBaseStop()`，前端不直接访问上位机。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/components/RobotControlConsolePanel.vue`](</Users/m1/apps/rober/pc-tools/workstation/src/components/RobotControlConsolePanel.vue>)，把首屏 `移动/导航` 卡片升级为“受控点动（需现场确认）”：方向键、停止、速度/时长输入、HIL checklist、禁用原因、最近一次代理结果都由 fail-closed 合同驱动。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/styles.css`](</Users/m1/apps/rober/pc-tools/workstation/src/styles.css>)，补齐受控点动卡片、点动键区、checklist 和状态胶囊样式，保持首屏简洁。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`](</Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts>) 与 [`/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`](</Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts>)，补齐首页文案、manual clamp、checklist gate、stop fail-safe 代理测试。
- 更新 [`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`](</Users/m1/apps/rober/docs/product/pc_tools_workstation.md>)，同步产品边界、真实联调边界和 vendor 引用。

## 接口影响

- 新增 PC workstation 本地接口：
  - `POST /api/robot-control/base/manual?baseUrl=<robot-api-base-url>`
  - `POST /api/robot-control/base/stop?baseUrl=<robot-api-base-url>`
- manual 请求体合同：
  - `direction: forward | back | left | right`
  - `speed: number`
  - `duration_ms: number`
  - `confirm_hil_checklist: boolean`
- manual fail-closed 规则：
  - 非 stop 方向必须 `confirm_hil_checklist=true`
  - `speed<=0.12`
  - `duration_ms<=800`
  - 方向不在白名单、数字无效、未确认 checklist、URL 不合法时直接 `command_rejected`
- stop fail-safe 规则：
  - 不要求 checklist
  - 只允许固定转发到 `/api/base/stop`
- 所有 manual/stop 响应固定：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
- 本轮 base command 代理对远端 true 字段只把会放松安全边界的字段视为危险：`safe_to_control`、`delivery_success`、`primary_actions_enabled`、`manual_control_enabled`、`command_dispatch_enabled`、`navigate_goal_enabled`、`keyboard_control_enabled`。远端为命令型 endpoint 返回 `sends_commands=true` 或 `robot_control_executed=true` 不再把 stop 代理误判成失败。

## 验证结果

运行时间：2026-06-11 00:39 CST。

主节点复核时间：2026-06-11 00:44 CST。复核时发现首轮实现把后退方向写成 `backward`，而上位机 `onboard/scripts/upper_robot_api.py` 的真实白名单是 `forward/back/left/right/stop`。已要求实现 agent 修正 Robot Control Base Manual/Stop V1 合同、测试、文档和 artifact，UI 仍显示“后退”，但实际发送 `back`。

```bash
cd pc-tools/workstation && npm run build
```

通过。输出包含：`33 modules transformed`、`built in 1.26s`。

主节点修正后复跑通过。输出包含：`33 modules transformed`、`built in 938ms`。

```bash
cd pc-tools/workstation && npm run test
```

通过。输出：`Test Files  2 passed (2)`、`Tests  68 passed (68)`。

主节点修正后复跑通过：`Test Files  2 passed (2)`、`Tests  68 passed (68)`。

```bash
cd pc-tools/workstation && npm run lint
```

通过，无 error/warning。

主节点修正后复跑通过，无 error/warning。

```bash
git diff --check
```

通过，无 whitespace error。

主节点修正后复跑通过，无 whitespace error。

```bash
python3 -m json.tool sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/local_health_8789.json
python3 -m json.tool sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/local_manual_rejected_response.json
python3 -m json.tool sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/remote_stop_proxy_response.json
```

通过，三个 JSON artifact 均可格式化。

主节点修正后重新生成并校验三个 JSON artifact，`local_manual_rejected_response.json` 与 `remote_stop_proxy_response.json` 的 `request_contract.allowed_directions` 均为 `["forward","back","left","right","stop"]`。

```bash
curl -sS http://127.0.0.1:8789/api/health
```

本地 workstation API smoke 通过；由于 `127.0.0.1:8787` 当时已有预先存在的服务占用，当前实现改在 `127.0.0.1:8789` 启动验证。返回 `api_routes` 已包含：
- `/api/robot-control/base/manual?baseUrl=<robot-api-base-url>`
- `/api/robot-control/base/stop?baseUrl=<robot-api-base-url>`

```bash
curl -sS -X POST 'http://127.0.0.1:8789/api/robot-control/base/manual?baseUrl=http%3A%2F%2F127.0.0.1%3A8789' -H 'Content-Type: application/json' --data '{"direction":"forward","speed":0.5,"duration_ms":1200,"confirm_hil_checklist":false}'
```

本地 manual gate smoke 通过 fail-closed 拒绝：
- `proxy_status=command_rejected`
- `failure_reason=confirm_hil_checklist_required`
- `clamped_speed_mps=0.12`
- `clamped_duration_ms=800`

```bash
curl -sS -X POST 'http://127.0.0.1:8789/api/robot-control/base/stop?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'
```

真实上位机 stop 安全 smoke 通过：
- `proxy_status=command_forwarded`
- `remote_http_status=200`
- `status=stopped`
- `hil_checklist_gate_status=stop_allowed_without_checklist`
- 仍保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`

相关 artifact：
- [`/Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/local_health_8789.json`](</Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/local_health_8789.json>)
- [`/Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/local_manual_rejected_response.json`](</Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/local_manual_rejected_response.json>)
- [`/Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/remote_stop_proxy_response.json`](</Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/remote_stop_proxy_response.json>)
- [`/Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/browser_pc_manual_gate_first_screen.png`](</Users/m1/apps/rober/sprints/2026.06.11_00-35_pc_manual_motion_hil_gate/artifacts/browser_pc_manual_gate_first_screen.png>)

浏览器验收：
- 打开 `http://127.0.0.1:8789/` 后默认仍是 `Rober 小车控制台` / `机器人` 页。
- 第一屏保留普通用户简易结构：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- `移动/导航` 卡片显示 `受控点动（需现场确认）`、方向键、`停止`、速度/时长输入和现场确认 checklist。
- 未输入地址时 `停止` 和非 stop 方向均 disabled；输入 `http://192.168.1.11:8787` 后 `停止` enabled，`前进` 在未勾 checklist 时仍 disabled。
- `task_id`、O6 base URL、peer/ICE/SDP、raw readback、proof flags 等工程字段仍留在 `高级诊断` 折叠区，不在第一屏铺开。

## 失败定位

- 第一轮真实 stop smoke 命中了远端命令型响应里的 `sends_commands=true` / `robot_control_executed=true`，workstation 一开始把它们沿用为 summary 级危险字段，导致 stop 被误判为 `command_failed`。
- 已修复：base manual/stop 代理改成只对会放松安全边界的 true 字段做 fail-closed 扫描，不再因为命令型 endpoint 合理返回“已发送”而把 stop 安全 smoke 误判失败。

## 剩余风险

- 本轮没有发送任何 `forward/back/left/right` 非零真实运动；真实联调只做了 stop 安全 smoke。这是刻意边界，不是遗漏。
- 前端和 Node 代理的 `0.12 m/s`、`800 ms` 是 workstation 侧保守门槛，不等于硬件/底盘最终 HIL 认可值；后续若要放宽，必须先补现场安全证据。
- 本轮只引用 vendor 资料中的链路事实：WAVE ROVER UART 为 newline-delimited JSON，项目真实证据链使用 `/dev/ttyS5 @ 115200`，速度控制参考 `T=1`，反馈请求参考 `T=130`。workstation 本身并不直接操作 UART。
- 首页仍保持普通用户简易风格，但高级诊断里保留了代理细节，便于现场排障。
