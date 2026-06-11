# PC Tools Workstation Product Boundary

## 定位

`pc-tools/workstation` 是 PC-only Node.js + Vue 工作站，也是 `pc-tools` 的主架构入口。它服务开发、调试、证据复盘、路线 JSON 摘要展示、Robot API 控制台 V1 只读状态聚合以及训练/标注准备，不服务普通手机用户，也不直接控制机器人。

CEO 最新要求是删除 `pc-tools` 下旧 Python。当前产品边界中，旧 Python 脚本、Python helper、Python unittest 和 Python gate 入口均不再作为 `pc-tools` 资产保留。必要的非 Python 材料保留为 README、JSON fixture 或 Node/Vue 工作站测试资产。

## 主架构

```text
pc-tools/workstation/
  src/App.vue                         # 全局状态、布局和页面组合
  src/client/workstationApi.ts        # /api/* client 与 query 参数拼接
  src/components/*.vue                # Route/Evidence/Training/Robot Control/Proof 页面组件
  src/server/index.ts                 # Express API 与静态 UI 托管入口
  src/server/catalog.ts               # Route Debug 响应聚合
  src/server/datasetAssets.ts         # Training/Labeling 本地资产只读清单
  src/server/evidenceAssets.ts        # Evidence JSON fixture 索引
  src/server/o7OperatorConsoleAcceptance.ts # O7 Console fail-closed acceptance guard
  src/server/o7OperatorConsole.ts     # O7 cloud-contract driven operator console draft
  src/server/o7LiveEndpointsManifest.ts # O7 live endpoints env-only readiness manifest
  src/server/o7CloudOperatorConsoleProbe.ts # O7 cloud runtime 本机回环 HTTP contract probe
  src/server/o7CloudArchiveTasksProbe.ts # O7 cloud archive tasks 本机回环 HTTP contract probe
  src/server/o7ConsumerReadAdapter.ts # O7 消费 O6 consumer read 的列表/详情 adapter
  src/server/o7RealtimeElevatorProbe.ts # O7 realtime/elevator snapshot 本机回环 HTTP contract probe
  src/server/o7LabelingPreview.ts     # O7-KR4 本地 fixture labeling 预览摘要
  src/server/o7CloudArchiveTasks.ts   # O7 KR3-KR6 本地 archive fixture 任务数据摘要
  src/server/o7RealtimeElevatorPreview.ts # O7-KR1/KR2 本地 fixture realtime/elevator 预览摘要
  src/server/o7RouteReplayPreview.ts  # O7-KR3 本地 fixture route replay 预览摘要
  src/server/o7SafeCommandPreview.ts  # O7-KR6 本地 fixture safe command 预览摘要
  src/server/o7VoicePreview.ts        # O7-KR5 本地 fixture ASR/TTS 预览摘要
  src/server/robotControlSummary.ts   # Robot API status/latest/readback 只读代理摘要
  src/server/waveRoverMaterialCoverage.ts # WAVE ROVER material coverage 只读扫描
  src/server/proofBoundary.ts         # Health、Training/Labeling、Proof Boundary 契约
  src/server/paths.ts                 # 仓库内路径和安全展示路径
  src/server/routeDebugLoader.ts      # 本地 route/status/task/reconciliation JSON safe summary
  src/shared/contracts.ts             # 前后端共享 fail-closed 契约
```

主技术栈：
- Node.js / Express API
- Vue / Vite UI
- TypeScript
- Vitest / ESLint / Vite build

前端分层约束：
- `App.vue` 只保留全局状态、刷新流程、错误处理和页面组合。
- `src/client/workstationApi.ts` 集中封装 `/api/*` 路径、fetch 和 route debug query 参数拼接。
- `src/components/` 只做展示与本地交互，不直接拼 API URL，不发明机器人状态。`RobotControlConsolePanel.vue` 通过 client 层调用 Node `GET /api/robot-control/summary` 和 O6 consumer detail adapter；Vue 不直接跨域访问上位机 Robot API。`O7FixturePreviewPanel.vue` 通过 client 层调用 fixture preview、probe、archive fixture 和 O6 consumer read adapter；route replay 主路径消费 consumer detail，旧 archive fixture player 只作为次路径 / debug fallback；页面不自动读取本地路径。

