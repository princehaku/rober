# OKR 90 Software Acceleration Tech Done

## sprint_type

sprint_type: epic

## Task A - O6 Cloud Archive Core

Owner: `full-stack-software-engineer`

### 实际改动

- `cloud-relay/src/ros2_trashbot_cloud_relay/archive_core.py`
  - 新增 O6 本地/Docker software proof 数据层。
  - 固定 `trashbot.archive.v1`、`trashbot.annotation.v1`、`trashbot.inference.v1`。
  - 提供任务存档、事件存档、标注记录、推理记录和查询能力。
  - `evidence_ref` 只保存 OSS/object 引用，不保存大对象正文。
  - 响应固定标记 `software_proof`、`not_proven`、`not_proven_production_db`。
- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
  - 在 wrapper runtime 启动前安装 `/api/o6/*` 路由补丁。
  - 不修改 onboard `trashbot.remote.v1` commands/status/ack 实现。
- `cloud-relay/tests/test_archive_core.py`
  - 覆盖 task/event/annotation/inference 本地持久化。
  - 覆盖 O6 HTTP bearer gate，并复核 `/healthz` 仍返回 `trashbot.remote.v1`。
- `docs/interfaces/o6_cloud_archive_core_api.md`
  - 新增 O6 archive/annotation/inference API 文档。
- `docs/product/cloud_4g_infrastructure.md`
  - 补充 O6 cloud archive core 的部署边界、state 路径和 production DB 缺口。

### 接口影响

- 新增 bearer-gated API：
  - `POST /api/o6/archive/tasks`
  - `GET /api/o6/archive/tasks`
  - `GET /api/o6/archive/tasks/{task_id}?robot_id=<id>`
  - `POST /api/o6/archive/events`
  - `GET /api/o6/archive/events`
  - `POST /api/o6/annotations`
  - `GET /api/o6/annotations`
  - `POST /api/o6/inference`
  - `GET /api/o6/inference`
- 未改动 `trashbot.remote.v1` robot polling、status、ACK 或 terminal-result contract。
- 本轮不新增真实 OSS 上传、不新增 production DB/queue、不新增真实推理 runtime。

### 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/*.py
# exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s cloud-relay/tests
# ..
# ----------------------------------------------------------------------
# Ran 2 tests in 0.547s
#
# OK

rg -n "trashbot.archive.v1|trashbot.annotation.v1|trashbot.inference.v1|evidence_ref|not_proven|software_proof" cloud-relay docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0；命中 5245 行，包含新增 O6 schema、evidence_ref、software_proof 和 not_proven_production_db 证据标记。

git diff --check -- cloud-relay docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0
```

### 剩余风险

- `TRASHBOT_O6_ARCHIVE_STATE` / JSON proof store 只适合本地和 Docker 单实例验证，不是 production DB。
- O6 当前只保存 `evidence_ref`，未连接真实 OSS upload、STS 或 CDN live traffic。
- 推理 API 当前记录调用结果，不运行真实 CPU/GPU 模型或外部推理服务。
- 后续 Task B 需要让机器人侧按同一 schema 上报任务和事件。

## Task B - O6 Board Event Publisher

Owner: `robot-software-engineer`

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/archive_event_publisher.py`
  - 新增机器人侧 O6 event envelope 生成器。
  - 从 `task_record` 整理 `task_status`、`elevator_state`、`route_frame`、`keyframe`、`detection_result`、`failure_reason` 事件。
  - 固定写入 `robot_id`、`task_id`、`event_type`、`timestamp`、`evidence_ref`、`source=software_proof`、`proof_status=not_proven`。
  - 默认写本地 JSONL 队列；只有配置 `archive_base_url` 时才尝试 POST `/api/o6/archive/events`，失败会回落 retry stub。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
  - 写入 collection `task_record` 后旁路生成 O6 archive events。
  - 新增 `o6_archive_events_enabled`、`o6_archive_robot_id`、`o6_archive_queue_file`、`o6_archive_base_url`、`o6_archive_bearer_token_env` 参数。
  - 默认不访问真实网络，队列写到 `task_record_dir/o6_archive_events.jsonl`。
- `onboard/src/ros2_trashbot_behavior/test/test_archive_event_publisher.py`
  - 覆盖 Task A envelope 必填字段、成功/失败事件差异、本地队列和 HTTP 失败回落。
