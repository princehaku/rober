# Sprint 2026.05.19_10-11 Hardware Real Material Escalation Request - Tech Done

## Hardware Infra Engineer

### sprint_type: epic

Run time: 2026-05-19 10:00 Asia/Shanghai。

### 实际改动

- `pc-tools/evidence/hardware_real_material_escalation_request.py`
  - 新增 `hardware_real_material_escalation_request` fail-closed PC gate，读取
    sanitized 输入后生成 artifact / summary。
  - 输出覆盖 WAVE ROVER/UART/HIL 真实材料、PR #5 2D LiDAR / ToF SKU/source、
    receipt/procurement、installation/wiring/power、calibration/HIL-entry、
    owner handoff、next required evidence 和 rerun command。
  - 明确 vendor/source 边界来自 `docs/vendor/VENDOR_INDEX.md`；当前本地 vendor
    tree 不证明 2D LiDAR / ToF 已采购、安装、接线、供电、标定或 HIL-entry。
  - 缺真实材料、unsupported schema、unsafe copy、HIL pass claim、field pass
    claim、delivery success claim、Objective 5 external proof claim 或
    `primary_actions_enabled=true` 时全部 fail closed。
- `tests/test_hardware_real_material_escalation_request.py`
  - 新增 4 个 focused unittest，覆盖 ready-not-proven summary、缺真实材料、
    unsafe/success wording fail-closed、临时路径归一化和否定句 HIL pass 误判。
- `docs/interfaces/hardware_real_material_escalation_request.md`
  - 记录 artifact / summary schema、字段白名单、fail-closed 条件和证据边界。
- `docs/product/production_hardware_boundary.md`
  - 补充硬件真实材料升级请求链路，说明它只把缺口变成可执行请求，不证明真实
    WAVE ROVER/UART/HIL、2D LiDAR / ToF 或 Objective 5 external proof。

### 验证结果

- `test -f docs/vendor/VENDOR_INDEX.md`
  - 结果：通过。
- `python3 -m py_compile pc-tools/evidence/hardware_real_material_escalation_request.py`
  - 结果：通过，无输出。
- `python3 -m unittest tests/test_hardware_real_material_escalation_request.py`
  - 结果：通过，`Ran 4 tests ... OK`。
- `rg -n "hardware_real_material_escalation_request|PR #5|2D LiDAR|ToF|WAVE ROVER|UART|HIL|docs/vendor/VENDOR_INDEX.md|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/interfaces docs/product/production_hardware_boundary.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request`
  - 结果：通过，命中 Hardware gate、PR #5、2D LiDAR / ToF、WAVE ROVER、
    UART、HIL、vendor index、`software_proof`、`not_proven`、
    `delivery_success=false`、`primary_actions_enabled=false`。
- `git diff --check -- pc-tools/evidence tests docs/interfaces docs/product/production_hardware_boundary.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request`
  - 结果：通过，无输出。

### 剩余风险

- 本轮没有真实 WAVE ROVER、UART、2D LiDAR、ToF、HIL 设备或真实手机。
- 本轮只把 Objective 1 真实材料缺口转成可执行升级请求，不证明 HIL pass、
  PR #4 route/elevator field pass、delivery success 或 Objective 5 external proof。

## Robot Platform Engineer

### sprint_type: epic