后端分层约束：
- `index.ts` 只挂载本地 PC API 和构建后的静态 UI，不挂载 ROS2、串口、控制或云端生产客户端。
- `catalog.ts` 只保留 Route Debug summary 聚合。
- `evidenceAssets.ts` 只索引 `pc-tools/evidence/fixtures/**/*.json`，不扫描或执行 `.py`。
- `datasetAssets.ts` 只读扫描 `pc-tools/training/` 和 `pc-tools/labeling/` 的本地数据集/标注资产，不执行训练、不上传数据、不写文件。
- `proofBoundary.ts` 集中输出 health 和 proof boundary。
- `routeDebugLoader.ts` 只读本地 JSON 并生成 safe summary；坏 JSON、缺文件、成功声明、控制声明、敏感复制和 evidence_ref 错配均 fail-closed。
- `o7RealtimeElevatorPreview.ts` 只读 query 指定的本地 `trashbot.o7.realtime_elevator_fixture.v1` JSON，并生成 `trashbot.o7.realtime_elevator_preview.v1` 安全摘要；坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/real realtime API/ROS2 /tf/latency <2s/route membership/elevator zone/real elevator state/elevator arrival/floor recognition/human takeover/robot control claim 均 fail-closed。
- `o7RouteReplayPreview.ts` 只读 query 指定的本地 `trashbot.o7.route_replay_fixture.v1` JSON，并生成 `trashbot.o7.route_replay_preview.v1` 安全摘要；坏 JSON、缺文件、unsupported schema、unsafe copy、success/control claim 均 fail-closed。
- `o7ConsumerReadAdapter.ts` 只允许本机 HTTP 回环 base URL，把 O6 `GET /api/o6/consumer/tasks` 和 `GET /api/o6/consumer/tasks/<task_id>` 压成 PC 端 `trashbot.pc_tools_workstation.o7_consumer_task_list.v1` / `trashbot.pc_tools_workstation.o7_consumer_task_detail.v1` 摘要；固定 `view=summary`、detail `include=trajectory,events,evidence,labeling,inference,tunnel`，递归扫描危险 true 字段，坏 URL、非回环、schema mismatch、fetch 失败或危险 true 字段均 fail-closed。detail 主路径优先使用远端 `trashbot.field_evidence_manifest.v1` 或已有 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1`；只有远端缺失 field evidence 且可选 query `fieldEvidenceManifestJson=<local-json>` 指向合法 `trashbot.field_evidence_manifest.v1` 时，才用本地 manifest 补齐 `field_evidence`，同时保持 `trajectory/events/evidence/labeling/inference/tunnel` 全部来自远端 O6 detail。本地 manifest 缺失、坏 JSON、顶层非 object、schema mismatch、unsafe copy 或危险 true claim 均 `fail_closed`。adapter 会把 `manifest_gate`、`artifact_status`、`not_proven`、`safe_to_control`、`delivery_success`、`primary_actions_enabled` 显式带到 O7 页面。
- `robotControlSummary.ts` 是 Robot Control V1 的唯一 Robot API 代理。它只接受 `baseUrl`，拒绝空值、非 HTTP、credentials、query/hash、非回环或非 RFC1918 局域网 host；白名单读取 `/api/status`、`/api/radar/status`、`/api/radar/scan-proof/latest`、`/api/map/proof/latest`、`/api/localize/proof/latest`、`/api/nav2/status`、`/api/nav2/proof/latest`、`/api/operator/report`、Camera/LiDAR/Base status/latest/readback 类 GET endpoint，并额外公开固定 POST 代理 `POST /api/robot-control/base/manual?baseUrl=...` 与 `POST /api/robot-control/base/stop?baseUrl=...`。这两个 POST 只能分别转发到上位机 `/api/base/manual` 与 `/api/base/stop`，不能拼任意路径，且所有响应继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。2026-06-11 本轮进一步把非 stop 点动升级为双门禁：`confirm_hil_checklist=true` 只是第一道门，Node 代理还必须在调用远端 `/api/base/manual` 之前短超时 GET 最新上位机 `/api/operator/report`，并从顶层或 `latest_result.operator_report` 的 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`，以及 `structured_hil_claims` 的 `external_video_recorded + external_video_ref`、`visible_content_proven + camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven + wheel_feedback_ref`、`physical_motion_lidar_delta_proven + scan_delta_ref` 得到完整现场材料；`real_route_map_proven` 只作为后续导航门禁材料，`delivery_success` 永远不作为 manual 放行条件。材料不足、fetch 失败、bad JSON、非 object 或危险 true 字段命中时，本机直接返回 HTTP 400 `command_rejected` / `failure_reason=operator_report_preflight_required`，响应带 `operator_report_preflight.missing_fields`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，并且不会调用远端 `/api/base/manual`。stop 仍可不经材料 gate 发送到固定 `/api/base/stop`，作为 fail-safe。Map lifecycle 也只开放固定代理：`GET /api/robot-control/map/list?baseUrl=...`、`POST /api/robot-control/map/start?baseUrl=...`、`POST /api/robot-control/map/save?baseUrl=...`、`POST /api/robot-control/map/reset?baseUrl=...`；它们只能分别转发到上位机 `/api/map/list`、`/api/map/start`、`/api/map/save`、`/api/map/reset`，POST body 只允许短 `map_name` 与 `artifact_path`，未知字段或超长字段直接本机拒绝。2026-06-11 新增现场材料提交固定代理 `POST /api/robot-control/operator/report?baseUrl=...`，只能转发到上位机 `/api/operator/report`；body 只允许 `operator_present`、`evidence_ref`、`physical_clearance_confirmed`、`emergency_stop_ready`、`observed_motion`、`observed_stop`、`reported_at`、`operator_notes`，以及 `structured_hil_claims` 内的 `external_video_recorded`、`external_video_ref`、`visible_content_proven`、`camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_ref`、`physical_motion_lidar_delta_proven`、`scan_delta_ref`、`real_route_map_proven`、`route_map_ref`、`delivery_success`、`site_state`。未知字段、错类型字段或顶层 `delivery_success/safe_to_control` 之类危险字段直接本机 400 拒绝，不透传给上位机。该 report 代理绝不调用 `/api/base/manual`、`/cmd_vel`、Nav2 goal、map/radar start，且响应顶层固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`；即使 `structured_hil_claims.delivery_success=true`，也只作为人工材料 claim 展示在高级诊断。代理采用端点级只读超时预算：`/api/status`、`/api/camera/health`、`/api/camera/devices` 使用更宽读取窗口，其他 proof/latest/readback 继续保持短超时；这样可以容忍真实上位机慢一点的状态聚合，同时不会放宽 URL 白名单、固定 endpoint 限制或危险字段扫描。它递归扫描 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`robot_control_executed=true` 等危险字段，命中即 blocked；map lifecycle 若观察到 `command_result.executed=true` 也会在 PC 响应中标记 blocked，但顶层 `robot_control_executed` 仍固定为 false。
- `o7LabelingPreview.ts` 只读 query 指定的本地 `trashbot.o7.labeling_fixture.v1` JSON，并生成 `trashbot.o7.labeling_preview.v1` 安全摘要；坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/submit/rollback/export claim 均 fail-closed。
- `o7SafeCommandPreview.ts` 只读 query 指定的本地 `trashbot.o7.safe_command_fixture.v1` JSON，并生成 `trashbot.o7.safe_command_preview.v1` 安全摘要；坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/dispatch/manual/navigate/keyboard/real command API/real robot ACK/robot control executed/ACK success/HIL or hardware verified claim 均 fail-closed。

`pc-tools/evidence/fixtures/**` 是 Evidence Tools 的 JSON fixture 来源。`pc-tools/route/` 只保留说明；Route Debug 的实际读取能力在 `pc-tools/workstation/src/server/routeDebugLoader.ts`。

## 功能入口

- Route Debug：通过 Node Route JSON Loader 读取本地 status/task/reconciliation JSON，生成 safe summary。
- Evidence Tools：索引 `pc-tools/evidence/fixtures/**/*.json`，展示 JSON fixture 资产分组。
- Hardware Materials：`GET /api/hardware/wave-rover/material-coverage` 扫描 `pc-tools/evidence/fixtures/wave_rover_*` 下的 WAVE ROVER 材料组，识别 `feedback_T1001.log`、项目侧 `odom_once.jsonl`、项目侧 `imu_once.jsonl`、项目侧 `battery_once.jsonl`、`operator_hil_report` / `operator_hil_report.json` 的 present/missing coverage，并在 Vue 面板中展示 `fixture_groups`、`gaps`、vendor source、串口参考、命令事实和 `not_proven_boundaries`。兼容旧路径 `GET /api/tools/hardware-materials`，但新 UI 入口使用前者。
- Training/Labeling：`GET /api/tools/training-labeling` 扫描 `pc-tools/training/` 和 `pc-tools/labeling/` 下的非 Python 资产，返回两个工作区的 roots、asset counts、manifest candidates、image/annotation counts、readiness、missing requirements 和 next actions；仍明确未接真实训练或标注流水线。
- Robot Control：`RobotControlConsolePanel` 是工作站默认首屏，不再藏在 `WorkstationTabs` 内。`GET /api/robot-control/summary?baseUrl=<robot-api-base-url>` 继续作为状态入口，路线、O7 控制台、预览、证据、硬件、数据和安全边界等工程 tab 统一下沉到默认关闭的 `高级工具`。2026-06-11 10:30 按用户反馈锁定普通用户简易首屏：首屏标题必须是 `Rober 小车控制台`，首屏只保留“小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航”五个简单卡片和一个短地址输入，普通动作只保留“连接/刷新、打开/关闭画面、刷新雷达、刷新地图、地图列表、停止”。首屏默认可见作用域为 `.simple-user-console`，前端测试会断言该作用域不出现 `检查路径`、`现场材料`、`HIL`、`Nav2`、`proof`、`key values`、`/cmd_vel`、`/api/base/manual`、`可点动`、`task_id`、`O6`、`O7`、`Mock`、`field manifest`。工程入口仍保留在默认关闭的 `高级诊断` / `高级工具` 中，供调试和验收复核使用。`task_id`、O6 base URL、Mock/field manifest、peer/ICE/SDP、readback table、O3 proof summary、route replay、map lifecycle HTTP 细节、raw evidence/readback、非 stop 点动、速度/时长输入、HIL checklist、检查路径、导航目标预检、定位重置、保存地图和 proof flags 都收进默认关闭的 `高级诊断`。`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false` 不再作为首屏视觉焦点；控制安全边界、后端合同和 fail-closed 字段不变。Robot API base URL 只交给 Node 代理；Vue 不直连上位机。O6 consumer detail 仍通过既有 `GET /api/o7/consumer-read/tasks/<task_id>` adapter 获取 trajectory/events/evidence/labeling/inference/tunnel 摘要，本地 field manifest 只作为显式 Mock/field evidence fallback。首屏的 `地图` 卡片现在只有“刷新地图 / 地图列表”和短状态；`save/start/reset` 不进入普通用户首屏，其中 `保存地图` 只在高级诊断中保留，`start/reset` 只以“受控/高级，禁用”呈现。首屏的 `移动/导航` 卡片只保留普通状态和 `停止`，不显示自动导航、最近证据摘要、方向点动、路径检查、速度上限、时长上限或 HIL checklist。当前受控点动 V1 只支持一次性低速短时 jog，不支持自动导航、键盘连续控制或地图点击目标。2026-06-11 新增 `/api/operator/report` 结构化 HIL 材料 readback：summary 会把 `operator_report_latest` 顶层现场确认和 `structured_hil_claims` 压缩成 `operator_hil_material_summary`，仅在默认关闭的 `高级诊断` 中展示 operator_present、physical_clearance、emergency_stop、外部视频、相机可见、轮速反馈、LiDAR delta、route/map、delivery claim、site_state、evidence_ref 和 report status。同区块新增“现场 HIL 材料”高级提交表单，允许现场人员填写 evidence_ref、site_state、外部视频 ref、相机 artifact ref、feedback ref、scan delta ref、route/map ref、operator notes 和若干 checkbox，然后通过 `提交现场材料（高级）` 走 workstation 固定 POST 代理提交给真实上位机。提交成功后页面自动刷新 Robot Control summary，并在高级诊断显示最近 submit 的 proxy status、HTTP、failure、rejected fields、dangerous fields 和 request claims。该表单不进入 `.simple-user-console` 首屏，首屏不得出现 HIL、delivery_success、structured_hil_claims、外部视频、轮速反馈等工程词。只有 `operator_report_latest` readback 中的精确人工 claim 路径（含真实上位机回显的 `latest_result.operator_report.structured_hil_claims.delivery_success`）不触发 hard-block；其它 endpoint/payload 伪造 `structured_hil_claims.delivery_success=true`，或任何非 claim 路径的 `delivery_success=true`、`hil_pass=true`、`safe_to_control=true` 仍然 fail-closed。
- Robot Control Base Manual/Stop V1：workstation 新增 `POST /api/robot-control/base/manual?baseUrl=<robot-api-base-url>` 与 `POST /api/robot-control/base/stop?baseUrl=<robot-api-base-url>` 两个固定代理。manual 只允许 `forward/back/left/right` 四个方向，Node 代理与前端同时对 `direction`、`speed`、`duration_ms` 做白名单和 clamp；本轮 UI/代理统一上限为 `speed<=0.12 m/s`、`duration<=800 ms`。非 stop 方向必须同时带 `confirm_hil_checklist=true` 且通过 Node 侧最新 `/api/operator/report` 现场材料 preflight 才允许转发；stop 允许在未勾 checklist、材料缺失时单独发送，作为 fail-safe 路径。无论上位机响应成功、失败还是超时，workstation 都不会把 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 或 `robot_control_executed` 置 true，也不会把这轮交付解释成 HIL pass。Manual/stop 代理响应现在会自动附带运动证据快照摘要：`evidence_capture_status=captured|partial|blocked`、`evidence_capture_endpoints`、`before_readback`、`after_readback`、`motion_evidence_summary` 和 `evidence_capture_blocked_reasons`；manual 还会附带 `operator_report_preflight`，记录 `/api/operator/report` 的 HTTP、report status、evidence ref、缺失字段和危险字段。该采集只在代理内部读取固定 GET endpoint：`/api/base/status`、`/api/base/feedback-samples/latest`、`/api/radar/status`、`/api/radar/scan-proof/latest`，分别在主请求或本地拒绝前后各读一次；不新增任意 GET/POST 透传能力。单个 endpoint 失败时主 manual/stop 结果仍按原规则返回，证据状态降级为 `partial` 或 `blocked`，高级诊断展示 before/after 短 readback，普通首屏不展示这些工程证据字段。
- Robot Control Base HIL Boundary：本轮真实联调边界只允许对真实上位机 `http://192.168.1.11:8787` 做材料不足的 no-motion reject 或 stop 类安全动作，包括 `POST /api/robot-control/base/stop?...`；禁止通过 workstation 向真实上位机发送 `forward/back/left/right` 的非零运动。该边界与硬件事实一起受本地 vendor 资料约束：`docs/vendor/VENDOR_INDEX.md` 指向的 `base_ctrl.py`、`config.yaml`、`json_cmd.h` 说明 WAVE ROVER 上下位机链路是 UART newline-delimited JSON，vendor Raspberry Pi 默认 `/dev/ttyAMA0 @ 115200`、备选注释 `/dev/serial0 @ 115200`；项目上车 Orange Pi 的实际串口设备必须现场确认，不能在 PC 或上车默认中硬编码 Raspberry Pi 路径。workstation 只消费上位机 HTTP API，不直接操作 UART、串口、GPIO 或 WAVE ROVER ESP32。
- Robot Control Radar/Map Proof Refresh V2：`Robot Control` tab 现在已经接入 Radar/Map proof refresh surface，用来刷新 `GET /api/radar/status`、`GET /api/radar/scan-proof/latest`、`POST /api/radar/scan-proof/refresh`、`GET /api/map/proof/latest`、`POST /api/map/proof/refresh` 的只读证据窗口。Radar refresh 固定通过 Node 代理向上位机 `POST /api/radar/scan-proof/refresh`，默认 body 是 `{ timeout_s: 20, runtime_warmup_s: 15, start_runtime: true }`；Map refresh 固定通过 Node 代理向上位机 `POST /api/map/proof/refresh`，默认 body 是 `{ timeout_s: 45 }`。Radar refresh 的长 warmup 是真实冷启动稳定性修正，用于等待 LiDAR driver、`/scan`、raw packet、scan hz 和 TF 同时进入 no-motion 证据窗口；它不允许前端传自定义参数，不改变 `docs/vendor/VENDOR_INDEX.md` 指向的 vendor/hardware facts。Radar refresh 只刷新 LiDAR/TF/no-motion scan proof snapshot，典型可见字段是 `scan_once_observed`、`scan_hz_observed`、`raw_packet_once_observed`、`tf_observed` 和 `blocked_reasons`；Map refresh 只刷新 no-motion map proof snapshot，典型可见字段是 `map_once_observed`、`map_file_observed`、`map_metadata_observed` 和 `blocked_reasons`。两个 refresh 允许出现 `sends_commands=true`、`starts_ros2=true` 这类非运动 evidence helper 结果，但首屏只显示“刷新雷达/刷新地图”和短状态；`scan/tf`、`map/evidence`、`latest_readback_key_values`、`non_motion_evidence_actions`、`hard_dangerous_true_fields`、`last refreshed time` 和 blocked reasons 都收进高级诊断区。它仍然不会打开 `/cmd_vel`、`/api/base/manual`、Radar start、Map start、Nav2 goal、keyboard control 和 map click goal；动作结束后会自动回刷 Robot Control summary。只有 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`command_dispatch_enabled=true`、`manual_control_enabled=true`、`navigate_goal_enabled=true`、`keyboard_control_enabled=true`、`robot_control_executed=true`、`sends_motion_commands=true`、`sends_base_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`opens_base_uart=true`、`uses_base_uart=true`、`hil_pass=true` 等硬危险 true 字段才会 fail closed。
- Robot Control Radar Start/Stop Controls V1：`Robot Control` tab 现在在默认关闭的 `高级诊断` 雷达详情区提供 `启动雷达（高级）` 和 `停止雷达（高级）` 两个按钮。PC 后端新增固定代理 `POST /api/robot-control/radar/start?baseUrl=<robot-api-base-url>` 与 `POST /api/robot-control/radar/stop?baseUrl=<robot-api-base-url>`，分别只转发到上位机 `/api/radar/start` 与 `/api/radar/stop`；浏览器 body 被忽略，上位机请求 body 固定 `{}`，不提供任意 endpoint 或任意参数透传。响应合同固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，并展示 `action`、`remote_endpoint`、`remote_http_status`、`command_result.mode`、`command_result.executed`、`command_result.ok`、`failure_reason`、`blocked_reasons` 和 `hard_dangerous_true_fields`。雷达 lifecycle 中 `sends_commands=true` 可表示传感器控制需要，不自动判定为硬危险；但任何 `sends_motion_commands=true`、`sends_base_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`uses_base_uart=true`、`safe_to_control=true`、`robot_control_executed=true` 等底盘/运动/安全字段都会让 PC 代理 fail closed。首屏雷达卡仍只保留 `刷新雷达` 和短状态，不出现启动/停止雷达按钮。2026-06-11 真实上位机已配置 `ROBER_RADAR_START_COMMAND` / `ROBER_RADAR_STOP_COMMAND` 到 LiDAR-only lifecycle 脚本，PC 高级雷达入口可消费真实 start/stop lifecycle：`POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787` 与 stop 返回 `lifecycle_forwarded`，`command_result.executed=true`、`ok=true`；这仍只证明雷达 runtime lifecycle 可控，不等于运动、Nav2 或 delivery proof。
- Robot Control Nav2 No-Motion Planning Check V1：`Robot Control` tab 的 `高级诊断 -> Nav2 规划详情` 保留 `检查路径（高级）`，用来触发 PC 后端固定代理 `POST /api/robot-control/nav2/proof/refresh?baseUrl=<robot-api-base-url>`。该代理只能转发到上位机固定 `/api/nav2/proof/refresh`，浏览器只提供 `baseUrl`，请求 body 由 Node 固定生成：`timeout_s=30`、`managed_runtime_opt_in=true`、`managed_timeout_s=30`、`managed_map_yaml=/root/rober/onboard/runtime/maps/trashbot_map.yaml`、`initialpose_opt_in=true`、`initialpose_x/y/yaw=0`、`path_generation_opt_in=true`、`path_generation_timeout_s=30`、`path_goal_frame_id=map`、`path_goal_x=0.8`、`path_goal_y=0`、`path_goal_yaw=0`。30s 是 clean-baseline direct Robot API 在同一 no-motion contract 下实测稳定窗口：20s 首轮可能 timeout，30s 可 fresh pass，观测到 `path_generated=true`、`path_point_count=31`、`root_causes=[]`。workstation fetch timeout 仍按固定 body 加余量计算并受 `timeout_cap_ms=90000` 封顶，避免无限等待。该入口只证明 managed no-motion 路径规划检查结果，不调用 `/api/nav2/start`、`/api/nav2/stop`、NavigateToPose、map click goal、keyboard control、`/cmd_vel` 或 `/api/base/manual`，也不打开底盘 UART。上位机可返回 `starts_ros2=true` 表示 proof helper 拉起 ROS2 证据 runtime，但必须保持 `starts_nav2=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。如果上位机返回 `path_generated=true` 或 `path_generation_succeeded=true`，普通首屏仍只显示移动/导航短状态和 `停止`；`latest_readback_key_values`、blocked reasons、hard dangerous fields、last refresh time 和 `/api/nav2/proof/refresh` 细节只在高级诊断展示。即使路径可生成，PC 响应顶层仍固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`；如果上位机返回 `starts_nav2=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`safe_to_control=true`、`robot_control_executed=true` 等硬危险 true 字段，PC 代理必须 fail closed。
- Robot Control Map Lifecycle Controls V1：`Robot Control` tab 现在接入固定 map lifecycle 代理，用来读取和触发上位机已有的 map lifecycle endpoint。PC 后端新增 `GET /api/robot-control/map/list?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/map/start?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/map/save?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/map/reset?baseUrl=<robot-api-base-url>`，分别固定转发到上位机 `/api/map/list`、`/api/map/start`、`/api/map/save`、`/api/map/reset`；不提供任意 endpoint。POST body 只允许 `map_name`、`artifact_path` 两个短文本字段，未知字段、非 object、超长或包含危险字符的字段都被本机拒绝。响应合同固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，并输出 `action`、`remote_http_status`、`map_count`、`map_names`、`command_result.mode`、`command_result.executed`、`failure_reason`、`blocked_reasons` 和 `hard_dangerous_true_fields`。首屏地图卡片只提供“刷新地图 / 地图列表”和短状态；`保存地图` 在高级诊断中保留，命令未配置时预期消费上位机 software guard，不伪造地图产物；`start/reset` 只在高级诊断以 disabled 受控按钮展示。本轮真实 smoke 边界只允许 `map/list` 和 guarded `map/save`，禁止执行真实 `map/start`，也禁止任何底盘运动、`/cmd_vel` 或 `/api/base/manual`。
- Robot Control Camera Preview V1：既有 `Robot Control` tab 现在包含真实摄像头实时图传观察面，但首屏已经收回到普通用户可读的简易风格，只显示“打开画面/关闭画面”和一句简单状态；`peer_id`、`ICE`、`SDP`、`cleanup` 和会话细节都收进 `<details>`。Node 侧新增 `POST /api/robot-control/camera/offer?baseUrl=<robot-api-base-url>` 和 `POST /api/robot-control/camera/peers/:peerId/close?baseUrl=<robot-api-base-url>`，继续复用 Robot Control 的 `baseUrl` 安全围栏：仅允许 HTTP、loopback/RFC1918、拒绝 credentials/query/hash，并且只允许这两个固定 camera 路径，响应也只保留 `schema/status/peer_id/answer/error` 安全摘要，同时固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。真实上位机当前返回的是顶层 `type/sdp/peer_id` answer，workstation proxy 已兼容这一真实 contract，同时保留对设计稿中嵌套 `answer` 形态的兼容。前端必须由用户显式点击 `打开画面` / `关闭画面` 触发，默认 `preview_status=idle_not_started`，页面初始不自动建会话；打开时创建 `RTCPeerConnection`、只申请 `recvonly video` transceiver、`setLocalDescription` 后等待 `iceGatheringState=complete` 或短超时，确保非 trickle 的上位机 offer SDP 内包含 host candidates，再通过 Node offer proxy 完成 offer/answer；收到远端 video track 后优先绑定 `RTCTrackEvent.streams[0]` 到带 `data-testid="robot-camera-preview-video"` 的 `<video>`，再主动调用 `play()`，并在高级诊断展示真实 video 元素的 `srcObject`、`readyState`、`videoWidth/videoHeight`、`presentedFrames` 或 `requestVideoFrameCallback` 状态。关闭、切换 `baseUrl`、重复打开和组件卸载时都先 cleanup 旧 peer。页面持续展示 `preview_status`、`failure_reason`、`peer_id`、video track/ICE 状态、video 元素绑定/帧状态、`last_offer_at`、`last_stop_at` 和 `cleanup_status`；若打开失败，最终状态保留 `start_failed`，不会被 cleanup 覆盖成 `stopped_by_user`。真实 browser smoke 不能再只用 `preview_status=streaming` 或 `video_track_state=live` 判定通过，必须采集 `data-testid="robot-camera-preview-video"` 的 `srcObject != null`、`readyState >= 2`、`videoWidth/videoHeight > 0` 或 frame callback/canvas pixel 证据，并可用远端 `/api/camera/health` 的 `remote_sdp_candidate_count>0`、`frames_read>0` 辅助解释。该范围明确不包含 cloud relay、TURN/STUN、音频、录制、截图归档或任何运动控制放开；即使图传成功，`/api/base/manual`、`/cmd_vel`、Nav2 goal、radar start、map start、keyboard control 和 map click goal 仍保持 disabled，且 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 不变。当前 run 已有两类真实 smoke：一是 `/api/camera/health` ready、`/api/camera/devices` 返回设备列表，证据保存在 `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/remote_camera_health_devices_2026-06-10.txt`；二是板端 `aiortc` self-test 通过上位机 `/api/camera/offer` 收到 `answer`、获取真实 `640x480` 视频帧、并经 `/api/camera/peers/{peer_id}/close` 把 active peers 从 `1` 回收至 `0`，证据保存在 `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/remote_aiortc_offer_frame_close_2026-06-10.json`。2026-06-11 的 PC 页面真实上位机 smoke 已补到浏览器可见帧级别，证据保存在 `sprints/2026.06.11_07-50_pc_camera_visible_frame_proof/artifacts/browser_camera_visible_frame_state.json`；Stop 后必须继续用 `/api/camera/health` 读回 `active_peer_connections=0`。
- Robot Control Camera Visible Content 2026-06-11 10:15：PC 页面 WebRTC 图传链路已证明可打开、可播放、可关闭并回收 peer，但真实画面仍近黑。本轮 Chrome 隔离浏览器通过 workstation Node proxy 连接 `http://192.168.1.11:8787`，`<video>` 状态为 `srcObject=true`、`readyState=4`、`videoWidth=640`、`videoHeight=480`，canvas `320x240` 采样为 `meanGray=1`、`nonBlackPixelsGt10=0`，video 区域截图仍为黑场；关闭后上位机 `/api/camera/health` 回到 `active_peer_connections=0`。因此 PC 普通首屏仍保持“打开画面/关闭画面”的简易入口，不新增工程词或控制入口；当前风险归因写为物理输入侧待现场处理，而不是 PC proxy、WebRTC、video 元素或服务 auto 选源的软件问题。
- O7 Operator Console：`GET /api/o7/operator-console` 返回 `trashbot.o7.operator_console.v1` cloud-contract draft，展示 O7 六个 KR 的最小视图：实时地图/机器人位置、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路。该入口的 `contract_source` 指向 `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`，状态固定为 `draft_blocked_not_proven` / `observe_only`，PC 不直连小车，不发送命令，不声明真实成功。O7 Console 现在同时展示 `realtime_map_snapshot`、`elevator_state_snapshot`、`route_replay_snapshot`、`labeling_queue_snapshot`、`voice_asr_tts_snapshot`、`safe_command_snapshot` 和 `board_media_preflight_summary`，让 operator 看到 map_ref、map frame、pose freshness、route membership、电梯状态链、楼层证据、人工接管原因、历史回放 task selector、selected task、trajectory frame count/sample、playback cursor/status、keyframe/evidence refs、state transition gaps、标注 review queue、selected item、label schema、allowed label types、draft labels、submit/rollback audit、dataset export 缺口、ASR stream status、partial/final transcript 槽位、TTS draft/voice profile、speaker dispatch/ACK/audit 缺口、手动转向 envelope、velocity/steering limits、navigate goal envelope、map goal slot、cloud command endpoint、idempotency key、confirmation policy、robot ACK status、timeout/cancel/stop/recovery evidence gaps 以及板端 RTC/摄像头/音频/ASR/TTS/on-robot media smoke 缺口，但仍不能替代真实上车 smoke、真实 ROS2 `/tf`、真实地图、真实电梯、真实历史任务归档、真实逐帧回放、真实标注队列、真实标注提交/回滚、真实训练集导出、真实 ASR 输入流、真实 TTS 播放、真实 speaker ACK、真实云端 voice API、真实 safe command API、真实 robot ACK、真实手控/键盘/寻路、真实 cancel/stop/recovery、真实底盘安全或 <2s 延迟证明。PC 的 realtime/elevator probe 也可以指向板端 operator gateway 回环 `GET /api/o7/realtime-elevator/snapshot`，此时只读取 board HTTP snapshot 中的 `/amcl_pose` 摘要；`local_ros_pose_topic_connected=true` 不等于 cloud production、ROS2 `/tf`、地图、电梯或控制链路已接通。
- O7 Live Endpoints Manifest：`GET /api/o7/live-endpoints/manifest` 返回 `trashbot.o7.live_endpoints_manifest.v1`，只读取 PC 后端进程环境变量并生成 O7-KR1..KR6 未来真实 API 的配置 readiness。当前 env 名称为 `O7_RTC_REALTIME_URL` / `O7_RTC_REALTIME_TOKEN`、`O7_CLOUD_ARCHIVE_URL` / `O7_CLOUD_ARCHIVE_TOKEN`、`O7_ROUTE_REPLAY_URL` / `O7_ROUTE_REPLAY_TOKEN`、`O7_ANNOTATION_API_URL` / `O7_ANNOTATION_API_TOKEN`、`O7_VOICE_API_URL` / `O7_VOICE_API_TOKEN`、`O7_SAFE_COMMAND_API_URL` / `O7_SAFE_COMMAND_TOKEN`。URL 只展示 `protocol://host/path`，不展示 query、hash、用户名或密码；token 只展示 `present` / `absent`。URL 含 credentials、query 或 hash 时 capability 标记为 `blocked` 且 `display_url=blocked_unsafe_url`；未配置 env 时 6 个 capability 都是 `not_configured`、`proof_status=not_proven`。该入口固定 `env_only=true`、`network_probe_executed=false`、`sends_commands=false`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`reads_hardware=false`、`token_values_exposed=false`、`url_query_hash_credentials_exposed=false`，并通过 `required_live_evidence` / `remaining_real_capability_gaps` 明确仍缺真实 RTC/视频、实时 pose、云归档、路线回放、标注提交、ASR/TTS、safe command API、robot ACK 和硬件安全证据。O7 Previews 页面只提供 `Load live endpoints manifest` 手动加载按钮，不提供 ping/connect/send/test command 类按钮。
- O7 RTC Signaling/Media Contract：机器人/云 relay 侧新增 `GET /api/o7/rtc-signaling/contract`，返回 `trashbot.o7.rtc_signaling_contract.v1` 静态 fail-closed 合同，作为 PC 后续 probe 和板端 RTC 对接的协议入口清单。它不读取 PC env 或 relay env token，不执行网络探测，不创建 WebRTC session，不读取硬件，不发送命令；固定 `source=software_proof`、`proof_status=not_proven`、`network_probe_executed=false`、`webrtc_session_created=false`、`media_transport_connected=false`、`video_track_received=false`、`realtime_pose_stream_connected=false`、`real_ros2_tf_connected=false`、`safe_to_control=false`、`sends_commands=false`、`reads_hardware=false`、`robot_control_executed=false`、`delivery_success=false`。合同只列出后续真实打通所需的 signaling endpoint、session/idempotency、offer/answer、ICE candidates、video/audio tracks、pose/elevator realtime events、credential handling、observability/evidence refs、failure/timeout semantics 和 forbidden actions；不得把该 endpoint 解释成 RTC/视频/ROS2 `/tf` 已通。
- O7 RTC Signaling Contract Probe：PC workstation 新增 `GET /api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>`，O7 Previews 页面新增手动 “RTC signaling contract probe” 面板。probe 只接受本机 HTTP 回环 `127.0.0.1` / `localhost` / `[::1]`，拒绝非 HTTP、非回环、credentials、query 和 hash；后端只拉取远端 `/api/o7/rtc-signaling/contract`，校验 schema `trashbot.o7.rtc_signaling_contract.v1`，递归扫描 `network_probe_executed`、`webrtc_session_created`、`media_transport_connected`、`video_track_received`、`real_ros2_tf_connected`、`sends_commands`、`reads_hardware`、`safe_to_control` 等危险 true 字段，命中即 `fail_closed`。响应只展示 remote schema、contract status、核心 false fields、protocol surface keys、required evidence refs、blocked/not_proven 和 dangerous true fields，不透传 token/auth/URL/credential-bearing payload。该入口固定 `network_probe_executed=false`、`connects_cloud_production=false`、`sends_commands=false`、`reads_hardware=false`，只是 HTTP contract probe，不证明真实 WebRTC/视频/ROS2 `/tf` 或 RTC media transport。
- O7 Cloud Operator Console Probe：`GET /api/o7/cloud-operator-console-probe?baseUrl=<url>` 由 PC Node 后端只读拉取指定回环 base URL 下的 `/api/o7/operator-console`，返回 `trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1`。允许的 base URL 仅限 `http://127.0.0.1`、`http://localhost`、`http://[::1]`；未提供、非 HTTP、非回环、带 credentials/query/hash、fetch 失败、schema 错误、返回体非 object 或危险字段为 true 都 fail-closed。UI 只展示 probe status、source base URL、remote schema、cloud API status、operator mode、KR ids、关键 false fields、blocked reasons 和 not proven；不提供 Bearer 输入框，不连接公网云或生产云，不发送命令，不读取硬件，不证明 4G、机器人在线或 O7 完成。
- O6 Cloud Archive API：`POST /api/o6/archive/tasks`、`GET /api/o6/archive/tasks` 和 `GET /api/o6/archive/tasks/<task_id>` 暴露 `trashbot.o6.cloud_archive.v1` 的本地 file-backed mock store，路径由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 环境变量注入，未设置时回落到临时目录默认文件。该接口只接受 `robot_id`、`task_id`、`started_at_ms`、`finished_at_ms`、`trajectory_frames[]`、`events[]` 和可选 `evidence_refs[]`，duplicate `task_id` 采用 idempotent upsert；坏 JSON、缺字段、数组过大、unsafe copy、`Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / credentials URL 都 fail-closed。响应固定 `source=local_mock_archive`、`real_cloud_db_connected=false`、`real_oss_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`，只提供 O6-shaped 数据源，不证明真实云数据库或 OSS 已接通。O7 以后可以把历史任务 / route replay / labeling / voice / safe command 继续消费这条 O6-shaped 数据，但这不等于 O7 已经连上真实 O6。
- O6 Consumer Read API：`GET /api/o6/consumer/tasks` 和 `GET /api/o6/consumer/tasks/<task_id>` 是当前推荐给 PC/后续手机消费的统一查询面。它在 relay 后端复用同一个 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`，把 archive task、events、evidence refs、labels、`model_inference.*` timeline 和 tunnel latest known snapshot 聚合成 `trashbot.o6.consumer_read.v1` 读模型，支持 `view=summary` 与 `include=trajectory,events,evidence,labeling,inference,tunnel`。PC 读历史任务、详情、轨迹、事件、打标状态和 tunnel 在线态时应优先走这两个 endpoint，而不是在前端重复 join 多条 `/api/o6/archive/*`、`/api/o6/tunnel/*`。该接口仍固定 `proof_status=not_proven`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`；`selected` 只是 store 单选标记，不等于 UI 用户选择；`tunnel_status` 明确是 latest known robot snapshot，不是 task 内历史事实；没有 labels / inference / tunnel 时必须显式返回 `pending`、`absent`、`blocked_not_proven` 等 fail-closed 摘要，不得伪造“真实没有异常”。
- O7 Consumer Detail Route Replay：O7 Previews 的 `O7 consumer read primary path` 现在把历史回放主路径切到 PC 后端 `GET /api/o7/consumer-read/tasks` 和 `GET /api/o7/consumer-read/tasks/<task_id>` adapter。operator 加载 task list 后选择 task，可选填写 `Local field evidence manifest JSON`，再加载 detail；UI 直接展示 `trajectory / events / evidence / labeling / inference / tunnel_status` 摘要，以及 local manifest query、field evidence contract/input/fail-closed reason。本地 manifest fallback 只补 `field_evidence`，不得覆盖远端 trajectory/events/evidence/labeling/inference/tunnel；远端已有合法 field evidence 时优先远端。`Consumer-detail route replay player` 的 Play/Pause、Previous/Next、Reset 和 range cursor 只改浏览器内存，不调用 API、不写后端、不发送机器人命令；缺 detail、unknown task、task id mismatch、轨迹缺失、blocked/not_proven/error/cancel 状态或 adapter fail-closed 时禁用导航并显示 blocker。`Consumer-detail trajectory minimap` 只使用 detail 样本中的有限数值型 `x_m/y_m` 归一化到固定 SVG viewBox；没有有效点时显示 `blocked_not_proven`，单点只显示 `readonly_consumer_detail_trajectory_single_point`，不声明真实地图或真实机器人位置。旧 `Cloud Archive Tasks` fixture route replay player 仍保留，但其 cursor 与 consumer 主路径 cursor 隔离，只作为次路径 / debug fallback。
- O6 Event Evidence Archive API：`POST /api/o6/archive/events`、`GET /api/o6/archive/events`、`POST /api/o6/archive/evidence`、`GET /api/o6/archive/evidence` 在同一个 O6 file-backed local/mock store 上补齐任务内增量 timeline。events 只允许附着已有 task，幂等键为 `task_id + event_id`，成功响应固定 `schema=trashbot.o6.archive_events.v1`、`source=local_mock_event_archive`、`archive_event_written=true`、`real_cloud_db_connected=false`、`real_oss_connected=false`、`safe_to_control=false`、`delivery_success=false`。evidence 只保存 `evidence_ref` basename 摘要，不保存图片/视频/音频原始内容，幂等键为 `task_id + evidence_id`，成功响应固定 `schema=trashbot.o6.archive_evidence.v1`、`source=local_mock_evidence_archive`、`archive_evidence_written=true`、`real_oss_upload_success=false`、`real_cloud_db_connected=false`、`real_oss_connected=false`、`safe_to_control=false`、`delivery_success=false`。GET 支持 task/robot/type/time/limit 过滤并只返回白名单字段；bad JSON、非对象、缺字段、数组过大、`unknown_task`、`unauthorized_task`、非法类型、越过 task 时间窗、unsafe content、真实能力声明和非法 query 都 fail-closed。PC 后续只能把这些数据作为 route replay、failure review、labeling seed 和 evidence timeline 的本地 mock 输入，不得解释成真实 OSS 上传、真实云数据库、真实生产云、真实机器人控制或真实现场采集成功。
- O6 Tunnel Online Status API：`POST /api/o6/tunnel/heartbeat`、`GET /api/o6/tunnel/robots` 与 `GET /api/o6/tunnel/robots/<robot_id>` 提供上位机隧道心跳 + 在线/离线状态快照的 local/mock 入口。该链路复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`，只读 `tunnel_provider` / `endpoint`（已脱敏） / `ttl_seconds` / `metadata`。`status` 与 `offline` 语义按 `now <= last_seen_at_ms + ttl_seconds*1000` 计算。固定响应 boundary 保留 `schema=trashbot.o6.tunnel_status.v1`、`source=local_mock_tunnel_status`、`proof_status=not_proven`、`real_tunnel_connected=false`、`real_4g_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`safe_to_control=false`。
- O6 Cloud Archive Labeling API：`POST /api/o6/archive/labels`、`GET /api/o6/archive/labels`、`GET /api/o6/archive/labels/<task_id>` 为 O7 标注前置链路提供 local/mock 写入与查询。`task_id + item_id + label_type` 为幂等键，必须依托已有 `archive task`，`robot_id` 与 task 不一致返回 `unauthorized_task`，不存在返回 `unknown_task`。`POST` 支持 idempotent upsert，`GET /api/o6/archive/labels` 提供任务级摘要（pending/partial/labeled），`GET /api/o6/archive/labels/<task_id>` 返回单 task itemized labels 与 task status。固定边界字段：`schema=trashbot.o6.archive_labeling.v1`、`source=local_mock_labeling`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`、`real_dataset_export_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`，并保留 `not_proven=[real_annotation_submit_success, real_annotation_review_api, real_dataset_export, real_o7_labeling_production]`。
- O6 Model Inference API：`POST /api/o6/archive/inference` 为 O7 电梯状态和楼层证据提供 local/mock 推理事件写入入口。它只允许对已有 O6 archive task 写入 `model_inference.elevator_door_state` / `model_inference.floor_recognition` 事件，幂等键为 `task_id + inference_id + input_id + result_type`，结果可通过 `GET /api/o6/archive/tasks/<task_id>` 的 `events[]` 读回。成功响应固定 `schema=trashbot.o6.model_inference.v1`、`source=local_mock_inference`、`proof_status=not_proven`、`real_gpu_model_connected=false`、`real_external_model_api_connected=false`、`real_model_inference_success=false`、`safe_to_control=false`、`robot_control_executed=false`。PC 后续只能把这些事件作为只读 evidence timeline / labeling seed / debug summary 使用，不得解释成真实电梯门识别、真实楼层到达、真实模型服务接通或任何可控制状态。
- O7 Cloud Archive Tasks Probe：`GET /api/o7/cloud-archive/tasks-probe?baseUrl=<url>` 由 PC Node 后端只读拉取指定回环 base URL 下的 `/api/o7/cloud-archive/tasks`，返回 `trashbot.pc_tools_workstation.o7_cloud_archive_tasks_probe.v1`。允许的 base URL 同样仅限本机 HTTP 回环；未提供、非 HTTP、非回环、带 credentials/query/hash、fetch 失败、schema 错误、返回体非 object 或危险字段为 true 都 fail-closed。UI 只展示 probe status、source base URL、remote schema、archive status、task count、selected/latest、四个 inspector 状态、四条 inspector summary、dangerous true fields、关键 false fields、blocked reasons 和 not proven；不提供 Bearer 输入框，不连接公网云或生产云，不读取真实 archive store，不发送命令，不读取硬件，不证明真实路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路或 O7 完成。
- O7 Realtime/Elevator Cloud Probe：`GET /api/o7/realtime-elevator-probe?baseUrl=<url>` 由 PC Node 后端只读拉取指定回环 base URL 下的 `/api/o7/realtime-elevator/snapshot`，返回 `trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1`。允许的 base URL 同样仅限本机 HTTP 回环；未提供、非 HTTP、非回环、带 credentials/query/hash、fetch 失败、schema 错误、返回体非 object 或危险字段为 true 都 fail-closed。UI 只展示 probe status、source base URL、remote schema、realtime/snapshot status、map ref/frame、`robot_pose_summary`、pose freshness、`probe_observed_at_ms`、`remote_pose_timestamp_ms`、`remote_pose_age_ms`、`freshness_gate_status`、固定 `latency_lt_2s_proven=false`、route membership false fields、elevator status、最多 5 条 `elevator_state_samples_summary`、current floor evidence、human takeover、dangerous true fields、关键 false fields、blocked reasons 和 not proven；不提供 Bearer 输入框，不连接公网云或生产云，不读取 ROS2 `/tf`、真实地图、真实电梯状态链或硬件，不发送命令，不证明 <2s 延迟、真实楼层识别、真实人工接管或 O7 完成。该 freshness gate 只是 PC 后端按远端 `robot_pose.timestamp_ms` 或 `pose_freshness.age_ms` 做的观察摘要，即使 age 小于 2000 也不能升级为真实低延迟证明。该区块现在还包含只读 `Realtime map pose preview` 与 `Elevator state timeline preview`：前者只从 `robot_pose_summary` 安全字符串解析 `x_m/y_m/yaw_rad` 并用固定 viewBox SVG 显示 map frame、中心轴、pose marker 和 heading，解析失败显示 `blocked_pose_coordinate_unavailable` 且不画 marker；后者只展示最多 5 条 `elevator_state_samples_summary` 摘要，空样本显示 `blocked_not_proven`。两个预览持续展示 `latency_lt_2s_proven=false`、`real_ros2_tf_connected=false`、`real_realtime_api_connected=false`、`real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`、`robot_control_executed=false`。
- O7 Cloud Archive Tasks：`GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>` 读取 operator 显式指定的本地 `trashbot.o7.cloud_archive_fixture.v1` archive fixture，返回 `trashbot.o7.cloud_archive_tasks.v1`。该入口是 KR3 历史路线回放、KR4 标注、KR5 ASR/TTS、KR6 手控/寻路的统一数据源雏形，只输出 task list、selected/latest task summary、trajectory/event/label/voice/command 的限量安全摘要，以及 `route_replay_inspector`、`labeling_queue_inspector`、`voice_asr_tts_inspector` 和 `safe_command_inspector`。route inspector 只展示 selected task 的 `map_frame`、`frame_count`、最多 5 条 sample frame、最多 5 条 event timeline、最多 5 条 keyframe ref 和固定 false 的 cursor 初始状态；labeling inspector 只展示 selected task 的 review item count、最多 5 条 sample review item、每个 item 最多 3 条 current label sample、schema 字段、allowed label types、draft labels、dataset export gaps 和固定 false 的 submit/rollback/export/API 字段；voice inspector 只展示 selected task 的 voice session、最多 5 条 ASR event sample、latest partial/final、TTS draft 安全文本摘要、speaker dispatch 缺口、media preflight dependency 和固定 false 的 ASR/TTS/runtime 字段；safe command inspector 只展示 selected task 的 command session、最多 5 条 command sample、manual turn envelope、navigate goal envelope、velocity/steering limits、map goal slot、idempotency/confirmation policy、robot ACK blocked summary、evidence gaps 和固定 false 的发送/手控/寻路/键盘/API/ACK/执行字段。若 selected task 只有 `labels[]`，adapter 会派生最小 review item 与 draft label 摘要，避免 KR4 UI 只有 count；若 selected task 只有旧式 `tts_draft` 单对象，adapter 也会派生 KR5 draft 摘要；若 selected task 缺少 `commands[]` 和 command envelope，KR6 inspector 会清空样本并 blocked。固定 `source=software_proof`、`real_cloud_archive_connected=false`、`real_realtime_api_connected=false`、`real_annotation_api_connected=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`asr_stream_connected=false`、`tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`robot_control_executed=false`。空路径、缺文件、坏 JSON、顶层非 object、unsupported schema、unsafe copy、success claim、control claim、real API connected claim 均 fail-closed。它不是 O6 真实云归档，不连接 realtime/annotation/voice/command API，不提交标注，不发送 TTS，不下发手控/寻路，不绑定键盘或地图点击，不证明真实交付成功。
- O7 Previews：`pc-tools/workstation` 新增独立 `O7 Previews` tab，与 `O7 Console` 分开。该 tab 提供五个本地 fixture JSON 路径输入和五个只读 `Load ... preview` 按钮，分别调用 `GET /api/o7/realtime-elevator-preview?fixtureJson=<local-json>`、`GET /api/o7/route-replay-preview?fixtureJson=<local-json>`、`GET /api/o7/labeling-preview?fixtureJson=<local-json>`、`GET /api/o7/voice-preview?fixtureJson=<local-json>`、`GET /api/o7/safe-command-preview?fixtureJson=<local-json>`。页面默认不自动读取任何本地路径；未加载显示 `not_loaded` / `fixture_json_not_provided`，空路径点击后由后端返回 `not_provided` fail-closed 摘要。每个 preview 展示 `schema`、`preview_status`、`input_status.status`、`failure_reason`、核心固定 false 字段、限量安全摘要、`blocked_reasons` 和 `not_proven`。该 tab 不提供 send/run/submit/control/play/export、方向键、地图点击、stop/cancel/recovery 或任何机器人动作入口。
- O7 Previews 现在还包含 `Cloud operator console probe`、`Cloud archive tasks probe`、`Realtime/elevator cloud probe` 和 `Cloud Archive Tasks` 区块。三个 probe 区块默认只填本机回环示例 URL，不自动发起请求；operator 点击对应 Probe 按钮后才调用 PC 后端 probe API，且浏览器不直接访问 relay。Archive 区块默认不读取本地路径；operator 输入 archive fixture 路径并点击 `Load archive tasks` 后才调用 `GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>`。UI 只展示 probe/archive status、input status、task list 数量、selected/latest task、inspector 状态、probe inspector summaries、安全摘要、route replay inspector、labeling queue inspector、voice ASR/TTS inspector、safe command inspector、realtime/elevator snapshot 摘要、dangerous true fields、fixed false fields、blocked reasons 和 not proven。Cloud archive probe 的四条 summary 分别压缩 route replay frame count/sample refs/首帧并固定 `playback_available=false`，labeling review item/schema/allowed types 并固定 `submit_enabled=false`，voice ASR/TTS count/text length/status 并固定 `tts_send_enabled=false`，safe command count/manual/navigate/ACK blocker 并固定 `command_dispatch_enabled=false` 和 `robot_control_executed=false`；这些 summary 只来自 relay response 的 `safe_summaries` 与 inspector 白名单字段，不展示完整远端 JSON。route inspector 区域用表格展示 selected task、map frame、frame count、sample frames、event timeline、keyframe refs 和 cursor false fields；同一区域提供 PC-only 本地 route replay player，`Previous frame`、`Next frame`、`Reset cursor` 和 range cursor 只改变浏览器本地 sample frame 下标，不调用 API、不写后端、不发送机器人命令，并在未加载 archive、无 selected task、无 sample frames、inspector blocked 或显式 `playback_available=false` 时显示 `blocked_not_proven` 且禁用 navigation。route inspector 同时提供只读 SVG 轨迹小地图，只消费 `route_replay_inspector.sample_frames` 的数值型 `x_m/y_m`，忽略无效坐标，固定 viewBox 归一化轨迹并把当前 marker 绑定到本地 route replay cursor；少于 2 个有效点或当前帧坐标无效时显示 blocked/unknown，不画成可用地图或确定 marker，并持续展示 `trajectory_points=<n>`、`map_frame=<...>`、`current_marker=<...>`、`safe_to_control=false`、`playback_available=false`、`robot_control_executed=false`。该 player 和 minimap 只用于检查 fixture sample frame 的 timestamp、pose、velocity、state、evidence ref 和轨迹形状，不等于真实云历史路线回放、真实地图叠加、真实机器人运动或真实控制。labeling inspector 区域用表格展示 sample review items，并提供 PC-only 本地 labeling review panel；加载 archive 后默认聚焦第一条 sample item，`Previous item`、`Next item`、`Reset item` 只改变浏览器本地 item cursor，不调用 API、不写后端、不提交、不回滚、不导出，并在未加载 archive、无 selected task、无 sample review items 或 inspector blocked 时显示 `blocked_not_proven` 且禁用 navigation。该 panel 展示当前 item 的 item/frame/media/evidence、current label sample、draft label sample、allowed label types/schema 和固定 false 字段，不等于真实 annotation API、真实标注提交/回滚、真实 draft autosave 或真实训练集导出。voice inspector 区域用表格展示 ASR event sample，并提供 PC-only 本地 voice ASR/TTS monitor panel；加载 archive 后默认聚焦第一条 sample ASR event，`Previous ASR event`、`Next ASR event`、`Reset ASR cursor` 只改变浏览器本地 ASR cursor，不调用 API、不写后端、不连接 ASR stream、不发送 TTS、不播放音频、不调度喇叭，并在未加载 archive、无 selected task、ASR events 与 TTS draft 同时为空或 inspector blocked 时显示 `blocked_not_proven` 且禁用 navigation。该 panel 展示当前 ASR event、latest partial/final 对比、`tts_draft.confirmation_required=true` 的只读审核摘要、speaker dispatch summary、media preflight dependency 和语音 false fields，不等于真实语音 API、真实 ASR/TTS runtime、真实 ASR stream、真实 TTS send/playback、真实 speaker ACK 或真实音频设备。safe command inspector 区域提供 PC-only 本地 safe command review panel；加载 archive 后默认聚焦第一条 command sample，`Previous command`、`Next command`、`Reset command cursor` 只改变浏览器本地 command cursor，不调用 API、不写后端、不发送命令、不绑定键盘，并展示当前 command、manual/navigate envelope、idempotency、confirmation、robot ACK blocker 和 evidence gaps；未加载 archive、无 selected task、command sample 与 manual/navigate envelope 同时缺失或 inspector blocked 时显示 `blocked_not_proven` 且禁用 command navigation。该 panel 不等于真实 command API、真实手控、真实寻路下发、真实 robot ACK、真实 stop/cancel/recovery 或硬件安全。realtime/elevator probe 区域展示 map ref/frame、`robot_pose_summary`、pose freshness、route membership false fields、电梯状态、限量电梯状态 sample、楼层证据和人工接管缺口，仍不提供自动播放、提交、导出、发送、控制、停止、取消或恢复类动作按钮。
- O7 Previews 新增 `O7 consumer read primary path` 区块，作为 O7 任务列表/详情与标注队列检查的首选读取入口。operator 只需提供本机回环 relay base URL，点击 `Load consumer task list` 后，workstation 后端固定请求 `GET /api/o6/consumer/tasks?view=summary&limit=50`；点击 `Load consumer task detail` 后，workstation 后端固定请求 `GET /api/o6/consumer/tasks/<task_id>?view=default&include=trajectory,events,evidence,labeling,inference,tunnel`，并可附带 `fieldEvidenceManifestJson=<local-json>` 作为远端缺 field evidence 时的本地只读补齐输入。UI 明确展示 `view=summary`、detail `include=` 策略、`safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`、`connects_cloud_production=false`、`robot_control_executed=false`、blocked reasons、not proven、样本计数和 `tunnel_status.temporal_alignment=latest_known_robot_snapshot_not_task_aligned`，让 fail-closed 语义在 primary path 中可见。consumer-detail labeling primary path 额外只读检查 `labeling/evidence/events/trajectory` 的短摘要，并把 `submit/export/rollback` 继续锁死为 false；该区块不绕过 relay、不连公网云、不发控制命令，也不把缺 labels / inference / tunnel 解释成真实“无异常”。
- Realtime/elevator probe 区域新增 `Realtime map pose preview` 与 `Elevator state timeline preview`。map pose preview 只从 `robot_pose_summary` 安全字符串解析 `x_m/y_m/yaw_rad`，解析失败显示 `blocked_pose_coordinate_unavailable` 且不画 marker；SVG 使用固定 viewBox 展示 map frame、中心轴、pose marker 和 yaw heading。timeline preview 只展示最多 5 条 `elevator_state_samples_summary`，空样本显示 `blocked_not_proven`。两个预览都固定展示真实能力关闸字段：`latency_lt_2s_proven=false`、`real_ros2_tf_connected=false`、`real_realtime_api_connected=false`、`real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`、`robot_control_executed=false`。
- O7 Previews 的 labeling review panel 仅作为 debug fallback。它只基于当前 `labeling_queue_inspector.sample_review_items`、`allowed_label_types` 和 `label_schema` 做浏览器内存草稿输入与前端校验，支持本地选择 label type、填写 `0..1` confidence 和 note。草稿按 `task_id:item_id` 隔离，切换 item 不会把上一条草稿显示到当前 item；`Reset draft` 只重置当前 item 的内存草稿。editor 固定展示 `submit_enabled=false`、`autosave_available=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`、`cloud_write_executed=false`，不新增 Submit/Save/Export 类入口，不调用 API、不写后端、不导出训练集，而且与 consumer-detail labeling primary path 的 cursor/state 隔离。
- O7 Previews 的 voice monitor / readonly TTS draft review 附近新增 `Local TTS draft editor`。它只基于当前 `voice_asr_tts_inspector.tts_draft`、`voice_session`、latest partial/final 和当前 ASR sample 做浏览器内存草稿输入与前端校验，支持本地填写 draft text、voice profile 和 language。archive 未加载、selected task 缺失、ASR/TTS 上下文缺失或 inspector blocked 时显示 `blocked_not_proven` 并禁用输入；trim 后空文本显示 `blocked_tts_text_empty`，超过 120 字符显示 `blocked_tts_text_too_long`，voice profile 或 language 为空时分别显示 `blocked_voice_profile_empty`、`blocked_language_empty`，有效时显示 `local_tts_draft_valid`。`Reset TTS draft` 只清除浏览器内存覆盖值，archive path 切换或重新 load archive 会重置本地草稿。editor 固定展示 `confirmation_required=true`、`tts_send_enabled=false`、`playback_available=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`speaker_dispatch.sends_to_robot=false`、`cloud_write_executed=false`，不新增 Send/Speak/Play/Dispatch/Save/Submit 类入口，不调用 API、不发送 TTS、不播放音频、不调度喇叭、不写云端。
- O7 Previews 的 safe command review panel 附近新增 `Local safe command draft editor`。它只基于当前 `safe_command_inspector.manual_turn_envelope`、`navigate_goal_envelope`、`velocity_limits`、`steering_limits`、`map_goal_slot`、`idempotency_key_requirement` 和 `confirmation_policy` 做浏览器内存草稿输入与前端校验，支持本地选择 `manual_turn` / `navigate_goal`、填写 manual direction、target `x/y/yaw` 和 idempotency key note / draft ref。archive 未加载、selected task 缺失、inspector blocked 或 manual/navigate 上下文不足时显示 `blocked_not_proven` 并禁用输入；manual direction 不在 `left/right/forward/backward/stop` 或 fixture `requested_direction` 集合内显示 `blocked_manual_direction_not_allowed`，navigate target 缺失或非 finite number 显示 `blocked_invalid_navigate_goal`，idempotency draft/ref 为空显示 `blocked_idempotency_key_missing`，有效时显示 `local_safe_command_draft_valid`。`Reset command draft` 只重置浏览器内存，archive path 切换或重新 load archive 会重置本地草稿。editor 固定展示 `confirmation_required=true`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`、`safe_to_control=false`、`cloud_write_executed=false`，不新增 Send/Run/Control/Navigate/Dispatch/Keyboard/Stop/Cancel/Recovery/Save/Submit 类入口，不调用 API、不下发手控或寻路、不绑定键盘、不写云端。
- O7 Operator Console Acceptance：`GET /api/o7/operator-console/acceptance` 从 `buildO7OperatorConsoleResponse()` 生成 `trashbot.o7.operator_console_acceptance.v1` 只读验收摘要，自动检查六个 KR snapshot schema、关键 fail-closed 字段、command/voice/labeling/route replay 禁用入口和危险外推 marker。该入口不读取硬件、不发送命令、不连接云端生产，也不在 UI 中呈现为真实 O7 能力。
- O7 Previews Acceptance Guard：`GET /api/o7/previews/acceptance` 返回 `trashbot.o7.previews_acceptance.v1`，在 O7 Previews tab 顶部通过 `Load previews acceptance guard` 按钮手动加载。该 guard 只汇总 `cloud_operator_console_probe`、`cloud_archive_tasks_probe`、`rtc_signaling_contract_probe`、`realtime_elevator_probe`、`route_replay_player`、`realtime_map_pose_preview`、`elevator_state_timeline_preview`、`route_replay_trajectory_minimap`、`labeling_review_panel`、`local_draft_annotation_editor`、`voice_monitor_panel`、`local_tts_draft_editor`、`safe_command_review_panel`、`local_safe_command_draft_editor` 的本地/HTTP 合同证据边界。每个 surface 都继续列出 `source_endpoint`、`ui_surface`、`evidence_boundary`、`blocked_reasons` 和 `not_proven`，且 `acceptance_status=blocked_not_proven`。`rtc_signaling_contract_probe` 明确 blocked 在 `real_rtc_signaling_session_not_created`、`webrtc_media_transport_not_connected`、`ros2_tf_not_connected`，not_proven 覆盖真实 signaling、WebRTC offer/answer、media transport、视频、实时 pose stream 和 ROS2 `/tf`。guard 固定展示 `reads_hardware=false`、`sends_commands=false`、`connects_cloud_production=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`playback_available=false`、`submit_enabled=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`robot_control_executed=false` 和所有 `real_*_connected=false`；`remaining_real_capability_gaps` 还包含 `rtc_signaling_contract_probe_does_not_prove_real_rtc_video_or_media_transport`。它不读取 fixture、不触发 probe、不连接生产云、不发送命令、不提升 O7 完成度，只用于提醒 CEO/operator 当前仍是 software proof。
- O7 Realtime/Elevator Fixture Preview：`GET /api/o7/realtime-elevator-preview?fixtureJson=<local-json>` 读取用户显式指定的本地安全 JSON fixture，支持 `trashbot.o7.realtime_elevator_fixture.v1`，并返回 `trashbot.o7.realtime_elevator_preview.v1`。该入口只输出 session metadata、map summary、robot pose summary、pose freshness summary、route membership requested text、最多 5 条电梯状态链 sample、当前楼层/目标楼层/人工接管摘要和 evidence/audit refs；固定 `source=software_proof`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`real_elevator_state_chain_connected=false`、`latency_lt_2s_proven=false`、`route_membership_summary.on_route=false`、`route_membership_summary.in_elevator_zone=false`、`robot_control_executed=false`。坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/real realtime API/ROS2 /tf/latency <2s/route membership/elevator zone/real elevator state/elevator arrival/floor recognition/human takeover/robot control claim 均 fail-closed。它不是云端 realtime API，不读取 ROS2 graph 或 `/tf`，不连接 Nav2、硬件或电梯设备，不发命令，不证明真实地图、真实位姿、真实延迟、真实路线成员、真实电梯状态、真实楼层识别、真实人工接管或真实交付成功。
- O7 Route Replay Fixture Preview：`GET /api/o7/route-replay-preview?fixtureJson=<local-json>` 读取用户显式指定的本地安全 JSON fixture，支持 `trashbot.o7.route_replay_fixture.v1`，并返回 `trashbot.o7.route_replay_preview.v1`。该入口只输出 task/route metadata、trajectory frame count、限量 sample frames、playback cursor initial state、keyframe/evidence refs、state transition count/gaps；固定 `source=software_proof`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`real_cloud_archive_connected=false`、`robot_control_executed=false`。坏 JSON、缺文件、unsupported schema、unsafe copy、success/control claim 均 fail-closed。它不是 O6 cloud archive，不是云端历史任务查询，不提供播放按钮，不读取 ROS graph，不发命令，不读取硬件。
- O7 Labeling Fixture Preview：`GET /api/o7/labeling-preview?fixtureJson=<local-json>` 读取用户显式指定的本地安全 JSON fixture，支持 `trashbot.o7.labeling_fixture.v1`，并返回 `trashbot.o7.labeling_preview.v1`。该入口只输出 queue metadata、review item count、最多 3 个 item sample、label schema summary、allowed label types、draft label count/sample、dataset export status/gaps 和 evidence refs；固定 `source=software_proof`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`real_annotation_api_connected=false`、`submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`robot_control_executed=false`。坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/submit/rollback/export availability claim 均 fail-closed。它不是 O6 annotation API，不提交标注，不回滚标注，不导出训练集，不读取 ROS graph，不发命令，不读取硬件。
- O7 Voice Fixture Preview：`GET /api/o7/voice-preview?fixtureJson=<local-json>` 读取用户显式指定的本地安全 JSON fixture，支持 `trashbot.o7.voice_fixture.v1`，并返回 `trashbot.o7.voice_preview.v1`。该入口只输出 voice session metadata、ASR event count、最多 3 个 ASR event sample、latest partial/final slot、TTS draft summary、speaker dispatch ACK/failure 缺口、media preflight dependency 和 evidence/audit refs；固定 `source=software_proof`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`asr_stream_connected=false`、`tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`robot_control_executed=false`。坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/ASR connected/TTS send/speaker dispatch/real voice runtime/speaker ACK success claim 均 fail-closed。它不是 voice cloud API，不监听麦克风，不发送 TTS，不播放音频，不读取 ROS graph，不发命令，不读取硬件。
- O7 Safe Command Fixture Preview：`GET /api/o7/safe-command-preview?fixtureJson=<local-json>` 读取用户显式指定的本地安全 JSON fixture，支持 `trashbot.o7.safe_command_fixture.v1`，并返回 `trashbot.o7.safe_command_preview.v1`。该入口只输出 command session metadata、manual turn envelope summary、navigate goal envelope summary、velocity/steering limit summaries、map goal slot、idempotency key requirement、confirmation policy、robot ACK summary、evidence gaps 和 audit/evidence refs；固定 `source=software_proof`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`。坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/dispatch/manual/navigate/keyboard/real command API/real robot ACK/robot control executed/ACK success/HIL or hardware verified claim 均 fail-closed。它不是云端 command API，不读取 ROS graph，不连接 Nav2，不打开串口，不发命令，不提供方向键、地图点击、stop、cancel 或 recovery 按钮，不把 fixture limits 解释为真实 HIL 安全限制。
- Proof Boundary：集中展示软件证明能覆盖什么、不能覆盖什么，避免误读为真实硬件或交付证明。

## O7 Operator Console 边界

O7 Operator Console 是云端契约驱动的最小运营视图，不是实时控制台。它把 O7 六个 KR 的目标界面先落到 PC 工作站中，便于 O6/O7 后续对齐 API 字段和验收缺口。

- 顶层 API 固定继承 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- `cloud_api_status=draft_blocked_not_proven`，`robot_connection=not_connected_by_pc`，`operator_mode=observe_only`。
- `manual_control_policy.command_dispatch_enabled=false`，`pc_direct_robot_connection=false`，`cloud_mediated_only=true`，`confirmation_required_before_future_dispatch=true`。
- `board_media_preflight_required=true`，`board_media_preflight_schema=trashbot.o7_board_media_preflight.v1`，`board_media_preflight_state=blocked`。
- `realtime_map_snapshot` 固定 `schema=trashbot.o7.realtime_map_snapshot.v1`、`snapshot_status=blocked_not_proven`、`map_ref.status=not_proven`、`map_frame.status=contract_placeholder_not_tf`、`pose_freshness.latency_lt_2s_proven=false`、`route_membership.on_route=false`、`route_membership.in_elevator_zone=false`，用于展示 O7-KR1 字段契约，不证明真实 ROS2 `/tf`、真实地图、真实机器人位姿或延迟小于 2 秒。
- `elevator_state_snapshot` 固定 `schema=trashbot.o7.elevator_state_snapshot.v1`、`snapshot_status=blocked_not_proven`、`current_state=not_connected`、`current_floor_evidence.status=not_proven`、`target_floor.confirmation_status=not_proven`、`human_takeover.required=true`、`human_takeover.reason=real_elevator_state_chain_not_proven`，用于展示 O7-KR2 字段契约，不证明真实电梯状态链、真实楼层证据、真实到达楼层或真实人工接管原因。
- `route_replay_snapshot` 固定 `schema=trashbot.o7.route_replay_snapshot.v1`、`snapshot_status=blocked_not_proven`、`playback_available=false`、`real_archive_connected=false`、`task_selector.status=blocked_no_cloud_task_archive`、`task_selector.available_task_count=0`、`selected_task.status=not_proven`、`trajectory.frame_count=0`、`trajectory.sample_frames=[]`、`playback_cursor.status=blocked_not_available`、`keyframes.count=0`、`state_transitions.status=blocked_no_state_transition_archive`，用于展示 O7-KR3 字段契约，不证明真实历史任务列表、真实 selected task、真实轨迹帧、真实关键帧截图、真实 evidence refs、真实状态转移或 O6 云端归档已经完成。
- `route_replay_snapshot.evidence_refs` 必须保留 `missing_o6_cloud_task_archive`、`missing_trajectory_api`、`missing_keyframe_archive`、`missing_state_transition_archive`；`state_transitions.gaps` 必须列出归档未连接、trajectory schema 未回填、keyframe refs 未回填和 transition timeline 未回填。
- `route_replay_snapshot.next_required_evidence` 是后续 O6/O7 对接清单，不是 PC 端云查询结果；包括 O6 cloud task archive query contract、历史任务列表 fixture、含 map frame 和 timestamp 的 trajectory schema、keyframe evidence ref archive sample、state transition timeline archive sample，以及 PC playback cursor 与 cloud frames 绑定且不触发机器人控制的证明。
- `labeling_queue_snapshot` 固定 `schema=trashbot.o7.labeling_queue_snapshot.v1`、`source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`、`submit_enabled=false`、`rollback_enabled=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`，用于展示 O7-KR4 字段契约，不证明真实 review queue、真实 selected item、真实截图/帧、真实 label schema、真实提交、真实回滚、真实训练集导出或 O6 annotation API 已完成。
- `labeling_queue_snapshot.review_queue.status=blocked_no_annotation_api`、`available_item_count=0`、`queue_ref=missing_o6_annotation_review_queue`；`selected_item.media_ref=missing_review_item_media_ref`、`evidence_ref=missing_selected_labeling_item_record`；`label_schema.status=blocked_no_label_schema_api`；`allowed_label_types` 仅是 `contract_placeholder_not_api`；`draft_labels.count=0` 且 `autosave_available=false`。
- `labeling_queue_snapshot.submit_audit` 和 `rollback_audit` 只展示 `future, disabled` endpoint 与 missing audit ref；UI 不提供 submit/rollback 按钮，也不写入本地文件或云端。
- `labeling_queue_snapshot.dataset_export.status=blocked_not_available`、`export_ref=missing_training_dataset_export`、`supported_formats=[]`，`dataset_export.gaps` 必须列出 annotation API 未连接、accepted label schema 未证明、reviewed items 不可用、dataset manifest export 不可用和 training split policy 未定义。
- `labeling_queue_snapshot.next_required_evidence` 是后续 O6/O7 对接清单，不是 PC 端云查询结果；包括 annotation review queue query contract、label schema fixture、selected review item media evidence ref、draft label payload schema、submit/rollback audit log sample、dataset export manifest contract，以及 PC labeling panel 与 cloud API 绑定且不触发机器人控制的证明。
- `voice_asr_tts_snapshot` 固定 `schema=trashbot.o7.voice_asr_tts_snapshot.v1`、`source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`、`asr_stream_connected=false`、`tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`，用于展示 O7-KR5 字段契约，不证明真实 ASR stream、真实 partial/final transcript、真实 TTS send/playback、真实 speaker ACK、真实音频设备、真实 RTC 或云端 voice API 已完成。
- `voice_asr_tts_snapshot.asr_stream.status=blocked_no_voice_api`、`connection_state=not_connected`、`partial_slot.evidence_ref=missing_asr_partial_transcript_trace`、`final_slot.evidence_ref=missing_asr_final_transcript_trace`；`tts_draft.status=draft_disabled`、`tts_draft.text=""`、`tts_draft.voice_profile=not_connected`、`tts_draft.confirmation_required=true`。
- `voice_asr_tts_snapshot.speaker_dispatch.status=blocked_not_available`、`speaker_dispatch.endpoint=POST /api/o7/operator/voice/tts (future, disabled)`、`speaker_dispatch.sends_to_robot=false`；`command_ack_audit.ack_status=blocked_no_ack_contract`、`audit_ref=missing_voice_command_audit_log`、`speaker_ack_ref=missing_speaker_dispatch_ack`、`failure_event_ref=missing_speaker_failure_event`。
- `voice_asr_tts_snapshot.media_preflight_dependency` 必须指向 `board_media_preflight_summary` 且 `status=blocked`；`next_required_evidence` 是后续 O6/O7/板端联调清单，不是 PC 端云查询结果，包括 voice ASR/TTS cloud API contract、ASR stream partial/final trace、TTS payload/ACK/audit、speaker ACK/failure event、board audio preflight 和无底盘运动的 RTC media smoke。
- `safe_command_snapshot` 固定 `schema=trashbot.o7.safe_command_snapshot.v1`、`source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`，用于展示 O7-KR6 字段契约，不证明真实手控、真实速度控制、真实转向控制、真实键盘控制、真实自动寻路下发、真实 cloud command API、真实 robot ACK 或真实底盘安全。
- `safe_command_snapshot.manual_turn_envelope` 只展示 `operator.safe_command_preview.v1`、`sends_to_robot=false`、`keyboard_arrow_keys_disabled`、`velocity_limited=true`、`steering_limited=true` 和 `missing_manual_turn_command_envelope_trace`；UI 不提供方向键按钮或键盘绑定。
- `safe_command_snapshot.velocity_limits` 和 `steering_limits` 固定 `status=blocked_no_robot_hil_limits`、`hardware_verified=false`，数值为 `null`；PC 不把 limits 占位解释为真实速度或转向安全边界。
- `safe_command_snapshot.navigate_goal_envelope` 固定 `sends_to_robot=false`、`goal_source=map_click_disabled`、`requires_map_goal_slot=true`；`map_goal_slot` 固定 `x_m/y_m/yaw_rad=null`、`status=empty_not_connected`，UI 不提供地图点击下发。
- `safe_command_snapshot.cloud_command_endpoint` 只展示 `POST /api/o7/operator/commands/manual-turn (future, disabled)` 和 `POST /api/o7/operator/commands/navigate-goal (future, disabled)`，`status=future_disabled`、`sends_to_robot=false`。
- `safe_command_snapshot.idempotency_key_requirement.required=true`、`header=Idempotency-Key`、`status=required_not_connected`；`confirmation_policy` 固定手控、寻路和键盘 hold 都需要确认但当前 `blocked_no_confirmation_ui`。
- `safe_command_snapshot.robot_ack_status.ack_status=blocked_no_robot_ack_contract`、`ack_ref=missing_robot_command_ack`、`timeout_ms=null`、`cancel_ack_ref=missing_robot_cancel_ack`、`stop_ack_ref=missing_robot_stop_ack`、`recovery_ref=missing_robot_recovery_event`。
- `safe_command_snapshot.evidence_gaps` 必须保留 timeout、cancel、stop、recovery 四类 missing token；`next_required_evidence` 是后续 O5/O7/Robot/Hardware 联调清单，不是 PC 端云查询结果，包括 safe command API bearer auth、幂等 replay rejection、manual turn payload schema、navigate goal payload schema、confirmation UI policy、robot ACK timeout trace、cancel/stop/recovery ACK trace 和 HIL/受控现场安全证据。
- `board_media_preflight_summary` 固定展示 `safe_to_control=false`、`primary_actions_enabled=false`、`device_probe_allowed=false`、`device_probe_attempted=false`、`software_proof_only=true`，并列出 RTC signaling/STUN/TURN、摄像头视频源、音频输入输出、ASR/TTS runtime 和 on-robot media smoke 缺口。
- `board_media_preflight_summary.not_proven` 必须覆盖真实 RTC session、真实摄像头视频、真实音频采集/播放、真实 ASR stream、真实 TTS playback、Orange Pi media runtime 和 on-robot media smoke。
- `board_media_preflight_summary.next_required_evidence` 是后续上车验收清单，不是 PC 端设备探测结果；包括 Orange Pi 摄像头/音频枚举、RTC signaling trace、带时间戳视频帧、ASR/TTS trace、CPU encoding budget 和无底盘运动的 media smoke。
- `kr_views` 必须包含 `O7-KR1` 到 `O7-KR6` 六项，状态只能是 `draft`、`blocked` 或 `not_proven`。
- `command_previews` 只展示未来 safe API envelope，所有条目固定 `sends_to_robot=false`，不得渲染成按钮或键盘控制。
- O7-KR1 需要后续 cloud realtime map/pose stream；O7-KR2 需要电梯状态链和楼层证据；O7-KR3 需要任务归档和轨迹帧；O7-KR4 需要打标队列和提交审计；O7-KR5 需要 ASR 事件流和 TTS ACK；O7-KR6 需要幂等 command API、robot ACK、超时、取消和恢复路径。
- PC 端不得绕过云端读取 ROS2、串口、Nav2 runtime 或 WAVE ROVER 状态；任何真实运动或语音播报必须等待 Robot/Hardware 提供安全验收材料。
- PC 端展示 board media preflight 缺口只说明 operator 能看见下一步证据清单，不证明真实 RTC、真实摄像头、真实音频、真实 ASR/TTS 或真实控制完成。
- PC 端展示 realtime/elevator snapshot 只说明 operator 能看见 O7-KR1/KR2 的字段槽位，不证明实时流接通、真实地图定位、真实电梯状态或历史电梯状态链回放。
- `GET /api/o7/realtime-elevator-preview?fixtureJson=<local-json>` 只说明 PC 能把本地 realtime/elevator fixture 压成安全摘要。即使返回 `preview_status=fixture_preview_ready`，也不证明真实 realtime API 接通、真实 ROS2 `/tf` forwarding、真实地图 artifact、真实机器人位置、真实刷新延迟小于 2 秒、真实路线成员、真实电梯区域、真实电梯状态链、真实当前楼层、真实目标楼层确认、真实人工接管或真实 delivery success。
- realtime/elevator fixture preview 的输入只允许 `trashbot.o7.realtime_elevator_fixture.v1`。输出不复制凭证、串口、`/cmd_vel` 或完整原始 event payload；仅保留 session、map、pose、freshness、route membership requested text、限量电梯状态 sample、楼层/目标楼层/人工接管摘要和 evidence refs。`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`real_elevator_state_chain_connected=false`、`latency_lt_2s_proven=false`、`route_membership_summary.on_route=false`、`route_membership_summary.in_elevator_zone=false`、`robot_control_executed=false`，UI 不得基于该接口提供实时控制、路线通过、电梯到达、楼层识别成功、人工接管已完成、恢复、控制、下发或云端成功文案。
- PC 端展示 route replay snapshot 只说明 operator 能看见 O7-KR3 的字段槽位，不证明 O6 cloud archive、历史任务列表、轨迹 API、关键帧 evidence refs、状态转移时间线或真实逐帧回放已经可用。
- `GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>` 中的 `route_replay_inspector` 比上一轮 archive summary 更接近 O7-KR3 的检查口径：operator 可以看到 selected task 的限量逐帧位置、速度、状态、event timeline、keyframe refs 和 cursor 初始 false 字段。但它仍只读取本地 archive fixture，`cursor_initial_state.safe_to_play=false`，不能解释成真实逐帧回放、云归档接通或机器人运动。
- `GET /api/o7/route-replay-preview?fixtureJson=<local-json>` 只说明 PC 能把本地 fixture 压成安全摘要。即使返回 `preview_status=fixture_preview_ready`，也不证明 O6 cloud archive 接通、真实历史任务存在、真实轨迹可播放、真实关键帧归档存在、真实状态转移时间线完整、真实机器人运动或真实 delivery success。
- route replay fixture preview 的输入只允许 `trashbot.o7.route_replay_fixture.v1`。输出不复制绝对路径、凭证、串口、`/cmd_vel` 或完整原始 frame payload；仅保留限量 sample frames、限量 keyframe refs 和限量 state transition sample。`playback_cursor_initial_state.safe_to_play=false`，UI 不得基于该接口提供播放、恢复、控制、下发或云端归档成功文案。
- PC 端展示 labeling queue snapshot 只说明 operator 能看见 O7-KR4 的字段槽位，不证明 O6 annotation API、真实 review queue、真实截图/帧、真实提交、真实回滚、真实审计日志或训练集导出已经可用。
- `GET /api/o7/labeling-preview?fixtureJson=<local-json>` 只说明 PC 能把本地标注 fixture 压成安全摘要。即使返回 `preview_status=fixture_preview_ready`，也不证明 O6 annotation API 接通、真实 review queue 存在、真实截图/帧可访问、真实 label schema 由云端返回、真实提交/回滚可用、真实训练集导出存在或真实 delivery success。
- labeling fixture preview 的输入只允许 `trashbot.o7.labeling_fixture.v1`。输出不复制绝对路径、凭证、串口、`/cmd_vel` 或完整原始 annotation payload；仅保留限量 review item sample、限量 current label summary、限量 draft label sample 和 dataset export gaps。`submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`，UI 不得基于该接口提供 submit、rollback、export、恢复、控制、下发或云端标注成功文案。
- PC 端展示 voice ASR/TTS snapshot 只说明 operator 能看见 O7-KR5 的字段槽位，不证明真实语音监听、真实 ASR partial/final、真实 TTS 发送/播放、真实 speaker ACK、真实音频设备、真实 RTC 或真实云端 voice API 已经可用。
- `GET /api/o7/voice-preview?fixtureJson=<local-json>` 只说明 PC 能把本地语音 fixture 压成安全摘要。即使返回 `preview_status=fixture_preview_ready`，也不证明真实 ASR stream、真实 partial/final transcript、真实 TTS send/playback、真实 speaker ACK/failure event、真实 media preflight、真实 RTC、真实云端 voice API、真实机器人控制或真实 delivery success。
- voice fixture preview 的输入只允许 `trashbot.o7.voice_fixture.v1`。输出不复制凭证、串口、`/cmd_vel` 或完整原始 ASR/TTS payload；仅保留限量 ASR event sample、latest partial/final slot、TTS draft summary、speaker ACK/failure 缺口和 media preflight gaps。`asr_stream_connected=false`、`tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`，UI 不得基于该接口提供 TTS 发送、播放、恢复、控制、下发或云端语音成功文案。
- PC 端展示 safe command snapshot 只说明 operator 能看见 O7-KR6 的字段槽位，不证明真实手动转向、真实速度控制、真实转向控制、真实键盘控制、真实自动寻路下发、真实 robot ACK、真实 timeout/cancel/stop/recovery 或真实底盘安全已经可用。
- `GET /api/o7/safe-command-preview?fixtureJson=<local-json>` 只说明 PC 能把本地 safe-command fixture 压成安全摘要。即使返回 `preview_status=fixture_preview_ready`，也不证明真实 command API 接通、真实手控、真实速度控制、真实转向限制、真实键盘控制、真实自动寻路下发、真实 robot ACK、真实 timeout/cancel/stop/recovery、真实 HIL/硬件安全或真实 delivery success。
- safe command fixture preview 的输入只允许 `trashbot.o7.safe_command_fixture.v1`。输出不复制凭证、串口、`/cmd_vel` 或完整原始 command payload；仅保留 command session、manual turn envelope、navigate goal envelope、limit summaries、map goal slot、idempotency/confirmation summaries、robot ACK blocked summary、evidence gaps 和 audit refs。`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`，UI 不得基于该接口提供方向键、地图点击、stop、cancel、recovery、发送、恢复、控制、下发或云端命令成功文案。
- `O7 Previews` tab 对五个 preview API 的 UI 边界与 API 边界一致：按钮文案只能是 `Load ... preview`，点击只触发 GET preview；任何返回 `fixture_preview_ready` 都只代表本地 fixture 已生成安全摘要，不证明真实 realtime API、ROS2 `/tf`、云归档、annotation API、voice API、safe command API、robot ACK、HIL/硬件安全或 delivery success。
- `GET /api/o7/operator-console/acceptance` 是 O7 Console 的 acceptance guard。它必须保持 `reads_hardware=false`、`sends_commands=false`、`connects_cloud_production=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_real_capability_proof=true`，并复核 `command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`tts_send_enabled=false`、`submit_enabled=false`、`playback_available=false`。该 guard 的 `blocked_not_proven_guard_ok` 只说明 fail-closed 契约未漂移，不证明 O7 任一真实能力完成。
- O7 Previews 顶部的 `O7 previews acceptance guard` 现在包含只读 `O7 real capability gap summary`。该 summary 不新增 API、不触发 probe、不读取 fixture、不发送命令，只消费已加载的 `GET /api/o7/previews/acceptance` 响应里的 `surfaces`、`remaining_real_capability_gaps`、`blocked`、`not_proven` 和 `fixed_false_fields`。前端按 O7-KR1~KR6 将既有 surface id 分组展示 matched surface count、surface ids、blocked/not_proven 摘要、`ready_for_real_operation=false`、remaining real capability gaps，以及 `safe_to_control=false`、`sends_commands=false`、`connects_cloud_production=false`、`robot_control_executed=false`。未加载 guard 时显示 `not_loaded`，不得把 14 个 software-proof surface 解释成 O7 完成度提升。

## O7 与 O6 Consumer Read 集成指导

- O7 的任务列表与任务详情在 PC 端默认使用 consumer read：
  - `GET /api/o6/consumer/tasks`
  - `GET /api/o6/consumer/tasks/<task_id>`
- 目的：统一字段语义（`task_status_summary`、`labeling_status`、`inference_status`、`tunnel_status_summary`、`proof_boundary`），避免在 O7 不同 tab 再次做底层 endpoint join。
- `view=summary` 适用于移动端或列表内嵌只读快照；PC 需要逐项排障时可加 `include=trajectory,events,evidence,labeling,inference,tunnel`。
- 容错原则：
  - task 不存在 / robot_id mismatch / limit 越界 / include/view 非法 / query 含危险字段：统一 fail-closed 处理，不展示“任务成功/可控制”。
  - `selected` 只保留 store 的单选标记，不等于用户 UI 选择状态。
- 本规则的作用域是 O7 开发/调试文案层：**不改变** `docs/interfaces/o6_cloud_archive_api.md` 已有 consumer read schema，不开启真实云 DB、OSS、TLS、4G 或 robot control 逻辑。

## Training/Labeling Asset Inventory 边界

Training/Labeling 是 Node-native 本地资产清单入口，不是训练入口、标注服务入口或数据上传入口。

- 顶层 API 固定继承 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- 顶层 API 固定输出 `real_pipeline_connected=false`。
- `roots.dataset=pc-tools/training`，`roots.labeling=pc-tools/labeling`。
- 每个 workspace 输出 `status`、`asset_counts`、`manifest_candidates`、`image_files`、`annotation_files`、`missing_requirements`、`next_actions`。
- 空目录必须输出 `empty_not_connected`，不得被 UI 或 API 文案解释为可训练、可标注或 ready。
- 只扫描非 Python 资产：`.json`、`.jsonl`、`.yaml`、`.yml`、常见图片扩展和常见标注扩展；`.py` 只计入 `ignored_python_files`，不进入资产列表。
- manifest candidate 只是人工检查入口，不代表数据集 schema 已通过，也不代表训练配置存在。
- UI 只显示资产 readiness、缺口和人工 next actions；不得提供 start、upload、execute 或任何真实 pipeline 控件。

## WAVE ROVER Material Coverage 边界

Hardware Materials 是 Node-native 只读入口，不恢复旧 Python evidence gate，不执行 ROS2、串口、HIL 或任何控制动作。它只统计本地 fixture 材料覆盖：

- 顶层 API 固定继承 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- 每个 `wave_rover_*` 材料组输出 `group`、`fixture_relative_path`、present/missing materials、coverage counts 和 material coverage status。
- 顶层同时输出 `fixture_groups`、`groups`、`gaps` 和 `not_proven_boundaries`；`fixture_groups` 是本轮主 contract 字段，`groups` 仅保留给既有调用方兼容。
- `gaps` 是补材料清单，不是失败结论；缺口补齐后仍保持 `proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`。
- 顶层 API 固定输出 `hardware_claim_level=software_material_coverage`，不得出现 `hil_verified` 或等价字段。
- `vendor_sources` 使用 `{ path, fact_ids }` 结构，当前来源包括 `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`。
- UI 文案必须明确 `coverage is not HIL pass`。文件齐备只说明材料 coverage，不说明 WAVE ROVER 上电、真实 UART 连通、轮向正确、反馈频率达标、IMU/battery 标定通过或真实 delivery success。
- UI 里的 coverage label 使用 `complete file/material coverage`，不得把 complete coverage 简写成 HIL pass 或 ready to control。
- 允许展示的 bounded vendor facts 来自 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料：UART newline-delimited JSON、`base_ctrl.py` 通过 `json.dumps(data)+"\n"` 发送并使用 `readline()` 接收、ESP32 `serialCtrl()` 收到 `\n` 后 `deserializeJson()` 并分发命令、Raspberry Pi vendor 示例默认 `/dev/ttyAMA0` 与 `115200` 且另有 `/dev/serial0` 注释、Orange Pi 串口路径未证明、`FEEDBACK_BASE_INFO=1001`、`T=1/T=11/T=13/T=130/T=131/T=142/T=143` 命令 ID、`ugv_advance.h` 中 `baseInfoFeedback()` 组装 `T=1001` 基础字段 `L/R/r/p/y/v`。
- `serial_reference` 只表达 vendor Raspberry Pi 示例：`vendor_rpi_default_device=/dev/ttyAMA0`、`vendor_rpi_alternate_device=/dev/serial0`、`baudrate=115200`、`orange_pi_device_status=not_proven`。不得声明 Orange Pi 使用这些路径，也不得声明波特率链路已验证。
- `command_facts` 只说明 vendor firmware 定义了 `T=1`、`T=11`、`T=13`、`T=130`、`T=131`、`T=142`、`T=143`，所有条目固定 `hardware_verified=false`。`T=13 CMD_ROS_CTRL` 不得被描述为已在当前底盘可用。
- `feedback_schema.T1001` 的 `base_fields` 为 `L/R/r/p/y/v`，来源为 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`。当 `moduleType=1` 时反馈字段可能变化，且 `y` 会被机械臂 `lastY` 覆盖，UI/API 必须保留该条件说明。
- `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 是项目侧 evidence material，不得写成 vendor 原生输出。
- 必须保留的 fail-closed token 包括：`hil_pass=false`、`hardware_connected=false`、`serial_path_not_proven`、`baudrate_link_not_proven`、`wheel_direction_not_proven`、`cmd_ros_ctrl_not_proven_on_chassis`、`feedback_frequency_not_proven`、`imu_calibration_not_proven`、`battery_calibration_not_proven`、`delivery_success_not_proven`。

## Fail-Closed 契约

所有 API/UI 必须可追溯到以下字段：
- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`

