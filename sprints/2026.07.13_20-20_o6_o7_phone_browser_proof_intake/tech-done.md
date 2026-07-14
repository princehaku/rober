# Tech Done - O6/O7 Phone Browser Proof Intake

## Robot Software Engineer

- sprint_type: epic
- run_time: 2026-07-13 20:44:36 CST
- owner: robot-software-engineer

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `phone_browser_terminal_material` O6 section，schema 固定为 `trashbot.o6.phone_browser_terminal_material.v1`。
  - proof boundary 固定为 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`。
  - 支持从 field evidence、artifact bundle、`field_motion_evidence_packet` 或轻量顶层字段 intake，同一 `task_id` 下写入 archive 并回读到 consumer alias / explicit include。
  - 输出固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
  - raw URL、cookie、Authorization、token、本地路径、screenshot body、DOM dump、traceback、`/cmd_vel`、serial/UART、WAVE ROVER 和 dangerous true field 均 fail closed 为 `blocked_not_proven`，不回显危险输入。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增同 task `true_phone_browser_evidence` / diagnostics / terminal result summary intake/readback 覆盖。
  - 新增 hostile payload 测试，覆盖 raw URL、cookie、Authorization、token、本地路径、screenshot body、DOM dump、traceback、`/cmd_vel`、serial/UART、WAVE ROVER 和 dangerous true field。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 记录 O6 archive/consumer 合同、include 名称、字段白名单和 fail-closed 边界。
- `docs/product/cloud_4g_infrastructure.md`
  - 记录该能力仅为 O6/O7 本地/mock 摘要 intake/readback，不等于真实云、4G、路线执行、送达或 HIL。
- `docs/product/remote_4g_mvp.md`
  - 记录 Full-stack 可消费的安全读模型和不可宣称的产品边界。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 结果：exit 0，无输出。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：`Ran 193 tests in 84.730s`，`OK`。
- `rg -n "phone_browser_terminal_material|true_phone_browser_evidence|software_proof_o6_o7_phone_browser_terminal_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false" onboard/src/ros2_trashbot_behavior docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/tech-done.md`
  - 结果：exit 0；命中 `remote_cloud_relay.py`、`test_remote_cloud_relay.py`、O6 API 文档、cloud/4G 产品文档、remote 4G MVP 文档和本文件中的 `phone_browser_terminal_material`、`true_phone_browser_evidence`、`software_proof_o6_o7_phone_browser_terminal_material_intake_only`、`safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake`
  - 结果：exit 0，无 whitespace error。

### 失败定位

- focused hostile 测试曾暴露 artifact bundle consumer alias 未暴露 `phone_browser_terminal_material`，已补齐 alias 后重跑通过。

### 剩余风险

- 仍是 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`，没有真实手机/browser 操作链、生产公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、route execution、delivery success 或 HIL。
- 该轮没有触碰硬件/vendor、WAVE ROVER、ESP32、Orange Pi、UART、串口、launch、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或 O5 CDN/TLS probe。

### 接口影响和协同

- Full-stack 可读取 `GET /api/o6/consumer/tasks/<task_id>?include=phone_browser_terminal_material`，或从 consumer detail 顶层 alias 读取同一 section。
- Product 可接受边界：本轮只能作为 O6/O7 support-only intake/readback 证据，不能提升为真实 phone/browser proof、delivery proof、production cloud proof 或 OKR 主进度。
- Hardware / Autonomy 无需本轮协同；Full-stack 后续只需按字段白名单展示，不应展示 raw URL、DOM、截图正文、cookie/token、本地路径或任何控制成功文案。

## Full-Stack Software Engineer

- sprint_type: epic
- run_time: 2026-07-13 20:58:36 CST
- owner: full-stack-software-engineer

