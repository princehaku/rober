# Sprint 2026.05.14_18-19 Mobile PWA Install Prompt Evidence Export - Tech Plan

sprint_type: epic

## Goal

实现 `mobile_pwa_install_prompt_evidence_export*`：把已捕获的 PWA install prompt 事件状态导出为 whitelist-only、phone-safe、可复制/下载的现场验收材料包，并通过 Robot metadata-only fence 证明该材料包不能触发控制、ACK、cursor、readiness 或 delivery result。

## Evidence Boundary

- 统一证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`
- export schema：`trashbot.mobile_pwa_install_prompt_evidence_export.v1`
- summary schema：`trashbot.mobile_pwa_install_prompt_evidence_export_summary.v1`
- copy schema：`trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1`
- 证据性质：Docker/local mobile software proof + Robot metadata-only compatibility proof
- 禁止宣称：真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、Objective 5 external proof、HIL、dropoff/cancel completion、delivery success

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5，改针对 Objective 4。
3. 理由：Objective 5 当前主要缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。本机只有 Docker，没有真实硬件或外部云材料；继续堆 O5 local metadata 不会移动 O5 completion。根据 stop rule，本轮转向 Objective 4 的真实手机验收前置材料能力。
4. Objective 4 当前约 94%，上轮已完成 `mobile_pwa_install_prompt_event_capture*`。本轮继续做 `mobile_pwa_install_prompt_evidence_export*`，补齐现场验收材料导出能力，但仍不宣称真实手机验收完成。

## 并行任务总览

本 sprint 是 Epic，默认并行启动 2 个工程 worker，加 1 个 Product 收口任务：

- Task A：`full-stack-software-engineer`，负责 `mobile/web` export UI、copy/download package、phone-safe whitelist 和前端围栏验证。
- Task B：`robot-software-engineer`，负责 remote bridge / protocol metadata-only compatibility fence 和后端围栏验证。
- Task C：`product-okr-owner`，负责收口文档、OKR 口径和证据边界复核。

Task A 与 Task B 文件范围互不重叠，必须并行启动。Task C 等 A/B 结果返回后执行。

## Task A - full-stack-software-engineer

### 目标

在手机 PWA 中增加 `mobile_pwa_install_prompt_evidence_export*` 导出能力。导出材料必须可复制/下载、phone-safe、whitelist-only，并保留 Start Delivery、Confirm Dropoff、Cancel fail closed。

### 建议文件范围

允许 Task A 修改：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `tests/test_mobile_web_entrypoint.py` 或现有 mobile web targeted test 文件
- 必要时更新 `docs/product/mobile_user_flow.md`
- 当前 sprint `tech-done.md`

不得修改：

- Robot command handlers、remote bridge control logic、hardware config、OKR closeout 文件。

### 实现要求

- 新增或复用 PWA 安装提示证据区，展示 export summary。
- 输入优先级：显式 `mobile_pwa_install_prompt_evidence_export*`，其次 `mobile_pwa_install_prompt_event_capture*`，再其次既有 `mobile_pwa_install_prompt_evidence*`、`mobile_device_handoff_session*`、`mobile_device_evidence_capture*`、`mobile_browser_acceptance_bundle*`，都缺失时派生 blocked-by-design export。
- copy/download package 必须包含：
  - `schema=trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1`
  - `schema_version=1`
  - `source=mobile_web`
  - `overall_status`
  - `install_prompt_capture_status`
  - `install_prompt_user_choice`
  - `appinstalled_status`
  - `display_mode`
  - `manifest_present`
  - `service_worker_status`
  - `client_reference`
  - `client_timestamp`
  - `safe_to_control=false`
  - `ack_semantics=accepted_processing_only_not_delivery_success`
  - `evidence_boundary=software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`
  - `not_proven`
  - `safe_phone_copy`
- copy/download package 不得包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、local filesystem path、traceback、checksum、complete artifact、raw robot response、raw event payload 或 robot/internal technical fields。
- Export 只产出 support/acceptance metadata，不新增控制授权条件。

### 验收命令

围栏命令由 Task A 执行并贴日志片段：

```bash
python3 -m unittest mobile.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "mobile_pwa_install_prompt_evidence_export|trashbot.mobile_pwa_install_prompt_evidence_export|software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate|accepted_processing_only_not_delivery_success|safe_to_control|not_proven" mobile/web mobile/fixtures tests
git diff --check -- mobile/web mobile/fixtures tests docs/product/mobile_user_flow.md sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
```

如 `node` 不可用，必须在 `tech-done.md` 写清无法做 JS 语法验证的影响和剩余风险，不能用 Python 编译 JS 文件替代。

## Task B - robot-software-engineer

### 目标

新增 `mobile_pwa_install_prompt_evidence_export*` Robot metadata-only compatibility fence，证明该 family 不触发 robot control、ACK、cursor、readiness 或 delivery result。

### 建议文件范围

允许 Task B 修改：

- `cloud-relay/src/ros2_trashbot_cloud_relay/` 下与 remote bridge / protocol metadata fence 相关文件
- `tests/` 或 `cloud-relay/tests/` 下 targeted remote bridge / protocol test 文件
- 必要时更新相关接口说明文档
- 当前 sprint `tech-done.md`

不得修改：

- `mobile/web` UI 实现、硬件配置、Nav2/behavior 业务状态机、OKR closeout 文件。

### 实现要求

- 新增 metadata-only family 识别：`mobile_pwa_install_prompt_evidence_export*`。
- metadata-only payload 单独出现时不得触发：
  - collect/dropoff/cancel
  - ACK POST
  - cursor advance 或 cursor persistence
  - terminal ACK
  - production readiness
  - HIL
  - dropoff/cancel completion
  - delivery success
- mixed payload 同时包含合法 `trashbot.remote.v1` command 时，只能由合法 command envelope 决定 action/ACK/cursor；export metadata 不得提升权限。
- 返回或测试日志必须保留证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`。