即使本地 JSON 读取成功，`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 仍固定不变。工作站不得因为存在 route/evidence fixture 而声明真实路线通过、真实投放完成或机器人可控制。

Robot Control V1 读取到 Robot API status/latest/readback 也只能证明“PC 端可读到短摘要”。端点级只读超时只用于减少真实慢端点被误判成 `fetch_failed`，固定 manual/stop 代理也只证明 workstation 能按安全门槛转发受控点动请求，不代表 UI 可以自由控制，也不代表控制安全边界放松。它不证明真实手控已开放、真实 `/cmd_vel` 发布、真实 `/api/base/manual` 已安全放开、真实 Nav2 goal dispatch、真实 map/radar runtime 启动、真实 Camera/LiDAR/Base HIL、真实 robot ACK 或真实 delivery success。Robot API 不可达、schema drift、缺字段、Mock fallback、O6 detail 不可达或危险 true 字段出现时，页面必须继续显示 blocked reason，并保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## PC Navigation Goal Preflight Gate V1

2026-06-11 新增 PC 端“导航目标预检（高级）”，目标是 `navigation_goal_preflight_only_no_motion`。它不是导航执行、不是自动寻路下发，也不证明真实 NavigateToPose 可以使用。

接口：

- Workstation endpoint：`POST /api/robot-control/nav2/goal/preflight?baseUrl=<robot-api-base-url>`。
- 请求体只允许 `goal_frame_id`、`goal_x`、`goal_y`、`goal_yaw`、`confirm_navigation_preflight` 五个字段。
- `goal_frame_id` 固定为 `map`；坐标和 yaw 只接受有限数字，并在 Node 端 clamp 到 `x/y [-3, 3] m`、`yaw [-3.1416, 3.1416] rad`。
- 未知字段、非 object body、非法 frame、非数字 goal 或非法 `baseUrl` 都由 workstation 本机 HTTP 400 拒绝。
- Node 代理只读取固定 GET：`/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/operator/report`、可选 `/api/nav2/status`。
- 该 endpoint 永远不调用 `/api/nav2/start`、NavigateToPose、`/cmd_vel` 或 `/api/base/manual`；响应固定 `robot_control_executed=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