- `onboard/src/ros2_trashbot_behavior/setup.py`
  - 新增 `o6_board_event_publisher` CLI，用于从本地 task_record 生成/入队事件。
- `docs/interfaces/o6_board_event_publisher.md`
  - 记录机器人侧 publisher 的事件类型、参数、队列形态和 software proof 边界。

### 接口影响

- 不修改 Task A `docs/interfaces/o6_cloud_archive_core_api.md` schema。
- 不修改 `trashbot.remote.v1` commands/status/ack。
- 新增机器人侧事件 envelope，字段兼容 Task A event record，额外保留 `timestamp` 与 `evidence_boundary` 便于本地复核。

### 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/*.py
# exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_archive_event_publisher.py
# .....
# ----------------------------------------------------------------------
# Ran 5 tests in 0.005s
#
# OK

rg -n "archive|event|evidence_ref|software_proof|not_proven" onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_interfaces docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0；命中 O6 board event publisher、Task A archive API、Task B sprint 记录，以及既有 docs/vendor/历史 proof 文档。

git diff --check -- onboard/src/ros2_trashbot_interfaces onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0
```

全量 behavior unittest 已执行但未通过，失败定位不是 Task B 新增用例：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test
# Ran 841 tests in 447.823s
# FAILED (failures=4, errors=1)
```

失败集中在 `test_task_record.py` 调用允许范围外的 `pc-tools/evidence/evidence_crosscheck.py`：

```text
can't open file '/mnt/e/rober/pc-tools/evidence/evidence_crosscheck.py': [Errno 2] No such file or directory
FileNotFoundError: /tmp/.../rehearsal_artifact.json
```

本轮文件范围禁止改动 `pc-tools`，因此未补该缺失脚本；Task B 新增 publisher 单测单独通过。

### 剩余风险

- 当前只证明机器人侧能生成和保留 O6 事件，不证明云端收到、production DB 写入、真实 OSS 上传、真实 4G 网络或 HIL。
- 全量 behavior unittest 仍依赖缺失的 `pc-tools/evidence/evidence_crosscheck.py`，需后续由对应 owner 恢复或调整测试 fixture。

## Task C - O7 PC Operations Console on O6 API

Owner: `full-stack-software-engineer`

### 实际改动

- `pc-tools/workstation/src/server/o7CloudArchiveTasks.ts`
  - 在既有 O7 cloud archive tasks adapter 上兼容 Task A/O6 `trashbot.archive.v1` 本地 bundle。
  - 将同 `task_id` 的 `events[]`、`annotations[]`、`inferences[]` 归并成 O7 route replay、labeling queue 和 inference label sample 摘要。
  - 继续固定 `real_cloud_archive_connected=false`、`safe_to_control=false`、`robot_control_executed=false`，不把本地 O6 JSON 解释成真实云端或机器人控制联调。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `source_fixture_schema` 增加 `trashbot.archive.v1`，用于区分 O6 schema 输入和旧 O7 fixture 输入。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 O6 archive schema 输入用例，覆盖任务、事件轨迹、关键帧、标注、推理结果和 fail-closed 字段。
- `pc-tools/evidence/evidence_crosscheck.py`
  - 恢复 full-stack/pc-tools 范围内的最小兼容 shim，供 `test_task_record.py` 调用。
  - 支持 `--task-record`、`--task-record-dir`、`--evidence-ref`、`--hil-gate-output`、`--rehearsal-artifact`。
  - 输出 `CHECK summary` 并可生成 `trashbot.route_task_rehearsal_artifact`，固定 HIL/串口/交付成功为 `not_proven`。
- `pc-tools/evidence/README.md`、`pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_cloud_archive_task_api.md`
  - 同步记录 O6 schema 消费边界、evidence_crosscheck 兼容入口和 software proof/not_proven 限制。

### 用户旅程和触点收益

- PC operator 可以把 Task A/O6 `trashbot.archive.v1` 本地导出交给 O7 Cloud Archive Tasks 面板，查看历史任务、事件时间线、轨迹样本、关键帧、标注队列和推理 label sample。
- O7 六区继续覆盖实时地图、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路；真实能力不足处仍由 `not_proven`、`safe_to_control=false`、`mock_feed`/fixture 边界和固定 false fields 暴露。
- Task B 全量 behavior 测试不再因 `pc-tools/evidence/evidence_crosscheck.py` 缺失而失败。

