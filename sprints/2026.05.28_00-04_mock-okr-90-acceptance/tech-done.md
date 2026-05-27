# Mock OKR 90 Acceptance Tech Done

## sprint_type

sprint_type: epic

## Task A - Objective 1 Mock Hardware Evidence

Owner：`robot-software-engineer`

### 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`
  - 增加 `Objective 1` / `90%+ mock/software completion` / `not_proven` 字段。
  - 增加 `virtual_hil_packet`，覆盖 JSON newline 编码、`T=1` wheel command、`T=1001` 反馈解析、IMU/Battery 发布路径、坏帧容错和参数边界。
  - 保留 `real WAVE ROVER`、`real UART/HIL`、`real Orange Pi serial device`、`real IMU/battery calibration` 为 `not_proven`。
- `onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
  - 增加 Objective 1 mock/software completion 和 virtual HIL packet 断言。
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - 增加 fake ROS publisher 测试，验证 `T=1001.y` 发布到 `/imu/data` yaw 四元数、`T=1001.v` 发布到 `/battery.voltage`。
- `docs/hardware/wave_rover_json_bridge.md`
  - 增加 Objective 1 mock 90 evidence 边界，明确本轮只证明 software proof，不证明真实 HIL。

### 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test
```

结果：`Ran 26 tests in 0.146s`，`OK`。

```bash
rg -n "Objective 1|90|mock|software proof|not_proven|WAVE ROVER|UART|HIL" onboard/src/ros2_trashbot_hardware docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0；匹配到本轮 Objective 1 mock/software completion、`not_proven` 风险边界、WAVE ROVER/UART/HIL vendor 引用和 sprint 记录。输出很大，因为扫描范围包含 `docs/vendor` 的厂商 HTML/SVG 资料。

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0，无 whitespace error。

### 剩余风险

- `90%+ mock/software completion` 不是 `source=hil_pass`。
- 真实 WAVE ROVER、真实 UART/HIL、真实 Orange Pi 串口、真实 IMU/battery 标定仍为 `not_proven`。
- `T=13` 仍只作为未验证 vendor 路径保留，不能作为默认生产控制模式。

## Task B - Objective 5 Mock Cloud Control Evidence

Owner：`full-stack-software-engineer`

### 实际改动

- `cloud-relay/tests/test_o5_mock_control_plane.py`
  - 新增 Objective 5 本地/mock control plane smoke。
  - 覆盖 `trashbot.remote.v1` commands/status/ack、bearer/env credential、mock 4G network recovery、mock DB/queue artifact、mock OSS/CDN manifest 和 preflight graceful degradation。
  - 断言 ACK 只代表 envelope 处理完成，`delivery_success=false`，真实 4G/SIM、HTTPS/TLS、production DB/queue、OSS/CDN live traffic 继续 `not_proven`。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 增加 Objective 5 `90%+ mock/software completion` 边界，明确 mock 证据可计入软件完成度，但不能替代真实公网/4G/production/OSS/CDN/phone 材料。
- `docs/product/cloud_4g_infrastructure.md`
  - 记录本轮 Task B 的 O5 mock control plane 证据范围和真实材料缺口。
- `o6_cloud_archive_state.json`
  - 已确认是 `trashbot.o6.archive_store.v1` runtime state，按任务要求从仓库根目录删除，Task B 测试全部使用临时目录状态文件。

### 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
```

结果：`Ran 4 tests in 1.214s`，`OK`。

```bash
test ! -e o6_cloud_archive_state.json
```

结果：退出码 0；仓库根目录未再生成 `o6_cloud_archive_state.json`。

```bash
rg -n "Objective 5|90|mock|software proof|not_proven|4G|production DB|OSS|CDN|live traffic" cloud-relay docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0；匹配到 Objective 5 mock/software completion、`not_proven`、4G、production DB、OSS/CDN 和 live traffic 风险边界。重定向计数为 `16062` 行，输出很大，因为扫描范围包含历史 docs 和 vendor 资料。

```bash
git diff --check -- cloud-relay docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0，无 whitespace error。

### 剩余风险