放行口径：

- `confirm_navigation_preflight=true`。
- localization latest 已加载，且 `status/latest proof` 显示 `localization_reset_observed` 或 `nav2_no_motion_localization_runtime_observed`。
- `localization_tf_observed.map_to_base_link=true` 或 `tf_chain_observed.map_to_base_link=true`。
- Nav2 proof latest 已加载，且 `path_generated=true` 或 `path_generation_succeeded=true`，同时 `path_point_count>0`。
- `/api/operator/report` 的材料 preflight passed；`delivery_success` claim 不参与放行。

通过时只返回 `proxy_status=preflight_passed`、`preflight_status=ready_for_navigation_goal_not_executed`。材料不足时返回 HTTP 400 `preflight_rejected`，带 `missing_requirements`、各 readback 摘要和 operator material gate 摘要，供 PC 高级诊断复核。

UI：

- 普通首屏仍只显示 `Rober 小车控制台` 与五张卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- 目标坐标、确认 checkbox、预检按钮和最近结果只在默认关闭的 `高级诊断 -> Nav2 规划详情` 中展示。
- 首屏不得出现目标坐标输入、Nav2 goal、HIL、structured_hil_claims、`/cmd_vel`、`/api/base/manual`、NavigateToPose 等工程词。

## PC Map Runtime Controls V1