Run time: 2026-05-19 10:00 Asia/Shanghai。

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 `robot_diagnostics_hardware_real_material_escalation_request_summary`
    safe alias，优先消费 Hardware worker 的 sanitized summary。
  - 支持 `hardware_real_material_escalation_request`,
    `hardware_real_material_escalation_request_summary` 和 robot diagnostics
    alias 三个只读输出键，清理 `latest_status` 中同名输入，避免把上游原始字段透传。
  - 缺 summary、unsupported schema/boundary、unsafe fields、success wording、
    weak/local evidence ref、`delivery_success=true` 或
    `primary_actions_enabled=true` 时 fail closed 到 `not_proven`。
  - 输出保持 `software_proof`、`not_proven`、`delivery_success=false`、
    `primary_actions_enabled=false`，并显式保持 ACK、cursor、Nav2、HIL 和
    motion authorization 全部 disabled。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 新增 safe alias happy path 覆盖 WAVE ROVER、UART、HIL、PR #5 2D LiDAR /
    ToF 材料缺口。
  - 新增 missing summary、unsupported schema、unsafe fields、success wording 和
    raw artifact 字段 fail-closed 测试。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 补充 Robot diagnostics 新 alias 的 schema、source boundary、只读范围和
    fail-closed 条件。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 结果：通过，无输出。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 202 tests in 0.509s`，`OK`。
- `rg -n "robot_diagnostics_hardware_real_material_escalation_request_summary|hardware_real_material_escalation_request|PR #5|WAVE ROVER|UART|HIL|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_10-11_hardware-real-material-escalation-request`
  - 结果：通过，命中 Robot alias、PR #5、WAVE ROVER、UART、HIL、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_10-11_hardware-real-material-escalation-request`
  - 结果：通过，无输出。

### 剩余风险

- 本轮 Robot 侧没有读取 raw artifact、串口、硬件设备或 ROS graph。
- 本轮仍不是真实 WAVE ROVER/UART/HIL，不证明真实 2D LiDAR / ToF，不证明
  PR #4 route/elevator field pass，不证明 Objective 5 external proof。

## User Touchpoint Full-Stack Engineer

### sprint_type: epic

Run time: 2026-05-19 10:00 Asia/Shanghai。

### 实际改动

- `mobile/web/app.js`
  - 新增只读 “硬件真实材料升级请求” panel，优先消费
    `robot_diagnostics_hardware_real_material_escalation_request_summary`，
    缺失时只兼容 safe `hardware_real_material_escalation_request_summary`。
  - 只展示 safe status、safe evidence ref、missing hardware materials、next
    required evidence、owner handoff、evidence boundary 和 `not_proven`。
  - 新增安全文本过滤和 fail-closed fallback；命中 raw/internal payload、
    ROS topic、底层设备细节、凭证、路径、完整 artifact、checksum、pass wording
    或 success/control wording 时降级为 `not_proven`。
  - 未新增 ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、
    Cancel 或 robot command；主按钮 gating 保持不变。
- `mobile/web/styles.css`
  - 新增 panel 与 grid 样式，复用现有 gate/card 视觉系统。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 新增 2 个 focused unittest，覆盖 panel 只读消费、Robot alias 优先、
    safe fallback、fixture fail-closed 和安全词边界。
- `mobile/fixtures/mobile_web_status.fixture.json`
  - 新增 safe `hardware_real_material_escalation_request_summary` fixture。
- `mobile/web/fixtures/status.json`
  - 新增 Robot diagnostics safe alias fixture。
- `docs/product/mobile_user_flow.md`
  - 补充手机端 panel 的消费顺序、字段白名单、证据边界和不触发控制动作约束。

### 验证结果

- `python3 mobile/web/test_mobile_web_entrypoint.py`
  - `Ran 118 tests in 0.850s`
  - `OK`
- `python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py`
  - 通过，无输出。
- `node --check mobile/web/app.js`
  - 通过，无输出。
- `rg -n "hardware_real_material_escalation_request|robot_diagnostics_hardware_real_material_escalation_request_summary|PR #5|2D LiDAR|ToF|WAVE ROVER|UART|HIL|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request`
  - 通过；命中项用于核对新增 safe alias、fixture、文档边界和既有控制词。
- `git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request`
  - 通过，无输出。

### 剩余风险

- 本轮只证明 mobile/web 能展示 Robot/Hardware 提供的 phone-safe metadata。
- 未证明真实硬件材料、真实手机/browser、真实 route/elevator field pass、
  Objective 5 external proof 或任何真实运动/投放结果。