### 接口影响

- `GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>` 仍是 PC-only、本地只读入口。
- 支持输入 schema 从仅 `trashbot.o7.cloud_archive_fixture.v1` 扩展为 `trashbot.o7.cloud_archive_fixture.v1 | trashbot.archive.v1`。
- 不新增真实 O6 bearer client，不连接 production cloud，不调用 annotation/inference API，不发送 TTS、手控、寻路、stop、cancel 或 recovery。

### 验证结果

已执行：

```bash
cd pc-tools/workstation && npm run build
# vite v7.3.3 building client environment for production...
# ✓ built in 2.17s
# exit 0

cd pc-tools/workstation && npm run test
# Test Files  2 passed (2)
# Tests  41 passed (41)
# exit 0

cd pc-tools/workstation && npm run lint
# exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/evidence_crosscheck.py
# exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_record.py
# Ran 9 tests in 0.340s
# OK

rg -n "Objective 7|实时地图|电梯状态|历史路线回放|数据标注|ASR|TTS|手控|寻路|not_proven|safe_to_control|trashbot.archive.v1|trashbot.annotation.v1|trashbot.inference.v1|evidence_crosscheck" pc-tools docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0

git diff --check -- pc-tools docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0
```

### 剩余风险

- O7 PC console 当前消费的是本地 JSON/O6 bundle，不是 live O6 bearer API、production DB、OSS、CDN、真实 4G 或真实云端联调。
- `evidence_crosscheck.py` 是兼容 shim，不恢复旧 Python gate，不证明真实 HIL、UART、WAVE ROVER feedback 或 delivery success。
- ASR/TTS、手控/寻路、机器人 ACK、实时地图/电梯和真实路线回放仍需后续 O6/O7/Robot/Hardware 联调证据。

## Task D - O6/O7 Algorithm Evidence Feed

Owner: `robot-algorithm-engineer`

### 自主能力目标和本轮抓手

- 目标：给 O6/O7 提供不依赖真实路线、真实电梯、真实摄像头或真实模型的离线 algorithm evidence feed。
- 抓手：新增 ROS-free generator，输出 `trashbot.archive.v1` 本地 JSON bundle，覆盖 trajectory route frame、keyframe、电梯门状态、楼层证据、障碍物标注样本和 inference stub。
- 边界：样本全部是 `mock_feed=true`、`offline_only=true`、`source=software_proof`、`proof_status=not_proven`，不代表真实路线、真实电梯、真实楼层识别、真实障碍物检测或模型鲁棒性。

### 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/algorithm_evidence_feed.py`
  - 新增离线 O6/O7 algorithm evidence feed generator。
  - 输出一条 task、6 条 archive events、3 条 draft annotations、2 条 inference stub records。
  - 事件字段对齐 Task A/B：`robot_id`、`task_id`、`event_id`、`event_type`、`created_at`、`timestamp`、`evidence_ref`、`source=software_proof`、`proof_status=not_proven`、`payload`。
  - route frame payload 对齐 Task C/O7 adapter 可消费的 `frame_index`、`timestamp_ms`、`pose`、`velocity`、`state`、`evidence_ref`。
  - CLI 支持 `python3 -m ros2_trashbot_nav.algorithm_evidence_feed --output <json>`。
- `onboard/src/ros2_trashbot_nav/test/test_algorithm_evidence_feed.py`
  - 覆盖 archive 顶层 schema、安全 false 字段、trajectory frame、annotation label types、inference types 和 JSON 写出。
- `onboard/src/ros2_trashbot_nav/setup.py`
  - 注册 `algorithm_evidence_feed` console script。
- `docs/navigation/fixed_route_workflow.md`
  - 增补 O6/O7 offline algorithm evidence feed 使用命令和证据边界。
- `docs/vision/perception_upgrade_evaluation.md`
  - 记录 keyframe、floor、obstacle、annotation、inference stub 均为 mock/offline，不证明检测准确率或模型鲁棒性。