2026-06-11 起，Robot Control 的普通首屏仍保持五卡片简洁布局。地图卡片只显示
`刷新地图`、`地图列表` 和短状态，不显示 `开始建图`、`保存地图`、`Start`、
`Reset`、`raw`、`HIL`、速度或点动类工程控件。

`高级诊断` 的地图详情允许固定 map lifecycle 操作：

- `地图列表`：GET-only 固定代理到上位机 `/api/map/list`。
- `开始建图（高级）`：POST 固定代理到上位机 `/api/map/start`。
- `保存地图`：POST 固定代理到上位机 `/api/map/save`。
- `Reset（受控/高级，禁用）`：仍保持禁用。

PC 代理 body 只允许短 `map_name` 和相对 `artifact_path` 字段；未知字段、绝对路径、
路径穿越或 shell 字符串会被拒绝。上位机再次校验 `map_name`，并忽略
`artifact_path`，地图文件只写入配置的 `map_artifact_dir`。

代理判定规则：

- `command_result.executed=true` 不再单独导致 `lifecycle_failed`，因为 no-motion
  helper 的 start/save 必须真实执行 ROS2 LiDAR+SLAM runtime 才能产出地图材料。
- 仍然 fail closed 于 HTTP 非 OK、远端 `failure_reason/error`、以及任何硬危险字段
  true：`safe_to_control`、`delivery_success`、`primary_actions_enabled`、
  `robot_control_executed`、`sends_motion_commands`、`sends_base_motion_commands`、
  `publishes_cmd_vel`、`calls_base_manual`、`uses_base_uart` 等。