- 本轮只证明 Objective 5 `90%+ mock/software completion`，不证明真实公网 HTTPS/TLS。
- 真实 4G/SIM outbound polling、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 仍为 `not_proven`。
- mock DB/queue 使用 file/SQLite proof store 和 artifact；不代表多实例一致性、生产队列顺序、灾备或真实生产迁移已经完成。

## Task C - Objective 6 Mock Archive 90 Evidence and Runtime State Fence

Owner：`full-stack-software-engineer`

### 实际改动

- `cloud-relay/src/ros2_trashbot_cloud_relay/archive_core.py`
  - 将 O6 默认 runtime state 从仓库根目录 `o6_cloud_archive_state.json` 改为系统临时目录下的同名文件。
  - 保留优先级：`TRASHBOT_O6_ARCHIVE_STATE` 显式路径 > `TRASHBOT_REMOTE_CLOUD_STATE` 同目录 `*.o6_archive.json` > `/tmp/o6_cloud_archive_state.json` fallback。
- `cloud-relay/tests/test_archive_core.py`
  - 新增默认 state path fence 断言，验证无 env 时不会落到仓库根。
  - 新增机器人侧 `archive_event_publisher`、`ros2_trashbot_nav.algorithm_evidence_feed` 与 `ArchiveStore` 的 schema 兼容测试。
  - 复用同一 `robot_id/task_id` 写入 task/event/annotation/inference，并验证查询详情返回 `trashbot.archive.v1` / `software_proof` / `not_proven`。
- `docs/interfaces/o6_cloud_archive_core_api.md`
  - 更新 `TRASHBOT_O6_ARCHIVE_STATE`、`TRASHBOT_REMOTE_CLOUD_STATE` 和 `/tmp` fallback 的 state 边界。
  - 增加 Objective 6 `90%+ mock/software completion` 证据说明。
- `docs/product/cloud_4g_infrastructure.md`
  - 记录 Task C O6 mock archive 90 证据和真实材料 `not_proven` 边界。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 algorithm evidence feed 可与 board event 一起进入 O6 archive core 的兼容证据。
- `docs/vision/perception_upgrade_evaluation.md`
  - 记录 keyframe/floor/obstacle/annotation/inference stub 只用于 schema proof，不证明真实模型或相机效果。

### 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
```

结果：`Ran 6 tests in 1.216s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_archive_event_publisher.py
```

结果：`Ran 5 tests in 0.003s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_algorithm_evidence_feed.py
```

结果：`Ran 3 tests in 0.001s`，`OK`。

```bash
test ! -e o6_cloud_archive_state.json
```

结果：退出码 0；仓库根目录没有 `o6_cloud_archive_state.json`。

```bash
rg -n "Objective 6|90|mock|software proof|not_proven|trashbot.archive.v1|o6_cloud_archive_state|TRASHBOT_O6_ARCHIVE_STATE|production DB|OSS" cloud-relay onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0；匹配到 Objective 6 mock/software completion、`trashbot.archive.v1`、`TRASHBOT_O6_ARCHIVE_STATE`、`o6_cloud_archive_state`、production DB、OSS 和 `not_proven` 边界。输出约 `20159` 行，包含既有 docs/vendor 资料命中。

```bash
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0，无 whitespace error。

### 剩余风险

- 本轮只证明 Objective 6 `90%+ mock/software completion`，不证明真实安全隧道。
- production DB/queue、真实 OSS upload、真实推理 runtime、live O6 API、真实云、真实 4G/SIM 和上车数据仍为 `not_proven`。
- `/tmp/o6_cloud_archive_state.json` fallback 只适合本地 smoke；生产部署仍必须显式配置 `TRASHBOT_O6_ARCHIVE_STATE` 或 production DB/queue。

## Task D - Objective 7 Mock Operations Console 90 Evidence

Owner：`full-stack-software-engineer`

### 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/algorithm_evidence_feed.py`
  - 在 O6/O7 offline mock archive bundle 中增加 `asr_transcript`、`tts_draft`、`safe_command_stub` events。
  - 保持 `source=software_proof`、`proof_status=not_proven`、`mock_feed=true`、`offline_only=true`，并新增真实 ASR/TTS、safe command API、robot ACK 缺口。