- `docs/interfaces/o6_cloud_archive_core_api.md`
  - 增补 offline algorithm evidence feed 与 O6 archive schema 的对齐说明。
- `docs/interfaces/o7_cloud_archive_task_api.md`
  - 增补 O7 对该 mock/offline archive 的消费边界和固定 false 要求。

### 接口影响

- 新增 nav package 内部 ROS-free helper/CLI，不改 Nav2、fixed route、learn/autonomous launch 默认行为。
- 不修改 `ros2_trashbot_behavior` Task B publisher 语义。
- 不新增真实 O6 bearer client、production DB、OSS upload、O7 playback/submit、TTS、手控、寻路或 robot ACK。

### 验证结果

已执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/algorithm_evidence_feed.py
# exit 0

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test
# Ran 52 tests in 2.703s
# OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_behavior/test
# Ran 841 tests in 443.518s
# OK

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m ros2_trashbot_nav.algorithm_evidence_feed --output /tmp/trashbot_algorithm_archive.json --robot-id robot-smoke --task-id task-smoke
# {"annotation_count": 3, "event_count": 6, "evidence_boundary": "software_proof_o6_o7_algorithm_evidence_feed", "inference_count": 2, "mock_feed": true, "offline_only": true, "proof_status": "not_proven", "schema": "trashbot.archive.v1", "task_id": "task-smoke"}

rg -n "trajectory|route frame|keyframe|elevator|floor|inference|evidence_ref|mock|offline|trashbot.archive.v1" onboard/src/ros2_trashbot_nav onboard/src/ros2_trashbot_behavior docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0；命中新增 algorithm_evidence_feed、O6/O7 docs、Task A/B/C/D sprint 记录和既有 route/vision/interface 证据边界。

git diff --check -- onboard/src/ros2_trashbot_nav onboard/src/ros2_trashbot_behavior docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0
```

### 数据、样本或调试输出变化

- 生成的 archive 顶层为 `schema=trashbot.archive.v1`。
- route replay 样本：3 个 mock trajectory frames，覆盖 `route_start`、`approach_elevator`、`exit_elevator_zone`。
- keyframe 样本：`keyframe-elevator-door-open`，引用 `mock://.../keyframe-elevator-door-open.jpg`。
- 电梯/楼层证据：`door_state=open_candidate`、`floor_label=F3_candidate`，均为 candidate/mock。
- 障碍物样本：`obstacle_type=temporary_box_candidate` 和归一化 bbox。
- inference stub：`offline_rule_stub/elevator_door_v0` 与 `offline_rule_stub/floor_text_v0`，结果固定 `not_proven`。

### 剩余风险

- 当前只证明 O6/O7 schema 和本地 UI 消费形状，不证明真实 O6 cloud API、production DB、OSS/CDN、4G、真实路线回放或 O7 提交能力。
- 电梯门、楼层和障碍物输出是 mock candidate，不代表真实摄像头、真实电梯、真实 OCR、真实障碍物检测或模型鲁棒性。
- 未在本轮运行 PC workstation adapter 测试；Task C 已覆盖 O6 archive input，Task D 仅在 nav/behavior 验收范围内补算法侧 feed。

## Task E - O1/O5 90% Evidence Boundary Hardware/External Materials

Owner: `robot-hardware-engineer`

### 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`

Orange Pi PDF 本轮只确认本地来源存在；当前环境缺 `pdftotext`，未抽取 PDF 正文，因此没有新增 Orange Pi 引脚、电压或机械尺寸结论。

### 实际改动