- 顶层 PC 合同继续固定 `safe_to_control=false`、`delivery_success=false`、
  `primary_actions_enabled=false`、`robot_control_executed=false`。

本轮 Browser smoke 结论：首屏 `.robot-console-grid` 为 5 张卡片，地图卡片只含
`刷新地图` 与 `地图列表`；首屏未出现 `开始建图`、`保存地图`、`Start`、
`Reset`、`raw`、`HIL`、`速度`、`点动`。打开 `高级诊断` 后，地图详情包含
`开始建图（高级）`、`保存地图`、`map_name（可选）` 和 `artifact_path（可选）`。

边界：该能力只证明 PC 可以经固定代理触发上位机 no-motion map runtime，不证明
地图质量、Nav2 可行驶、真实运动、WAVE ROVER HIL、robot ACK 或 delivery success。

2026-06-11 08:05 起，上位机 map lifecycle helper 对 `/scan` clean proof 做了
稳定化：`/scan_once_observed` 仍是必需条件，但 helper 会用 sensor_data QoS 的
`ros2 topic echo --once /scan` 做最多 2 次独立采样并记录 attempts。PC 代理因此可在
远端 clean pass 时返回 `proxy_status=lifecycle_forwarded`、`remote_http_status=200`
和 `command_result.ok=true`。