- `onboard/src/ros2_trashbot_nav/test/test_algorithm_evidence_feed.py`
  - 增加 ASR/TTS stub、手控/寻路 stub、`real_asr_tts_runtime`、`real_safe_command_api`、`real_robot_ack` 断言。
- `pc-tools/workstation/src/server/o7CloudArchiveTasks.ts`
  - 对 O6 `trashbot.archive.v1` bundle 增加白名单派生：`route_frame` 进入历史路线回放，`keyframe` 进入 keyframe refs，`annotations`/`inferences` 进入数据标注/推理摘要，`asr_transcript`/`tts_draft` 进入 ASR/TTS stub，`safe_command_stub` 进入手控/寻路 stub。
  - 所有派生继续固定 `safe_to_control=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`robot_control_executed=false`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展 O6 archive schema consumption 测试，覆盖 O7 六区中的历史路线回放、数据标注、推理摘要、ASR/TTS stub、手控/寻路 stub 和 fail-closed false fields。
- `docs/interfaces/o6_cloud_archive_core_api.md`
  - 记录 offline algorithm feed 现在包含 ASR/TTS stub 和 safe-command stub，但不证明真实 runtime、TTS playback、robot ACK 或 dispatch readiness。
- `docs/interfaces/o7_cloud_archive_task_api.md`
  - 记录 O6 `trashbot.archive.v1` 到 O7 archive tasks 的白名单派生规则和固定 false 边界。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 记录 O6 bundle 可支撑 Objective 7 `90%+ mock/software completion` 的 ASR/TTS 与手控/寻路 stub evidence，同时保留真实能力 `not_proven`。
- `docs/product/pc_tools_workstation.md`
  - 更新 PC workstation 产品边界，明确 O6 bundle 可被 O7 PC adapter 消费为六区 mock/live-like evidence，但不连接 live O6 bearer API，不发送 TTS，不执行真实手控/Nav2。

### 验证结果

已执行：

```bash
cd pc-tools/workstation && npm run build
```

结果：退出码 0；`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过，Vite 输出 `✓ built in 2.05s`。

```bash
cd pc-tools/workstation && npm run test
```

结果：退出码 0；`Test Files 2 passed (2)`，`Tests 41 passed (41)`。

```bash
cd pc-tools/workstation && npm run lint
```

结果：退出码 0；ESLint 无输出错误。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_algorithm_evidence_feed.py
```

结果：退出码 0；`Ran 3 tests in 0.002s`，`OK`。

```bash
rg -n "Objective 7|90|mock|software proof|not_proven|实时地图|电梯状态|历史路线回放|数据标注|ASR|TTS|手控|寻路|safe_to_control|robot_control_executed" pc-tools cloud-relay onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0；匹配到 Objective 7 mock/software completion、实时地图、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路、`safe_to_control=false`、`robot_control_executed=false` 和真实能力 `not_proven` 边界。重定向计数为 `17202` 行，包含既有 docs/vendor SVG/HTML 资料命中。