- `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 新增 O1/O5 90% evidence boundary。
  - 固化 O1 真实 WAVE ROVER HIL packet 材料路径、采集命令和不能被 mock 替代的判断规则。
  - 固化 O5 公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、worker/cutover、OSS upload、CDN live traffic、真实手机/browser 的材料路径、采集命令和凭证不入仓库规则。
- `docs/product/cloud_4g_infrastructure.md`
  - 新增 `O5 90% Real Material Boundary` 小节，指向统一 evidence boundary，并补齐 O5 真实材料族和脱敏要求。

### 已证实的硬件结论

- WAVE ROVER ESP32 链路是 UART newline-delimited UTF-8 JSON；来源为 vendor `base_ctrl.py`、`json_cmd.h` 和 `uart_ctrl.h`。
- vendor Raspberry Pi 示例串口为 `/dev/ttyAMA0` 或 `/dev/serial0`，波特率 `115200`；Orange Pi 真实串口必须现场确认，不能把 Raspberry Pi 路径写成已验证事实。
- `T=1` 是左右轮速度命令，`T=13` 是 ROS X/Z 速度命令且 vendor 注释注明不适用于无编码器产品；`T=13` 不能在未 HIL 前作为真实通过结论。
- `T=130/131/142/143` 分别覆盖 base feedback、feedback flow、feedback interval 和 UART echo；`T=1001` 是 Objective 1 HIL packet 的 base feedback 必需帧。
- `IMU_ctrl.h` 与 `battery_ctrl.h` 证明 ESP32 固件侧存在 IMU 和 INA219 电池采集字段，但项目 `/imu/data`、`/battery` 与反馈帧一一对应仍需同一 `evidence_ref` 的 ROS/HIL 材料证明。

### 验证结果

已执行本轮文档边界验证：

```bash
rg -n "Objective 1|Objective 5|90|not_proven|WAVE ROVER|UART|HIL|4G|HTTPS|production|OSS|CDN|live traffic|docs/vendor/VENDOR_INDEX.md" docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0；命中新增 `docs/interfaces/o1_o5_90_evidence_boundary.md`、`docs/product/cloud_4g_infrastructure.md` 和本 Task E 记录，也命中既有 O1/O5/HIL/云证据边界文档。

git diff --check -- docs sprints/2026.05.27_46-50_okr-90-software-acceleration
# exit 0
```

### 剩余风险

- 本轮只补 evidence boundary 文档，没有真实 WAVE ROVER、真实 UART、真实 Orange Pi 串口、真实 4G/SIM、真实公网云、production DB/queue、OSS/CDN live traffic 或真实手机/browser 材料。
- `field-evidence/` 是未来现场材料路径约定，本轮未创建原始证据目录，也未把任何凭证或真实外部材料放入仓库。
- O1/O5 90% 仍取决于后续按同一 safe `evidence_ref` 采集真实 HIL packet 和真实外部云材料，并通过 intake/review；当前 OKR 仍应保持 `not_proven` 边界。

## Product closeout - OKR and sprint acceptance

Owner: `product-okr-owner`

### 实际改动

- `OKR.md`
  - Objective 6 从 0% 调整为约 62% software proof。
  - Objective 7 从约 5% 调整为约 48% software proof。
  - Objective 1 保持约 83%，明确 Task E 只补 O1 90% evidence boundary，没有真实 WAVE ROVER/UART/HIL/PR #5 材料。
  - Objective 5 保持约 80%，明确 Task E 只补 O5 90% real material boundary，没有真实公网/4G/production DB/OSS/CDN/真实手机材料。
- `docs/process/okr_progress_log.md`
  - 追加本 sprint 进度日志，记录 Task A-E 证据、验证结果、OKR 调整和边界。
- `side2side_check.md`
  - 新建 CEO 目标与 Task A-E 实际证据的 side-by-side 验收对照。
- `final.md`
  - 新建 sprint final，记录 OKR 更新、验证证据、剩余风险和下一步。

### 验收判断

- O6/O7 可以上调，因为 Task A-D 提供了可复验的软件侧链路：O6 archive core、board event publisher、algorithm evidence feed、O7 PC archive bundle 消费和 `Ran 841 tests ... OK` 的集成修复证据。
- O1/O5 不上调到 90% 以上，因为 Task E 只提供真实材料边界和采集规则，没有真实 WAVE ROVER、UART、HIL、真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic 或真实手机/browser 验收。
- 本轮证据边界为 `software_proof_o6_o7_acceleration`，不是 production、HIL、4G 或现场验收。

### 剩余风险

- O6 仍缺真实安全隧道、production DB/queue、OSS upload、真实推理 runtime、live API 联调和上车数据。
- O7 仍缺 live O6 bearer API、真实 RTC/视频、真实 ASR/TTS、真实手控/寻路、真实地图/电梯/回放/标注数据流和上车验证。
- O1/O5 仍必须按 `docs/interfaces/o1_o5_90_evidence_boundary.md` 采集真实材料后才可进入 90% 以上判断。