PC `GET /api/robot-control/map/list` 当前返回的是截断摘要：`map_count` 代表远端总数，
`map_names` 只展示前若干项。因此当地图数量较多时，新 YAML 可能在摘要里可见，而同名
PGM 可能被截断；完整 YAML/PGM 仍以远端 `/api/map/list` 或 latest proof 的
`proof.map_files` 为准。后续如需 PC 页面逐项核对 YAML/PGM，应扩展 PC server 的 list
摘要，而不是放宽上位机 map lifecycle gate。

## PC Localization Reset Controls V1

2026-06-11 起，Robot Control 新增 `定位重置（高级）`。该按钮只放在默认关闭的
`高级诊断 -> Nav2 规划详情` 中；普通首屏仍只有五张卡片和普通动作：
`连接/刷新`、`打开画面/关闭画面`、`刷新雷达`、`刷新地图`、`地图列表`、
`停止`。首屏不显示 `检查路径`、`定位重置`、`initialpose`、`AMCL`、
`proof/readback/raw`、`HIL`、速度/点动、`safe_to_control`、`/cmd_vel` 或
`/api/base/manual`。

PC 后端新增固定代理：

```text
POST /api/robot-control/localize/reset?baseUrl=<robot-api-base-url>
```

代理只转发到上位机固定 `POST /api/localize/reset`，浏览器 body 被忽略。上位机请求
body 固定为：