```bash
git diff --check -- pc-tools cloud-relay onboard/src/ros2_trashbot_nav docs sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0，无 whitespace error。

### 剩余风险

- 本轮只证明 Objective 7 `90%+ mock/software completion`，不证明 live O6 bearer API。
- 真实 RTC/视频、真实 ASR/TTS、真实 TTS 播放、真实手控/Nav2、真实 robot ACK、真实 browser/手机和上车数据仍为 `not_proven`。
- PC adapter 只消费本地 O6/O7 mock archive bundle 或本机回环 probe，不连接生产云、不发送命令、不读取硬件。

## Task E - Product Acceptance and OKR Closeout

Owner：`product-okr-owner`

### 实际改动

- `OKR.md`
  - 将 Objective 1、Objective 5、Objective 6、Objective 7 的当前进度统一更新为 `90%+ mock/software completion；real material not_proven`。
  - 在 4.1 当前 OKR 进度快照中明确本轮 90%+ 只代表 mock/software completion，不代表真实硬件、真实公网/4G、production DB/queue、OSS/CDN live traffic、真实 RTC/ASR/TTS、真实手控/Nav2、真实 browser/手机或上车完成。
- `docs/process/okr_progress_log.md`
  - 追加 `2026-05-28 00-04｜mock-okr-90-acceptance` 记录，汇总 Task A-D 的证据、验证结果、失败定位和真实材料缺口。
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/side2side_check.md`
  - 新增 Product side-by-side 验收，对照 PRD/tech-plan 验收口径核对 O1/O5/O6/O7。
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/final.md`
  - 新增 sprint final，收口本轮完成度、验证范围和后续真实材料风险。
- `sprints/2026.05.28_00-04_mock-okr-90-acceptance/tech-done.md`
  - 追加本 Product closeout 记录。

### Task A-D 证据汇总

| Task | Objective | 验收判断 | 验证结果 | 失败定位 | 剩余风险 |
| --- | --- | --- | --- | --- | --- |
| Task A | O1 硬件协议可信底盘 | 通过，达到 `90%+ mock/software completion` | `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test`：`Ran 26 tests ... OK`；required `rg` 通过；scoped `git diff --check` 通过 | 无最终失败；`rg` 输出大是因为包含 docs/vendor 厂商资料 | 真实 WAVE ROVER、真实 UART/HIL、真实 Orange Pi 串口、真实 IMU/battery 标定仍 `not_proven` |
| Task B | O5 云中转控制面 | 通过，达到 `90%+ mock/software completion` | `python3 -m unittest discover -s cloud-relay/tests`：`Ran 4 tests ... OK`；`test ! -e o6_cloud_archive_state.json` 通过；required `rg` 和 scoped `git diff --check` 通过 | 无最终失败 | 真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 仍 `not_proven` |
| Task C | O6 云端核心后端 | 通过，达到 `90%+ mock/software completion` | cloud-relay tests：`Ran 6 tests ... OK`；behavior archive publisher：`Ran 5 tests ... OK`；nav feed：`Ran 3 tests ... OK`；`test ! -e o6_cloud_archive_state.json` 通过；required `rg` 和 scoped `git diff --check` 通过 | 无最终失败 | 真实安全隧道、production DB/queue、真实 OSS upload、真实推理 runtime、live O6 API、真实云、真实 4G/SIM 和上车数据仍 `not_proven` |
| Task D | O7 PC 端运营调试平台 | 通过，达到 `90%+ mock/software completion` | `npm run build` 通过；`npm run test`：`2 passed / 41 passed`；`npm run lint` 通过；nav feed unittest：`Ran 3 tests ... OK`；required `rg` 和 scoped `git diff --check` 通过 | 无最终失败 | live O6 bearer API、真实 RTC/视频、真实 ASR/TTS、真实 TTS 播放、真实手控/Nav2、真实 robot ACK、真实 browser/手机和上车数据仍 `not_proven` |

### 验证结果

Product closeout 已执行：

```bash
test ! -e o6_cloud_archive_state.json
```

结果：退出码 0。

```bash
rg -n "Objective 1|Objective 5|Objective 6|Objective 7|90|mock/software completion|software proof|真实材料|not_proven|Task A|Task B|Task C|Task D|o6_cloud_archive_state" OKR.md docs/process/okr_progress_log.md sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0。

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.28_00-04_mock-okr-90-acceptance
```

结果：退出码 0，无 whitespace error。

### 剩余风险

- 本轮 OKR 提升只按 CEO 允许的 mock 数据口径判定，不能作为真实硬件或真实生产效果验收。
- O1/O5/O6/O7 的真实材料仍为 `not_proven`，后续必须分别补真实 WAVE ROVER/HIL、公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、live O6 API、真实 RTC/ASR/TTS、真实手控/Nav2、真实 browser/手机和上车数据。
- Product closeout 未运行 Docker/Humble build、真实 Orange Pi、真实 WAVE ROVER/UART、HIL、真实云、真实 4G/SIM、真实 OSS/CDN、真实 PC browser、真实手机或现场路线/电梯验证。