### 实际改动

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 新增 O7 selected-task `phone-browser-proof/intake` adapter，baseUrl 仅允许 local-loopback，固定转发 O6 `POST /api/o6/archive/field-evidence`。
  - 写入最小 `phone_browser_terminal_material` 安全摘要，并立即从 O6 receipt readback；返回 `trashbot.pc_tools_workstation.o7_phone_browser_proof_intake_result.v1`。
  - fail closed 覆盖非回环 URL、task mismatch、dangerous true、raw URL/token/local path/raw body、控制词和坏 O6 receipt。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/o7/consumer-read/tasks/:taskId/phone-browser-proof/intake?baseUrl=<local-loopback-url>` 路由。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增前端 client action，浏览器只调用 PC adapter，不直连 O6 field-evidence。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 phone/browser terminal material summary、request body 和 intake receipt 共享类型，并把 `phone_browser_terminal_material` 加入 O7 consumer task detail。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 新增 selected-task UI：safe evidence ref、terminal result type、accepted materials、captured time、action blocker、receipt summary、material readback、false fields 和 not_proven 展示。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 adapter success/update/fail-closed/HTTP route 覆盖。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 UI fixture、按钮 flow、URL 调用和 receipt 文案覆盖。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 记录 O7 phone/browser proof intake API、字段白名单、readback contract 和 proof boundary。
- `docs/product/pc_tools_workstation.md`
  - 记录用户旅程、selected-task 操作边界、receipt-only 语义和固定 false 字段。

### 用户旅程变化和触点收益

- Operator 在 O7 Previews 选择同一 task 并加载 consumer detail 后，可点击 `接收 phone/browser 材料`，把安全 terminal material 摘要写入 O6，并在同一屏看到 `phone_browser_terminal_material_written=true`、`phone_browser_terminal_material_readback=true`、`same_task_id_consumed=true`、`safe_evidence_ref`、accepted/missing/rejected materials。
- UI 明确展示 proof boundary：`software_proof_o6_o7_phone_browser_terminal_material_intake_only`。该入口只证明 phone/browser terminal material 摘要进入 O6/O7 readback，不证明真实 phone/browser 验收、路线执行、送达、HIL 或 production cloud。

### 接口影响和 Robot Software/O6 合同依赖

- O7 新增：`POST /api/o7/consumer-read/tasks/<task_id>/phone-browser-proof/intake?baseUrl=<local-loopback-url>`。
- O6 依赖：`POST /api/o6/archive/field-evidence` 必须返回 `trashbot.o6.field_evidence_archive.v1`、`source=local_mock_field_evidence_archive`、`proof_status=not_proven`、`field_evidence_written=true`、`write_status=created|updated`，并在同一 task 下回显 `phone_browser_terminal_material`。
- 固定 false fields 必须保持：`safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`、`robot_control_executed=false`。

### 验证结果

- `cd pc-tools/workstation && npm run test`
  - 结果：`Test Files 3 passed (3)`，`Tests 507 passed (507)`。
  - 首轮失败定位：O7 response-side unsafe scanner 把允许的固定 false key `reads_local_path=false` 误判成 raw local path；已改为 response 只扫描字符串值，保留 request body 对 `raw_body` / `local_path` key 的 fail-closed。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过；Vite 输出 `✓ built in 1.98s`，仅保留现有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`
  - 结果：exit 0，无 eslint 输出。
- `rg -n "phone-browser-proof/intake|o7_phone_browser_proof_intake|phone_browser_terminal_material|software_proof_o6_o7_phone_browser_terminal_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false" pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/tech-done.md`
  - 结果：exit 0；命中 O7 adapter、server route、client API、shared contract、Vue UI、Vitest、接口文档、产品文档和本 sprint 留档。
- `git diff --check -- pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake`
  - 结果：exit 0，无 whitespace error。

### 剩余风险

- 仍是 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`，没有真实手机/browser 操作链、生产云、真实 4G、route execution、delivery success 或 HIL。
- 该轮未触碰硬件/vendor、WAVE ROVER、ESP32、Orange Pi、UART、ROS2 launch、`/cmd_vel`、`/api/base/manual`、NavigateToPose、O5 CDN/TLS probe 或 O5 readiness packet consumption。