```json
{
  "timeout_s": 8,
  "managed_runtime_opt_in": true,
  "managed_timeout_s": 12,
  "initialpose_opt_in": true,
  "initialpose_x": 0,
  "initialpose_y": 0,
  "initialpose_yaw": 0,
  "initialpose_frame_id": "map",
  "path_generation_opt_in": false
}
```

响应摘要会展示 `initialpose_published`、`amcl_pose_observed`、
`localization_tf_observed`、`managed_runtime_started`、
`managed_runtime_cleanup_ok`、`localization_reset_observed` 和 blocked/root cause。
PC 顶层仍固定 `safe_to_control=false`、`delivery_success=false`、
`primary_actions_enabled=false`、`robot_control_executed=false`。

该入口不调用 `NavigateToPose`、Nav2 start/stop、`ComputePathToPose`、
`/cmd_vel`、`/api/base/manual`、底盘 UART 或 `/dev/ttyS5`。它只证明 no-motion
AMCL localization material，不证明路径执行、真实运动、HIL 或 delivery success。

## PC Manual HIL Gate Current Evidence

2026-06-11 10:35 的真实 PC proxy smoke 证明当前 `手动移动/运动` 非 stop gate
仍应保持关闭。PC workstation 对 `http://192.168.1.11:8787` 读取
`/api/operator/report`、`/api/base/status`、`/api/base/feedback-samples/latest`、
`/api/radar/status` 和 `/api/radar/scan-proof/latest` 均为 HTTP 200；但
operator report 仍缺 `external_video_recorded`、`visible_content_proven`、
`wheel_feedback_lr_nonzero_proven` 和 `physical_motion_lidar_delta_proven`。

本轮只通过 PC proxy 执行 `POST /api/robot-control/base/stop`，远端固定
`/api/base/stop` 返回 HTTP 200。随后一次 `forward speed=0.12 duration_ms=800`
manual request 带 `confirm_hil_checklist=true`，但 PC 本地返回 HTTP 400
`command_rejected` / `operator_report_preflight_required`，响应内
`remote_http_status=null`。该结果是 gate 正常拒绝，不是运动失败；它证明 PC 未绕过
preflight 调用远端 `/api/base/manual`。

上一轮相机近黑结论仍参与 gate：`visible_content_proven=false` 是阻止真实手动运动的
合理缺口，除非 operator report 后续提供独立外部视频和可见相机 artifact refs，并且
PC gate 重新判定通过。当前普通首屏结构和所有危险字段保持不变：
`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
`robot_control_executed=false`。后续 gate 全部通过时，也只能通过 PC proxy 做 exactly
one 低速短时 jog 并立即 stop，不能直调远端 `/api/base/manual`。

## PC 普通用户简易控制契约 V1

2026-06-11 10:45 起，PC workstation 的默认首屏按 CEO 反馈恢复并锁定为
“普通用户简易控制台”。后续增加雷达、摄像头、建图、定位、移动或导航能力时，必须先
满足本节契约；不得为了暴露工程能力再次把首屏改成 debug / HIL / proof 面板。

不可变首屏契约：

- 默认首屏标题固定为 `Rober 小车控制台`。
- 默认首屏只允许一个短地址输入和五张普通用户卡片：`小车连接`、`实时画面`、`雷达`、
  `地图`、`移动/导航`。
- 默认可见动作只允许：`连接/刷新`、`打开画面/关闭画面`、`刷新雷达`、`刷新地图`、
  `地图列表`、`停止`。
- 默认首屏不展示工程词、协议词、证据词、调参控件或危险动作，包括但不限于：
  `HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`O6`、`O7`、
  `Mock`、`field manifest`、`task_id`、`key values`、`现场材料`、`检查路径`、
  `保存地图`、`开始建图`、`定位重置`、速度、时长、点动、导航目标坐标、raw/readback。
- 工程能力必须放在默认关闭的 `高级诊断` 或 `高级工具` 内；展开高级区是显式 operator 行为，
  不能影响普通首屏的第一眼观感。

渐进解锁契约：

- `实时画面`：首屏只提供打开/关闭和一句可读状态。WebRTC peer、ICE/SDP、video 元素、
  canvas pixel、设备枚举、近黑判断和 cleanup 细节只进高级诊断。图传成功也不解锁移动。
- `雷达`：首屏只提供 `刷新雷达` 和短状态；默认刷新路径使用
  `scan-proof refresh(start_runtime=true)` 的 no-motion 证据窗口。雷达 start/stop、
  scan hz、raw packet、TF、blocked reasons 和 lifecycle 细节只进高级诊断。雷达刷新通过
  只证明 LiDAR/TF 可观测，不等于可运动或可导航。
- `地图`/建图：首屏只提供 `刷新地图` 与 `地图列表`。`开始建图（高级）`、`保存地图`、
  map_name、artifact_path、map lifecycle HTTP 细节只进高级诊断。建图能力只能作为 no-motion
  SLAM/runtime evidence capture 渐进开放，不能在首屏暴露 Start/Save/Reset 风格按钮。
- `定位/路径检查`：首屏不出现 `检查路径`、`定位重置`、initialpose、AMCL、Nav2 goal 或
  坐标输入。定位重置、no-motion path generation、导航目标预检都只作为高级诊断里的
  “检查/预检”能力；通过只表示 readiness / preflight，不表示 NavigateToPose 已执行。
- `移动/导航`：首屏默认只显示普通状态和 `停止`。停止是 fail-safe 常驻动作；非 stop 手动移动、
  方向点动、速度/时长、键盘连续控制、地图点击目标、自动导航下发全部默认隐藏。只有在真实
  operator report、可见图传、轮速反馈、LiDAR delta 和外部视频引用等现场材料全部通过后，
  才能在高级诊断中做一次低速短时 jog；首屏仍不得出现方向按钮。

后续编码验收口径：

- 前端回归必须继续以 `.simple-user-console` 为普通首屏作用域，断言五张卡片存在，且上述禁词
  在该作用域内全部不存在。
- 新增任何 PC 能力时，必须同时给出两类断言：普通首屏不被污染；高级诊断中相应能力可见且
  仍保持 fail-closed 字段。
- Browser/DOM smoke 需要覆盖桌面视口下首屏第一屏，不得只靠组件单测证明。
- PC build/test/lint 通过只能证明软件侧 UI/contract；真实上车 evidence capture 仍需分别
  记录雷达、实时图传、建图、定位/路径检查、手动移动的真实 artifact。
- OKR 进度不得因为新增首屏按钮或本地 fixture 预览上调；只有真实上位机、真实 browser 或
  真实现场 artifact 可提升 O7 证据质量。

下一步 owner 和最短执行路径：

- 主责 owner：`full-stack-software-engineer` 负责 PC 简易首屏 contract 的代码回归和 UI
  smoke；涉及上位机 endpoint 稳定性时，只请 `robot-software-engineer` 补固定 API 事实，
  不让工程细节进入首屏。
- 最短路径 1：先保持首屏五卡片不变，补 `.simple-user-console` 禁词测试与 Browser smoke
  作为每次 PC 能力变更的固定验收。
- 最短路径 2：按真实 evidence capture 顺序推进：`打开画面` 修到可见内容 → `刷新雷达`
  稳定 no-motion scan proof → `刷新地图/地图列表` 产出地图材料 → 高级诊断做定位/路径
  预检 → 材料齐备后高级诊断执行 exactly one 低速短时 jog 并 stop。
- 最短路径 3：每一步只把普通用户需要知道的结果同步到五张卡片，把 endpoint、raw JSON、
  proof flags、HIL 材料和失败根因留在高级诊断。

## 禁止声明

第一阶段不得声明完成：
- 真实 ROS2 runtime
- 真实 Nav2/fixed-route runtime pass
- 真实路线采集或关键帧实景验证
- 真实电梯、WAVE ROVER 运动、串口反馈或 HIL pass
- dropoff/cancel completion、delivery success 或安全控制
- 真实手机/browser proof
- 4G、云端、OSS/CDN 生产链路
- 真实训练、真实标注、真实投放或真实交付成功
- O7 实时地图/机器人位置、电梯状态链、历史路线回放、标注提交、ASR/TTS runtime、手控或寻路 dispatch
- Robot Control V1 已经放开真实持续手控、真实 `/cmd_vel`、真实自动导航、Nav2 goal、radar start、keyboard control 或 map click goal
- PC Map Runtime Controls V1 已经证明地图质量、Nav2 可行驶、真实运动、HIL 或 delivery success
- PC Localization Reset Controls V1 已经证明路径执行、真实运动、HIL 或 delivery success
- PC Manual HIL Gate Current Evidence 已经证明真实非零手动运动、HIL movement pass、
  `safe_to_control=true` 或可绕过 PC proxy 直接调用 `/api/base/manual`

普通首屏不提供工程 Start/Save/Reset、Confirm、Cancel、Dropoff、Collect、Nav2 goal、
手控、速度/点动或任何真实运动/交付控制入口。当前仅 `高级诊断` 地图详情提供
no-motion map runtime 的 `开始建图（高级）` / `保存地图` 固定入口；它们只触发
LiDAR+SLAM 建图材料采集，不等于真实底盘控制、Nav2 执行、delivery 或安全放行。

## 运行与验证

工作站验证只使用 Node/Vue gate：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
```

删除旧 Python 的范围检查使用 PowerShell：

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

该检查应返回空结果。上述验证只证明 PC 工作站软件链路，不证明真实机器人、真实硬件、真实手机、真实云链路或真实交付成功。