### 验收命令

围栏命令由 Task B 执行并贴日志片段：

```bash
python3 -m unittest discover -s tests -p '*remote*bridge*test*.py'
python3 -m unittest discover -s tests -p '*protocol*test*.py'
python3 -m py_compile $(rg --files cloud-relay/src tests | rg '\.py$')
rg -n "mobile_pwa_install_prompt_evidence_export|trashbot.mobile_pwa_install_prompt_evidence_export|software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate|metadata-only|delivery success|ACK|cursor" cloud-relay/src tests
git diff --check -- cloud-relay/src tests sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
```

若 discover pattern 因文件命名不匹配出现 `NO TESTS RAN` 或 0 tests，必须改为具体现有 test module / class / method 命令，不能把 0 tests 当作产品证明。

## Task C - product-okr-owner

### 目标

在 A/B 完成后做阶段收口，确保 sprint 留档、OKR 口径和产品文档同步状态真实。

### 文件范围

允许 Task C 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `docs/product/mobile_user_flow.md`，仅当 A/B 实现已改变产品行为或新增用户可见材料区时
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/tech-done.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/side2side_check.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/final.md`

### 收口要求

- 汇总 Task A/B 实际改动和验证日志。
- 明确本轮只证明 `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`。
- 若验证完整且 UI/Robot fence 均通过，可谨慎评估 Objective 4 是否上调；Objective 5 除非有真实外部证据，否则保持约 68%。
- final 必须回顾本 tech-plan 的 `OKR 最低优先级核对` 是否仍成立。
- 检查是否存在未处理 TODO、范围外改动、无证据成功宣称、或 docs 滞后。

### 验收命令

```bash
rg -n "mobile-pwa-install-prompt-evidence-export|mobile_pwa_install_prompt_evidence_export|software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|full-stack-software-engineer|robot-software-engineer" OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
git diff --check -- OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
```

## 本计划创建阶段验收命令

本阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，不实现产品代码。必须运行：

```bash
test -f sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/pre_start.md && test -f sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/prd.md && test -f sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|mobile_pwa_install_prompt_evidence_export|software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate|Objective 5|Objective 4|full-stack-software-engineer|robot-software-engineer" sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
git diff --check -- sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
```

## 风险边界

- 本轮不是硬件 sprint，不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸。
- 如果后续工程实现触及硬件事实，必须先读 `docs/vendor/VENDOR_INDEX.md` 和其指向的 vendor 文件。
- 本轮禁止 broad tests；只运行 Task A/B/C 的 targeted unittest、syntax check、required `rg` 和 scoped `git diff --check`。
- 不得把 copy/download/export 材料、ACK、HTTP accepted、receipt、browser proof 或 software proof 写成 delivery success。
