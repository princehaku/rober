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
- `src/components/` 只做展示与本地交互，不直接拼 API URL，不发明机器人状态。`RobotControlConsolePanel.vue` 通过 client 层调用 Node `GET /api/robot-control/summary` 和 O6 consumer detail adapter；Vue 不直接跨域访问上位机 Robot API。它的默认首屏必须保持 `Rober 小车控制台` + `.simple-user-console` 五卡片的普通用户视图，短状态、少量按钮和可停止入口留在首屏，`task_id`、`O6`、`O7`、`HIL`、`proof`、`/cmd_vel`、`/api/base/manual`、`field manifest` 等工程字段都必须折叠到默认关闭的 `高级诊断`。`O7FixturePreviewPanel.vue` 通过 client 层调用 fixture preview、probe、archive fixture 和 O6 consumer read adapter；route replay 主路径消费 consumer detail，旧 archive fixture player 只作为次路径 / debug fallback；页面不自动读取本地路径。

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
- `robotControlSummary.ts` 是 Robot Control V1 的唯一 Robot API 代理。它只接受 `baseUrl`，拒绝空值、非 HTTP、credentials、query/hash、非回环或非 RFC1918 局域网 host；白名单读取 `/api/status`、`/api/radar/status`、`/api/radar/scan-proof/latest`、`/api/map/proof/latest`、`/api/localize/proof/latest`、`/api/nav2/status`、`/api/nav2/proof/latest`、`/api/operator/report`、Camera/LiDAR/Base status/latest/readback 类 GET endpoint，并额外公开固定 POST 代理 `POST /api/robot-control/base/manual?baseUrl=...`、`POST /api/robot-control/base/first-jog?baseUrl=...` 与 `POST /api/robot-control/base/stop?baseUrl=...`。这些 POST 只能分别转发到上位机固定 `/api/base/manual` 或 `/api/base/stop`，不能拼任意路径，且所有响应继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。2026-06-11 本轮进一步把非 stop 点动升级为双门禁：`confirm_hil_checklist=true` 只是第一道门，Node 代理还必须在调用远端 `/api/base/manual` 之前短超时 GET 最新上位机 `/api/operator/report`，并从顶层或 `latest_result.operator_report` 的 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`，以及 `structured_hil_claims` 的 `external_video_recorded + external_video_ref`、`visible_content_proven + camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven + wheel_feedback_ref`、`physical_motion_lidar_delta_proven + scan_delta_ref` 得到完整现场材料；`real_route_map_proven` 只作为后续导航门禁材料，`delivery_success` 永远不作为 manual 放行条件。材料不足、fetch 失败、bad JSON、非 object 或危险 true 字段命中时，本机直接返回 HTTP 400 `command_rejected` / `failure_reason=operator_report_preflight_required`，响应带 `operator_report_preflight.missing_fields`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，并且不会调用远端 `/api/base/manual`。2026-06-21 新增 first-jog 固定入口用于打破首次运动证据循环：它仍要求 `operator_present/physical_clearance_confirmed/emergency_stop_ready=true` 和外部视频或可见相机 ref，但不把 `wheel_feedback_lr_nonzero_proven` 与 `physical_motion_lidar_delta_proven` 作为前置材料；这两个字段只能作为首次低速试动后的输出证据。first-jog 通过后也只转发一次 clamp 后的 `/api/base/manual`，不会把顶层 proof flags 置 true。stop 仍可不经材料 gate 发送到固定 `/api/base/stop`，作为 fail-safe。Map lifecycle 也只开放固定代理：`GET /api/robot-control/map/list?baseUrl=...`、`POST /api/robot-control/map/start?baseUrl=...`、`POST /api/robot-control/map/save?baseUrl=...`、`POST /api/robot-control/map/reset?baseUrl=...`；它们只能分别转发到上位机 `/api/map/list`、`/api/map/start`、`/api/map/save`、`/api/map/reset`，POST body 只允许短 `map_name` 与 `artifact_path`，未知字段或超长字段直接本机拒绝。2026-06-11 新增现场材料提交固定代理 `POST /api/robot-control/operator/report?baseUrl=...`，只能转发到上位机 `/api/operator/report`；body 只允许 `operator_present`、`evidence_ref`、`physical_clearance_confirmed`、`emergency_stop_ready`、`observed_motion`、`observed_stop`、`reported_at`、`operator_notes`，以及 `structured_hil_claims` 内的 `external_video_recorded`、`external_video_ref`、`visible_content_proven`、`camera_artifacts_ref`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_ref`、`physical_motion_lidar_delta_proven`、`scan_delta_ref`、`real_route_map_proven`、`route_map_ref`、`delivery_success`、`site_state`。未知字段、错类型字段或顶层 `delivery_success/safe_to_control` 之类危险字段直接本机 400 拒绝，不透传给上位机。该 report 代理绝不调用 `/api/base/manual`、`/cmd_vel`、Nav2 goal、map/radar start，且响应顶层固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`；即使 `structured_hil_claims.delivery_success=true`，也只作为人工材料 claim 展示在高级诊断。代理采用端点级只读超时预算：`/api/status`、`/api/camera/health`、`/api/camera/devices` 使用更宽读取窗口，其他 proof/latest/readback 继续保持短超时；这样可以容忍真实上位机慢一点的状态聚合，同时不会放宽 URL 白名单、固定 endpoint 限制或危险字段扫描。它递归扫描 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`robot_control_executed=true` 等危险字段，命中即 blocked；map lifecycle 若观察到 `command_result.executed=true` 也会在 PC 响应中标记 blocked，但顶层 `robot_control_executed` 仍固定为 false。
- 2026-06-25 当前普通手控口径覆盖上面 2026-06-11 的双门禁：`POST /api/robot-control/base/manual` 和键盘 pulse 的非 stop 动作只要求本地 `confirm_hil_checklist=true`、固定方向枚举、速度/时长 clamp；Node 不再为普通低速手控读取 `/api/operator/report` 或要求 wheel/LiDAR/视频材料完整。operator report 仍保留为高级证据提交与送达/验收材料来源，不作为普通低速手控预检。
- `o7LabelingPreview.ts` 只读 query 指定的本地 `trashbot.o7.labeling_fixture.v1` JSON，并生成 `trashbot.o7.labeling_preview.v1` 安全摘要；坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/submit/rollback/export claim 均 fail-closed。
- `o7SafeCommandPreview.ts` 只读 query 指定的本地 `trashbot.o7.safe_command_fixture.v1` JSON，并生成 `trashbot.o7.safe_command_preview.v1` 安全摘要；坏 JSON、缺文件、unsupported schema、unsafe copy、success/control/dispatch/manual/navigate/keyboard/real command API/real robot ACK/robot control executed/ACK success/HIL or hardware verified claim 均 fail-closed。

`pc-tools/evidence/fixtures/**` 是 Evidence Tools 的 JSON fixture 来源。`pc-tools/route/` 只保留说明；Route Debug 的实际读取能力在 `pc-tools/workstation/src/server/routeDebugLoader.ts`。

## 功能入口

- Route Debug：通过 Node Route JSON Loader 读取本地 status/task/reconciliation JSON，生成 safe summary。
- Evidence Tools：索引 `pc-tools/evidence/fixtures/**/*.json`，展示 JSON fixture 资产分组。
- Hardware Materials：`GET /api/hardware/wave-rover/material-coverage` 扫描 `pc-tools/evidence/fixtures/wave_rover_*` 下的 WAVE ROVER 材料组，识别 `feedback_T1001.log`、项目侧 `odom_once.jsonl`、项目侧 `imu_once.jsonl`、项目侧 `battery_once.jsonl`、`operator_hil_report` / `operator_hil_report.json` 的 present/missing coverage，并在 Vue 面板中展示 `fixture_groups`、`gaps`、vendor source、串口参考、命令事实和 `not_proven_boundaries`。兼容旧路径 `GET /api/tools/hardware-materials`，但新 UI 入口使用前者。
- Training/Labeling：`GET /api/tools/training-labeling` 扫描 `pc-tools/training/` 和 `pc-tools/labeling/` 下的非 Python 资产，返回两个工作区的 roots、asset counts、manifest candidates、image/annotation counts、readiness、missing requirements 和 next actions；仍明确未接真实训练或标注流水线。
- Robot Control：`RobotControlConsolePanel` 是工作站默认首屏，不再藏在 `WorkstationTabs` 内。`GET /api/robot-control/summary?baseUrl=<robot-api-base-url>` 继续作为状态入口，路线、O7 控制台、预览、证据、硬件、数据和安全边界等工程 tab 统一下沉到默认关闭的 `高级工具`。普通用户首屏必须保持 `Rober 小车控制台` + `.simple-user-console` 五卡片、短状态和少量普通按钮；`task_id`、`O6`、`O7`、`HIL`、`proof`、`key values`、`/cmd_vel`、`/api/base/manual`、`field manifest` 等工程词必须留在默认关闭的 `高级诊断`。`task_id`、O6 base URL、Mock/field manifest、peer/ICE/SDP、readback table、O3 proof summary、route replay、map lifecycle HTTP 细节、raw evidence/readback、非 stop 点动、速度/时长输入、HIL checklist、检查路径、导航目标预检、Nav2 目标执行、送达确认、定位重置和 proof flags 都收进默认关闭的 `高级诊断`。首屏的 `地图` 卡片现在允许普通用户动作 `刷新地图 / 地图列表 / 重新建图 / 保存地图`；其中 `重新建图` 和 `保存地图` 仍只走固定 map lifecycle 代理，不暴露 `map_name`、`artifact_path`、Start/Reset 风格按钮或任何 ROS/串口参数。首屏的 `移动/导航` 卡片只保留最小安全确认、普通状态、`重新定位`、`现场画面记录`、`记录画面`、`试动一下` 和 `停止`；不再显示额外 `移动前检查` 按钮，也不显示自动导航、最近证据摘要、方向点动、路径检查、速度上限、时长上限、目标坐标、送达确认或 HIL checklist。`记录画面` 只把人工填写的视频编号作为 external video ref 提交到固定 operator report 代理，不伪造轮速、LiDAR delta、route map 或 delivery success；`试动一下` 只调用固定 first-jog 代理，当前无可视材料时显示“还需要先记录现场画面，小车没有移动”。当前普通首屏仍只支持一次性低速短时 jog；受限 Nav2 目标执行和送达确认只允许在默认关闭的高级诊断里显式勾选确认后触发。2026-06-11 新增 `/api/operator/report` 结构化 HIL 材料 readback：summary 会把 `operator_report_latest` 顶层现场确认和 `structured_hil_claims` 压缩成 `operator_hil_material_summary`，仅在默认关闭的 `高级诊断` 中展示 operator_present、physical_clearance、emergency_stop、外部视频、相机可见、轮速反馈、LiDAR delta、route/map、delivery claim、site_state、evidence_ref 和 report status。同区块新增“现场 HIL 材料”高级提交表单，允许现场人员填写 evidence_ref、site_state、外部视频 ref、相机 artifact ref、feedback ref、scan delta ref、route/map ref、operator notes 和若干 checkbox，然后通过 `提交现场材料（高级）` 走 workstation 固定 POST 代理提交给真实上位机。提交成功后页面自动刷新 Robot Control summary，并在高级诊断显示最近 submit 的 proxy status、HTTP、failure、rejected fields、dangerous fields 和 request claims。该表单不进入 `.simple-user-console` 首屏，首屏不得出现 HIL、delivery_success、structured_hil_claims、外部视频、轮速反馈等工程词。只有 `operator_report_latest` readback 中的精确人工 claim 路径（含真实上位机回显的 `latest_result.operator_report.structured_hil_claims.delivery_success`）不触发 hard-block；其它 endpoint/payload 伪造 `structured_hil_claims.delivery_success=true`，或任何非 claim 路径的 `delivery_success=true`、`hil_pass=true`、`safe_to_control=true` 仍然 fail-closed。
- 2026-06-23 05:05 起，普通首屏不再显示 `小车地址` 输入框或默认上位机 URL；页面固定使用默认上位机 `http://192.168.1.11:8787` 自动加载 summary，首屏只显示“默认小车 / 已使用默认地址 / 连接刷新”。地址输入与恢复默认地址按钮下沉到默认关闭的 `高级诊断 -> 连接详情`，仅用于高级联调；恢复默认不会自动发送控制动作，也不会调用 Nav2、manual、delivery complete 或 `/cmd_vel`。
- 2026-06-23 21:05 起，普通首屏 `默认小车` 行会展示短地址 `192.168.1.11:8787`，用于现场确认当前固定上位机；仍不展示完整 `http://...` URL 输入框，改地址继续只能在默认关闭的高级连接详情里进行。该展示只读本页 base URL，不自动刷新、不调用 Nav2、manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 08:10 起，PC 工作站 Node API 支持通过 `HOST` 环境变量覆盖监听地址，并新增 `npm run api:public`，方便局域网访问。2026-06-25 起默认公开端口统一改为 `7001`：`npm run api`、`npm run api:public`、`npm run dev` 和 `npm run dev:public` 默认都是 `HOST=0.0.0.0 PORT=7001`，仍可用 `HOST/PORT` 覆盖。public 脚本只暴露 PC 工作站本机服务，不自动执行 Nav2、manual、delivery complete、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 13:45 起，Node API public 启动前会先探测监听地址；当 `0.0.0.0:7001` 被其他进程占用时，直接输出 `address already in use`、`lsof/netstat` 排查命令和 `PORT=<free-port> npm run api` 兜底命令，不再先打印“listening”再抛 Node 栈。该启动诊断只影响 PC 工作站可访问性，不会调用 Nav2、manual、delivery complete、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 15:35 起，PC 工作站 Node API 默认监听地址使用 `0.0.0.0`；2026-06-25 起默认端口使用 `7001`。直接运行 `npm run api` 即可让同局域网设备访问构建后的 Node/Express 工作站，仍可用 `HOST=<host> PORT=<port>` 在启动前覆盖。`api:public` 保留为兼容旧入口；端口冲突提示同步改为 `PORT=<free-port> npm run api`。该改动只影响 PC 工作站 HTTP 可达性，不自动执行 Nav2、manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 23:55 起，Vite 开发入口也同步为默认 `0.0.0.0`；2026-06-25 起默认端口使用 `7001`。直接运行 `npm run dev` 就能在同局域网访问前端开发页，仍可用 `HOST=<host> PORT=<port>` 覆盖。`npm run api` 继续是 Node/Express 构建后入口，两个入口不能同时占用 7001；这只改变 PC 工作站 HTTP 可达性，不自动执行 Nav2、manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-25 16:55 起，Robot Control summary 的地图叠图外参读取从只看 `/api/localize/proof/latest` 扩展为按 `localize_proof_latest -> nav2_proof_latest -> nav2_status -> status` 顺序查找结构化 `base_link_to_laser_frame_transform`。真实上位机 O10 timeout fallback 若已经从 `/tf_static` 读到 `base_link -> laser_frame`，PC 也能把该外参提升到 `o3_proof_summary.frame_transforms.base_link_to_laser_frame`，用于后续雷达点投影；没有显式数值时仍保持 `null`，前端不能猜安装偏移。该读取只消费现有 proof/latest 和 status，不发布 `/initialpose`，不启动 Nav2，不执行 NavigateToPose，不调用 manual/keyboard/stop 或 `/cmd_vel`。
- 2026-06-25 18:40 起，普通首屏地图 caption 会在路线存在时显示路线叠图状态：最新 no-motion planner path preview 已按真实地图 `origin/resolution/width/height` 转成蓝色 polyline 时显示 `路线已显示 N/M 个点`；路线已生成但地图画面未加载时显示 `路线已准备，刷新地图画面查看`；没有路线时不额外显示路线文案，保持默认首屏简洁。该 caption 只消费 `GET /api/robot-control/summary` 里的 `path_preview_points` 和只读 map preview，不调用 Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 2026-06-25 18:50 起，同一条 no-motion planner path preview 还会在地图上显示路线端点：有真实执行目标 marker 时只补 `起点`，没有执行目标时显示 `起点/终点`。端点 marker 来自 path 首尾点，只说明规划路线首尾，不代表机器人当前位置，也不会放开发车门禁或调用 Nav2 execute/manual/keyboard/delivery/`/cmd_vel`。
- 2026-06-25 22:00 起，普通首屏“行程操作”在地图已显示路线点时，把可执行提示和红色按钮从泛化 `执行行程` 收敛为 `执行图上路线`，并在提示里写明“地图上已显示路线 N 个点”。这只让 operator 知道即将执行的是地图里看到的路线；实际执行仍走原固定 Nav2 execute 代理和后端定位/路线复查 gate，不自动发车、不调用 manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 2026-06-25 21:00 起，普通首屏地图会区分“当前路线”和“最近路线”：如果 `path_preview_points` 仍存在但 `path_generated/path_generation_succeeded` 没有证明当前 planner 成功，地图继续照实画出最近路线点，但 caption 改为 `最近路线已显示 N/M 个点，待重新规划`，端点状态也标为最近路线。该提示只修正 WYSIWYG 语义，不自动重新规划、不执行 Nav2、不调用 manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 2026-06-25 19:20 起，普通首屏地图 caption 新增 `坐标口径`：有 map-frame 机器人位置时明确说明雷达点和路线已贴到地图；没有机器人位置但有 scan preview 时说明雷达只是车身局部轮廓、不贴地图；只有路线时说明路线仍按地图坐标显示但雷达不贴图。该提示只消费现有 summary/map preview，不刷新 proof、不启动雷达/建图、不调用 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 2026-06-11 15:50 起，首屏“实时画面”卡片不再把 `video` 会话打开直接表述成乐观成功。workstation 会在浏览器本地把 `<video data-testid="robot-camera-preview-video">` 缩放绘制到临时 canvas，并只在内存里计算 `mean_luma`、`max_luma`、`non_black_ratio_ge16` 三个保守指标。普通用户首屏只显示 `未打开 / 连接中 / 已打开 / 画面可见 / 画面偏暗 / 失败` 六种短状态；其中 `画面可见` 只有在三项指标同时过保守阈值时才允许显示，`画面偏暗` 会提示“画面太暗，先检查镜头/光线”，避免把 near-black 640x480 帧误说成“画面已打开”。采样失败不会把 `safe_to_control`、`primary_actions_enabled`、`delivery_success`、`robot_control_executed` 提升为 true，也不会把工程词带回首屏。`sample_status`、`mean_luma`、`max_luma`、`non_black_ratio_ge16`、`sampled_at`、`sample_attempts` 和失败原因只保留在默认关闭的 `高级诊断`。
- 2026-06-25 17:50 起，普通首屏“实时画面”在 Robot API readback 显示 `camera.status=ready` 或 `devices_status=loaded`、但本页还没有打开 WebRTC 画面时，仍保持状态 `未打开`，但提示改为 `相机在线，点打开画面。`。这只区分“相机服务在线”和“画面已经打开”，不会自动调用 `/api/camera/offer`、`/api/camera/first-frame/probe`、Nav2、manual、keyboard、stop、delivery 或 `/cmd_vel`。
- 2026-06-25 17:55 起，普通首屏“实时画面”新增固定 16:9 画面框。未打开、连接中、失败或 `画面偏暗` 时，状态和短提示直接显示在画面框内；只有本地 `<video>` 像素采样确认 `画面可见` 后才移除遮罩，让真实视频帧本身成为画面主体。这只是前端 WYSIWYG 呈现，不会自动打开 WebRTC、不调用 first-frame probe、Nav2、manual、keyboard、stop、delivery 或 `/cmd_vel`。
- 2026-06-22 起，PC 代理的 `POST /api/robot-control/camera/first-frame/probe` 会额外透出 `visible_content_candidate`、`sample_path`、`sample_write_ok`、`max_luma` 和 `dynamic_range_luma`。这些字段只放在默认关闭的 `高级诊断`，用于复核上位机是否真的写出可追溯样张；普通首屏仍只显示短状态和“打开画面/关闭画面”。本轮真实上位机 probe 已生成 `/root/rober/onboard/runtime/camera/first_frame_probe_1782060889824.jpg`，并用该 ref 提交 operator report，使 first-jog readiness 从缺 `external_video_or_visible_camera` 变为 `ready_for_first_jog`。该材料不证明轮速反馈、LiDAR 位移、路线地图或 delivery success。
- 2026-06-22 起，普通首屏在 `试动一下` 返回 `wheel_feedback_lr_nonzero_proven=true` 后才显示 `保存轮速证据`。该按钮只把 first-jog 响应里的 wheel raw L/R、during-motion T1001 帧数和短 evidence ref 写入固定 `POST /api/robot-control/operator/report` 代理，不再次调用 `/api/base/manual`、Nav2 goal、stop 之外的控制接口，也不自动补齐 LiDAR delta、real route map 或 delivery success。普通用户看到的状态只保留“轮速证据已拿到/已保存”这类短句；完整 `structured_hil_claims` 仍留在默认关闭的 `高级诊断`。
- 2026-06-22 13:23 起，默认关闭的 `高级诊断` 顶部新增 `目标收口进度`，把 CEO 当前四个收口目标压成只读 checklist：`wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控`。该面板只消费当前已读 summary、Nav2 latest、delivery latest/check/complete、first-jog 和 base feedback sample 结果，不自动发车、不提交 operator report、不调用 delivery complete，也不把任何 success 字段提升为 true。普通首屏继续不显示该目标进度或工程词。
- 2026-06-22 15:34 起，`目标收口进度` 的 `PC 键盘连续手控` 不再只因为 summary 存在 `bounded_repeating_manual_pulse` 合同就显示满足；必须同时满足当前 manual gate，也就是现场 checklist、operator report 材料、wheel raw L/R 非零和 LiDAR motion delta 都已经齐备。合同存在但材料未齐时，高级诊断显示“键盘入口已在，仍需补齐...”，避免把“入口实现”误判成“真实可手控”。
- 2026-06-22 18:05 起，普通首屏“本轮进度”、键盘面板和 `启用键盘` 按钮统一要求 summary 同时声明 `safe_command_boundary.keyboard_control_mode=bounded_repeating_manual_pulse` 与 `keyboard_reuses_manual_gate=true`。即使现场材料 gate 已满足，只要 summary 未读到该合同，首屏仍显示“还差：键盘入口”，按钮保持禁用，高级诊断显示“键盘合同未从 summary 读到”；这样避免 UI 在后端合同缺失或旧上位机响应下误提示键盘可用。
- 2026-06-23 14:00 起，普通首屏键盘面板新增四个屏幕方向键；它们只在 `启用键盘` 后可用，并完全复用既有 bounded repeating manual pulse、manual gate、松手 stop、移出 stop 和 `/api/robot-control/base/manual` / `/api/robot-control/base/stop` 固定代理。未启用键盘或材料 gate 未满足时按钮保持 disabled，不新增 `/cmd_vel`、Nav2 或绕过 operator report preflight 的控制通道。
- 2026-06-22 13:26 起，页面初载在读取 Robot Control summary 后，会自动预载两个固定只读 GET 代理：`GET /api/robot-control/nav2/goal/execution/latest` 与 `GET /api/robot-control/delivery/latest`，用于让 `目标收口进度` 立即显示最近 Nav2 goal 与 delivery gate 状态。该预载不调用 `POST /api/robot-control/nav2/goal/execute`、`POST /api/robot-control/delivery/complete`、`/api/base/manual`、`/cmd_vel` 或任何运动/送达确认接口。
- 2026-06-22 13:40 起，普通首屏 `移动/导航` 卡片新增 `任务收口` 只读状态：显示 `未读取 / 检查中 / 待行程结果 / 待确认 / 已送达`，并提供 `刷新送达状态` 与 `复查送达条件` 两个普通按钮。它们分别只调用固定 `GET /api/robot-control/delivery/latest` 和 `POST /api/robot-control/delivery/check`（后端固定 `confirm=false`），不会调用 `POST /api/robot-control/delivery/complete`、`POST /api/robot-control/operator/report`、Nav2 goal、`/api/base/manual` 或 `/cmd_vel`。首屏只展示“行程已完成，还需补齐 N 项送达确认”这类短句，不显示 `delivery_success`、`/api/delivery`、blocked field name、route/map ref 或 raw readback；真正送达确认和 checklist 仍只在默认关闭的高级诊断里显式操作。
- 2026-06-23 13:41 起，`GET /api/robot-control/delivery/latest`、`POST /api/robot-control/delivery/check` 和最终 `delivery/complete` 代理会显式返回 `missing_required_material`，普通首屏会把该数组与 `blocked_reasons` 合并后生成“上位机还差：现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达”等提示。这样真实上位机 latest 即使 `blocked_reasons` 为空，也能直接展示送达缺项；该读取不自动复查、不提交 operator report、不调用 delivery complete、不执行 Nav2、manual、stop、keyboard pulse 或 `/cmd_vel`。
- 2026-06-22 13:45 起，普通首屏同一 `任务收口` 区新增 `准备送达材料` 与 `保存送达草稿`。`准备送达材料` 只复用既有 `prefillDeliveryMaterialRefs`：读取最近 Nav2 execution ref、必要时调用固定 camera first-frame probe 获取样张 ref，并刷新 delivery latest；不提交 operator report、不确认送达。`保存送达草稿` 只在视频材料和行程材料都已预填后调用固定 `POST /api/robot-control/operator/report`，写入 `delivery_material_draft_not_operator_confirmed`、`observed_motion=false`、`observed_stop=false`、nested `delivery_success=false`；它不会调用 `delivery/complete`、Nav2 goal、manual 或 `/cmd_vel`。首屏只显示 `可准备 / 已预填 / 已保存` 等短状态，不展示 ref 和工程字段。
- 2026-06-22 18:55 起，`保存送达草稿` 成功后会自动调用一次固定 `POST /api/robot-control/delivery/check?baseUrl=...`，也就是 `confirm=false` 的送达缺口复算；这样现场保存材料后立刻看到剩余确认项。该自动复算不调用 delivery complete、不写送达成功、不发车。
- 2026-06-22 19:15 起，`保存送达草稿` 成功后页面会自动聚焦到普通首屏的 `最终确认` 区，并把材料状态文案改为 `请完成下方最终确认`；该跳转只改变页面焦点，不自动勾选、不提交送达确认、不调用 delivery complete。
- 2026-06-22 19:25 起，普通首屏 `最终确认` 区新增 `勾选安全三项`，只在本地勾选“人在旁边可接管 / 周围安全 / 停止手段就绪”，减少重复点击；它不勾选到达、停止、材料核对或确认送达，也不提交 operator report、delivery complete、manual 或 `/cmd_vel`。
- 2026-06-22 19:35 起，普通首屏 `最终确认` 区新增 `已看到到达并停稳`，只在 operator 显式点击后本地勾选“已观察到到达/移动”和“已观察到停止”；它不勾选材料核对或确认送达，也不提交 operator report、delivery complete、manual 或 `/cmd_vel`。
- 2026-06-22 19:45 起，普通首屏 `最终确认` 区新增 `材料已核对`，只在 operator 显式点击后本地勾选“视频和行程材料已核对”；它不勾选确认已投放/送达，也不提交 operator report、delivery complete、manual 或 `/cmd_vel`。
- 2026-06-22 19:55 起，普通首屏 `最终确认` 区新增 `确认已投放/送达` 本地按钮，只在 operator 显式点击后勾选最后一项；它仍不提交 operator report 或 delivery complete，必须再点击红色 `确认送达` 才会进入后端 delivery gate。
- 2026-06-23 01:32 起，普通首屏 `最终确认` 区新增 `全部已确认` 本地按钮，用于现场人员一次性勾选安全、到达停稳、材料核对和确认投放七项。它仍只修改本页 checkbox，不保存材料、不提交 operator report、不调用 delivery complete、不执行 Nav2、manual、stop 或 `/cmd_vel`；红色 `确认送达（不发车）` 仍是唯一进入后端 delivery gate 的动作。
- 2026-06-23 02:20 起，普通首屏 `最终确认` 区会显示红色 `确认送达（不发车）` 的后端 gate 结果：通过时显示 `送达提交已通过：上位机已确认送达完成`，被 gate 拒绝时显示 `送达提交未通过：还差...` 的普通缺口摘要。该提示只消费本次 `delivery/complete` 响应，不自动重试、不再次提交 operator report、不执行 Nav2、manual、stop 或 `/cmd_vel`。
- 2026-06-23 07:20 起，普通首屏 `执行行程` 成功后会自动聚焦到 `任务收口` 的送达材料状态区，让现场人员自然看到 `准备送达材料` 下一步。该聚焦只改变滚动位置和焦点，不自动准备材料、不提交 operator report、不调用 delivery complete、manual、stop 或 `/cmd_vel`；失败、旧行程或缺反馈样本不会触发该跳转。
- 2026-06-23 07:35 起，普通首屏 `准备送达材料` 成功预填视频和行程材料后会自动聚焦 `保存送达草稿（不确认）`。该聚焦只帮助现场继续下一步，仍不自动保存草稿、不提交 delivery complete、不执行 Nav2、manual、stop 或 `/cmd_vel`；草稿保存成功后才继续聚焦最终确认区。
- 2026-06-23 07:50 起，普通首屏 `全部已确认` 或最后一步 `确认投放/送达` 让最终确认条件满足后，会自动聚焦红色 `确认送达（不发车）` 按钮。该聚焦不自动提交 operator report、不调用 delivery complete、不执行 Nav2、manual、stop 或 `/cmd_vel`，仍要求现场人员再显式点击一次红色按钮。
- 2026-06-23 08:05 起，`确认送达（不发车）` 通过上位机 delivery gate 后，普通首屏会自动聚焦到 `键盘手控` 面板，提示现场进入最后的 PC 键盘连续手控验证。该聚焦不启用键盘、不发送 keyboard pulse、不调用 manual、stop、Nav2 或 `/cmd_vel`；仍必须先点 `启用键盘（按键才动）`，再按住方向键/WASD 产生连续脉冲证据。
- 2026-06-23 08:20 起，若 delivery gate 通过时键盘 gate 已经满足，普通首屏会优先聚焦 `启用键盘（按键才动）` 按钮；若键盘 gate 仍缺材料，则优先聚焦 `复查手控条件` 按钮并显示缺项。该聚焦不自动启用键盘、不发送 keyboard pulse、manual、stop、Nav2 或 `/cmd_vel`。
- 2026-06-23 12:15 起，普通首屏 `本轮进度` 的 `去送达` 不再只聚焦整个最终确认区，而是按当前送达缺口直达下一手动作：缺本轮行程时回到 `行程执行`，缺行程/视频材料时聚焦 `准备送达材料` 或 `保存送达草稿（不确认）`，材料齐但现场确认未完成时聚焦 `全部已确认`，全部勾选后聚焦红色 `确认送达（不发车）`。该聚焦只改变滚动位置和焦点，不自动准备材料、不自动保存草稿、不提交 operator report、不调用 delivery complete、Nav2、manual、stop、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 14:15 起，当送达草稿覆盖 first-jog 基础安全确认且仍保留现场画面材料时，普通首屏 `移动/导航` 按钮行直接显示 `恢复试动确认`，`本轮进度 -> 去恢复确认` 也优先聚焦这个顶部按钮。该按钮只复用固定 operator report 代理恢复 `operator_present/physical_clearance/emergency_stop` 与已有视觉材料，不调用 first-jog、manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。
- 2026-06-23 14:30 起，`恢复试动确认` 成功后若普通首屏仍判断雷达未运行，页面会先聚焦 `启动雷达` / `刷新雷达`，雷达已运行时才聚焦 `试动一下`。该跳转只改变焦点顺序，不自动启动雷达、不自动试动、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 23:50 起，上一条“恢复后先聚焦雷达”的口径被 wheel 优先流程替换：`恢复试动确认` 成功后直接回到 `wheel raw L/R 非零` 的下一手动作，通常是 `开始低速试动读非零 L/R` 或轮速卡点确认；雷达仍留给行程执行和 LiDAR 移动记录，不再抢占 wheel raw L/R 复验焦点。该跳转仍只移动焦点，不自动点击试动、不启动雷达、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 13:30 起，普通首屏 `本轮进度` 的 `去行程/去行程卡点` 不再只聚焦 `行程操作` 大面板，而是按当前行程缺口直达下一手控件：未勾选安全确认时聚焦行程前确认 checkbox，确认后聚焦红色 `执行行程`，已有本轮行程材料时聚焦 `重新读取行程（只读）`。该聚焦只改变滚动位置和焦点，不自动勾选、不调用 Nav2 preflight/execute、不提交送达、不发送 manual/stop 或 `/cmd_vel`。
- 2026-06-23 13:25 起，Robot Control summary 会把上位机 `/api/radar/status` 中 `controls.start.command.configured` 压缩成 `readback_summary.lidar.radar_start_configured`。当该值明确为 `false` 时，普通首屏不再提示现场继续点 `启动雷达`，而是显示 `上位机雷达启动命令未配置`、禁用普通雷达启动按钮并把行程/送达/键盘 LiDAR delta 的下一步改成 `先配置雷达启动命令`。该提示只消费只读 radar status，不自动配置上位机、不启动雷达、不执行 Nav2、manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-25 起，PC workstation 的 Node API 和 Vite dev 默认公开入口改为 `0.0.0.0:7001`，避开本机 Clash Verge 常用的 `7071`。`HOST/PORT` 仍可覆盖，`api:public` / `dev:public` 也显式使用 `7001`；该变更只影响 PC 工具监听地址，不改 Clash 配置、不调用上位机控制接口、不执行 Nav2、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。
- 2026-06-25 起，普通首屏区分 `雷达未运行` 和 `雷达待刷新`：当上位机只读状态显示 `lifecycle_running=true` 但最新 scan proof stale/incomplete 时，首屏显示“雷达待刷新”，行程/送达/键盘下一步都指向 `刷新雷达`，不再提示重复 `启动雷达`。该刷新仍只走固定 radar proof refresh，不触发底盘、Nav2 execute、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-25 起，普通首屏 `实时画面` 保留固定尺寸的真实 `<video>` 画面框，`地图` 卡片新增现场地图视口：只消费已有 summary、map refresh、map lifecycle 和 operator route/map readback；读到地图时显示 `地图可见/地图记录已读取`，读不到定位时明确显示 `位置未读到`，雷达 marker 直接显示 `雷达已运行/雷达待刷新/雷达未运行`。该视口不伪造机器人坐标，不显示 route/map ref、endpoint 或 proof 字段，不自动启动雷达/建图/发车，也不调用 Nav2 execute、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。
- 2026-06-25 14:50 起，地图视口优先读取真实地图画面：PC 后端新增 `GET /api/robot-control/map/preview?baseUrl=<robot-api-base-url>`，固定只读转发到上位机 `/api/map/preview`，只接受 PNG data URL 摘要并继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。普通首屏新增 `刷新地图画面`，加载成功时在地图卡片内显示真实 YAML/PGM 渲染图，失败或缺图时才回退到原来的状态网格；该刷新不调用 `/api/map/start`、Nav2 execute、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。
- 2026-06-25 15:00 起，地图视口里的雷达 marker 改为地图内 overlay：当 summary 读到 `amcl_pose_observed/localization_tf_observed` 时，雷达运行态会在机器人 marker 位置显示脉冲圈；当雷达运行但地图坐标未读到时，地图中央明确显示 `雷达已运行，位置未读到` 或 `雷达待刷新，位置未读到`，不再把雷达状态藏成右上角 badge 或画假坐标。该改动只消费现有 summary 和 map preview，不新增 scan 点云、不启动雷达、不执行 Nav2/manual/keyboard/stop/delivery，也不调用 `/cmd_vel`。
- 2026-06-25 16:12 起，地图视口新增雷达扫描范围 overlay：雷达已运行或待刷新时，地图中会显示半透明扫描扇区；有 AMCL/map-frame 位置时扇区跟随机器人 marker，缺定位时扇区居中并用虚线表示“占位，等待机器人地图位置”。该层只读 summary 和 map preview，不新增 scan 点坐标、不自动启动雷达、不发送 manual/keyboard/Nav2/stop/delivery 或 `/cmd_vel`。
- 2026-06-25 16:20 起，Robot Control summary 新增只读 `scan_preview_points` 合同：PC 后端会从上位机 `/api/radar/scan-proof/latest` 或 `/api/radar/status` 里的结构化 scan 点，或 LaserScan `ranges + angle_min + angle_increment` 抽样生成相对雷达点；普通首屏在有 AMCL/map-frame 位姿时把这些点以小点叠到同一地图视口，并显示 `雷达点 N 个`，缺 ranges/点位或缺定位时明确显示点位未读取/等待位置。该层不从状态自行伪造点云，不推导机器人全局坐标，不启动雷达、不执行 Nav2/manual/keyboard/stop/delivery，也不调用 `/cmd_vel`。
- 2026-06-25 17:35 起，普通首屏地图在“已有 scan 点但还没有 map-frame 机器人位置”时，会在地图框右上角显示 `雷达局部点 N 个，等待地图位置` 的局部点云小窗。该小窗只表达雷达自身坐标系里的轮廓，不把点落到真实地图坐标；一旦 `robot_pose.frame_id=map` 可用，仍切回原来的真实地图叠点路径。该展示不启动雷达、不刷新 proof、不执行 Nav2/manual/keyboard/stop/delivery，也不调用 `/cmd_vel`。
- 2026-06-25 20:30 起，即使当前 LiDAR lifecycle 已停，只要 summary 仍带最近 `scan_preview_points`，普通首屏地图也会显示 `最近雷达局部点 N 个，雷达未运行，等待地图位置`，并在坐标口径里说明这是最近局部轮廓、不贴地图。该展示只消费既有只读 artifact，不自动启动雷达、不刷新 proof、不执行 Nav2/manual/keyboard/stop/delivery，也不调用 `/cmd_vel`。
- 2026-06-25 21:45 起，上述“雷达已停但有最近 scan 点”的状态也会同步到地图主 marker：marker 文案显示 `雷达未运行，显示最近点`，避免 operator 只看到 `雷达未运行` 而忽略右上角局部点云仍是最近记录。该提示仍不贴地图坐标、不自动启动雷达、不调用 manual/Nav2/keyboard/stop/delivery 或 `/cmd_vel`。
- 2026-06-25 17:20 起，上位机 `/api/radar/scan-proof/latest` 会在只读加载 `runtime/lidar_scan_proof_latest.json` 时，从 `topic_reads.results.scan_once.stdout_preview` 的 LaserScan YAML 解析 `frame_id`、`angle_min`、`angle_increment`、`range_min`、`range_max` 和 `ranges`，过滤 NaN/inf 与越界距离后抽样输出 `scan_preview_points`。PC summary 因此能直接读取真实 artifact 里的雷达快照点位；该 readback 不启动 ROS2、不打开 LiDAR 串口、不发送 A5 60、不触发 Nav2/manual/keyboard/stop/delivery 或 `/cmd_vel`，并继续固定 `safe_to_control=false`、`delivery_success=false`。
- 2026-06-25 16:30 起，上车 O10 localization helper 会从 `/amcl_pose` YAML 输出解析 `amcl_pose {frame_id,x,y,z,yaw,source}`，上位机 `/api/localize/proof/latest` 和 `/api/localize/reset` 只读透出该坐标；PC Robot Control summary 把它压成 `o3_proof_summary.robot_pose`。普通首屏地图只有在 `robot_pose.frame_id=map` 且真实地图 preview 可用时，才把机器人 marker、雷达扇区、雷达脉冲和 scan 点转换到真实地图坐标；只有 AMCL/TF observed 布尔但没有 x/y 时不再把机器人画在地图中心。该改动不发布 `/initialpose` 之外的新动作，不启动 Nav2、不发送 manual/keyboard/stop/delivery 或 `/cmd_vel`。
- 2026-06-25 16:37 起，O10 helper 会从实际 `tf2_echo base_link laser_frame` 输出解析 `base_link_to_laser_frame_transform`，上位机 localization latest/reset 只读透出该外参；PC summary 标准化为 `o3_proof_summary.frame_transforms.base_link_to_laser_frame`。普通首屏地图渲染 laser/laser_frame scan 点时，若该外参存在，会先把点从雷达坐标转到 base_link，再按 `robot_pose` 转到 map-frame，并在短状态显示 `已套用雷达外参`；外参缺失时仍不猜默认偏移。该路径只读 TF proof，不启动雷达、Nav2、manual、keyboard、stop、delivery 或 `/cmd_vel`。
- 2026-06-25 15:10 起，地图视口新增最近 Nav2 目标点 overlay：PC latest 代理会从上位机 `/api/nav2/goal/execution/latest` 的 `latest_result.goal_request` 压缩出 `goal_frame_id/goal_x/goal_y/goal_yaw`，普通首屏用真实地图的 `origin/resolution/width/height` 把目标点画到地图上。新鲜且带 feedback 的成功行程显示为 `终点`，旧成功显示为 `历史目标`，未完成/未通过显示为 `目标待复验`。该 overlay 仍只读 latest artifact，不重新执行 Nav2、不确认送达、不调用 manual/keyboard/stop 或 `/cmd_vel`；当前还不是完整路径线，完整路径需要上位机提供 path/trajectory 点。
- 2026-06-25 起，Nav2 目标预检按普通发车前最小确认口径收敛：PC 后端只要求 `confirm_navigation_preflight=true` 与固定只读定位/路径 readback，不再读取或要求 `/api/operator/report` 现场材料；普通首屏执行行程仍要求先勾“行程前安全确认”，后端执行代理仍只接受固定 `/api/nav2/goal/execute` 且需要 `confirm_navigation_execution=true`。
- 2026-06-23 13:45 起，上位机 `upper_robot_api.py` 不再依赖手工设置 `ROBER_RADAR_START_COMMAND` / `ROBER_RADAR_STOP_COMMAND` 才能启动雷达；默认命令使用受管 `o1_lidar_lifecycle.sh start --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame` 与 `o1_lidar_lifecycle.sh stop`，并继续通过白名单校验拒绝 `/dev/ttyS5`、`T=1/T=13/T=130/T=131`、`/cmd_vel` 和 `/api/base/manual`。部署该上位机版本后，PC summary 应读到 `radar_start_configured=true`，普通首屏才会恢复可点击 `启动雷达`；这仍只启动 LiDAR lifecycle，不开放底盘、Nav2 execute、delivery complete、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 12:30 起，普通首屏 `本轮进度` 的 `去键盘` 复用键盘 gate 的下一步聚焦规则：键盘条件满足时聚焦 `启用键盘（按键才动）`，仍缺恢复确认、轮速记录或雷达移动记录时聚焦对应补证动作，其它缺项时聚焦 `复查手控条件`。该聚焦不启用键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 12:45 起，普通首屏 `本轮进度` 四个目标行各自显示短 `下一步`：轮速、行程、送达和键盘都能在同一块里看到当前动作提示。总主按钮仍只指向第一处未完成卡点；每行下一步只展示文字，不自动刷新、不自动提交、不执行 Nav2、manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 13:00 起，当键盘 gate 只剩 `雷达移动记录` 且雷达未运行时，普通首屏 `复查手控条件`、`去键盘` 和键盘下一步文案都会先指向 `启动雷达` / `刷新雷达`，再提示试动读取雷达移动记录。该聚焦不自动启动雷达、不自动刷新、不调用 first-jog/manual/keyboard pulse/stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- 2026-06-23 09:05 起，普通首屏 `复查手控条件` 刷新后会根据最新 gate 自动聚焦下一步：键盘 gate 已满足时聚焦 `启用键盘（按键才动）`；仍缺恢复确认、轮速记录或雷达移动记录时，聚焦对应的恢复/试动/保存区域；其它缺项才保持聚焦 `复查手控条件`。该复查仍只读取 summary、底盘反馈、Nav2 latest 和 delivery latest，不启用键盘、不发送 keyboard pulse、manual、stop、Nav2 或 `/cmd_vel`。
- 2026-06-23 02:35 起，普通首屏 `行程执行` 和 `任务收口` 会在最近 Nav2 goal 成功材料带 `generated_at_ms` 时显示“约 N 分钟/小时/天前”；超过 15 分钟的 latest 成功会额外提示“这条记录较旧，如需本轮复验，请重新执行行程”。该提示只消费 `GET /api/robot-control/nav2/goal/execution/latest`、本次受限 execute 响应或 delivery 摘要里的短时间字段，不自动执行 Nav2、不提交送达、不发送 manual/stop 或 `/cmd_vel`。
- 2026-06-23 03:20 起，超过 15 分钟的 Nav2 `goal_succeeded` 只作为历史参考展示，不再让普通首屏 `本轮进度` 显示 `行程执行已完成`，也不再把 `检查行程/执行行程` 按钮锁成 `行程已完成`。这类旧记录会让 `任务收口` 和 `验收卡点` 指向“重新执行本轮行程”，避免现场拿旧路线证据继续做送达确认。该口径只调整前端状态和按钮可用性，不自动执行 Nav2、不提交送达、不发送 manual/stop 或 `/cmd_vel`。
- 2026-06-23 03:35 起，普通首屏和高级区的最终送达提交也要求本轮 Nav2 成功材料未超过 15 分钟。旧路线下即使视频/行程 ref 已预填、七项最终确认都已勾选，`确认送达（不发车）` 仍保持禁用并显示 `确认送达（先重新行程）`，submit handler 也会直接返回，不提交 operator report 或 delivery complete。该 gate 只防止旧路线材料进入 delivery success，不自动执行 Nav2、不提交送达、不发送 manual/stop 或 `/cmd_vel`。
- 2026-06-23 02:50 起，普通首屏 `任务收口` 的送达材料状态在 latest delivery 摘要带 `generated_at_ms` 时显示“送达材料草稿已保存，约 N 分钟/小时/天前”；超过 15 分钟的草稿会提示“这份草稿较旧，如本轮已重新到达，请重新准备材料或重新确认”。该提示只读 latest delivery 的短时间字段，不保存新草稿、不提交 operator report、不调用 delivery complete、Nav2、manual、stop 或 `/cmd_vel`。
- 2026-06-22 15:18 起，`GET /api/robot-control/delivery/latest` 会从上位机 latest delivery result 的 `operator_report.structured_hil_claims` 中抽取短 `delivery_material_refs` 摘要：operator evidence ref、external video ref、camera artifact ref、route/map ref 和 site_state。前端只在本页输入为空时用这些 ref 预填“送达材料”，让 PC 页面刷新后能恢复真实上位机已有的送达草稿材料；它不提交 operator report、不调用 delivery complete、不自动勾选最终确认，也不把 `delivery_success` 或控制权限提升为 true。
- 2026-06-23 13:55 起，若 Robot Control summary 的 `operator_report_latest` 仍是 missing/旧报告，但 `delivery/latest` 里保留 `delivery_material_draft_not_operator_confirmed` 的画面 ref，普通首屏也允许 `恢复试动确认`。恢复请求只把 delivery latest 的 external video/camera ref 和 route/map ref 写回固定 operator report 代理，并补 operator/clearance/estop 三项；不会伪造 wheel/LiDAR/delivery success，不调用 first-jog、manual、keyboard pulse、stop、Nav2、delivery complete 或 `/cmd_vel`。若当前只读 `L/R=0/0`，恢复成功后仍先聚焦 `已检查轮速卡点`，不会直接试动。
- 2026-06-23 05:50 起，普通首屏和高级 `目标收口进度` 不再只凭新鲜 `delivery_success=true` 点亮送达完成；当 `delivery/latest` 带有 route/map ref 时，必须和当前未过期 Nav2 execution 的 `evidence_ref` 一致，否则只显示“送达成功记录的行程材料不是本轮记录”，并保持 `送达确认待完成`。这个 gate 只消费只读 latest/execution 摘要和本页已填材料，不自动准备材料、不提交 operator report、不调用 delivery complete、Nav2、manual、stop 或 `/cmd_vel`。
- 2026-06-22 15:22 起，普通首屏 `任务收口` 会把上位机 delivery gate 的 blocked reasons 翻成普通缺口提示，例如“上位机还差：现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达”。该提示只读 `delivery/latest`、`delivery/check` 或 `delivery/complete` 的缺口摘要，不展示字段名，不自动勾选 checklist，不提交 operator report，也不调用 delivery complete。
- 2026-06-22 13:52 起，普通首屏“小车连接”状态只表达 PC 是否读到上位机分项状态：只要 `robot_api_connection.loaded_count>0` 且没有 dangerous true fields，即使 `/api/status` 超时、雷达 proof 缺失或个别只读 endpoint blocked，也显示 `已连接`，提示“部分项目未通过，可展开高级诊断”。危险 true 字段仍显示 `有异常`，所有控制、送达和 success gate 保持 fail-closed；完整 `failed_count/blocked_count/blocked_reasons` 仍保留在高级诊断。
- 2026-06-11 15:25 起，首屏“雷达”卡片不再只看最近一次 refresh 成败，而是优先消费 `readback_summary.lidar` 里的 `continuous_scan_status`、`lifecycle_running`、`lifecycle_state`、`continuous_window_observed`、`continuity_window_status`、`latest_scan_proof_fresh`。普通用户只会看到短句 `雷达已运行 / 雷达未运行 / 刷新中 / 刷新失败`；当 `lifecycle_running=true`、`continuous_window_observed=true` 且 `latest_scan_proof_fresh=true` 时，首屏显示 `雷达已运行`，否则 fail-closed 为 `雷达未运行` 或 `刷新失败`。字段名、`continuity_blocked_reasons` 和完整 key values 继续只留在默认关闭的 `高级诊断`。
- Robot Control Base Manual/Stop V1：workstation 新增 `POST /api/robot-control/base/manual?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>` 与 `POST /api/robot-control/base/stop?baseUrl=<robot-api-base-url>` 固定代理。manual/first-jog 只允许 `forward/back/left/right` 四个方向，Node 代理与前端同时对 `direction`、`speed`、`duration_ms` 做白名单和 clamp；本轮代理统一上限为 `speed<=0.12 m/s`、`duration<=800 ms`。普通 manual 非 stop 方向现在只要求 `confirm_hil_checklist=true`，Node 代理不再为了普通低速手控额外读取 `/api/operator/report` 或要求 wheel/LiDAR/视频材料完整；operator report、轮速非零、LiDAR delta 和送达材料继续作为证据/验收材料展示，但不阻塞已确认安全的低速点动。first-jog 是首次低速试动专用入口，只放宽 wheel feedback 与 LiDAR motion delta 这两个“动作后才能证明”的前置条件，仍要求现场基础三项和外部视频或可见相机 ref；当前 2026-06-21 真实上位机 smoke 因缺 `external_video_or_visible_camera` 返回 HTTP 400 `first_jog_preflight_required`，`remote_http_status=null`，未调用远端 `/api/base/manual`。stop 允许在未勾 checklist、材料缺失时单独发送，作为 fail-safe 路径。无论上位机响应成功、失败还是超时，workstation 都不会把 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 或 `robot_control_executed` 置 true，也不会把这轮交付解释成 HIL pass。Manual/first-jog/stop 代理响应现在会自动附带运动证据快照摘要：`evidence_capture_status=captured|partial|blocked`、`evidence_capture_endpoints`、`before_readback`、`after_readback`、`motion_evidence_summary` 和 `evidence_capture_blocked_reasons`；manual/first-jog 还会附带 `operator_report_preflight`，记录为 `not_required_for_confirmed_manual` 或首动视觉材料缺口。该采集只在代理内部读取固定 GET endpoint：`/api/base/status`、`/api/base/feedback-samples/latest`、`/api/radar/status`、`/api/radar/scan-proof/latest`，分别在主请求或本地拒绝前后各读一次；不新增任意 GET/POST 透传能力。单个 endpoint 失败时主 manual/first-jog/stop 结果仍按原规则返回，证据状态降级为 `partial` 或 `blocked`，高级诊断展示 before/after 短 readback，普通首屏不展示这些工程证据字段。
- 2026-06-22 12:00 起，PC 键盘连续手控合同为：W/A/S/D 与方向键映射到 `forward/left/back/right`，按住时以前端 timer 每 `260 ms` 重复发送一次短 `240 ms` manual pulse，松开当前方向键、窗口失焦、页面隐藏、方向切换或点击 `键盘停止` 时立即清 timer 并走固定 `POST /api/robot-control/base/stop?baseUrl=...`。每个键盘 pulse 仍复用 `POST /api/robot-control/base/manual?baseUrl=...`，并继续要求本地安全确认、速度 `<=0.12 m/s` 和时长 `<=800 ms`；普通低速手控不再要求 operator report preflight 或现场材料完整。summary 的 `safe_command_boundary.keyboard_control_mode=bounded_repeating_manual_pulse`、`keyboard_jog_interval_ms=260`、`keyboard_jog_duration_ms=240`、`keyboard_reuses_manual_gate=true` 用于 UI 展示和测试锁定；`keyboard_control_enabled` 仍固定 `false`，表示没有放开 O7/cloud/primary command 级键盘控制能力。该键盘入口不直接访问串口、不发布 `/cmd_vel`，也不改变 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`。
- 2026-06-22 13:34 起，键盘连续手控入口从默认关闭的高级诊断提升到普通首屏 `移动/导航` 卡片：普通用户能直接看到 `启用键盘`、`键盘停止` 和 W/A/S/D/方向键说明，但仍必须先点击让键盘面板获得焦点，输入框和页面其它区域按键不会触发手控。首屏只显示“移动条件还没满足/可手控/已启用/手控中”等普通话术，不展示 `external_video_recorded`、operator report 缺项、HIL、`/api/base/manual` 或 raw readback；完整 gate 状态、pulse、interval 和 stop trigger 仍保留在默认关闭的 `高级诊断`。
- 2026-06-25 22:15 起，普通首屏键盘说明会直接写明 `按住会持续低速移动，约每 0.26 秒续一次；松开即停`，节奏来自 summary 的 `keyboard_jog_interval_ms`，但不在首屏展示 endpoint、raw pulse 或 `/cmd_vel`。该说明只改变文案，不自动启用键盘、不发送 keyboard pulse/manual/stop，也不改变安全确认 gate。
- 2026-06-23 09:45 起，普通首屏 `雷达` 卡片在 summary/readback 显示 LiDAR lifecycle 未运行时会出现 `启动雷达`。该按钮复用固定 `POST /api/robot-control/radar/start` workstation 代理，只启动传感器 lifecycle，不调用底盘 manual/stop、Nav2 execute、delivery complete、keyboard pulse 或 `/cmd_vel`；`停止雷达` 和完整 lifecycle endpoint/status 仍只放在默认关闭的 `高级诊断`。
- 2026-06-23 10:00 起，普通首屏点击 `启动雷达` 返回后会把焦点带回 `刷新雷达`，并提示 `雷达启动已返回，请点刷新雷达确认状态`。这只改变焦点和下一步提示，不自动触发 scan-proof refresh，也不调用底盘 manual/stop、Nav2 execute、delivery complete、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 15:15 起，普通首屏 `启动雷达` 只有在 lifecycle 响应 `command_result.ok=true` 时才提示 `雷达启动已返回` 并聚焦 `刷新雷达`；若返回 `command_not_configured`、blocked、failed 或其它未成功状态，则显示 `雷达启动没有成功...` 并把焦点留在 `启动雷达`。该判断只消费固定 radar start proxy 响应，不自动重试、不自动刷新、不触发底盘、Nav2、delivery 或 keyboard。
- 2026-06-23 16:05 起，Robot Control summary 兼容真实上位机未安装独立 `GET /api/radar/scan-proof/latest` 与 `GET /api/radar/raw-packet-proof/latest` 的情况：这两个 radar latest 端点返回 404 时，PC 端只把对应雷达 proof 摘要标记为 `missing`，不再把整机连接状态误判为 `blocked`。同轮把重只读端点 `GET /api/status` 与 `GET /api/camera/health` 的读取预算从 4s 扩到 8s，以适配真实上位机 80KB 级 status 聚合和摄像头健康探测；其它 endpoint HTTP 错误、bad JSON、危险 true 字段仍 fail-closed。该兼容只改善普通首屏连接可读性，不自动启动雷达、不执行 Nav2、不发送 manual/keyboard/stop 或 `/cmd_vel`。
- 2026-06-23 10:15 起，普通首屏 `刷新雷达` 确认雷达已运行后，会自动把焦点移到 `轮速记录` 面板，帮助现场继续低速试动采集 wheel raw L/R 和 LiDAR delta。该聚焦只改变滚动位置和焦点，不自动点击 `试动一下`、不调用 first-jog/manual/keyboard pulse/stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- 2026-06-23 13:15 起，普通首屏 `刷新雷达` 确认雷达已运行后，不再只停在 `轮速记录` 大面板，而是复用轮速目标的具体下一手动作：优先聚焦 `已检查轮速卡点`、`检查后重试读非零 L/R`、`恢复试动确认` 或 `试动一下`。该聚焦只改变滚动位置和焦点，不自动点击、不调用 first-jog/manual/keyboard pulse/stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- 2026-06-23 11:00 起，普通首屏 `本轮进度` 的 `去轮速/去轮速记录卡点` 会直接聚焦当前轮速下一手动作：先落到 `已检查轮速卡点`，检查后落到 `检查后重试读非零 L/R`，恢复试动材料时落到 `恢复试动确认`，材料齐备时落到 `试动一下`。该聚焦只改变滚动位置和焦点，不自动点击按钮、不调用 first-jog/manual/keyboard pulse/stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- 2026-06-23 21:25 起，普通首屏已经读到 `wheel L/R=0/0` 且雷达 lifecycle 未运行时，`wheel raw L/R 非零` 的下一步重新聚焦轮速本身：先点 `已检查轮速卡点`，再点 `检查后重试读非零 L/R`；不再把 wheel 行主按钮改成 `去雷达`，也不再用 `先启动雷达再试动` 禁用轮速重试。雷达仍作为 `行程执行` 和 `键盘手控` 的移动记录缺口独立提示。该调整只改变焦点顺序、按钮文案和前端禁用条件，不自动试动、不自动启动雷达、不调用 first-jog/manual/keyboard pulse/stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- 2026-06-23 22:25 起，普通首屏把真实上位机 `feedback_voltage_v` 的长小数供电读数格式化为最多两位小数，例如 `12.43049049` 显示为 `反馈电压约 12.43V`。这只影响普通首屏和 `本轮进度` 文案，高级诊断与接口原始值不变；电压仍只用于现场供电排查，不作为 wheel raw L/R 非零、运动、Nav2 或 delivery success 证明。
- 2026-06-23 13:46 起，普通首屏 `本轮进度` 的 wheel 行在当前只读 `L/R=0/0` 时，即使没有 `feedback_voltage_v`，也固定提示 `检查电机使能、供电、模式和现场空间后重试读取轮速`，并把 `去轮速` 聚焦到本地 `已检查轮速卡点` 按钮。该提示只消费已读 summary 或只读底盘反馈，不自动点击卡点确认、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-22 20:15 起，普通首屏键盘面板新增 `复查手控条件`，复用本轮进度的只读刷新链路：读取 summary、固定 `base/feedback-samples` 和 Nav2/delivery latest/check 读回，用于 operator 补完轮速/LiDAR/送达材料后立即刷新 `启用键盘` 状态。该按钮不 arm 键盘、不发送 manual/stop、不调用 `/cmd_vel`。
- 2026-06-23 00:14 起，普通首屏 `启用键盘` 在连接、键盘合同、移动前检查和现场画面都已满足，但键盘 gate 仍缺轮速材料时显示 `启用键盘（先补轮速）`。2026-06-23 00:18 起，同一状态下 `复查手控条件` 显示 `复查手控条件（先补轮速，不发车）`。两个按钮仍保持安全边界：前者禁用，后者只做只读刷新；都不 arm 键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 21:45 起，当键盘 gate 仍缺轮速材料且普通首屏当前读到 `wheel L/R=0/0` 时，键盘区下一步从泛化的 `读取并保存轮速记录` 改为 `检查轮速卡点，再重试读非零 L/R`；点击 `复查手控条件（先补轮速，不发车）` 或 `去键盘` 会优先聚焦 `已检查轮速卡点` 本地按钮，而不是直接聚焦试动按钮。该聚焦只引导 wheel raw L/R 证据采集顺序，不自动点击卡点确认、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 22:45 起，当键盘 gate 被 wheel raw L/R 非零材料挡住且当前只读反馈为 `L/R=0/0` 时，键盘区下一步会直接复述当前轮速、T1001 帧数和短电压，例如 `当前轮速 L/R=0/0，已读到 12 帧，反馈电压约 12.43V；下一步：检查轮速卡点，再重试读非零 L/R`。该提示只复用已读 summary/feedback-samples，不启用键盘、不发送 keyboard pulse/manual/stop，不调用 Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 00:37 起，若键盘 gate 的移动前检查、现场画面和轮速记录已满足，但仍缺雷达移动记录，普通首屏 `启用键盘` 显示 `启用键盘（先补雷达）`，`复查手控条件` 显示 `复查手控条件（先补雷达，不发车）`。该状态下键盘仍禁用；复查按钮仍只读刷新，不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 00:45 起，普通首屏键盘入口的其它禁用态也改为动作化按钮文案：未连接时显示 `启用键盘（先连接）`，summary 缺键盘合同时显示 `启用键盘（先复查入口）`，缺移动前检查时显示 `启用键盘（先做检查）`，缺现场画面时显示 `启用键盘（先记录画面）`；`复查手控条件` 同步显示对应动作并标注 `不发车`。这些文案不改变键盘 gate，不 arm 键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 00:55 起，普通首屏键盘手控面板新增实时状态行：未满足时显示当前缺项，ready 但未启用时显示 `未启用，先点启用键盘。`，启用后显示 `等待按键，按住才会动。`，按住期间显示 `正在前进/后退/左转/右转，松开即停。`，松开停止后显示 `已停止，按住方向键可继续点动。`。该行只读取前端已有键盘状态，不改变 gate，不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-22 12:05 起，PC 代理的 manual/first-jog 响应会把上位机 `serial_motion_transaction.feedback_during_motion.t1001_feedback_frames` 压成 raw L/R 摘要：`feedback_during_motion_t1001_frame_count`、`feedback_after_stop_t1001_frame_count`、`wheel_feedback_latest_raw_left`、`wheel_feedback_latest_raw_right`、`wheel_feedback_nonzero_frame_count` 和 `wheel_feedback_lr_nonzero_proven`。这些字段来自 WAVE ROVER vendor `T=1001` 基础反馈帧中的 `L/R`，只在默认关闭的高级诊断展示；若上位机没有 during-motion 帧或 L/R 仍为 0/0，PC 必须显示 `not_loaded` 或 `false`，不能把只读 T1001 计数解释成轮速非零。高级诊断新增 `轮速非零试采（高级）` 按钮，复用 first-jog 固定代理和现场材料 gate，目的只是更直接采集 raw L/R，不新增任意 endpoint、不绕过 checklist/operator report，也不进入普通首屏。
- 2026-06-12 02:00 起，workstation 新增固定高级代理 `POST /api/robot-control/base/feedback-samples?baseUrl=<robot-api-base-url>`，只向上位机 `/api/base/feedback-samples` 发送后端写死的短批量 `T=130` 反馈采样请求：`sample_count=3`、`sample_interval_s=0.15`、`read_timeout_s=0.25`、`read_window_s=0.35`。浏览器不能传串口、方向、速度、duration 或任意 endpoint；该代理不调用 `/api/base/manual`、`/api/base/stop`、`/cmd_vel`、Nav2 goal、Radar/Map start。普通 `.simple-user-console` 首屏不新增底盘反馈按钮；入口只在默认关闭的 `高级诊断 -> 现场点动设置 / 控制边界`，并展示 `t1001_observed_count/completed_sample_count`、`feedback_ack_t1001_observed`、`sends_motion_commands=false`、`robot_control_executed=false` 和 dangerous true fields。真实上位机 `root@192.168.1.11:37878` 验证中，direct `/api/base/feedback-samples` 与 PC proxy 均观察到 `T=1001` 为 `3/3`，PC proxy 返回 `samples_forwarded`、`remote_http_status=200`、`dangerous=[]`；这只证明底盘反馈只读链路活着，不证明轮速非零、物理移动、HIL pass 或手动点动已放行。
- 2026-06-12 02:20 起，Robot Control summary 对 `T=130` 只读底盘反馈的危险字段判定做精确收口：`/api/status` 中的 `base.sends_commands`、`base.feedback_readback.sends_commands`，`/api/base/status` 中的 `sends_commands`、`feedback_readback.sends_commands`，以及 `/api/base/feedback-samples/latest` 中的 `sends_commands`、`latest_result.sends_commands` 不再把 PC summary 整体打成 blocked。该豁免只针对上述 endpoint/path 的只读反馈字段；`sends_motion_commands=true`、`sends_base_motion_commands=true`、`calls_base_manual=true`、`publishes_cmd_vel=true`、`robot_control_executed=true` 仍照常 hard-block。`/api/base/status` 与 `/api/base/feedback-samples/latest` 的读取预算同步从 1.5s 调整到 4s，以匹配真实 `T=130` readback 窗口。真实 PC proxy 复测 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`robot_api_connection.status=readable`、`loaded_count=13`、`blocked_count=0`、`failed_count=0`、`dangerous_true_fields=[]`；这只修复只读连接误判，不开放非 stop 点动或导航执行。
- 2026-06-12 02:35 起，`readback_summary.base` 增加 `latest_t1001_observed_count` 与 `feedback_link_status`，把真实底盘反馈链路状态从压缩 key values 提升到稳定摘要。`feedback_link_status=t1001_observed_not_motion_proof` 只说明 vendor `T=1001` 反馈帧已被观察到，不能作为 `wheel_feedback_lr_nonzero_proven`、物理运动、HIL pass 或点动放行依据。为避免真实板端只读 latest/status 间歇性超过 1.5s，Robot Control summary 的 map/localize/Nav2/operator/radar/base 只读 endpoint 统一使用 4s 读取窗口；这些 endpoint 仍只 GET 状态和 artifact，不发送 `/api/base/manual`、`/cmd_vel`、NavigateToPose 或 start/stop 控制。真实 PC proxy 复测返回 `console_status=loaded_fail_closed_summary`、`robot_api_connection.status=readable`、`loaded_count=13`、`failed_count=0`、`dangerous_true_fields=[]`，并显示 `readback_summary.base.latest_t1001_observed_count=3`、`feedback_ack_status=t1001_observed`。
- 2026-06-22 01:25 起，上位机 `/api/base/feedback-samples` 会把 vendor `T=1001` 的 `L/R/r/p/y/v` 精简帧保存在 `t1001_feedback_frames`，并生成 `wheel_feedback_summary`。PC 代理同步透出 `wheel_feedback_lr_nonzero_proven`、`wheel_feedback_nonzero_observed`、`wheel_feedback_nonzero_frame_count`、`wheel_feedback_latest_left_speed`、`wheel_feedback_latest_right_speed` 和 `wheel_feedback_source`，Robot Control summary 的 `readback_summary.base` 也会显示 wheel material 状态。判定规则保持保守：只有同一帧 `T=1001` 中 `L` 与 `R` 都是有限非零数值，才清除 `wheel_feedback_lr_nonzero_not_proven` gap；单侧非零、跨帧拼接或只有 T1001 计数都不算通过。真实上位机并发点动采样中，`T=1001` 可读但 `L/R` 仍为 `0`，因此 PC 显示 `wheel_feedback_lr_nonzero_proven=false`，不会把 `safe_to_control`、`hil_pass`、`delivery_success` 或 `primary_actions_enabled` 置 true。
- 2026-06-22 13:25 起，高级诊断的 `采集底盘反馈（高级）` 结果把只读 `T=1001` 的 raw wheel 摘要提升为单独行：`latest_L`、`latest_R`、`nonzero_frames`、`proven` 和 `source=vendor_t1001_L_R`。真实 PC proxy 复测 `POST /api/robot-control/base/feedback-samples` 返回 `t1001=3/3`、`latest_L=0`、`latest_R=0`、`nonzero_frames=0`、`proven=false`，所以 wheel raw L/R 非零仍未完成；UI 不能把反馈链路可读误说成轮速非零。
- 2026-06-22 15:27 起，Robot Control summary 的 `readback_summary.base` 增加最新只读 `wheel_feedback_latest_left_speed/right_speed`，普通首屏“轮速记录”也会显示当前只读 L/R。2026-06-22 20:45 起，summary 同步透出 `feedback_voltage_v`，普通首屏在 L/R 仍为 `0/0` 时会显示“已读到底盘反馈，但当前轮速是 L/R=0/0；反馈电压约 ...V”，并继续提示检查电机使能、供电、模式和现场空间。该提示只消费 summary 或高级只读采样结果，不调用 `/api/base/manual`、first-jog、Nav2 或 `/cmd_vel`，也不把 `T=1001` 静态反馈或电压外推成 wheel raw L/R 非零。
- 2026-06-23 00:22 起，普通首屏 `本轮进度` 标题下新增 `本轮下一步` 单行提示，按 `轮速记录 -> 行程执行 -> 送达确认 -> 键盘手控` 顺序选择第一项未完成目标，并复用该目标的普通 hint。该提示只是前端只读引导，不自动点击 `去轮速/去行程/去送达/去键盘`，不刷新接口，不发送 manual、first-jog、Nav2、delivery complete、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 00:57 起，普通首屏 `本轮进度` 新增 `当前状态` 单行摘要，把 `轮速记录 / 行程执行 / 送达确认 / 键盘手控` 四项压成一行，例如 `当前状态：轮速记录待完成；行程执行已完成；送达确认待完成；键盘手控未满足。`。该摘要只消费页面已有只读状态，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 01:00 起，普通首屏 `本轮进度` 新增 `当前读数` 单行，把当前已读轮速、行程、送达和键盘材料压成一句普通话；轮速未完成时优先显示已读 `L/R`，行程成功时显示最近行程成功和反馈次数，送达和键盘只显示完成/未满足结论。该摘要只消费页面已有只读状态，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`，也不会把 `L/R=0/0` 外推成 wheel raw L/R 非零。
- 2026-06-23 01:04 起，普通首屏 `本轮进度` 新增 `验收卡点` 单行，按 `轮速记录 -> 行程执行 -> 送达确认 -> 键盘手控` 顺序显示当前第一处真实缺口。当前只读轮速明确为 `L/R=0/0` 时，直接提示检查电机使能、供电、模式和现场空间后重试；行程成功但送达未完成时，直接复用送达下一步。该卡点只消费页面已有只读状态，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 05:35 起，当 latest operator report 被送达草稿覆盖、first-jog 只缺基础安全确认时，普通首屏 `验收卡点` 优先显示 `送达草稿覆盖了试动确认，先恢复试动确认，再低速试动读非零 L/R`。该提示优先级高于当前只读 `L/R=0/0` 排障提示，避免现场跳过恢复确认直接查电机；它不自动恢复材料、不调用 first-jog/manual、delivery complete、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 06:05 起，同一送达草稿覆盖 first-jog 基础确认的状态也会同步到普通首屏键盘区：`启用键盘` 显示 `先恢复确认`，`复查手控条件` 显示 `先恢复确认，不发车`，下一步提示为 `恢复试动确认（不会发车）`。这避免现场从键盘区被带去重复“移动前检查”，但不会自动点击恢复确认、不发送 keyboard pulse/manual/stop、不调用 delivery complete、Nav2 或 `/cmd_vel`。
- 2026-06-23 06:20 起，同一状态下普通首屏 `本轮进度` 主按钮从 `去轮速记录卡点` 改为 `去恢复确认`，轮速行按钮从 `去轮速` 改为 `去恢复`，点击后只滚动并聚焦 `恢复试动确认` 按钮。该跳转不自动点击恢复确认、不提交 operator report、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 06:35 起，`恢复试动确认` 提交成功后会自动把焦点移到 `开始低速试动读非零 L/R` 按钮，帮助现场按顺序继续采集 wheel raw L/R。该焦点移动只发生在 operator report 代理成功后，不自动点击试动、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 06:50 起，first-jog 返回 `wheel_feedback_lr_nonzero_proven=true` 后会自动把焦点移到 `保存轮速记录` 按钮，帮助现场把已拿到的 wheel raw L/R 证据写入 operator report。该焦点移动不自动保存、不提交 operator report、不再次调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 07:05 起，`保存轮速记录` 成功写入 operator report 后会自动把焦点移到 `行程操作` 面板，帮助现场进入完整 Nav2 路线执行步骤。该焦点移动不自动勾选行程确认、不调用 Nav2 preflight/execute、不发送 first-jog/manual/keyboard pulse/stop、delivery complete 或 `/cmd_vel`。
- 2026-06-23 01:06 起，普通首屏 `本轮进度` 标题行新增 `去处理卡点` 按钮，自动定位到当前第一项未完成目标对应的普通面板。该按钮只执行本页 scroll/focus，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 01:09 起，`去处理卡点` 按钮改为动态文案：`去行程卡点`、`去轮速记录卡点`、`去送达卡点` 或 `去键盘手控卡点`，让现场点击前就能知道会跳到哪个普通面板。按钮行为不变，仍只执行本页 scroll/focus，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 01:12 起，`去送达卡点` 的定位更精确：送达材料还缺时聚焦送达状态/材料区；材料已保存或已预填、但最终确认仍缺项时，优先聚焦 `最终确认` 面板。该按钮仍只执行本页 scroll/focus，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- 2026-06-23 01:16 起，普通首屏 `本轮进度` 不再把键盘 gate 满足直接算作键盘目标完成；gate 满足但还没发生方向输入时显示 `键盘手控待验证`，发生过键盘方向输入后才显示 `键盘手控已验证`。当轮速、行程和送达都已收口且只剩键盘时，验收卡点显示 `键盘已解锁，点击启用键盘后按住方向键验证。`。该区分只调整前端状态口径，不自动 arm 键盘、不发送 keyboard pulse、manual、stop 或 `/cmd_vel`。
- 2026-06-23 01:20 起，默认关闭的高级 `目标收口进度` 也采用同一键盘验收口径：`PC 键盘连续手控` 必须在键盘 gate 满足后发生过方向输入才 ready；gate 满足但未按键时显示 `键盘入口已就绪，仍需按住方向键现场验证`。该区分只调整前端只读收口口径，不自动 arm 键盘、不发送 keyboard pulse、manual、stop 或 `/cmd_vel`。
- 2026-06-23 02:05 起，键盘验收口径继续收紧：`PC 键盘连续手控` 只有在按键触发的固定 `POST /api/robot-control/base/manual` pulse 返回 `command_forwarded` 且远端 HTTP 为 2xx 后，才显示 `键盘手控已验证`。单纯按键事件、manual proxy 拒绝、远端 4xx/5xx 或 fetch 失败都只显示 `键盘手控待验证`，并提示 `键盘手控请求未成功，未记为已验证`；这避免把 UI keydown 误判成真实连续手控。
- 2026-06-23 03:05 起，`PC 键盘连续手控` 的验收口径从“1 次成功 pulse”收紧为“同一次按住方向键期间至少 2 次固定 manual pulse 返回 `command_forwarded` 且远端 HTTP 为 2xx”。普通首屏和高级 `目标收口进度` 会显示 `已成功 N/2 次`，第 1 次成功后仍保持 `键盘手控待验证`，第 2 次成功后才显示 `键盘手控已验证`。这只调整前端验收口径和文案，不自动 arm 键盘、不发送额外 pulse、不绕过 manual gate、不调用 delivery complete、Nav2、stop 或 `/cmd_vel`。
- 2026-06-23 09:25 起，同一次按住达到 2/2 后，普通首屏 `键盘手控` 面板本身也会显示 `已验证`，live 状态提示 `键盘手控已验证，已连续 2/2 次`，避免现场只看面板时误以为仍停在“可手控/已启用”。按键仍必须由 operator 按住触发，页面不自动发送额外 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 23:05 起，`PC 键盘连续手控` 验收口径继续收紧：同一次按住达到 `2/2` 后仍保持 `键盘手控待验证`，提示 `松开按键完成停止收口`；只有松开后固定 `POST /api/robot-control/base/stop` 已发送，才显示 `键盘手控已验证`。该调整只改变前端验收状态和文案，不改变 pulse/stop 代理、不自动发额外 motion、不调用 Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 23:20 起，键盘停止收口还要求 stop proxy 自身 `command_forwarded` 且远端 HTTP 为 2xx；如果 release stop 返回 rejected、4xx/5xx 或 fallback failure，普通首屏显示 `键盘停止请求未成功，未记为已验证`，`PC 键盘连续手控` 继续保持未完成。该调整只收紧前端验收判定，不改变 stop 代理路径、不自动重试、不发送额外 keyboard pulse/manual/Nav2/delivery complete 或 `/cmd_vel`。
- 2026-06-23 23:35 起，若 operator 松开方向键时上一条 keyboard manual pulse 仍在请求中，PC 会先显示 `已松开，正在发送停止`，并在该 pulse 返回后补发一次固定 `POST /api/robot-control/base/stop`。这避免 release stop 被 `manualCommandPending` 吃掉；仍不绕过 manual/stop 固定代理，不自动启动新的 motion、不调用 Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 01:55 起，`目标收口进度` 和普通首屏 `本轮进度` 会区分 wheel raw L/R 的证据来源：本轮 first-jog during-motion、只读采样非零、历史 operator report 材料分别显示不同提示。若历史材料存在但当前只读 T1001 为 L/R=`0/0`，页面显示 `已有历史非零材料；当前只读 L/R=0/0，本轮复验需低速重试`，避免现场把停车/静态读回误解成当前轮速仍为非零；该提示不刷新接口、不调用 first-jog/manual、不写 operator report，也不把静态 `0/0` 外推成新的 wheel proof。
- 2026-06-23 04:50 起，`目标收口进度` 进一步收紧 wheel raw L/R 口径：`/api/robot-control/base/feedback-samples` 这类只读采样即使返回 `wheel_feedback_lr_nonzero_proven=true`，也只显示“只读轮速已出现非零”，不会把 `wheel raw L/R 非零` 标为已满足，也不会启用 `保存轮速记录`。收口仍要求本轮 first-jog/manual during-motion raw L/R 非零，或带 ref 的 operator report 材料；该变更不调用 first-jog/manual、operator report、delivery complete、Nav2 或 `/cmd_vel`。
- 2026-06-23 20:00 起，`目标收口进度` 再次收紧历史 wheel 材料：即使 operator report 里已有带 ref 的历史非零 wheel 材料，只要当前只读 T1001 明确为 L/R=`0/0`，`wheel raw L/R 非零` 仍保持未完成，并引导本轮低速复验。该改动只改变收口状态和提示，不自动试动、不提交 operator report、不执行 Nav2、不提交 delivery complete、不发送 manual、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 18:00 起，`目标收口进度` 的 `wheel raw L/R 非零` 未完成项在已有只读 T1001 当前读回时，也会显示 `当前只读 L/R=<L>/<R>，已读到 N 帧；仍需低速试动窗口保存非零 L/R`。这让高级验收视图和普通首屏看到同一份当前读数，但仍保持 `ready=false`，不把静态 T1001、停车 L/R=`0/0` 或只读帧数外推为 wheel proof。
- 2026-06-23 00:28 起，普通首屏 `轮速记录` 的试动按钮在当前只读 L/R 已明确为 `0/0` 时显示 `低速试动读非零 L/R`；试动失败后显示 `重试低速试动读非零 L/R`，恢复试动确认后显示 `开始低速试动读非零 L/R`。这只改变按钮文案，仍复用原有 first-jog gate、固定低速短时参数和 operator material 前置条件。
- 2026-06-23 00:31 起，普通首屏 `轮速记录` 的试动按钮在禁用态也直接显示下一步：未连小车显示 `连接后试动读轮速`，请求处理中显示 `等待上一条请求`，送达草稿覆盖试动材料时显示 `先恢复确认再试动`，缺现场画面时显示 `先记录画面再试动`。这些文案不改变禁用条件，也不绕过 first-jog preflight。
- 2026-06-23 00:34 起，普通首屏 `保存轮速记录` 按钮在禁用态也显示当前下一步：缺画面时为 `保存轮速记录（先记录画面）`，送达草稿覆盖试动材料时为 `保存轮速记录（先恢复确认）`，材料已齐但还没试动时为 `保存轮速记录（先试动）`，试动后仍未拿到非零 L/R 时才显示 `保存轮速记录（等非零 L/R）`。按钮启用条件不变，仍只允许保存本轮 first-jog during-motion 同帧非零 L/R 材料。
- 2026-06-23 01:45 起，普通首屏 `轮速记录` 在当前卡点为 L/R=`0/0` 时显示 `已检查轮速卡点` 本地按钮。它只让现场人员确认电机使能、供电、模式和现场空间已查完，并把试动按钮文案从 `先查卡点再重试读非零 L/R` 改为 `检查后重试读非零 L/R`；不调用 first-jog、manual、stop、Nav2、delivery complete 或 `/cmd_vel`，也不把 wheel raw L/R 非零置为完成。
- 2026-06-23 10:30 起，普通首屏或高级诊断执行 `刷新当前轮速（只读）/采集底盘反馈` 后，若读到 T1001 但 L/R 仍为 `0/0`，页面会把焦点移到 `已检查轮速卡点` 本地按钮。该聚焦只帮助现场排查电机使能、供电、模式和空间，不自动点击排查按钮、不调用 first-jog/manual/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 10:45 起，现场点击 `已检查轮速卡点` 后，页面会把焦点移到 `检查后重试读非零 L/R` 试动按钮；若试动按钮仍不可用，则保留在轮速记录区域。该本地确认仍不调用 first-jog/manual/stop、Nav2、delivery complete 或 `/cmd_vel`，也不把 wheel raw L/R 非零置为完成。
- 2026-06-23 14:45 的“轮速 0/0 时先聚焦雷达”口径已在 2026-06-23 21:25 被替换：现场点击 `已检查轮速卡点` 后，即使雷达未运行，也优先聚焦 `检查后重试读非零 L/R`。这只允许 operator 在 first-jog gate 已满足时继续采集 wheel raw L/R，不自动点击试动、不绕过现场材料 gate、不发送 manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- 2026-06-23 15:00 的“本轮进度 wheel 行改为去雷达”口径已在 2026-06-23 21:25 被替换：`本轮进度` 主按钮保持 `去轮速记录卡点`，轮速行按钮保持 `去轮速`，总 `本轮下一步` 继续展示当前 L/R 和轮速排障提示。雷达缺口仍在行程和键盘行提示，不再覆盖 wheel raw L/R 收口。
- 2026-06-23 17:20 起，PC summary 的底盘反馈摘要会从真实 `/api/base/status.feedback_readback.t1001_feedback_frames[]` 数组派生 fresh T1001 帧数；当上位机没有显式 `t1001_feedback_frame_count` 字段时，普通首屏仍能显示当前读到的 fresh 帧数，而不会退回 stale `feedback-samples/latest` 旧计数。该派生只用于只读展示，不证明 wheel raw L/R 非零、真实运动、HIL pass 或 delivery success。
- 2026-06-23 17:40 起，当 `/api/base/status` 本次 fresh readback 已读到 T1001 帧时，PC summary 的 `latest_feedback_status` 显示为 `fresh_base_status_readback`，不再把嵌套 `feedback-samples/latest` 的 stale 状态放到普通首屏轮速提示里；stale samples 仍保留在高级 readback key values 里供排障。该改动只修正只读展示优先级，不改变 wheel raw L/R 非零、真实运动、HIL 或 delivery success 判定。
- 2026-06-23 00:25 起，普通首屏最终 `确认送达` 按钮在已有送达草稿但 checklist 未齐时不再只显示缺项数量，而是按当前第一组缺口显示 `确认送达（先勾选安全）`、`确认送达（先确认到达）`、`确认送达（先核对材料）` 或 `确认送达（先确认投放）`。2026-06-23 00:40 起，该动作化文案扩展到所有禁用态：缺材料时显示 `确认送达（先准备材料）`，材料已预填但未保存草稿时也直接显示下一步人工确认。按钮禁用状态和 gate 不变；这些文案只引导 operator 勾选本地确认项，不提交 operator report、不调用 delivery complete、不发送 Nav2、manual 或 `/cmd_vel`。
- 2026-06-23 00:48 起，普通首屏 `行程操作` 的 `检查行程` / `执行行程` 按钮在未勾选行程前确认时统一显示 `先勾选确认`，未连接小车时显示连接后再检查/执行。按钮启用条件不变；未勾选确认时不调用 preflight、不执行 Nav2，不发送 `/cmd_vel`、manual 或 delivery complete。
- 2026-06-23 00:51 起，普通首屏 `行程操作` 的最近结果按钮显示为 `读取行程结果（只读）`，已有成功行程时显示 `重新读取行程（只读）`。该按钮只调用最近 Nav2 execution latest 读回，不执行 Nav2 goal，不发送 `/cmd_vel`、manual 或 delivery complete。
- 2026-06-23 16:40 起，普通首屏 `行程操作` 会把雷达运行作为完整行程的前置提示：当 summary 判断雷达未运行时，`检查行程` / `执行行程` 按钮禁用并显示 `先启动雷达`，状态提示为 `待雷达`，`本轮进度 -> 去行程` 只聚焦 `启动雷达` / `刷新雷达`。该 gate 只影响前端引导和按钮启用，不自动启动雷达、不调用 Nav2 preflight/execute、不发送 manual、delivery complete 或 `/cmd_vel`。
- 2026-06-23 17:00 起，普通首屏 `本轮进度` 在行程卡点遇到雷达未运行时也统一指向雷达：总按钮和行程行按钮显示 `去启动雷达/去雷达`，总下一步和验收卡点直接提示 `雷达未运行，先启动雷达，再执行完整行程`。这些入口仍只是 scroll/focus，不自动启动雷达、不自动刷新、不调用 Nav2 preflight/execute、manual、delivery complete 或 `/cmd_vel`。
- 2026-06-23 18:20 起，高级 `目标收口进度` 的 `完整 Nav2 路线执行` 未完成项也会在雷达未运行时显示 `雷达未运行，先启动雷达，再检查或执行完整行程`，和普通首屏行程卡点保持一致。该提示只改变只读验收文案，不自动启动雷达、不执行 Nav2、不提交送达、不发送 manual 或 `/cmd_vel`。
- 2026-06-23 18:40 起，高级 `目标收口进度` 的 `delivery success` 未完成项也会在本轮完整行程未完成时先指向行程前置；若雷达未运行，提示 `送达确认前先启动雷达并完成本轮完整行程`。该提示只调整验收顺序文案，不自动启动雷达、不执行 Nav2、不提交 delivery complete、不发送 manual 或 `/cmd_vel`。
- 2026-06-23 19:00 起，普通首屏 `送达确认` 在本轮行程未完成且雷达未运行时，也直接提示 `下一步：先启动雷达，再完成本轮行程`，红色 `确认送达（不发车）` 的禁用文案显示 `确认送达（先启动雷达）`，`本轮进度 -> 去送达` 只聚焦雷达启动入口。该改动不自动启动雷达、不执行 Nav2、不提交 delivery complete、不发送 manual 或 `/cmd_vel`。
- 2026-06-23 19:20 起，普通首屏 `刷新雷达` 确认雷达已运行后，不再固定聚焦 `轮速记录`，而是回到 `本轮进度` 的当前第一缺口：轮速未完成则回轮速，轮速已完成则回行程，行程已完成则回送达或键盘。该跳转只移动焦点，不自动试动、不执行 Nav2、不提交 delivery complete、不启用键盘、不发送 manual 或 `/cmd_vel`。
- 2026-06-23 19:40 起，普通首屏读到 `GET /api/robot-control/nav2/goal/execution/latest` 已加载但最近行程状态不是成功时，不再显示成“还没读到最近行程成功结果”，而是提示 `最近行程未通过，需要检查或重新执行完整行程`，送达下一步同步指向检查/重执行行程。普通首屏仍不展示 `not_proven` 字段名，也不自动执行 Nav2、delivery complete、manual、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 20:20 起，高级 `送达收口检查` 里的 `Nav2 路线执行成功` 子项也复用 latest 未通过口径：读到最近行程不是成功时显示 `最近行程未通过，需检查或重新执行完整行程`，避免普通首屏和高级送达 checklist 对同一份 latest 证据给出不同下一步。该提示只读已加载状态，不自动执行 Nav2、delivery complete、manual、keyboard pulse 或 `/cmd_vel`。
- 2026-06-23 22:05 起，普通首屏若同时读到雷达未运行和旧/未通过/不完整行程证据，`行程执行`、`送达确认`、`本轮进度` 与高级目标收口统一提示 `先启动雷达，再重新执行本轮行程`。禁用态 `确认送达` 显示 `确认送达（先雷达再行程）`，避免现场误以为只启动雷达就能沿用旧路线完成 delivery success。该提示只调整文案和焦点顺序，不自动启动雷达、不执行 Nav2、不提交 delivery complete、不发送 manual、keyboard pulse 或 `/cmd_vel`。
- 2026-06-21 23:50 起，普通首屏 `移动/导航` 卡片接入 first-jog 普通流程：`现场画面记录` 输入框 + `记录画面` 按钮提交外部视频 ref，`试动一下` 按钮调用 `POST /api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>`。该入口固定 `direction=forward`、`speed=0.08`、`duration_ms=500`、`confirm_hil_checklist=true`，不开放速度/时长/方向输入，不显示工程 endpoint，不调用旧 `/api/robot-control/base/manual` 前端路径。真实 PC proxy smoke 在当前缺 external video/visible camera 材料时返回 HTTP 400 `first_jog_preflight_required`、`remote_http_status=null`、`robot_control_executed=false`，普通首屏只显示“小车没有移动”。
- 2026-06-22 起，普通首屏 `移动/导航` 的状态提示按 first-jog 真实前置条件收窄：没有外部视频或可见相机材料时显示 `待记录` 和“先记录现场画面，再试动一下”；已有现场画面材料但完整 manual HIL 材料仍未齐时显示 `待试动` 和“现场画面已记录；可以试动一下”。轮速非零和 LiDAR motion delta 仍是试动后的证据，继续只在高级诊断完整材料清单中展示，不作为普通 first-jog 前的首屏提示。
- 2026-06-22 00:40 起，manual/first-jog/stop 响应新增 `motion_evidence_gaps`。该字段是试动后的补证据清单，不是放行依据：本机拒绝或远端失败时包含 `motion_command_not_forwarded`，快照不完整时包含 `before_after_evidence_snapshot_incomplete`，未看到结构化轮速非零 proof 时包含 `wheel_feedback_lr_nonzero_not_proven`，未看到 LiDAR motion delta proof 时包含 `physical_motion_lidar_delta_not_proven`；stop 固定返回 `stop_command_not_motion_proof`。`T=1001` 只读反馈仍只能证明底盘反馈链路可读，不能清除轮速非零 gap。
- 2026-06-22 00:55 起，Robot Control summary 新增 `first_jog_readiness_summary`，把 first-jog 前置条件变成稳定合同：`basic_safety_ready` 表达 operator/clearance/estop 三项，`visual_material_ready` 表达外部视频或可见相机材料，`missing_fields` 和 `next_action` 用于普通首屏提示。当前真实上位机 summary 为 `blocked_missing_visual_material`、`basic_safety_ready=true`、`visual_material_ready=false`、`next_action=record_visual_material`；这仍不放宽后端 first-jog preflight。
- Robot Control Base HIL Boundary：本轮真实联调边界只允许对真实上位机 `http://192.168.1.11:8787` 做材料不足的 no-motion reject 或 stop 类安全动作，包括 `POST /api/robot-control/base/stop?...`；禁止通过 workstation 向真实上位机发送 `forward/back/left/right` 的非零运动。该边界与硬件事实一起受本地 vendor 资料约束：`docs/vendor/VENDOR_INDEX.md` 指向的 `base_ctrl.py`、`config.yaml`、`json_cmd.h` 说明 WAVE ROVER 上下位机链路是 UART newline-delimited JSON，vendor Raspberry Pi 默认 `/dev/ttyAMA0 @ 115200`、备选注释 `/dev/serial0 @ 115200`；项目上车 Orange Pi 的实际串口设备必须现场确认，不能在 PC 或上车默认中硬编码 Raspberry Pi 路径。workstation 只消费上位机 HTTP API，不直接操作 UART、串口、GPIO 或 WAVE ROVER ESP32。
- Robot Control Radar/Map Proof Refresh V2：`Robot Control` tab 现在已经接入 Radar/Map proof refresh surface，用来刷新 `GET /api/radar/status`、`GET /api/radar/scan-proof/latest`、`POST /api/radar/scan-proof/refresh`、`GET /api/map/proof/latest`、`POST /api/map/proof/refresh` 的只读证据窗口。Radar refresh 固定通过 Node 代理向上位机 `POST /api/radar/scan-proof/refresh`，默认 body 是 `{ timeout_s: 20, runtime_warmup_s: 15, start_runtime: true }`；Map refresh 固定通过 Node 代理向上位机 `POST /api/map/proof/refresh`，默认 body 是 `{ timeout_s: 45 }`。Radar refresh 的长 warmup 是真实冷启动稳定性修正，用于等待 LiDAR driver、`/scan`、raw packet、scan hz 和 TF 同时进入 no-motion 证据窗口；它不允许前端传自定义参数，不改变 `docs/vendor/VENDOR_INDEX.md` 指向的 vendor/hardware facts。Radar latest/refresh/status 现在都输出同一个最新 `evidence_ref/latest_evidence_ref`：优先保持 LiDAR artifact 自带 ref；缺失时从 `generated_at_ms` 派生 `o1-lidar-scan-proof-<generated_at_ms>`；旧 ISO `generated_at` 只派生安全可读 ref；artifact 缺失、坏 JSON 或根节点非 object 时不伪造成功 ref。PC proxy 的 `last_result_evidence_ref` 直接读取这个字段，artifacts/docs 可直接引用本轮雷达 proof id。Radar refresh 只刷新 LiDAR/TF/no-motion scan proof snapshot，典型可见字段是 `scan_once_observed`、`scan_hz_observed`、`raw_packet_once_observed`、`tf_observed` 和 `blocked_reasons`；Map refresh 只刷新 no-motion map proof snapshot，典型可见字段是 `map_once_observed`、`map_file_observed`、`map_metadata_observed` 和 `blocked_reasons`。两个 refresh 允许出现 `sends_commands=true`、`starts_ros2=true` 这类非运动 evidence helper 结果，但首屏只显示“刷新雷达/刷新地图”和短状态；`scan/tf`、`map/evidence`、`latest_readback_key_values`、`non_motion_evidence_actions`、`hard_dangerous_true_fields`、`last refreshed time` 和 blocked reasons 都收进高级诊断区。它仍然不会打开 `/cmd_vel`、`/api/base/manual`、Radar start、Map start、Nav2 goal、keyboard control 和 map click goal；动作结束后会自动回刷 Robot Control summary。只有 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`command_dispatch_enabled=true`、`manual_control_enabled=true`、`navigate_goal_enabled=true`、`keyboard_control_enabled=true`、`robot_control_executed=true`、`sends_motion_commands=true`、`sends_base_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`opens_base_uart=true`、`uses_base_uart=true`、`hil_pass=true` 等硬危险 true 字段才会 fail closed。
- 2026-06-11 15:15 起，`GET /api/radar/status` 额外补上只读 lifecycle/continuity 合同，解决之前 PC/proxy 已能 start/stop LiDAR lifecycle、`scan-proof/latest` 也 fresh，但 status 仍固定 `continuous_scan_status=not_proven` 的缺口。上位机现在继续只读 `runtime/lidar_scan_proof_latest.json`，并优先只读 `bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh status`，脚本缺失时再 fallback 同目录脚本；因此新增 `lifecycle_status`、`lifecycle_running`、`lifecycle_state`、`lifecycle_pid`、`continuous_window_observed`、`continuity_window_status`、`continuity_blocked_reasons`。当 lifecycle `running=true` 且 latest proof 四项观测齐全、artifact freshness=`fresh` 时，`continuous_scan_status` 会返回 `latest_proof_fresh_while_lifecycle_running`，明确表示“当前连续窗口观察到 lifecycle running + fresh proof”；它不是长稳连续扫描统计证明，也不是 motion/HIL 许可。若 lifecycle 未运行、status 脚本失败、proof 缺失或 stale，status 会继续 fail-closed，并暴露 `lidar_lifecycle_not_running`、`lifecycle_status_read_failed`、`latest_scan_proof_missing`、`latest_scan_proof_stale` 等真实 blocker。无论这些字段如何变化，PC 侧仍必须保持 `safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`delivery_success=false`。
- 2026-06-11 12:45 clean-baseline PC proxy refresh：本轮没有改普通用户首屏组件、`App.vue` 或样式，只用临时本机 API `http://127.0.0.1:18788` 通过固定代理触发真实上位机 `http://192.168.1.11:8787` 的 radar/map proof refresh。证据目录是 `sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/`。Radar proxy response 的 `latest_readback_key_values` 为 `scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`，`hard_dangerous_true_fields=[]`；direct latest readback 的 `latest_result.generated_at=2026-06-11T05:06:46.418393Z` 晚于本轮 `run_started_at=2026-06-11T05:05:22.613Z`。当时 radar latest contract 还没有独立 `evidence_ref`，本轮后续 micro sprint 已补齐该合同，旧记录保留为 gap 来源。Map proxy response 的 `evidence_ref=o3-map-lifecycle-1781154452321`、`map_once_observed=true`、`map_file_observed=true`、`map_metadata_observed=true`；direct latest `generated_at_ms=1781154494512` 晚于本轮开始时间，并保持 `sends_motion_commands=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。本轮 DOM smoke 只验证 `.simple-user-console` 默认可见标题 `Rober 小车控制台` 和五个普通卡片 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`，并确认 `HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、`检查路径` 不在默认可见首屏。
- Robot Control Radar Start/Stop Controls V1：`Robot Control` tab 现在在默认关闭的 `高级诊断` 雷达详情区提供 `启动雷达（高级）` 和 `停止雷达（高级）` 两个按钮。PC 后端新增固定代理 `POST /api/robot-control/radar/start?baseUrl=<robot-api-base-url>` 与 `POST /api/robot-control/radar/stop?baseUrl=<robot-api-base-url>`，分别只转发到上位机 `/api/radar/start` 与 `/api/radar/stop`；浏览器 body 被忽略，上位机请求 body 固定 `{}`，不提供任意 endpoint 或任意参数透传。响应合同固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，并展示 `action`、`remote_endpoint`、`remote_http_status`、`command_result.mode`、`command_result.executed`、`command_result.ok`、`failure_reason`、`blocked_reasons` 和 `hard_dangerous_true_fields`。雷达 lifecycle 中 `sends_commands=true` 可表示传感器控制需要，不自动判定为硬危险；但任何 `sends_motion_commands=true`、`sends_base_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`uses_base_uart=true`、`safe_to_control=true`、`robot_control_executed=true` 等底盘/运动/安全字段都会让 PC 代理 fail closed。首屏雷达卡仍只保留 `刷新雷达` 和短状态，不出现启动/停止雷达按钮。2026-06-11 真实上位机已配置 `ROBER_RADAR_START_COMMAND` / `ROBER_RADAR_STOP_COMMAND` 到 LiDAR-only lifecycle 脚本，PC 高级雷达入口可消费真实 start/stop lifecycle：`POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787` 与 stop 返回 `lifecycle_forwarded`，`command_result.executed=true`、`ok=true`；这仍只证明雷达 runtime lifecycle 可控，不等于运动、Nav2 或 delivery proof。
- Robot Control Nav2 No-Motion Planning Check V1：`Robot Control` tab 的 `高级诊断 -> Nav2 规划详情` 保留 `检查路径（高级）`，用来触发 PC 后端固定代理 `POST /api/robot-control/nav2/proof/refresh?baseUrl=<robot-api-base-url>`。该代理只能转发到上位机固定 `/api/nav2/proof/refresh`，浏览器只提供 `baseUrl`，请求 body 由 Node 固定生成：`timeout_s=30`、`managed_runtime_opt_in=true`、`managed_timeout_s=30`、`managed_map_yaml=/root/rober/onboard/runtime/maps/trashbot_map.yaml`、`initialpose_opt_in=true`、`initialpose_x/y/yaw=0`、`path_generation_opt_in=true`、`path_generation_timeout_s=30`、`path_goal_frame_id=map`、`path_goal_x=0.8`、`path_goal_y=0`、`path_goal_yaw=0`。30s 是 clean-baseline direct Robot API 在同一 no-motion contract 下实测稳定窗口：20s 首轮可能 timeout，30s 可 fresh pass，观测到 `path_generated=true`、`path_point_count=31`、`root_causes=[]`。2026-06-11 19:45 起，workstation fetch timeout 按固定 body 加 60s 余量计算并受 `timeout_cap_ms=150000` 封顶；上位机 helper cap 同步为 132s，fixed body 的 120s raw 预算不会被 upper wrapper 截断，且 PC proxy 等待窗口明确大于 upper helper cap。该入口只证明 managed no-motion 路径规划检查结果，不调用 `/api/nav2/start`、`/api/nav2/stop`、NavigateToPose、map click goal、keyboard control、`/cmd_vel` 或 `/api/base/manual`，也不打开底盘 UART。上位机可返回 `starts_ros2=true` 表示 proof helper 拉起 ROS2 证据 runtime，但必须保持 `starts_nav2=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。如果上位机返回 `path_generated=true` 或 `path_generation_succeeded=true`，普通首屏仍只显示移动/导航短状态和 `停止`；`latest_readback_key_values`、blocked reasons、hard dangerous fields、last refresh time 和 `/api/nav2/proof/refresh` 细节只在高级诊断展示。即使路径可生成，PC 响应顶层仍固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`；如果上位机返回 `starts_nav2=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`safe_to_control=true`、`robot_control_executed=true` 等硬危险 true 字段，PC 代理必须 fail closed。
- Robot Control Delivery Completion Gate V1：`Robot Control` tab 的 `高级诊断 -> Nav2 规划详情` 新增 `确认送达（高级）`，走固定代理 `POST /api/robot-control/delivery/complete?baseUrl=<robot-api-base-url>`，只能转发到上位机 `/api/delivery/complete`。浏览器只能提交 `confirm_delivery_completion`、短 `delivery_evidence_ref` 与短 notes，不能传任意 endpoint、Nav2 goal、manual、stop、地图名、串口或速度参数。上位机 gate 只读取最近 `GET /api/nav2/goal/execution/latest` 和 `GET /api/operator/report`，要求最近 Nav2 goal succeeded、现场 report ready、observed motion/stop、nested `structured_hil_claims.delivery_success=true`、route/map ref 以及外部视频或可见相机 ref 全部齐备；缺项时返回 `blocked_missing_delivery_material` 和 `delivery_success=false`。只有该 gate 全部通过时，PC 端这个固定响应允许 `delivery_success=true` 与 `proof_status=proven`，其它 summary/manual/Nav2 execution/operator report/O7 fixture 路径里的 `delivery_success=true` 仍按危险字段 fail-closed。该按钮默认不在普通首屏出现，且确认送达本身不发送任何运动命令，PC 响应保留 `robot_control_executed=false`。
- 2026-06-22 12:10 起，`高级诊断 -> Nav2 规划详情` 新增 `提交送达材料并确认（高级）` 快捷入口。现场人员必须显式勾选“现场确认已到达/投放，且视频与 route/map ref 可复核”，并填写送达视频 ref 与 route/map ref；可用 `使用最近 Nav2 ref` 从最近一次 PC Nav2 execution response 的 `evidence_ref` 预填 route/map ref。点击后 PC 先通过固定 `POST /api/robot-control/operator/report?baseUrl=...` 提交 operator report，写入 `operator_present/physical_clearance_confirmed/emergency_stop_ready/observed_motion/observed_stop=true` 与 nested `structured_hil_claims.delivery_success=true`、`real_route_map_proven=true`、`route_map_ref`、`external_video_recorded=true`、`external_video_ref`；只有 report 代理成功后才继续调用固定 delivery gate。该入口不自动执行 Nav2、不发 manual/stop、不发布 `/cmd_vel`，也不把任何未勾选或空 ref 的现场材料当真。
- Robot Control Map Lifecycle Controls V1：`Robot Control` tab 现在接入固定 map lifecycle 代理，用来读取和触发上位机已有的 map lifecycle endpoint。PC 后端新增 `GET /api/robot-control/map/list?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/map/start?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/map/save?baseUrl=<robot-api-base-url>`、`POST /api/robot-control/map/reset?baseUrl=<robot-api-base-url>`，分别固定转发到上位机 `/api/map/list`、`/api/map/start`、`/api/map/save`、`/api/map/reset`；不提供任意 endpoint。POST body 只允许 `map_name`、`artifact_path` 两个短文本字段，未知字段、非 object、超长或包含危险字符的字段都被本机拒绝。响应合同固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，并输出 `action`、`remote_http_status`、`map_count`、`map_names`、`command_result.mode`、`command_result.executed`、`failure_reason`、`blocked_reasons` 和 `hard_dangerous_true_fields`。首屏地图卡片提供“刷新地图 / 地图列表 / 重新建图 / 保存地图”和短状态；`重新建图`、`保存地图` 都只调用固定代理，不让浏览器传动态 endpoint、串口、速度或 ROS 参数。`reset` 仍只在高级诊断中以禁用按钮保留。本轮真实 smoke 已允许 PC 代理执行一次 no-motion `/api/map/start`，禁止任何底盘运动、`/cmd_vel` 或 `/api/base/manual`。
- Robot Control Camera Preview V1：既有 `Robot Control` tab 现在包含真实摄像头实时图传观察面，但首屏已经收回到普通用户可读的简易风格，只显示“打开画面/关闭画面”和一句简单状态；`peer_id`、`ICE`、`SDP`、`cleanup` 和会话细节都收进 `<details>`。Node 侧新增 `POST /api/robot-control/camera/offer?baseUrl=<robot-api-base-url>` 和 `POST /api/robot-control/camera/peers/:peerId/close?baseUrl=<robot-api-base-url>`，继续复用 Robot Control 的 `baseUrl` 安全围栏：仅允许 HTTP、loopback/RFC1918、拒绝 credentials/query/hash，并且只允许这两个固定 camera 路径，响应也只保留 `schema/status/peer_id/answer/error` 安全摘要，同时固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。真实上位机当前返回的是顶层 `type/sdp/peer_id` answer，workstation proxy 已兼容这一真实 contract，同时保留对设计稿中嵌套 `answer` 形态的兼容。前端必须由用户显式点击 `打开画面` / `关闭画面` 触发，默认 `preview_status=idle_not_started`，页面初始不自动建会话；打开时创建 `RTCPeerConnection`、只申请 `recvonly video` transceiver、`setLocalDescription` 后等待 `iceGatheringState=complete` 或短超时，确保非 trickle 的上位机 offer SDP 内包含 host candidates，再通过 Node offer proxy 完成 offer/answer；收到远端 video track 后优先绑定 `RTCTrackEvent.streams[0]` 到带 `data-testid="robot-camera-preview-video"` 的 `<video>`，再主动调用 `play()`，并在高级诊断展示真实 video 元素的 `srcObject`、`readyState`、`videoWidth/videoHeight`、`presentedFrames` 或 `requestVideoFrameCallback` 状态。关闭、切换 `baseUrl`、重复打开和组件卸载时都先 cleanup 旧 peer。页面持续展示 `preview_status`、`failure_reason`、`peer_id`、video track/ICE 状态、video 元素绑定/帧状态、`last_offer_at`、`last_stop_at` 和 `cleanup_status`；若打开失败，最终状态保留 `start_failed`，不会被 cleanup 覆盖成 `stopped_by_user`。真实 browser smoke 不能再只用 `preview_status=streaming` 或 `video_track_state=live` 判定通过，必须采集 `data-testid="robot-camera-preview-video"` 的 `srcObject != null`、`readyState >= 2`、`videoWidth/videoHeight > 0` 或 frame callback/canvas pixel 证据，并可用远端 `/api/camera/health` 的 `remote_sdp_candidate_count>0`、`frames_read>0` 辅助解释；其中元素尺寸和帧计数只能说明链路/帧流活跃，画面内容是否可见必须依赖像素/luma 或现场 artifact。该范围明确不包含 cloud relay、TURN/STUN、音频、录制、截图归档或任何运动控制放开；即使图传链路活跃，`/api/base/manual`、`/cmd_vel`、Nav2 goal、radar start、map start、keyboard control 和 map click goal 仍保持 disabled，且 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 不变。当前 run 已有两类真实 smoke：一是 `/api/camera/health` ready、`/api/camera/devices` 返回设备列表，证据保存在 `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/remote_camera_health_devices_2026-06-10.txt`；二是板端 `aiortc` self-test 通过上位机 `/api/camera/offer` 收到 `answer`、获取真实 `640x480` 视频帧、并经 `/api/camera/peers/{peer_id}/close` 把 active peers 从 `1` 回收至 `0`，证据保存在 `sprints/2026.06.10_23-05_pc_camera_webrtc_preview/artifacts/remote_aiortc_offer_frame_close_2026-06-10.json`。2026-06-11 的 PC 页面真实上位机 smoke 已补到浏览器 video 元素和帧流链路级别，证据保存在 `sprints/2026.06.11_07-50_pc_camera_visible_frame_proof/artifacts/browser_camera_visible_frame_state.json`；这仍不单独证明画面内容可见，Stop 后必须继续用 `/api/camera/health` 读回 `active_peer_connections=0`。
- Robot Control Camera Visible Content 2026-06-11 10:15：PC 页面 WebRTC 图传链路已证明可打开、可播放、可关闭并回收 peer，但真实画面仍近黑。本轮 Chrome 隔离浏览器通过 workstation Node proxy 连接 `http://192.168.1.11:8787`，`<video>` 状态为 `srcObject=true`、`readyState=4`、`videoWidth=640`、`videoHeight=480`，canvas `320x240` 采样为 `meanGray=1`、`nonBlackPixelsGt10=0`，video 区域截图仍为黑场；关闭后上位机 `/api/camera/health` 回到 `active_peer_connections=0`。因此 PC 普通首屏仍保持“打开画面/关闭画面”的简易入口，不新增工程词或控制入口；当前风险归因写为物理输入侧待现场处理，而不是 PC proxy、WebRTC、video 元素或服务 auto 选源的软件问题。
- Robot Control Camera Service Reproducibility 2026-06-11 19:14：8088 服务脚本已入仓为 `onboard/scripts/local_webrtc_camera_smoke.py`，PC 侧合同不变，普通首屏仍只提供“打开画面/关闭画面”和短状态。上位机 `/api/camera/health` 现在可回读 camera service 的 `source_candidates_summary/current_selection`、active frame/failure 计数和 last closed peer 摘要；`/api/camera/devices` 仍是只读枚举，成功 schema 为历史兼容的 `trashbot.local_webrtc_camera_devices.v1`；`/api/camera/offer` 成功 schema 为 `trashbot.local_webrtc_camera_offer.v1`，在依赖缺失、invalid offer 或首帧不可读时结构化 fail-closed，不伪造图像；`/api/camera/peers/{peer_id}/close` 成功 schema 为 `trashbot.local_webrtc_camera_close.v1`。该改动只解决服务可复现/可诊断缺口，不解决真实 `/dev/video1` first-frame timeout，也不放宽任何 PC 控制、安全或可见内容判定。
- Robot Control Camera Source Diagnostics 2026-06-11 21:05：PC Robot Control summary 现在从固定只读 `/api/camera/health` 与 `/api/camera/devices` 摘要出 `video_source`、`video_source_mode`、`selected_path`、`active_peer_count`、`last_offer_error` 和 `last_offer_failure_reason`，并只在默认关闭的 `高级诊断 -> 实时画面详情` 展示。真实上位机当前经 PC proxy 读回 `video_source=/dev/video1`、`selected_path=/dev/video1`、`active_peer_count=0`、`last_offer_error=first_frame_unreadable`、`last_offer_failure_reason=first_frame_timeout`。2026-06-11 23:05 起，summary 还透传 `source_readiness` 与 `source_failure_reason`：未发 offer 的源选择状态显示为 `source_selected_not_probed`，真实 offer 首帧失败后显示 `source_readiness=first_frame_failed`、`source_failure_reason=first_frame_timeout`。普通用户首屏仍不展示这些工程字段，不新增相机源切换按钮，也不解锁任何运动或导航能力。
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

2026-06-12 起，Robot Control 的普通首屏仍保持五卡片简洁布局，但地图卡片允许
普通用户直接使用 `刷新地图`、`地图列表`、`重新建图`、`保存地图` 四个动作。按钮文案必须
保持普通语言，不显示 `Start`、`Reset`、`raw`、`HIL`、速度或点动类工程控件。

普通入口和 `高级诊断` 的地图详情都只能调用固定 map lifecycle 代理：

- `刷新地图画面`：GET-only 固定代理到上位机 `/api/map/preview`，仅返回 PGM 转 PNG 的 data URL 摘要。
- `地图列表`：GET-only 固定代理到上位机 `/api/map/list`。
- 普通 `重新建图` / 高级 `开始建图（高级）`：POST 固定代理到上位机 `/api/map/start`。
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

本轮 Browser smoke 结论：首屏 `.robot-console-grid` 为 5 张卡片，地图卡片包含
`刷新地图`、`地图列表`、`重新建图`、`保存地图`；首屏未出现 `开始建图`、`Start`、
`Reset`、`raw`、`HIL`、`速度`、`点动`。打开 `高级诊断` 后，地图详情包含
`开始建图（高级）`、`保存地图`、`map_name（可选）` 和 `artifact_path（可选）`。

边界：该能力只证明 PC 可以经固定代理触发上位机 no-motion map runtime；地图质量必须
继续由上位机 latest proof/readback 判定，不证明 Nav2 可行驶、真实运动、WAVE ROVER HIL、
robot ACK 或 delivery success。

2026-06-22 起，上位机 map lifecycle proof 会在保存后输出 `slam_map_quality`，PC
map proof refresh 的高级诊断 readback 同步展示
`latest_map_quality_status`、`latest_map_free_cell_count` 和
`latest_map_usable_for_navigation`。真实上位机当前结果为
`latest_map_quality_status=no_free_cells`、`latest_map_free_cell_count=0`、
`latest_map_usable_for_navigation=false`；PC 首屏仍只保留普通地图动作，不把这些
工程字段暴露到 `.simple-user-console`。

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

2026-06-25 14:50 起，上位机新增 `/api/map/preview`，只读 `runtime/maps` 下的安全
地图名，解析 YAML 中的相对 PGM，并用 Python 标准库把 P5 PGM 转成 PNG data URL。
PC 端固定代理 `GET /api/robot-control/map/preview` 只接受 `data:image/png;base64,`
且限制摘要大小；普通首屏地图视口成功时直接渲染真实地图图片，保留雷达/定位短 marker，
失败时回退为状态网格。该链路只读文件和 HTTP GET，不启动 SLAM、不保存地图、不发车、
不调用 Nav2、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。

2026-06-25 15:00 起，雷达 marker 不再作为地图右上角状态贴片展示。已定位时，`雷达`
marker 和脉冲圈固定叠在机器人 marker 上；未定位时，地图视口中央显示“雷达运行/待刷新，
位置未读到”，同时保留左下角“位置未读到”缺口。这样现场人员能直接区分“雷达在跑但没地图
坐标”和“雷达 marker 已经有地图坐标”，避免把缺定位状态误看成真实地图坐标。

2026-06-25 15:10 起，最近 Nav2 goal 的目标点也进入同一个真实地图 frame。PC 只接受
`goal_frame_id=map` 的短数字坐标，并按地图 YAML metadata 换算为图片百分比；坐标缺失、
非 map frame 或地图 metadata 不完整时不画 marker。该设计让普通首屏直接看到“最近行程
要去哪里”，但不把 single goal marker 说成完整路线轨迹。

## PC Localization Reset Controls V1

2026-06-11 起，Robot Control 新增 `定位重置（高级）`。该按钮放在默认关闭的
`高级诊断 -> Nav2 规划详情` 中。2026-06-12 起，普通首屏的 `移动/导航` 卡片允许
一个用户语言按钮 `重新定位`，复用同一个固定 no-motion localize reset 代理；普通首屏
仍只有五张卡片和普通动作：`连接/刷新`、`检查小车`、`打开画面/关闭画面`、`刷新雷达`、
`刷新地图`、`地图列表`、`重新建图`、`保存地图`、`重新定位`、`停止`。首屏不显示
`检查路径`、`定位重置`、`initialpose`、`AMCL`、
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
  "timeout_s": 30,
  "managed_runtime_opt_in": true,
  "managed_timeout_s": 30,
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

2026-06-11 22:45 真实 PC proxy 复测发现旧固定 body
`timeout_s=8 / managed_timeout_s=12` 在实板定位 runtime 上窗口偏短：上位机已发布
`/initialpose` 且看到 `/amcl_pose`，但 `map->base_link` TF 未完整观测时就被 wrapper
截断，导致 `localization_reset_observed=false`。本轮将 PC 固定 body 与上位机默认值同步
提升到 `timeout_s=30 / managed_timeout_s=30`，PC fetch cap 提升到 `120000ms`。
复测后 `定位重置（高级）` 返回 `refresh_forwarded/refreshed`，readback 显示
`localization_reset_observed=true`、`managed_runtime_cleanup_ok=true`；随后
`检查路径（高级）` 返回 `path_generated=true/path_generation_succeeded=true/path_point_count=31`。
`导航目标预检（高级）` 仍因 operator report 材料不足返回 HTTP 400，只剩
`operator_report_preflight_required`，没有执行 NavigateToPose、`/cmd_vel` 或
`/api/base/manual`。

2026-06-12 04:45 起，普通首屏 `移动/导航` 卡片新增 `重新定位`。本轮 Browser DOM
smoke 确认 `.simple-user-console` 默认可见按钮包含 `重新定位` 和 `停止`，高级诊断
默认关闭，普通首屏不出现 `定位重置`、`initialpose`、`AMCL`、`Nav2`、`proof`、
`HIL`、`/cmd_vel` 或 `/api/base/manual`。真实 PC proxy 对
`http://192.168.1.11:8787` 调用固定 `POST /api/robot-control/localize/reset`
返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`，
`latest_proof_status=nav2_no_motion_localization_runtime_observed`，
`initialpose_published=true`、`amcl_pose_observed=true`、
`localization_reset_observed=true`、`managed_runtime_cleanup_ok=true`、
`hard_dangerous_true_fields=[]`。这只证明普通 PC 触点能触发 no-motion 重新定位材料，
不证明 NavigateToPose、底盘移动、HIL 或 delivery success。

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
- 默认首屏固定使用默认小车地址，不显示地址输入框；可见主体是五张普通用户卡片：`小车连接`、`实时画面`、`雷达`、
  `地图`、`移动/导航`。
- 默认可见动作只允许：`连接/刷新`、`恢复默认`、`检查小车`、`打开画面/关闭画面`、`刷新雷达`、
  `刷新地图`、`地图列表`、`重新建图`、`保存地图`、`重新定位`、`记录画面`、`试动一下`、`停止`。
- 默认首屏不展示工程词、协议词、证据词、调参控件或危险动作，包括但不限于：
  `HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`O6`、`O7`、
  `Mock`、`field manifest`、`task_id`、`key values`、`现场材料`、`检查路径`、
  `开始建图`、`定位重置`、速度、时长、点动、导航目标坐标、raw/readback。
- 工程能力必须放在默认关闭的 `高级诊断` 或 `高级工具` 内；展开高级区是显式 operator 行为，
  不能影响普通首屏的第一眼观感。

渐进解锁契约：

- `实时画面`：首屏只提供打开/关闭和一句可读状态。WebRTC peer、ICE/SDP、video 元素、
  canvas pixel、设备枚举、近黑判断和 cleanup 细节只进高级诊断。若 summary 已证明当前相机源
  首帧失败，首屏只显示普通提示“相机没有出画面，检查摄像头/视频线。”，不得显示
  `source_readiness`、`first_frame_timeout` 或 `/dev/video*`。图传成功也不解锁移动。
- `雷达`：首屏只提供 `刷新雷达` 和短状态；默认刷新路径使用
  `scan-proof refresh(start_runtime=true)` 的 no-motion 证据窗口。雷达 start/stop、
  scan hz、raw packet、TF、blocked reasons 和 lifecycle 细节只进高级诊断。雷达刷新通过
  只证明 LiDAR/TF 可观测，不等于可运动或可导航。
- `地图`/建图：首屏提供 `刷新地图`、`地图列表`、`重新建图`、`保存地图`。`map_name`、
  `artifact_path`、map lifecycle HTTP 细节和 Reset 只进高级诊断。建图能力只能作为
  no-motion SLAM/runtime evidence capture 渐进开放，首屏不能暴露 Start/Reset 风格按钮。
- `定位/路径检查`：首屏允许 `重新定位` 这个普通用户动作，但不出现 `检查路径`、`定位重置`、
  initialpose、AMCL、Nav2 goal 或坐标输入。`重新定位` 只调用固定 no-motion
  `/api/localize/reset` 代理；定位重置详情、no-motion path generation、导航目标预检都只作为
  高级诊断里的“检查/预检”能力；通过只表示 readiness / preflight，不表示 NavigateToPose 已执行。
- `移动/导航`：首屏默认只显示最小安全确认、普通状态、`重新定位`、`记录画面`、`试动一下` 和
  `停止`。勾选安全确认就是普通发车前最小预检，不再额外展示 `移动前检查` 按钮，也不会因为勾选
  自动提交 operator report。停止是 fail-safe 常驻动作；非 stop 手动移动、
  方向点动、速度/时长、键盘连续控制、地图点击目标、自动导航下发全部默认隐藏。只有在真实
  operator report、可见图传、轮速反馈、LiDAR delta 和外部视频引用等现场材料全部通过后，
  才能在高级诊断中做一次低速短时 jog；首屏仍不得出现方向按钮。缺少运动前材料时，首屏只显示
  普通提示“移动前先完成画面、轮子和周围环境检查；需要时可直接停止。”，不得显示
  `operator_report`、`physical_motion_lidar_delta_proven` 或 endpoint/raw/readback。
- `检查小车`：首屏允许一个普通用户按钮复用安全的一键巡检链路，只显示
  `待检查 / 检查中 / 已检查 / 需要处理 / 检查失败` 这类短状态。它可以依次读取画面、雷达、
  地图、定位和停止结果，但不得把 endpoint、proof、Nav2、HIL、raw/readback 或失败根因放到
  首屏；完整结果仍只在默认关闭的高级诊断中展示。

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
- 最短路径 2：按真实 evidence capture 顺序推进：`打开画面` 先证明链路/帧流，再用像素/luma 或现场 artifact 证明内容可见 → `刷新雷达`
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

## 2026-06-11 PC No-motion Readiness Chain Current Smoke

`sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/` 这一轮只收口既有 no-motion
readiness artifacts，不重跑真实上位机链路，也不把任何结果解释成自动导航、真实移动或
送达成功。

本轮已实测的 proxy / readback 事实：

- `radar proof refresh` 返回 `raw_packets_parsed`，`scan_once_observed=true`、
  `scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`；
  但 `lifecycle_running=false`、`continuous_window_observed=false`，仍是 no-motion
  readiness，不是持续运动证明。
- `map proof refresh` 返回 `map_once_artifact_metadata_observed`。
- `map list` 由 24 增至 26，新增 `pc_no_motion_20260611_162507.yaml` 可见；
  `map start` 与 `map save` 仅作为固定 no-motion lifecycle helper 通过。
- `localize reset` 返回 `nav2_no_motion_localization_runtime_observed`，
  `initialpose_published=true`、`amcl_pose_observed=true`、`managed_runtime_cleanup_ok=true`。
- `nav2 proof refresh` 返回 `nav2_no_motion_path_generation_runtime_observed`，
  `path_generation_succeeded=true`、`path_point_count=18`、`planner_server_active=true`。

Cleanup 读回继续证明 no motion / no base manual / no ttyS5 占用：

- `cmd_vel_topic_count=0`
- `base_manual_http_count=0`
- `ttyS5_lsof_begin`、`ttyS5_fuser_begin`、`cmd_vel_publishers_begin` 均无占用结果

普通首屏契约仍保持不变：默认标题是 `Rober 小车控制台`，`.simple-user-console`
仍只保留五张普通卡片 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`，
默认首屏不出现 `检查路径`、`现场材料`、`HIL`、`Nav2`、`proof`、`/cmd_vel`、
`/api/base/manual`、`Mock`、`field manifest`、`task_id` 等工程词。

证据文件：

- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/no_motion_readiness_chain_summary.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/02_pc_radar_refresh.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/04_pc_map_proof_refresh.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/05_pc_map_list_before.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/06_pc_map_start.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/07_pc_map_save.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/08_pc_map_list_after.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/10_pc_localize_reset.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/12_pc_nav2_refresh.json`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/raw/15_remote_cleanup_readback.log`
- `sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/pc_plain_home_smoke_vitest.json`

## 2026-06-11 真实 PC Proxy Map Lifecycle 证据

本轮 `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/` 未改 PC 产品代码，
只用临时 workstation API `http://127.0.0.1:18790` 通过固定代理访问真实上位机
`http://192.168.1.11:8787`。普通首屏保持简易风格，建图/保存只在默认关闭的
`高级诊断` 内作为 operator 入口。

真实代理链路结果：

- `GET /api/robot-control/map/list?...` 前置读取成功，`map_count=22`。
- `POST /api/robot-control/map/start?...` 使用短安全 `map_name`：
  `pc_map_lifecycle_20260611_1350`，返回 `lifecycle_forwarded`。
- `POST /api/robot-control/map/save?...` 使用同一 `map_name`，返回
  `lifecycle_forwarded`。
- save 后再次 list 成功，`map_count=24`，新增候选包含
  `pc_map_lifecycle_20260611_1350.yaml`。
- reset 未测，记录为 `not_attempted_by_safety_boundary`，避免破坏既有地图或状态。
- 未知字段拒绝 smoke：`POST /api/robot-control/map/save?...` 加
  `arbitrary_endpoint=/api/base/manual` 被本机 400 拒绝，
  `remote_http_status=null`，没有透传到上位机。

安全语义：本轮是 no-motion map lifecycle evidence capture，不是用户发车、
手控、Nav2 执行或 HIL。artifact summary 固定记录：
`safe_to_control=false`、`delivery_success=false`、
`primary_actions_enabled=false`、`robot_control_executed=false`、
`sends_motion_commands=false`、`publishes_cmd_vel=false`、
`calls_base_manual=false`、`uses_base_uart=false`。

首屏边界：DOM smoke 证明 `.simple-user-console` 仍包含标题
`Rober 小车控制台` 和五卡片 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。
默认可见首屏未出现 `开始建图`、`HIL`、`proof`、`Nav2`、
`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、`检查路径`。高级诊断中仍保留
`开始建图（高级）`、`保存地图`、`地图列表`，作为 operator 显式展开后的固定代理入口。

证据文件：

- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/01_map_list_before.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/02_map_start.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/03_map_save.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/04_map_list_after.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/05_map_save_unknown_field_reject.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/pc_plain_user_home_dom_smoke.json`

## 2026-06-11 真实 PC Proxy Localization Reset 证据

本轮 `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/` 未改 PC 产品代码，
只用临时 workstation API `http://127.0.0.1:18791` 通过固定代理访问真实上位机
`http://192.168.1.11:8787`。普通首屏保持简易风格，`定位重置（高级）` 继续只在默认
关闭的 `高级诊断` 内作为 operator 入口。

真实代理链路结果：

- 前置 summary 和直接 `/api/localize/proof/latest` 只读成功。
- `POST /api/robot-control/localize/reset?...` 返回 HTTP 200，
  `proxy_status=refresh_forwarded`、`remote_endpoint=/api/localize/reset`、
  `remote_http_status=200`。
- 请求故意携带 `endpoint=/api/base/manual`、`path_generation_opt_in=true`、
  `sends_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`
  和伪造 `cmd_vel`；代理仍忽略浏览器 body，没有透传任意 endpoint 或运动字段。
- `evidence_ref=o10-amcl-nav2-runtime-1781157704384`。
- 后置 latest readback 证明 `initialpose_published=true`、
  `amcl_pose_observed=true`、`amcl_pose_frame_id=map`、
  `amcl_frame_params={base_frame_id: base_link, global_frame_id: map, odom_frame_id: odom}`、
  `root_causes=[]`。

安全语义：本轮是 no-motion `/initialpose + AMCL` 定位材料采集，不是用户发车、
手控、NavigateToPose、Nav2 goal、固定路线执行或 HIL。artifact summary 固定记录：
`safe_to_control=false`、`delivery_success=false`、
`primary_actions_enabled=false`、`robot_control_executed=false`、
`sends_motion_commands=false`、`publishes_cmd_vel=false`、
`calls_base_manual=false`、`uses_base_uart=false`。

首屏边界：DOM smoke 证明 `.simple-user-console` 仍包含标题
`Rober 小车控制台` 和五卡片 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。
默认可见首屏未出现 `定位重置`、`initialpose`、`AMCL`、`HIL`、`proof`、`Nav2`、
`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、`检查路径`。高级诊断中仍保留
`定位重置（高级）`、`/api/localize/reset`、`initialpose_published` 和
`amcl_pose_observed`。

Cleanup：本机临时 API `127.0.0.1:18791` 已停止且端口无监听；SSH 只读检查
`root@192.168.1.11:37878` 显示 `trashbot-upper-robot-api.service=active`，无长期
localize/Nav2/AMCL/helper 进程残留，`/dev/ttyS5` 和 `/dev/ttyACM0` 的 `lsof/fuser`
均无输出。

证据文件：

- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/pc_proxy/localize_reset_proxy_response.json`
- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/pc_proxy/localize_reset_smoke_corrected_summary.json`
- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/dom_smoke/pc_plain_user_home_dom_smoke.json`
- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/cleanup_ssh_process_device_check.txt`

## 2026-06-11 PC Radar Lifecycle Continuity Current Smoke

`sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/` 未改 PC 产品代码或样式。
本机 workstation API `http://127.0.0.1:18792` 通过固定 PC radar lifecycle 代理连接
真实上位机 `http://192.168.1.11:8787`，执行雷达
start -> during readback -> proof refresh -> stop -> cleanup。

PC proxy 结果：

- `POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787` 返回
  `proxy_status=lifecycle_forwarded`、`remote_http_status=200`、
  `command_result.executed=true`、`command_result.ok=true`。
- `POST /api/robot-control/radar/stop?baseUrl=http://192.168.1.11:8787` 返回同样的
  forwarded/200/executed/ok。
- PC 响应顶层继续固定 `robot_control_executed=false`，没有把 sensor lifecycle
  误声明成机器人控制执行。

during window 结果：

- 4 轮 direct upper `POST /api/radar/scan-proof/refresh`，body 固定为
  `{"start_runtime":false,"timeout_s":12}`，只观察 already-running lifecycle。
- 每轮都得到新 evidence ref，proof state 均为
  `scan_once_hz_raw_packet_tf_observed`。
- scan hz 约 `14.555`、`15.807`、`15.532`、`15.925` Hz；raw packet once 与 TF
  均观测到。
- refresh readback 固定 `read_only_topic_observation=true`、
  `sends_base_motion_commands=false`、`sends_motion_commands=false`、
  `uses_base_uart=false`。

产品/接口 gap：`GET /api/radar/status` during 和 after stop 都仍返回
`continuous_scan_status=not_proven`，blocked reason 为 `scan_continuity_not_observed`。
因此 PC 当前可通过 proxy 控制雷达 start/stop 并刷新 proof，但 status 合同还不能表达
continuous lifecycle running、窗口连续性或 freshness；页面仍只能基于 latest proof
展示一次性观测。

安全边界保持：

- 未调用 `/api/base/manual`。
- 未发布 `/cmd_vel`。
- 未启动 Nav2。
- 未发送非零运动。
- 未写 WAVE ROVER UART `/dev/ttyS5`。
- 未执行 `T=1/T=13/T=130/T=131`。

Cleanup：临时 API `127.0.0.1:18792` 已停止且端口无监听；SSH 只读检查显示 LiDAR
lifecycle stopped，`/dev/ttyACM0` 与 `/dev/ttyS5` 的 `lsof/fuser` 均无输出，
上位机 `upper_robot_api.py --port 8787` 仍在运行，radar status HTTP 200。

证据文件：

- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/summary.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/pc_proxy/01_pc_proxy_radar_start.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/direct_upper/02_during_window.jsonl`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/pc_proxy/03_pc_proxy_radar_stop.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/remote_device/04_after_stop_device_process.log`

## 2026-06-11 真实 PC Camera Link Plain UI Current Smoke 证据

本轮 `sprints/2026.06.11_14-20_pc_camera_plain_ui_current_smoke/` 未改 PC 产品代码，
只用本机 workstation UI/API 通过固定代理访问真实上位机
`http://192.168.1.11:8787`。执行动作限定为连接/刷新、打开实时画面、关闭实时画面
和 DOM/video stats 读取。

图传链路/视频元素活跃结果：

- 上位机 `/api/status` 只读返回成功，`camera.status=ready`、
  `camera.offer_path=/api/camera/offer`。
- 打开图传后，页面 video 元素 `present=true`、`visible=true`、`videoWidth=640`、
  `videoHeight=480`、`readyState=4`、`paused=false`，`currentTime` 持续增长到
  `376.085`。
- 页面没有 canvas 元素，`canvases=[]`。
- 这些 PC DOM/video 字段只证明 video 元素在页面上可见、`640x480` 帧流到达且播放时间推进；
  它们不证明画面内容可见。同轮硬件/OpenCV 证据仍显示 `/dev/video1` near-black。
- 关闭图传后，`preview_status=stopped_by_user`、`ice_connection_state=closed`、
  `video_track_state=stopped`、`cleanup_status=peer_closed:closed`，video 回到
  `readyState=0`、`videoWidth=0`、`videoHeight=0`。

普通首屏边界：可见首屏组合仍包含 `Rober 小车控制台`，`.simple-user-console`
内五卡片为 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。默认可见文本未出现
`HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`定位重置`、`AMCL`、
`task_id`、`Mock`、`检查路径`。当前 DOM 事实是标题位于 `robot-console`
section head/topbar，五卡片位于 `.simple-user-console`；验收应沿用
`App.test.ts` 的 `visiblePlainHomeText()` 组合首屏口径，不把标题未嵌入
`.simple-user-console` 判定为本轮 bug。

安全语义：本轮没有调用 `/api/base/manual`、没有发布 `/cmd_vel`、没有 Nav2 start、
没有非零运动、没有 WAVE ROVER UART。浏览器截图裁剪在 video clip 阶段超时，
因此没有像素 luma 统计；本轮证据边界为 video/canvas DOM stats、video intrinsic
size、readyState/currentTime 和 cleanup diagnostics，只能说明图传链路/视频元素活跃，
不证明内容可见、真实运动、HIL pass、delivery success 或 PC 控制放行。

证据文件：

- `sprints/2026.06.11_14-20_pc_camera_plain_ui_current_smoke/artifacts/pc_camera_visible_video_stats.json`

## 2026-06-11 PC Proxy Real Board Control Smoke 证据

本轮 `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/` 未改 PC UI 代码、
普通首屏组件或样式，只用临时 workstation API `http://127.0.0.1:18793` 通过固定 PC
proxy 连接真实上位机 `http://192.168.1.11:8787`。执行范围限定为 summary 读取、
radar/map/Nav2 no-motion proof refresh、camera health/devices 只读 readback、
base stop smoke，以及 manual 非 stop gate rejection。

结果：

- summary、radar refresh、map refresh、Nav2 refresh、base stop 均返回 HTTP 200；
  manual forward gate rejection 返回本机 HTTP 400。
- radar refresh 经 PC proxy 转发到 `/api/radar/scan-proof/refresh`，生成
  `evidence_ref=o1-lidar-scan-proof-1781172841393`，`scan_once_observed=true`、
  `scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`；
  但 lifecycle stopped，continuous window 未证明。
- map refresh 经 PC proxy 转发到 `/api/map/proof/refresh`，生成
  `evidence_ref=o3-map-lifecycle-1781172868360`，`map_once_observed=true`、
  `map_file_observed=true`、`map_metadata_observed=true`。
- Nav2 no-motion refresh 经 PC proxy 转发到 `/api/nav2/proof/refresh`，但真实上位机返回
  `blocked_with_root_cause`，`path_generated=false`、`path_generation_succeeded=false`、
  `path_point_count=0`、`planner_server_active=false`。这只证明 proxy 链路可达，不证明
  Nav2 规划可用。
- camera 本轮只消费 summary 的固定 proxy readback，`camera.status=ready`、
  `devices_status=loaded`、`preview_status=idle_not_started`；未打开 WebRTC peer，
  因此无 camera cleanup 需求。
- base stop 经 PC proxy 转发到固定 `/api/base/stop`，`remote_http_status=200`、
  `status=stopped`、`evidence_capture_status=captured`，但顶层仍固定
  `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
  `robot_control_executed=false`。
- manual forward `speed=0.12 duration_ms=800 confirm_hil_checklist=true` 被本机 proxy
  拒绝，`remote_http_status=null`、`failure_reason=operator_report_preflight_required`。
  缺少 `external_video_recorded`、`visible_content_proven`、
  `wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`，所以未调用真实
  `/api/base/manual` 成功路径。

安全边界保持：未执行非 stop motion，未发布 `/cmd_vel`，未改变普通用户默认首屏。默认首屏
仍是 `Rober 小车控制台` + `.simple-user-console` 五卡片
`小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`；工程项继续留在默认关闭的
`高级诊断` / `高级工具`。

Artifacts：

- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/pc_proxy_smoke_key_conclusions.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/summary.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/radar_refresh.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/map_refresh.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/nav2_refresh.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/camera_health_devices_from_summary.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/base_stop.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/manual_non_stop_gate_rejection.json`

## 2026-06-11 PC Camera First-frame Probe Proxy

`sprints/2026.06.11_22-00_pc_camera_first_frame_probe_proxy/` 把板端
`onboard/scripts/camera_first_frame_probe.py` 接入 PC 高级诊断。新增链路为：

```text
Vue 高级诊断按钮
  -> POST /api/robot-control/camera/first-frame/probe
  -> POST /api/camera/first-frame/probe
  -> camera_first_frame_probe.py
```

普通用户首屏不变，仍是 `.simple-user-console` 的
`小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航` 五卡片；首帧探针只出现在默认关闭的
“高级诊断 / 实时画面详情”中。

真实 PC proxy smoke 连接 `http://192.168.1.11:8787` 后返回：

- `schema=trashbot.pc_tools_workstation.robot_control_camera_first_frame_probe_proxy.v1`
- `remote_endpoint=/api/camera/first-frame/probe`
- `remote_http_status=503`
- `status=first_frame_timeout`
- `probe_key_values.device=/dev/video1`
- `probe_key_values.requested_fourcc=MJPG`
- `probe_key_values.open_ok=true`
- `probe_key_values.read_ok=false`
- `probe_key_values.failure_reason=capture_read_call_timeout`
- `probe_key_values.visible_content_proven=false`
- `safe_to_control=false`
- `robot_control_executed=false`

这证明 PC 页面已经能触发真实板端底层 camera first-frame 诊断；但它也再次证明当前
`/dev/video1` 首帧不可读，不能宣称实时图传可见内容恢复。下一步仍需要现场排查
DV20 输入源、线缆、供电、采集卡状态，或换 known-good UVC 后用同一高级按钮复测。

## 2026-06-12 PC Camera Backend Smoke

`sprints/2026.06.12_01-15_camera_backend_capture_matrix/` 把相机首帧高级诊断扩展为
backend matrix。PC 代理调用 `/api/camera/first-frame/probe` 时固定传
`include_backend_smoke=true`，上位机在 OpenCV 首帧失败后继续运行固定白名单采集：
`v4l2-ctl MJPG`、`v4l2-ctl YUYV`、`ffmpeg mjpeg`、`ffmpeg yuyv422`。普通首屏不变；
这些结果只显示在默认关闭的 `高级诊断 / 实时画面详情`。

真实 PC proxy 连接 `http://192.168.1.11:8787` 后返回：

- `remote_http_status=503`
- `status=first_frame_timeout`
- `probe_key_values.open_ok=true`
- `probe_key_values.read_ok=false`
- `probe_key_values.failure_reason=capture_read_call_timeout`
- `probe_key_values.backend_smoke_status=backend_no_frame_observed`
- `probe_key_values.backend_frame_observed=false`
- `probe_key_values.backend_attempts=4`

这把实时图传 blocker 从“WebRTC/OpenCV 首帧失败”进一步下钻为“DV20 `/dev/video1`
在 V4L2/ffmpeg 后端也没有帧输出”。PC 页面现在能给现场人员一个更直接的结论：检查
DV20 输入源、HDMI/USB 线缆、供电、采集卡，或换 known-good UVC 复测。

证据文件：

- `sprints/2026.06.11_22-00_pc_camera_first_frame_probe_proxy/artifacts/04_pc_proxy_first_frame_probe.json`
- `sprints/2026.06.11_22-00_pc_camera_first_frame_probe_proxy/artifacts/05_pc_proxy_summary_after_probe.json`
- `sprints/2026.06.11_22-00_pc_camera_first_frame_probe_proxy/artifacts/06_remote_cleanup.txt`

## 2026-06-11 PC Evidence Sweep Button

`sprints/2026.06.11_22-15_pc_evidence_sweep_button/` 在默认关闭的
`高级诊断 / 任务与证据` 中新增“一键证据巡检（高级）”。它按固定顺序复用现有代理：

1. summary
2. camera first-frame probe
3. radar scan proof refresh
4. map proof refresh
5. Nav2 no-motion proof refresh
6. base stop

普通用户首屏不变；该按钮不调用 `/api/base/manual` 成功路径，不发布 `/cmd_vel`，不执行
NavigateToPose。真实 PC proxy smoke 连接 `http://192.168.1.11:8787` 后，雷达、地图、
Nav2 no-motion 和 stop 均返回固定代理结果；相机仍返回
`first_frame_timeout/capture_read_call_timeout`。这说明 PC 已经能把当前可安全执行的
evidence capture 串成一键高级巡检，但实时图传可见内容和非 stop 运动 gate 仍未完成。

2026-06-11 22:30 起，同一条安全巡检链路在普通首屏 `小车连接` 卡片中提供一个
`检查小车` 按钮。首屏只显示短状态和普通提示，例如 `待检查`、`检查中`、`需要处理`、
`已检查`；不会显示 `proof`、`Nav2`、`HIL`、endpoint、raw/readback 或底层失败字段。
完整巡检步骤、HTTP 结果和相机 first-frame 失败原因仍保留在默认关闭的
`高级诊断 / 任务与证据` 中。该首屏按钮仍复用上述只读/stop 顺序，不调用
`/api/base/manual` 成功路径，不发布 `/cmd_vel`，不执行 NavigateToPose。

证据文件：

- `sprints/2026.06.11_22-15_pc_evidence_sweep_button/artifacts/08_sweep_summary.json`
- `sprints/2026.06.11_22-15_pc_evidence_sweep_button/artifacts/09_cleanup.txt`

## 2026-06-11 Live Evidence Status Recapture

`sprints/2026.06.11_23-45_live_evidence_status_recapture/` 通过 PC fixed proxy 对真实上位机
`http://192.168.1.11:8787` 重新走了一轮安全 evidence recapture。调用顺序为 summary、
camera first-frame probe、radar scan proof refresh、map proof refresh、localize reset、
Nav2 no-motion proof refresh、base stop、summary after。该链路没有请求
`/api/base/manual`、`/cmd_vel`、NavigateToPose 或 `/api/nav2/start`。

本轮结果：

- Camera：systemd camera service 已恢复 active；PC summary 读回
  `source_first_frame_failed/first_frame_timeout`，仍未证明可见图传。
- Radar：`radar_scan_proof_refresh` HTTP 200，summary after 显示
  `latest_scan_proof_fresh=true`，但 lifecycle 仍是 stopped。
- Map：`map_proof_refresh` HTTP 200，结果为 `map_once_artifact_metadata_observed`。
- Localization：`localize_reset` HTTP 200，固定 no-motion reset 路径可执行。
- Nav2：`nav2_no_motion_proof_refresh` HTTP 200，但结果为 `blocked_with_root_cause`，
  当前 root cause 是 localization TF：`map_to_odom_not_observed`、
  `/tf_topic_missing`、`base_link_to_laser_frame_not_observed`，因此
  `path_generated=false`。
- Stop：`base_stop` HTTP 200，`status=stopped`，`evidence_capture_status=captured`。

这证明 PC fixed proxy 能重新采集雷达、地图、定位和 stop 的安全证据，同时也把当前阻塞
明确收敛为 camera 首帧失败、Nav2 localization TF 缺口和运动前材料缺失。

## 2026-06-12 Nav2 TF Readiness Reprobe

`sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/` 去掉 subagent 依赖后，直接在
`root@192.168.1.11:37878` 上复测 Nav2 no-motion proof。代码只改
`o10_amcl_nav2_runtime_proof.py` 的 source probe/readiness 窗口，不改 PC 普通用户简易首屏，
不请求 `/api/base/manual`、不发布 `/cmd_vel`、不打开 `/dev/ttyS5`。

本轮结果：

- TF source：`/tf=true`、`/tf_static=true`，AMCL 参数读回
  `global_frame_id=map`、`odom_frame_id=odom`、`base_frame_id=base_link`、
  `tf_broadcast=true`。
- TF chain：`map_to_odom=true`、`odom_to_base_link=true`、
  `base_link_to_laser_frame=true`、`map_to_base_link=true`。
- Nav2 path：`ComputePathToPose` action 可用且 goal accepted，但返回
  `path_point_count=0`，当前 root cause 已收敛为
  `compute_path_to_pose_empty_path`。
- Safety：`safe_to_control=false`、`sends_motion_commands=false`、
  `uses_base_uart=false`、`managed_runtime_cleanup_ok=true`。

证据文件：

- `sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/02_direct_helper_nav2_after_tf_readiness_fix.clean.json`
- `sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/03_upper_runtime_nav2_latest_after_api_refresh.json`
- `sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/05_upper_api_nav2_latest_summary.json`

这意味着上一轮的 localization TF blocker 已解除；下一轮应集中处理 planner/costmap 返回空
path 的原因，而不是继续消耗 `/tf_topic_missing`。

## 2026-06-12 Nav2 Planner Empty Path Recovery

`sprints/2026.06.12_00-55_nav2_planner_empty_path/` 继续不使用 subagent，直接定位
`compute_path_to_pose_empty_path`。根因不是 TF，而是当前 `trashbot_map.yaml` 的 bounds 为
`x=-6.1478..5.1021`、`y=-5.9246..-0.0246`，而固定 no-motion proof 使用的
原始 start/goal `(0,0)->(0.8,0)` 已落在地图上边界外。当前 runtime map 还显示
`free=0`、`unknown=26506`、`occupied=44`，因此这只能作为 planner 软件证据，不是可行驶路线证明。

本轮结果：

- Helper 新增 map yaml/PGM analysis，artifact 写入 bounds、origin、resolution、尺寸和 cell 计数。
- 当固定 proof 点越界时，只在 planner-only `ComputePathToPose` 中使用
  `map_bounds_adapted_no_motion_planner_probe`：原始点仍保留，实际 no-motion test start/goal
  夹到地图内侧。
- 真实上位机 API refresh 返回 `nav2_no_motion_path_generation_runtime_observed`，
  `path_generation_succeeded=true`、`path_point_count=30`、`root_causes=[]`。
- Safety 仍保持 `safe_to_control=false`、`sends_motion_commands=false`、`uses_base_uart=false`，
  未请求 `/api/base/manual`、未发布 `/cmd_vel`、未打开 `/dev/ttyS5`。

证据文件：

- `sprints/2026.06.12_00-55_nav2_planner_empty_path/artifacts/06_remote_map_inventory.json`
- `sprints/2026.06.12_00-55_nav2_planner_empty_path/artifacts/08_upper_runtime_nav2_latest_after_map_adaptive_goal.json`
- `sprints/2026.06.12_00-55_nav2_planner_empty_path/artifacts/10_upper_api_nav2_latest_summary.json`

下一步如果要进入真实移动，需要先补齐更强地图质量、相机可见内容、外部视频、轮速非零和
LiDAR motion delta；本轮不构成真实导航或手动移动放行。

## 2026-06-12 PC Full Safe Evidence Sweep

`sprints/2026.06.12_02-50_pc_full_safe_evidence_sweep/` 在不使用 subagent 的前提下，
通过 PC fixed proxy 对真实上位机 `http://192.168.1.11:8787` 跑了一轮完整安全巡检。
调用顺序覆盖 summary、camera first-frame probe、radar start/refresh/stop、map
list/refresh、localize reset、Nav2 no-motion proof refresh、base feedback samples 和
base stop。该巡检没有调用 `/api/base/manual` 成功路径，没有发布 `/cmd_vel`，没有执行
NavigateToPose，也没有把普通用户首屏改回工程风格。

PC 侧本轮已证明的能力：

- summary 可读：`robot_api_connection.status=readable`，危险字段为空。
- 雷达固定代理可触发 lifecycle start/stop，scan proof refresh 读到 scan、scan hz、
  raw packet 和 TF，证据号 `o1-lidar-scan-proof-1781187807175`。
- 地图固定代理可 refresh 到 `map_once_artifact_metadata_observed`，证据号
  `o3-map-lifecycle-1781183225157`。
- 底盘反馈固定只读采样 3/3 读到 `T=1001`，但这仍是 feedback link，不是运动证明。
- stop 固定代理返回 `status=stopped`。

本轮未完成项也必须留在 PC 产品边界里：camera first-frame probe 仍是
`first_frame_timeout/capture_read_call_timeout`；localize reset 与 Nav2 no-motion proof
在这次 full sweep 中回落为 `blocked_with_root_cause`，其中 Nav2 readback 为
`path_generated=false/path_point_count=0`。PC 高级诊断当前能判断失败，但 localize 的对象型
root cause 在摘要里仍会被压成 `[object Object]`，后续应单独改善可读性。

## 2026-06-12 Nav2 Map Quality Blocker Readback

`sprints/2026.06.12_03-20_nav2_map_quality_blocker/` 修正了 PC 高级诊断里对象型
root cause 的展示：Robot Control summary / fixed proxy 的 key values 现在会把 object/array
压成短 JSON，而不是 `[object Object]`。普通 `.simple-user-console` 首屏未改，工程 root cause
仍只在默认关闭的高级诊断中展示。

真实 PC proxy 连接 `http://192.168.1.11:8787` 后，Nav2 fixed proxy 读回：

- `proxy_status=refresh_forwarded`
- `remote_http_status=200`
- `last_result_status=blocked_with_root_cause`
- `path_generation_boundary=path_generation_blocked_by_map_has_no_free_cells`
- `path_generated=false`
- `path_point_count=0`
- `root_causes=[{"layer":"map quality","reason":"map_has_no_free_cells_for_nav2_path_proof"}]`

这说明 PC 页面已经能把当前“不能定位移动”的主要原因展示成可读诊断：现有地图没有 free
cell，不是浏览器参数、PC proxy body、NavigateToPose 或底盘串口问题。本轮仍不放开
`/api/base/manual`、`/cmd_vel` 或 NavigateToPose。

## 2026-06-12 Map Quality Readback On Plain Console

`sprints/2026.06.12_04-05_map_quality_readback/` 把同一份地图质量 blocker 前移到
PC 地图列表链路。上位机 `/api/map/list` 现在会只读解析本地 map YAML/PGM，并返回
`map_quality_summary`、`map_usable_for_navigation` 和 `map_needs_rebuild`。PC fixed
proxy 只白名单透出短摘要，不把完整路径或栅格细节塞进普通首屏。

真实上位机 readback 显示：

- `map_count=26`
- `checked_yaml_count=13`
- `usable_map_count=0`
- `no_free_cell_map_count=13`
- `map_quality_summary.status=no_free_cells`

普通 `.simple-user-console` 的地图卡片现在在点击“地图列表”后显示：
`当前地图不可导航，需要重新建图。`。浏览器验证确认高级诊断仍默认关闭，首屏没有出现
`Nav2`、`proof`、`HIL`、`/cmd_vel` 或 `/api/base/manual`。

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

## 2026-06-22 Default Robot Address And Keyboard Manual Gate

`sprints/2026.06.22_02-40_pc_default_keyboard_control/` 将 PC 控制台的小车地址默认固定为
`http://192.168.1.11:8787`。页面加载后会自动读取该上位机的 Robot Control summary，但不会自动发送运动命令；普通首屏仍保持面向普通用户的简易风格，高级诊断继续默认折叠。

键盘连续手控入口现在放在普通首屏“移动/导航”卡片：operator 必须先点击 `启用键盘`，让键盘面板获得焦点，然后按住 W/A/S/D 或方向键，才会按 240ms 短脉冲重复走固定 `/api/robot-control/base/manual` proxy；普通页面全局按键、输入框内按键不会触发手控。松开按键、键盘面板失焦、窗口失焦、页面隐藏或切换小车地址会收口并发送 stop。非 stop 键盘点动复用现有 `canSendManualMotion` 门禁，必须同时满足地址、现场 checklist、operator HIL material；材料不满足时不会发送 manual。高级诊断的“现场点动设置 / 控制边界”只保留完整状态、pulse 和 stop trigger 读数。stop 仍保留为独立 fail-safe。

本轮同步修正了 PC 前端 base feedback fallback 字段，使失败态也包含 `wheel_feedback_lr_nonzero_proven`、左右轮速和来源字段。该字段语义依据 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 反馈资料：上位机只读采样 `T=130` 请求、观察 `T=1001` 中的 `L/R`，不发送底盘运动命令，也不把 feedback link 外推为真实移动证明。

真实 PC proxy smoke 连接默认上位机后得到：

- summary 可通过默认地址读取，但当前 `robot_api_connection.status=degraded`，camera health 有 `fetch_timeout_4000ms`，`delivery_success=false`，`primary_actions_enabled=false`。
- `/api/robot-control/map/list` 返回 `map_usable_for_navigation=true`，`usable_map_count=1`。
- `/api/robot-control/base/feedback-samples` 返回 3/3 个 `T=1001` 样本，`sends_motion_commands=false`，但 `wheel_feedback_lr_nonzero_proven=false`，左右轮速仍为 `0/0`。
- `/api/robot-control/nav2/goal/preflight` 仍拒绝，缺 `localization_runtime_or_reset_not_observed`、`path_generation_not_observed`、`path_point_count_not_positive` 和 `operator_report_preflight_required`，且确认没有调用 `/api/nav2/start`、NavigateToPose、`/cmd_vel` 或 `/api/base/manual`。
- `/api/robot-control/base/stop` 可转发并返回 `status=stopped`。

因此本轮只完成 PC 易用性和 gated 键盘入口；完整 Nav2 路线执行、wheel raw L/R 非零和 delivery success 仍是未证明现场能力。

## 2026-06-22 Nav2 Route Proof Readback Repair

`sprints/2026.06.22_10-41_nav2_route_proof_readback/` 修复了 PC fixed Nav2 proof 和上位机 helper 的两处现场问题：

- PC fixed body 不再写死 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`，避免把空地图强塞给上位机。
- 上位机 Nav2 helper 在 managed runtime 缺省地图选择时，优先从 canonical map candidates 中挑选包含 free cell 的 YAML/PGM。
- `lifecycle_manager` 延迟 3 秒启动，避开 map_server/AMCL service 发现竞态。
- 当 managed runtime 本轮已加载可用地图并观测到 `/map` 时，旧 `map_lifecycle_latest.json` 的 blocked 状态不再阻止本轮 `ComputePathToPose` proof。
- PC summary 的 Nav2 proof 聚合改为 proof-first：旧失败 readback 的 `false/0` 不覆盖后续 `nav2_proof_latest` 的 `true/path_point_count`。

真实 PC proxy 连接默认上位机 `http://192.168.1.11:8787` 后，`POST /api/robot-control/nav2/proof/refresh` 返回：

- `last_result_status=refreshed`
- `latest_proof_status=nav2_no_motion_path_generation_runtime_observed`
- `evidence_ref=o10-amcl-nav2-runtime-1782095872075`
- `managed_runtime_map_yaml=/root/rober/onboard/runtime/maps/fixed_free_cells_20260622_0112.yaml`
- `managed_runtime_map_yaml_source=canonical_map_proof_usable_yaml_candidate`
- `path_generation_boundary=explicit_opt_in_compute_path_to_pose_action_no_motion`
- `path_generated=true`
- `path_generation_succeeded=true`
- `path_point_count=31`
- `root_causes=[]`

PC summary 复验显示 `o3_proof_summary.path_generated=true`、`path_generation_succeeded=true`、`path_point_count=31`，但安全状态仍保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，键盘和 NavigateToPose 真实执行仍锁定。当前 `first_jog_readiness_summary.status=blocked_missing_visual_material`，缺 `external_video_or_visible_camera`；因此本轮不证明 wheel raw L/R 非零，也不证明 delivery success。

## 2026-06-22 First-Jog In-Motion Wheel Feedback Readback

`sprints/2026.06.22_10-50_first_jog_inmotion_feedback/` 把 first-jog 从“停车后读反馈”
调整为“点动窗口内读一次反馈、再强制 stop、最后再读停车反馈”。PC proxy 会把上位机
manual 响应里的 `manual_wheel_feedback_summary` 摘成 `remote_motion_key_values`，
高级诊断展示 `motion wheel feedback`，并在计算 `motion_evidence_gaps` 时优先参考
点动窗口内的 wheel material，避免停车后的 `0/0` 覆盖真实运动窗口证据。

真实上位机连接默认地址 `http://192.168.1.11:8787` 后，本轮先关闭 stale WebRTC peer
`f040d79c10d4`，再通过 PC first-frame probe 重新取得可见样张：

- `remote_http_status=200`
- `status=frame_read`
- `visible_content_proven=true`
- `sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782096252146.jpg`

随后提交 operator report `evidence_ref=first-jog-visual-1782096252146`，
PC summary 的 first-jog 状态变为 `ready_for_first_jog`。真实 PC first-jog
`direction=forward`、`speed=0.04`、`duration_ms=800` 成功转发到上位机，
`manual_command_executed=true`、`auto_stop_executed=true`、
`feedback_during_motion_attempted=true`，但本轮实测 `T=1001` 的 `L/R` 仍为 `0/0`，
所以 `wheel_feedback_lr_nonzero_proven=false`、`delivery_success=false`、
`primary_actions_enabled=false` 仍保持锁定。

本轮进一步直连上位机做了三条低风险诊断，均在发送后执行 stop：

- `T=1`：`{"T":1,"L":0.12,"R":0.12}`，点动窗口内与停车后 `T=1001 L/R=0/0`。
- `T=13`：`{"T":13,"X":0.1,"Z":0}`，随后请求 `T=130`，`T=1001 L/R=0/0`。
- `T=11`：`{"T":11,"L":60,"R":60}`，随后请求 `T=130`，`T=1001 L/R=0/0`。

因此 PC 易用性和证据读回链路继续推进，但 wheel raw L/R 非零、完整 Nav2 路线执行和
delivery success 仍不是已完成能力；下一轮应在人工现场确认电机使能、供电、急停、模式、
底盘架空/落地状态和固件反馈语义后继续 HIL。

## 2026-06-22 Same-Session Wheel Raw L/R Proof

`sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/` 修正了上一节的关键假设：
不是 WAVE ROVER `T=1001 L/R` 完全不可用，而是上位机原先把运动命令、运动中 `T=130`、
stop 和停车后 `T=130` 拆成多个短串口会话，容易错过真正的运动窗口。现在
`/api/base/manual` 对非 stop 点动使用同一个串口会话完成：

- 写入 `T=1` 点动命令。
- 立即写入 `T=130` 并读取运动窗口内 feedback。
- 到达脉冲时限后写入 `T=1,L=0,R=0` stop。
- 再写入 `T=130` 并读取停车后 feedback。

真实上位机直连验证 `POST /api/base/manual`、`direction=forward`、`speed=0.12`、
`duration_ms=800` 得到：

- 运动窗口 compact frames 包含 `{"T":1,"L":0.12,"R":0.12}`、`{"T":130}`、
  `{"T":1001,"L":61,"R":61,...}`。
- 停车后 compact frames 包含 `{"T":1,"L":0,"R":0}`、`{"T":130}`、
  `{"T":1001,"L":0,"R":0,...}`。
- `manual_wheel_feedback_summary.lr_nonzero_observed=true`。

真实 PC first-jog 复验 `direction=forward`、`speed=0.04`、`duration_ms=800` 返回：

- `proxy_status=command_forwarded`
- `remote_http_status=200`
- `remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true`
- `wheel_feedback_latest_left_speed=20`
- `wheel_feedback_latest_right_speed=20`
- `evidence_capture_status=captured`
- `motion_evidence_gaps=["physical_motion_lidar_delta_not_proven"]`

PC evidence capture 同步改为串行固定 GET，单 endpoint timeout 提到 5 秒，避免上位机同步读
串口/雷达时被并发请求互相挤到 timeout。该修复让 wheel raw L/R 非零在 PC 工作流里可复验，
但仍不解锁 `delivery_success`、`safe_to_control` 或 `primary_actions_enabled`。完整 Nav2
路线执行与真实交付成功仍需后续路线运行、到达/投放验收和 operator report 收口。

## 2026-06-22 Nav2 NavigateToPose Execution Proof

`sprints/2026.06.22_11-30_nav2_goal_execution_pc_proxy/` 新增 PC 固定高级代理
`POST /api/robot-control/nav2/goal/execute?baseUrl=<robot-api-base-url>`，只转发到上位机
`POST /api/nav2/goal/execute`。该入口默认仍在 `高级诊断 -> Nav2 规划详情` 内，不进入
`.simple-user-console` 普通首屏；普通首屏继续保持面向普通用户的简易风格和 `停止` 安全入口。

上位机新增 `o11_nav2_goal_execution_proof.py`，显式 opt-in 后会托管启动 map/amcl、发布一次
`/initialpose`、等待 planner/controller/BT/behavior lifecycle active，再发送 bounded
`NavigateToPose`。helper 结束后会清理托管 runtime；PC 代理等待窗口大于上位机 helper 的结构化超时，
避免浏览器先超时而丢失 artifact。

真实 PC proxy 连接默认上位机 `http://192.168.1.11:8787` 后，`goal=(map, 0.8, 0, 0)`、
`result_timeout_s=4` 的复验结果为：

- `proxy_status=execution_forwarded`
- `remote_http_status=200`
- `status=goal_succeeded`
- `nav2_goal_execution_proven=true`
- `goal_accepted=true`
- `result_received=true`
- `result_status=succeeded`
- `feedback_sample_count=8`
- `robot_control_executed=true`
- `hard_dangerous_true_fields=[]`
- `delivery_success=false`

PC guard 对这个固定 endpoint 只放行预期会出现的 `robot_control_executed`、
`sends_motion_commands` 和 `sends_commands`，仍然阻断 `safe_to_control=true`、
`primary_actions_enabled=true`、`delivery_success=true`、`hil_pass=true`、`calls_base_manual=true`
等不应由导航 proof 自动声明的字段。Nav2 goal succeeded 只能证明路线执行链路可用；它不等于
垃圾投放、到桶确认或 delivery success。

2026-06-22 13:17 起，PC 高级诊断的送达确认区新增 `送达收口检查`。它把 delivery latest/check/complete
返回的 `blocked_reasons` 与当前表单状态合并，按 `Nav2 路线执行成功`、`现场报告 ready_for_review`、
`现场观察到运动/到达`、`现场观察到停止`、`确认已投放/送达`、`视频与 route/map ref` 六项显示
`已满足/未满足`。该摘要只做现场操作提示，不自动勾选 checklist，不提交 operator report，不调用
delivery complete，也不把 `delivery_success` 提升为 true。真实读回仍显示当前 delivery gate 缺
`confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、
`operator_observed_stop` 和 `structured_hil_claims.delivery_success`，因此 delivery success 仍未完成。

2026-06-22 13:20 起，送达草稿和最终送达 operator report 会保留已有 motion evidence 材料：当
Robot Control summary 中的 `operator_hil_material_summary.wheel_feedback` 或 `lidar_delta` 已经是
`true; ref=...` 时，提交送达草稿/最终确认会把 `wheel_feedback_lr_nonzero_proven + wheel_feedback_ref`
和 `physical_motion_lidar_delta_proven + scan_delta_ref` 一并带入新 report，避免 delivery draft 把
之前保存的 wheel raw L/R 或 LiDAR delta 材料覆盖成 false。若 summary 没有明确 `true; ref=...`，
这些字段仍保持 false/缺 ref；PC 不会凭空生成 wheel、LiDAR 或 delivery success 证据。

2026-06-22 13:30 起，送达草稿同样会保留已有 basic safety 三项：只有当前 Robot Control summary
已读到 `operator_present=true`、`physical_clearance=true`、`emergency_stop=true` 时，草稿 report
才保留对应顶层字段；否则仍写 false。这样 delivery draft 不再无意覆盖 first-jog 前置安全确认，
但也不会把未确认的 operator/clearance/estop 凭空改成 true。`observed_motion`、`observed_stop` 和
`delivery_success` 在草稿中仍固定为 false，最终送达仍必须走完整现场 checklist。

2026-06-22 12:15 起，PC 高级诊断补充固定只读入口
`GET /api/robot-control/nav2/goal/execution/latest?baseUrl=<robot-api-base-url>`，只转发到上位机
`GET /api/nav2/goal/execution/latest`。它用于页面刷新后找回最近 NavigateToPose artifact 的
`evidence_ref`，并让“使用最近 Nav2 ref”同时支持刚执行结果和上位机 latest 结果，预填
送达 operator report 的 `route_map_ref` 与 `delivery_evidence_ref`。该 latest 入口不会重新发送
Nav2 goal，不调用 `/api/base/manual` 或 `/cmd_vel`，顶层继续固定
`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
`robot_control_executed=false`；只有送达视频、route/map ref、现场 observed motion/stop 等人工材料
补齐后，才能再走 delivery gate。

同轮继续补充只读送达缺口入口
`GET /api/robot-control/delivery/latest?baseUrl=<robot-api-base-url>`，只转发到上位机
`GET /api/delivery/latest`。高级诊断中的“读取送达缺口（高级）”会展示最近 delivery gate
状态、`missing_required_material`、Nav2 子状态和 operator report 子状态，用于区分“Nav2 已成功”
与“operator 送达材料仍未补齐”。该入口不提交 `/api/operator/report`、不调用
`/api/delivery/complete`、不触发 Nav2 或底盘运动；即使 latest 显示缺项，PC 也只把缺项列给现场人员，
不会自动代填或伪造 observed motion/stop、视频 ref、route/map ref 或 delivery claim。

2026-06-22 14:00 起，PC 新增固定 `POST /api/robot-control/delivery/check?baseUrl=...`，
高级诊断按钮为“复算送达缺口（高级）”。它转发到上位机 `/api/delivery/complete`，但 body 由
PC 后端写死为 `confirm_delivery_completion=false`、`delivery_evidence_ref=delivery-gap-check-not-confirmed`，
浏览器传入的 confirm 或 success 字段会被忽略。因此该入口只能让上位机用当前 Nav2 latest 与
operator report latest 重新生成 blocked 缺项，不能确认送达；若远端意外返回 `delivery_success=true`，
PC 会按危险字段阻断。

2026-06-22 12:55 起，送达材料快捷表单新增“使用最近画面 ref”。该按钮复用既有固定
`POST /api/robot-control/camera/first-frame/probe?baseUrl=...`，从响应
`probe_key_values.sample_path` 预填“送达视频 ref”。如果本页已经有 camera probe 结果则直接使用，
否则先触发一次固定 camera first-frame probe。该按钮不提交 operator report、不调用 delivery gate、
不勾选现场确认，也不把相机样张外推为 `observed_motion/observed_stop` 或 delivery success；它只减少
现场人员手动复制可追溯画面 ref 的成本。

同轮继续新增“预填送达材料（高级）”组合按钮：先用固定
`GET /api/robot-control/nav2/goal/execution/latest` 找回最近 `goal_succeeded` 的
`evidence_ref`，再用固定 camera first-frame probe 取得 `sample_path`，最后刷新固定
`GET /api/robot-control/delivery/latest` 缺口面板。该按钮只填 `route/map ref`、
`delivery_evidence_ref`、`operator evidence ref` 和“送达视频 ref”，不提交
`/api/operator/report`、不调用 `/api/delivery/complete`，也不替 operator 勾选“现场确认已到达/投放”。

2026-06-22 13:40 起，同一表单新增“提交送达草稿（高级）”。该按钮只在已经有“送达视频 ref”
和 `route/map ref` 时可用，提交固定 `/api/robot-control/operator/report` 草稿：保存
`external_video_ref`、`camera_artifacts_ref`、`route_map_ref` 等材料引用，但刻意写入
`operator_present=false`、`physical_clearance_confirmed=false`、`emergency_stop_ready=false`、
`observed_motion=false`、`observed_stop=false`、`structured_hil_claims.delivery_success=false` 和
`site_state=delivery_material_draft_not_operator_confirmed`。它不会调用 `/api/delivery/complete`，
不会触发运动，也不会把 operator report 404 直接升级为 delivery success；用途只是把缺口从“无 report”
推进成“有草稿材料但缺现场确认”的可复核状态。

2026-06-22 15:10 起，“提交送达材料并确认（高级）”不再使用一个总确认 checkbox。PC 表单改为逐项
现场 checklist：现场有人确认并可接管、周围安全、急停/停止手段、已观察到到达/运动、已观察到停止、
视频与 `route/map ref` 可复核、确认已投放/送达。只有所有项目和“送达视频 ref”、
`route/map ref` 都齐全时，按钮才会提交 `operator_present=true`、`observed_motion=true`、
`observed_stop=true` 与 `structured_hil_claims.delivery_success=true` 的 operator report，再调用固定
`/api/robot-control/delivery/complete` 交给上位机 gate 合成最终结论；缺任一项时 PC 不提交 operator report，
也不调用 delivery complete。该变化只收紧高级送达收口入口，不改变普通用户首屏，也不把当前草稿材料、
camera sample 或 Nav2 goal succeeded 自动外推成真实 delivery success。

2026-06-22 15:12 起，普通首屏“确认送达”和高级“提交送达材料并确认”提交最终 operator report 时，
会把已填写的“送达视频 ref”同时写入 `external_video_ref` 与 `camera_artifacts_ref`，并保持
`visible_content_proven=true`。这只是让最终确认 report 保留草稿阶段已经准备好的视觉材料，避免
delivery gate 因最终 report 缺 `visible_content_proven/camera_artifacts_ref` 被误卡住；PC 仍不自动勾选
现场 checklist，不绕过 `/api/robot-control/delivery/complete`，也不发送 Nav2、manual 或 `/cmd_vel`。

2026-06-22 15:55 起，高级点动区新增 `wheel raw L/R progress` 摘要，用于区分 WAVE ROVER vendor
`T=1001` 静态反馈链路和真实运动窗口轮速证明。该摘要采用 `docs/vendor/VENDOR_INDEX.md` 指向的
WAVE ROVER UART JSON 事实：`T=130` 可请求底盘反馈，`T=1001` 的 `L/R` 是 raw 轮速字段；但
`POST /api/robot-control/base/feedback-samples` 不发送运动命令，所以即使观察到 `T=1001`，只要
`sends_motion_commands=false` 且 `L/R=0/0`，PC 会显示 `static T1001 feedback only`，提示下一步是恢复
first-jog/operator report 材料后再运行轮速非零试采。若 manual/first-jog 返回
`remote_motion_key_values`，该摘要优先展示 during-motion `feedback_during_motion_t1001_frame_count`、
raw `latest_L/latest_R` 和 `wheel_feedback_lr_nonzero_proven`；若被 operator report preflight 挡住，
则直接显示缺失字段，避免现场把静态采样误判成 wheel raw L/R 非零。

2026-06-22 16:25 起，普通 `移动/导航` 卡片新增 `恢复试动确认`。它解决一个现场流程摩擦：
送达草稿会写入上位机唯一的 latest operator report，保留可见画面 ref 但把
`operator_present/physical_clearance_confirmed/emergency_stop_ready` 置为 false，从而挡住后续 first-jog
轮速非零试采。该按钮只在 `first_jog_readiness_summary.status=blocked_missing_basic_safety` 且已有
visual material 时可用；点击后复用 latest summary 中明确 `true; ref=...` 的外部视频/相机 ref，重新提交
基础安全三项为 true 的 operator report。它不调用 `/api/base/manual`、`/api/base/first-jog`、`/cmd_vel`
或 delivery complete，不写 `wheel_feedback_lr_nonzero_proven`、LiDAR delta、route map 或
`delivery_success=true`；用途只是把 first-jog 从送达草稿覆盖状态恢复到可由现场人员试动的前置状态。
同轮高级诊断新增 `first-jog material restore` 摘要，明确上位机 operator report 是 latest-only slot：
若 latest report 的 `site_state=delivery_material_draft_not_operator_confirmed` 且仍保留视觉材料，PC 会显示
`latest-only operator report ... action=restore first-jog confirmation`，避免现场误以为上位机存在可自动回退的
历史 first-jog 材料。
2026-06-22 17:05 起，普通首屏 `试动一下` 按钮也绑定同一 readiness gate：当
`first_jog_readiness_summary.status=blocked_missing_basic_safety` 且 `恢复试动确认` 可用时，`试动一下`
直接禁用，避免现场点了才收到后端 `first_jog_preflight_required`。只有 summary 已是
`ready_for_first_jog`，或本页刚成功提交 `记录画面` / `恢复试动确认` 后，按钮才允许调用固定 first-jog
代理；代理侧仍会再次读取 latest operator report 并 fail-closed。
同轮首屏补充普通禁用原因，例如“试动按钮已锁定：请先点恢复试动确认。”或“请先记录现场画面。”，
让现场知道下一步操作，而不暴露 endpoint、HIL、proof 或 raw feedback 细节。
2026-06-22 17:35 起，普通首屏会在 `试动一下` 返回后显示短轮速证据摘要：若
`remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true`，显示“轮速证据已拿到：L/R=...，运动帧=...”；
若已试动但非零未证明，则显示当前 L/R 与运动帧数量并提示未拿到非零证据。完整
`remote_motion_key_values`、during-motion T1001 帧数和 gaps 仍保留在高级诊断；普通摘要不改变
`delivery_success=false`、`safe_to_control=false` 或 `primary_actions_enabled=false`。

2026-06-22 13:55 起，普通首屏键盘连续手控入口改为“条件满足才可启用”：`启用键盘` 按钮直接绑定
手控 gate，移动前检查、现场材料或轮速记录不足时保持禁用，并继续显示普通话术“先完成移动前检查和轮速记录”。
条件满足后点击启用会聚焦键盘面板，按住 `W/A/S/D` 或方向键期间首屏显示 `手控中` 与“当前方向：
前进/后退/左转/右转”，松开、窗口失焦或页面隐藏仍发送停止。该变化只改善 PC 首屏可理解性，不改变
`/api/robot-control/base/manual` 的 checklist/operator report gate，也不放宽 stop 之外的运动权限。
2026-06-22 18:05 起，上述“条件满足”同时包含后端 summary 的键盘合同；manual gate 齐备但合同缺失时，普通
首屏继续显示“还差：键盘入口”，不会让用户点亮键盘面板。

2026-06-22 13:57 起，普通首屏 `移动/导航` 卡片新增“本轮进度”四项压缩状态：轮速记录、行程执行、
送达确认、键盘手控。该区域只消费当前已读 summary、最近行程结果和送达状态，不触发任何运动、Nav2
执行或送达确认；文案刻意避免 `Nav2/proof/HIL/API` 等工程字段。若 wheel L/R 非零、最近行程成功、
送达完成或键盘 gate 可用，对应项显示 `已完成` 或 `可使用`；否则显示 `待完成/未满足` 并给出下一步
普通提示。完整字段和证据引用仍保留在高级诊断。
2026-06-22 18:25 起，普通首屏 `本轮进度 -> 刷新进度` 会额外调用固定只读
`POST /api/robot-control/base/feedback-samples?baseUrl=...`，让轮速记录直接刷新当前 T1001 帧数与 L/R。
该调用仍只发送后端写死的 T=130 反馈采样，不传方向、速度、duration、串口或任意 endpoint，不调用
`/api/base/manual`、Nav2 goal、delivery complete 或 `/cmd_vel`；L/R 仍为 0/0 时只提示“仍需试动读到非零”，
不会把 T1001 计数解释成 wheel raw L/R 非零完成。
2026-06-22 18:35 起，`本轮进度` 四个快捷按钮从统一“去处理”改为明确的 `去轮速 / 去行程 / 去送达 / 去键盘`。
这些按钮仍只把焦点移动到对应普通首屏面板，不调用行程执行、送达确认、manual、stop 或任何材料提交接口。

2026-06-22 14:00 起，普通首屏 `任务收口` 新增“最终确认”小面板，复用高级送达确认同一组
`deliveryOperatorConfirmations` 和同一条 `submitDeliveryOperatorReportAndComplete` 安全路径。面板默认不勾选；
只有已经准备送达材料、人在旁边可接管、周围安全、停止手段就绪、已观察到到达/移动、已观察到停止、
视频和行程材料已核对、确认已投放/送达全部满足时，`确认送达` 才可点击。点击后先提交 operator report，
再调用固定 `/api/robot-control/delivery/complete` 让上位机 gate 合成结果；仍不发送 Nav2 goal、manual、
`/cmd_vel` 或任何底盘运动。普通首屏不展示 ref/API 字段，避免把最终确认误解成工程调试入口。
2026-06-22 18:30 起，最终确认面板在送达材料未准备时也会显示普通缺口清单：先列“送达材料”，再列
人在旁边可接管、周围安全、停止手段就绪、已观察到到达/移动、已观察到停止、视频和行程材料已核对、
确认已投放/送达。材料准备后清单自动收敛到 7 个现场确认项；这只是 UI 提示，不自动勾选、不提交
operator report、不调用 delivery complete。
2026-06-22 18:40 起，普通首屏保存送达草稿成功后，最终确认状态从泛化的“待勾选”细化为“待确认”，
提示“送达材料已保存；现场逐项确认后再提交”。这只解释下一步，不自动勾选现场确认，也不触发
delivery complete。
2026-06-22 18:45 起，送达草稿覆盖 latest operator report 后，普通首屏所有“恢复试动确认”提示都会明确
标注“不会发车”。该动作只恢复 first-jog 前置现场确认材料，仍不调用 `/api/base/manual`、Nav2、delivery
complete 或 `/cmd_vel`。
2026-06-22 18:50 起，普通首屏“轮速记录”小面板新增 `读取轮速 / 重试读取轮速` 按钮，复用既有
first-jog 固定代理，便于现场在 L/R 仍为 0/0 时直接从轮速区域重试采集。按钮仍受 first-jog gate 控制；
禁用时不发送请求，点击时也不会走旧 `/api/base/manual` 或 `/cmd_vel`。
2026-06-22 19:00 起，`恢复试动确认` 成功后，轮速按钮文案从 `读取轮速` 变为 `开始试动读轮速`，
明确提醒下一步会进入 first-jog 试动窗口；恢复确认本身仍不会发车。
2026-06-22 20:05 起，`试动一下 / 开始试动读轮速` 返回后会自动追加一次固定只读
`POST /api/robot-control/base/feedback-samples?baseUrl=...`，让普通首屏立即刷新当前 T1001 L/R；
该采样依据 `docs/vendor/VENDOR_INDEX.md` 中 WAVE ROVER `T=130` 反馈请求和 `T=1001` L/R 反馈来源，
不发送方向、速度、manual、Nav2 或 `/cmd_vel`，也不把 0/0 或 T1001 计数外推成轮速非零。

2026-06-22 14:03 起，普通首屏 `移动/导航` 卡片新增常驻“轮速记录”小面板。该面板把 wheel raw
L/R 非零采集拆成 `待准备 → 待试动 → 可保存 → 已保存` 的普通状态：默认提示先记录现场画面，再通过
`试动一下` 固定 first-jog 入口读取轮速；只有 first-jog 返回
`remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true` 时，`保存轮速记录` 才可点击。保存动作仍只写
operator report，不再次发送运动命令、不补 LiDAR/route/delivery。轮速字段事实沿用
`docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料：`T=1001` 的 `L/R` 是底盘反馈字段；本轮未修改
串口、底盘协议或硬件参数。

2026-06-22 14:08 起，普通首屏 `移动/导航` 卡片新增“行程操作”入口，把原高级区的固定目标预检/执行流程翻译成
`检查行程`、`执行行程`、`读取行程结果` 三个按钮。默认必须先勾选“人在旁边、周围安全、停止手段就绪”，
否则检查和执行按钮禁用；勾选后普通入口会设置既有 `confirm_navigation_preflight` 或
`confirm_navigation_execution`，再调用固定 PC 代理 `/api/robot-control/nav2/goal/preflight` 或
`/api/robot-control/nav2/goal/execute`。该入口不开放地图点击、任意目标或任意 endpoint；默认目标仍沿用当前
`map` frame 的 `x=0.8,y=0,yaw=0` 受限参数。普通首屏文案继续只显示“行程”，不展示 `Nav2/proof/API`
字段；执行结果只用于“行程执行”状态和后续送达材料，不自动确认 delivery success。

2026-06-25 17:32 起，普通首屏 `检查行程` 作为不发车预检动作，不再被雷达 lifecycle 状态禁用：现场勾选
`人在旁边、周围安全、停止手段就绪` 后，即使雷达未运行或待刷新，也可以先调用固定
`/api/robot-control/nav2/goal/preflight` 查看路线 gate。

2026-06-25 19:00 起，普通首屏 `行程操作` 进一步收敛为最小现场确认：雷达状态只在雷达卡片、地图扫描点和
WYSIWYG 提示里展示，不再作为 `检查行程` 或 `执行行程` 的前端硬挡。勾选同一个安全确认后，行程按钮直接显示
`检查行程` / `执行行程`；真正发车仍必须走 `confirm_navigation_execution` 与后端固定 execute gate。后端
`/api/robot-control/nav2/goal/preflight` 会合并 `/api/localize/proof/latest`、`/api/nav2/proof/latest` 和
`/api/nav2/status` 的定位证据：当 localize latest 是旧失败，但 Nav2 proof/status 已证明 AMCL pose、
`map_to_base_link` 和路径点时，预检不再被 stale localize 单点误挡。该改动不会自动调用
`/api/robot-control/nav2/goal/execute`、`/api/base/manual`、keyboard pulse、delivery complete 或 `/cmd_vel`。

2026-06-25 18:01 起，普通首屏 `行程操作` 新增 `准备行程（不发车）`。该按钮在勾选同一个现场安全确认后可用，
底层只调用固定 `POST /api/robot-control/nav2/proof/refresh` 刷新 no-motion planner proof，并把结果翻译成
`行程准备已刷新` 或 `行程准备还没完成`。它不会调用 `/api/robot-control/nav2/goal/execute`、`NavigateToPose`、
`/api/base/manual`、keyboard pulse、delivery complete 或 `/cmd_vel`；真正发车仍必须再点 `执行行程` 并通过后端 execute gate。
2026-06-25 19:30 起，若 `GET /api/robot-control/summary` 已带 `path_generated/path_generation_succeeded=true` 和正数
`path_point_count/path_preview_point_count`，普通首屏 `行程操作` 会直接显示 `已准备` 和路线点数，例如 `已读到路线 36 个点`，
不要求现场先重复点击 `准备行程（不发车）`。按钮 gate 不变：检查/执行仍必须先勾同一个安全确认，真正执行仍由后端 execute gate 复查。
2026-06-25 19:40 起，同一个 summary 路线准备状态也会进入普通首屏 `本轮进度`：`行程执行` 行显示 `路线已准备 N 个点`，
`当前读数` 显示 `路线已准备 N 点`，验收卡点说明仍需执行完整行程并读到成功结果。该展示不自动调用 nav2 refresh、execute、manual 或 `/cmd_vel`。
2026-06-25 19:50 起，`本轮进度 / 行程执行` 的路线准备提示会跟随安全确认状态：未勾选时提示 `先勾选行程前确认`，
勾选后才提示 `下一步检查或执行行程`，避免普通用户在未完成最小确认时误以为可以直接发车。
2026-06-25 20:00 起，若 summary 或 no-motion proof 已经带正数路线点，并且现场已勾选安全确认，普通首屏会把下一步进一步收敛为
`可执行行程 / 下一步：执行行程`，焦点仍只落到 `执行行程` 按钮，不会自动点击；真正 NavigateToPose 仍必须 operator 显式点击并由后端 execute gate 复查定位和路线。
2026-06-25 18:06 起，若 `准备行程（不发车）` 返回 `planner_server_not_active` root cause，普通首屏会翻译为
`行程服务还没准备好，先点重新定位，或稍后再准备一次。`，不把 `planner_server_not_active/root_causes` 暴露给普通用户。
本轮真实 7001 no-motion proof 结果为 `proxy_status=refresh_forwarded`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`、
`path_generated=false`、`path_point_count=0`、`root_causes=[planner_server_not_active]`；这证明 PC 准备入口安全转发，但不证明完整行程可执行。

2026-06-25 17:56 起，PC 后端 `POST /api/robot-control/nav2/goal/execute` 在转发真实
`/api/nav2/goal/execute` 前，会先复用同一套本机导航预检读取
`/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/nav2/status`。即使有人绕过前端按钮直接 POST
执行接口，只要定位 TF、路线生成或路径点数缺失，PC 也会返回 `execution_rejected`，并且不会向上位机发送
NavigateToPose 执行请求。该后端门禁仍只要求现场安全确认加路线/定位材料，不重新引入 operator report/HIL
材料作为普通行程预检前置；它也不会调用 `/api/base/manual`、keyboard pulse、delivery complete 或 `/cmd_vel`。

2026-06-22 15:14 起，普通首屏点击 `执行行程` 后如果固定代理返回 `goal_succeeded` 和 evidence ref，PC 会自动把
这次行程材料填入送达材料候选，并把“任务收口”材料状态显示为“待画面”。这一步不调用 camera probe、
不提交 operator report、不调用 delivery complete，也不替现场勾选最终确认；用途只是省掉用户从“行程成功”
到“准备送达材料”之间手动复制 route/map ref 的一步。

2026-06-22 14:12 起，普通首屏“轮速记录”下一步提示按当前 first-jog readiness 分流：如果上位机 latest
operator report 是送达草稿、仍保留画面材料但 basic safety 为 false，`first_jog_readiness_summary.status`
会是 `blocked_missing_basic_safety`。此时轮速记录不再提示重新记录现场画面，而是显示“先点恢复试动确认，
再试动读取轮速”。该文案匹配当前真实上位机状态：`/api/base/status` 只读 T=1001 L/R 仍为 `0/0`，
`/api/nav2/goal/execution/latest` 已有 `goal_succeeded` 材料，`/api/delivery/latest` 仍缺 operator 最终确认。

2026-06-22 14:15 起，`恢复试动确认` 按钮从移动/导航顶部动作行移动到“轮速记录”小面板内，和“保存轮速记录”
放在同一行。这样当轮速记录提示“先点恢复试动确认”时，现场人员可以直接在同一模块完成无运动的 latest
operator report 修复，再继续 `试动一下`。按钮行为不变：只提交 first-jog 前置 basic safety report，不调用
`/api/base/manual`、first-jog、Nav2 或 delivery complete。

2026-06-22 14:18 起，普通首屏“本轮进度”新增 `刷新进度` 按钮。它只读刷新 PC summary、最近一次行程执行结果
和最近一次送达状态，用于现场确认 wheel raw L/R 非零、完整路线执行、delivery success、键盘手控 gate
这些收口项有没有变化。该按钮不调用行程执行、送达确认、底盘手控或 `/cmd_vel`，所以不会因为刷新进度触发
小车运动或把送达结果自动写成成功。

2026-06-22 14:22 起，普通首屏“本轮进度”四项新增 `去处理` 快捷按钮。按钮只在当前页面滚动并聚焦到对应普通面板：
轮速记录、行程操作、任务收口或键盘手控，不调用任何 Robot API，也不勾选送达确认、不保存材料、不执行行程、
不发送底盘手控。这样现场人员可以从收口状态直接跳到下一步操作区，同时保持所有真实运动和 delivery success
仍由原按钮和安全 gate 控制。

2026-06-22 14:53 起，普通首屏“最终确认”在送达材料已预填后显示还差哪些人工确认项，例如人在旁边、周围安全、
停止手段、已观察到移动/停止、材料已核对和确认已投放/送达。该提示只读取本页 checkbox 状态，不自动勾选、
不提交 operator report、不调用 delivery complete，也不把 delivery success 置 true；它只是降低现场漏勾导致
delivery gate 继续 blocked 的概率。

2026-06-22 14:56 起，普通首屏 `试动一下` 若已经进入运动采样窗口、但返回的 wheel raw `L/R` 仍是 `0/0`
或其它非非零值，会显示“检查电机使能、供电、模式和现场空间后重试”。`轮速记录` 面板同步显示同样的待重试
提示，并继续禁用 `保存轮速记录`。该文案只解释失败后的现场排查方向，不把静态或运动窗口 `L/R=0/0`
当作 wheel raw L/R 非零证据，也不额外调用 operator report、manual 或 `/cmd_vel`。

2026-06-22 14:59 起，普通首屏键盘手控禁用时会显示还差哪些普通步骤：小车连接、移动前检查、现场画面、
轮速记录或雷达移动记录。该提示由现有手控 gate 和现场材料 summary 只读计算，不展示 HIL/operator report
字段名，不自动提交材料，也不放开 `/api/base/manual`；条件满足后提示消失，仍需用户点击 `启用键盘` 并聚焦面板。
2026-06-22 15:31 起，普通首屏“轮速记录”面板会单独解释“雷达移动记录”缺口：如果 summary 仍缺
LiDAR motion delta，页面显示“雷达移动记录还没拿到：试动时需要雷达看到前后变化，之后键盘手控才会解锁。”
若已经试动但返回 `physical_motion_lidar_delta_not_proven`，则提示检查雷达运行和现场空间后重试。该提示只读
summary 或 first-jog 响应缺口，不调用雷达 start/stop、manual、first-jog、Nav2 或 `/cmd_vel`，也不伪造
LiDAR delta 材料。

2026-06-22 15:03 起，普通首屏 `保存轮速记录` 在写入 wheel raw L/R 非零材料时会保留已有的雷达移动记录：
如果当前 summary 中 `lidar_delta` 已经是明确 `true; ref=...`，提交的 operator report 会继续携带
`physical_motion_lidar_delta_proven=true` 和同一个 `scan_delta_ref`。没有明确 ref 时仍保持 false，不伪造
LiDAR delta。这样保存 wheel 材料不会把已经满足的键盘手控 gate 材料冲掉。

2026-06-22 15:05 起，同一个 `保存轮速记录` 也会保留已有完整路线材料：若当前 summary 的 `route_map`
已经是 `true; ref=...`，新的 wheel report 会继续携带 `real_route_map_proven=true` 和原 `route_map_ref`。
没有明确 ref 时仍保持 false，不凭轮速记录伪造路线材料。这样 latest-only operator report 不会因为保存 wheel
材料而丢失完整 Nav2 路线执行证据，降低后续 delivery success gate 被重新挡住的概率。

2026-06-22 15:09 起，普通首屏所有会写 operator report 的非 delivery 动作统一保留已有进度材料：
`移动前检查`、`记录画面`、`恢复试动确认`、`保存轮速记录` 都会从当前 summary 继承明确
`true; ref=...` 的 wheel、LiDAR 和 route/map ref。没有明确 ref 时仍保持 false，不伪造任何证明；该修复只防止
上位机 latest-only report slot 被普通动作覆盖后丢失已完成的 wheel/Nav2/键盘 gate 材料。

2026-06-22 15:40 起，PC 代理的 first-jog/manual 运动证据压缩白名单包含
`physical_motion_lidar_delta_proven`、`lidar_motion_delta_proven`、`scan_delta_observed` 和 `scan_delta_ref`，
避免上位机已经读到的 LiDAR 位移材料在 workstation 合同里被丢弃。普通首屏 `保存轮速记录` 也会在同轮
first-jog 已消除 LiDAR delta 缺口时，把 `physical_motion_lidar_delta_proven=true` 和可追溯 `scan_delta_ref`
随 wheel raw L/R 一起写入 operator report；若同轮未证明 LiDAR delta，仍保持缺项，不伪造材料。

2026-06-22 15:45 起，Robot Control summary 会从上位机 `/api/base/feedback-samples/latest` 的
`wheel_feedback_summary.latest_pair.left_speed/right_speed` 派生既有 `wheel_feedback_latest_left_speed` 和
`wheel_feedback_latest_right_speed` 摘要字段。这样普通首屏无需重新采样或进入高级诊断，也能直接显示当前只读
T=1001 wheel raw L/R，例如真实 readback 中的 `L/R=0/0`；该派生只读 latest artifact，不发送运动命令，
也不把静态 `0/0` 当作 wheel raw L/R 非零证明。

2026-06-22 15:52 起，Robot Control summary 对 `/api/base/status` 内的 fresh `feedback_readback` 做优先级修正：
若本次 status 同步读到 `t1001_feedback_frame_count`，PC 摘要会把它作为当前 `latest_t1001_observed_count`，
优先于同一 payload 里可能已经 stale 的 `feedback_samples_latest.latest_t1001_observed_count`。这匹配当前真实
上位机状态：fresh `/api/base/status` 可读到 12 帧 T=1001 且 L/R 仍为 `0/0`，旧 samples latest artifact 只有
3 帧且已 stale。该修正只改善普通首屏诊断，不发送 T=130、first-jog、manual、Nav2 或 delivery 请求。

2026-06-22 16:00 起，普通首屏“本轮进度”的 `轮速记录` 项会直接显示当前只读轮速和帧数，例如
`当前轮速 L/R=0/0，已读到 12 帧，仍需试动读到非零。` 该提示来自 PC summary 或本页刚执行的只读底盘反馈采样，
用于解释 wheel raw L/R 非零为什么仍未满足；它不触发新的底盘采样、first-jog、manual 或 `/cmd_vel`。

2026-06-22 16:08 起，普通首屏“本轮进度”的 `送达确认` 项会复用 delivery gate 缺项，直接显示普通步骤：
例如 `还差：现场确认报告、已观察到到达/移动、已观察到停止、确认已投放/送达、最后点击确认送达。`
该提示来自已经读取的 delivery latest/check 结果，只做下一步指引，不自动勾选最终确认、不提交 operator report，
也不调用 delivery complete。

2026-06-22 16:18 起，普通首屏“本轮进度”的 `键盘手控` 项复用键盘 gate 缺项清单，不再只显示泛化的
“先完成移动前检查和轮速记录”。未满足时会显示 `先补齐键盘手控条件。还差：移动前检查、轮速记录、
雷达移动记录。` 这与键盘面板下方的普通提示一致；仍不改变 `/api/base/manual` 放行条件，也不会自动启用键盘。

2026-06-22 16:26 起，普通首屏“本轮进度”的 `轮速记录` 项在 latest operator report 是送达草稿、
视觉材料仍在但 basic safety 三项被覆盖时，会把下一步改成 `先点恢复试动确认，再试动读非零。`
例如当前可读到 `L/R=0/0` 和 13 帧 T=1001 时，进度区显示：
`当前轮速 L/R=0/0，已读到 13 帧，先点恢复试动确认，再试动读非零。`
该提示只基于 summary/readback，不发送 first-jog 或 manual。

2026-06-22 20:55 起，如果 summary 读到 `feedback_voltage_v`，`本轮进度` 的 `轮速记录` 项也会补充
`反馈电压约 ...V`，用于现场判断反馈在线和供电读数可见；该电压不作为 wheel raw L/R 非零、运动或 HIL 证明。

2026-06-22 17:14 起，普通首屏 `任务收口` 在送达 gate 缺项下方新增一条 `下一步` 提示，并同步追加到
`本轮进度` 的 `送达确认` 项。提示只根据已读送达材料 ref 和本页本地确认勾选生成，例如先提示
`准备送达材料`、材料已有后提示 `勾选安全三项`，再逐步提示到达停稳、核对材料、确认投放和点击确认送达；
它不自动勾选、不提交 operator report、不调用 `/api/delivery/complete`。

2026-06-22 17:17 起，普通首屏 `键盘手控` 在未满足 gate 时也显示单步 `下一步` 提示，并同步追加到
`本轮进度` 的 `键盘手控` 项。优先级为连接小车、复查手控条件、移动前检查、记录现场画面、读取并保存轮速记录、
试动读取雷达移动记录；该提示不改变 keyboard bounded pulse 合同，不自动启用键盘，也不调用 `/api/base/manual`。

2026-06-22 17:19 起，普通首屏在只读或试动结果显示 wheel `L/R=0/0` 时，`轮速记录` 小面板新增单独
`下一步` 提示；如果 `本轮进度` 同时读到反馈电压，也会把 `仍需试动读到非零` 改成
`下一步：检查电机使能、供电、模式和现场空间后重试读取轮速`。该提示只解释现场排障方向，不发送
first-jog、manual、stop、Nav2 或 `/cmd_vel`，也不把静态 T1001 反馈、电压或 `0/0` 当作非零证明。

2026-06-22 17:23 起，普通首屏 `行程操作` 和 `本轮进度 / 行程执行` 在最近行程读到成功时显示普通证据摘要：
`最近行程成功，反馈 ... 次；送达仍需现场确认。` 该摘要只消费 `/api/robot-control/nav2/goal/execution/latest`
或 delivery gate 已读到的压缩 key，不展示 evidence ref、Nav2/API/proof 字段，不触发行程执行、送达确认、
manual 或 `/cmd_vel`，也不把行程成功外推成 delivery success。

2026-06-22 17:29 起，普通首屏 `最终确认` 的 `确认送达` 按钮在禁用时直接显示缺项数量，例如
`确认送达（还差 8 项）`；全部确认项满足后恢复为 `确认送达`。按钮文案和 `还差 ... 项` 提示共用同一
缺项列表，只改善现场可读性，不放宽 `plainDeliveryConfirmReady`，也不自动提交 operator report 或
`/api/delivery/complete`。

2026-06-22 17:33 起，普通首屏 `启用键盘` 按钮在未满足 gate 时显示缺项数量，例如 `启用键盘（还差 3 项）`；
全部满足后恢复为 `启用键盘`。按钮文案复用普通键盘缺项列表，只改善 PC 键盘连续手控入口的可读性，
不放宽 `canArmKeyboardControl`，也不会自动启用键盘、发送 `/api/base/manual` 或 `/cmd_vel`。

2026-06-22 17:37 起，普通首屏 `复查手控条件` 按钮也会显示当前键盘 gate 缺项数量，例如
`复查手控条件（还差 3 项）`；全部满足后恢复为 `复查手控条件`。该按钮仍只调用普通进度刷新链路，
不发送 keyboard pulse、manual、stop 或 `/cmd_vel`。

2026-06-22 17:41 起，普通首屏 `保存轮速记录` 按钮在未拿到同帧非零 L/R 前显示
`保存轮速记录（等非零 L/R）`，拿到 `wheel_feedback_lr_nonzero_proven=true` 后恢复为 `保存轮速记录`。
按钮仍沿用既有 `plainFirstJogWheelEvidenceReady` gate，不自动保存、不调用 operator report、不发送
first-jog、manual、stop、Nav2 或 `/cmd_vel`。

2026-06-22 17:45 起，普通首屏 `小车地址` 默认固定为 `http://192.168.1.11:8787`，并新增
`默认地址` 按钮用于用户误清空或改错后恢复该地址。该按钮只修改本地输入框，不自动连接/刷新、不调用
Nav2、delivery、manual、first-jog、stop 或 `/cmd_vel`；恢复后仍需用户显式点击 `连接/刷新`。

2026-06-22 17:49 起，普通首屏读到最近行程已完成后，`检查行程` 和 `执行行程` 按钮都会改为
`行程已完成` 并保持禁用，`读取行程结果` 改为 `重新读取行程`。这样现场人员不会在已有成功行程材料时误点
再次执行；读取按钮仍只读 latest 结果，不调用 Nav2 execute、delivery、manual、first-jog、stop 或 `/cmd_vel`。

2026-06-22 17:52 起，普通首屏 `最终确认` 的四个辅助按钮会直接显示下一步：`下一步：勾选安全三项`、
`下一步：确认到达停稳`、`下一步：核对材料`、`下一步：确认投放/送达`；对应项已勾选后显示
`安全三项已勾选`、`已确认到达停稳`、`材料已核对`、`已确认投放/送达`。这些按钮仍只改本地 checkbox，
不提交 operator report、不调用 delivery complete，也不触发 Nav2、manual、first-jog、stop 或 `/cmd_vel`。

2026-06-22 17:54 起，普通首屏 `复查手控条件` 按钮在键盘 gate 未满足时显示
`复查手控条件（还差 N 项，不发车）`；全部满足后恢复为 `复查手控条件`。该按钮仍只刷新 summary、
底盘只读反馈、最近行程和送达状态，不发送 keyboard pulse、manual、first-jog、stop、Nav2 或 `/cmd_vel`。

2026-06-22 17:57 起，普通首屏 `轮速记录` 小面板里的 first-jog 入口从 `读取轮速` 改为
`低速试动读轮速`，恢复材料后显示 `开始低速试动读轮速`，失败后显示 `重试低速试动读轮速`。
文案只说明轮速非零需要低速试动窗口，不放宽 first-jog gate、不自动发车，也不把静态 T1001 `L/R=0/0`
当作 wheel raw L/R 非零证明。

2026-06-22 18:00 起，普通首屏 `确认送达` 按钮在全部确认项满足后显示为 `确认送达（不发车）`；
缺项时仍显示 `确认送达（还差 N 项）`。按钮只在可提交状态下解释动作边界，后端 gate、operator report
和 delivery complete 合同不变，不发送 Nav2、manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-22 18:03 起，普通首屏 `复查送达条件` 按钮会显示 `复查送达条件（还差 N 项，不确认）`；
当前未读到缺口时显示 `复查送达条件（不确认）`。该按钮仍只调用固定 `POST /api/robot-control/delivery/check`
且后端请求固定 `confirm_delivery_completion=false`，不提交 operator report、不调用 delivery complete，不发车。

2026-06-22 18:06 起，普通首屏 `启用键盘` 在 gate 全部满足后显示为 `启用键盘（按键才动）`；未满足时仍显示
`启用键盘（还差 N 项）`。点击启用只让键盘面板获得焦点，不发送 keyboard pulse、manual、stop、Nav2
或 `/cmd_vel`；真正手控仍必须后续按住 W/A/S/D 或方向键，并继续复用 manual gate。

2026-06-22 18:09 起，普通首屏键盘面板里的 `键盘停止` 显示为 `键盘停止（随时可点）`。该按钮仍走既有
固定 stop 代理，用于收口键盘循环；不放宽非 stop manual gate，不发送 keyboard pulse、Nav2 或 `/cmd_vel`。

2026-06-22 18:12 起，普通首屏 `刷新送达状态` 显示为 `刷新送达状态（只读）`，pending 时显示 `刷新中`。
它仍只调用固定 `GET /api/robot-control/delivery/latest`，不提交 operator report、不调用 delivery complete，
不执行 Nav2、manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-22 18:15 起，普通首屏 `本轮进度` 的刷新按钮显示为 `刷新进度（只读）`，pending 时显示 `刷新中`。
它仍只刷新 summary、base feedback samples、Nav2 latest 和 delivery latest/check 读回，不执行行程、不确认送达、
不发送 manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-22 18:19 起，普通首屏 `保存送达草稿` 显示为 `保存送达草稿（不确认）`，pending 时显示 `保存中`。
该按钮仍只提交 material-only operator report 草稿，写入 `delivery_success=false` 和
`delivery_material_draft_not_operator_confirmed`，不会调用 delivery complete、Nav2、manual、first-jog、stop、
keyboard pulse 或 `/cmd_vel`。

2026-06-22 18:23 起，PC summary 会把上位机 `feedback_samples_latest.freshness.status` 提炼为底盘
`latest_feedback_status`；普通首屏轮速记录若读到 `stale`，会提示 `历史轮速样本已过期，以当前读回为准`。
该提示只解释 `/api/base/status` 与 latest sample 的新旧关系，不发送 T=1/T=13、manual、first-jog、Nav2、
delivery complete、keyboard pulse 或 `/cmd_vel`，也不会把历史样本外推成 wheel raw L/R 非零证明。

2026-06-22 23:24 起，普通首屏从 `GET /api/robot-control/delivery/latest` 读到上位机已有
`delivery_material_draft_not_operator_confirmed` 草稿时，也会把送达材料状态显示为 `已保存`，并提示
`送达材料草稿已保存；请完成下方最终确认`。该提示只消费 latest readback，不自动勾选最终确认、
不提交 operator report、不调用 delivery complete，不发送 Nav2、manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-23 00:04 起，普通首屏“小车连接”会把全量 Robot API `fetch_timeout_*` 读回失败翻成
`上位机没回应；检查小车电源、网络和上位机服务后再点连接/刷新`。该提示只消费 PC summary 的
`robot_api_connection.blocked_reasons`，不会把 timeout 当成已连接，也不会触发 Nav2、delivery complete、
manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-23 00:08 起，普通首屏检测到送达材料草稿已存在时，禁用态 `确认送达` 按钮从
`确认送达（还差 N 项）` 调整为 `确认送达（先确认 N 项）`。该文案只强调现场最终确认步骤，不自动勾选、
不提交 operator report、不调用 delivery complete，不发送 Nav2、manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-23 00:11 起，普通首屏“轮速记录”新增 `刷新当前轮速（只读）`。该按钮只复用固定
`POST /api/robot-control/base/feedback-samples?baseUrl=...` 读取当前 T1001 L/R，pending 时显示 `刷新中`；
不发送 T=1/T=13、manual、first-jog、stop、Nav2、delivery complete、keyboard pulse 或 `/cmd_vel`。

2026-06-23 03:50 起，普通首屏和高级诊断的最终送达确认都要求送达材料里的 route/map ref 与当前未过期
行程结果的 `evidence_ref` 一致。若页面从 `/api/robot-control/delivery/latest` 恢复了旧草稿，但又读到一条
新的本轮行程成功记录，`确认送达` 会显示 `确认送达（先更新行程材料）` 并保持禁用；点击 `准备送达材料`
只把 route/map ref 更新为当前行程 ref，不提交 operator report、不调用 delivery complete，不发送 Nav2、
manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-23 04:05 起，普通首屏“完整 Nav2 路线执行”不再只看 `goal_succeeded`，还要求当前未过期行程结果
带有 `feedback_sample_count` 或 `nav2_feedback_sample_count` 且大于 0。若读到新鲜 `goal_succeeded` 但反馈样本为
0 或缺失，PC 会提示 `最近行程缺少反馈样本，需要重新读取或执行完整行程`，并继续禁用送达最终确认。该规则只
收紧 UI gate，不自动执行行程、不提交 delivery complete，也不发送 manual、first-jog、stop、keyboard pulse 或
`/cmd_vel`。

2026-06-23 05:20 起，Nav2 证据优先级继续收紧：页面一旦读到本页执行结果或直接
`/api/robot-control/nav2/goal/execution/latest`，就以该直接结果作为本轮行程权威来源，不能再用
`delivery/latest` 中的旧 `nav2_feedback_sample_count` 或 route/map 摘要把直接 no-feedback / stale 行程补成完成。
若直接 latest 是 `goal_succeeded` 但反馈样本为 0，普通首屏继续显示 `本轮行程` 缺口，最终确认按钮保持
`确认送达（先重新行程）` 禁用，并且不会提交 operator report、delivery complete、manual 或 `/cmd_vel`。

2026-06-23 04:20 起，普通首屏 `delivery success` 也按当前证据收口：`delivery/latest` 或 completion 读到
`delivery_success=true` 但带有过期 `generated_at_ms/response_generated_at_ms` 时，只显示为旧送达成功记录，
`本轮进度` 仍保持 `送达确认待完成`，最终确认面板提示 `旧送达成功记录不能用于本轮，仍需重新确认送达`。
刚点击确认送达后返回的 completion success 若无时间戳，仍按当前提交结果处理。该规则不自动提交 operator report、
不调用 delivery complete，不发送 Nav2、manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

2026-06-23 04:35 起，普通首屏 `PC 键盘连续手控` 的验证不再跨松开累计脉冲。前端会区分“本次按住”和
“最佳连续”：松开方向键后当前按住计数清零，只有同一次按住会话内连续成功转发至少 2 个 bounded manual pulse，
`本轮进度` 才显示键盘已验证。两次分开的单脉冲只会显示 `最佳连续 1/2 次`，仍要求继续按住完成连续验证。
该规则不放宽 manual gate，不发送额外 Nav2、delivery complete、first-jog、stop 或 `/cmd_vel`。

2026-06-25 16:06 起，PC 普通首屏手控预检精简为最小安全确认：勾选 `人在旁边、周围安全、停止手段就绪`
或扫地式建图卡片的同等安全确认后，即可启用键盘连续手控和固定低速点动。`POST /api/robot-control/base/manual`
仍只允许固定 `/api/base/manual`、固定方向枚举、速度 `<=0.12 m/s`、时长 `<=800 ms`，并继续要求
`confirm_hil_checklist=true`；但 Node 代理不再为了普通手控额外读取 `/api/operator/report`，响应中的
`operator_report_preflight.status` 记录为 `not_required_for_confirmed_manual`，
`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 仍不变。
operator report、轮速非零、LiDAR delta 和送达材料继续作为证据/验收流程展示，但不再阻塞普通低速手控入口。
2026-06-25 20:15 起，普通首屏把 `移动/导航` 和 `扫地式建图` 的安全确认同步为同一个确认状态：勾任一处都会让
行程、键盘和扫图流程共享“人在旁边、周围安全、停止手段就绪”的最小确认；取消任一处也会同步取消。该同步只改变本地 gate
和复选框显示，不自动启动地图记录、不启用键盘、不执行 Nav2、不发送 manual/stop 或 `/cmd_vel`。

2026-06-25 17:44 起，普通首屏“扫地式建图”的 `启用键盘扫图` 入口必须等地图记录启动成功后才可用。现场确认后按钮先显示
`先开始记录`，只有固定 `/api/robot-control/map/start` 返回 `command_result.executed=true` 后才恢复为
`启用键盘扫图`；点击启用仍只聚焦键盘面板，不发送 `/api/base/manual`，真正移动必须后续按住方向键/WASD。
这保持普通键盘手控的最小安全确认入口，同时避免 operator 在未记录地图时先移动。

2026-06-25 17:53 起，普通首屏“扫地式建图”卡片在地图记录启动或保存后新增 `刷新扫图画面`。该按钮只复用
`GET /api/robot-control/map/preview` 读取真实地图图片和 cell 统计，让 operator 在扫图流程内直接看到最新地图覆盖；
记录未启动前按钮显示 `先开始记录` 并禁用。它不调用 `/api/robot-control/map/start`、`/api/base/manual`、
Nav2、keyboard pulse、delivery complete 或 `/cmd_vel`。

2026-06-25 17:57 起，普通首屏“扫图覆盖”会额外显示当前画面口径：未开始记录时说明这是最近地图画面，地图记录中显示
`地图记录中；覆盖条是上次刷新结果，点刷新扫图画面才是当前画面。`，地图已保存后提示刷新检查覆盖效果。该提示只来自本页 map lifecycle 和只读
map preview 状态，不推断真实底盘运动、不自动刷新、不调用 map start、manual、Nav2、keyboard pulse、delivery complete
或 `/cmd_vel`。
2026-06-25 21:30 起，普通首屏“扫地式建图”在地图记录启动后会先把 `保存当前地图` 收紧为 `先刷新画面` 并禁用；
只有本轮点击 `刷新扫图画面` 且只读 map preview 成功返回后，普通保存按钮才恢复可点。该 gate 只保证 operator 保存前看过当前地图画面，
不自动刷新、不自动保存、不发送 manual/keyboard pulse/Nav2/delivery complete/stop 或 `/cmd_vel`。

2026-06-25 19:10 起，普通首屏“扫地式建图”卡片新增 `下一步` 流程按钮，把 operator 依次带到安全确认、开始记录、
启用键盘、按住方向键扫图、停止或保存地图。该按钮只做 `scrollIntoView + focus`，不会自动勾选确认、不会调用
`/api/robot-control/map/start`、不会发送 `/api/base/manual`、不会 stop、不会保存地图，也不会调用 Nav2、delivery complete
或 `/cmd_vel`；真实动作仍必须由现场人员点击对应按钮或按住方向键触发。

2026-06-25 20:45 起，普通首屏“自动扫图准备”在 `free_roam_autonomy=locked` 时明确显示能力边界：
自动扫图未开放，当前只支持人工按住扫图流程 `开始记录 -> 启用键盘 -> 按住方向键/WASD -> 停止 -> 保存地图`。
该提示只改变文案和首屏误操作预期，不打开自动扫图按钮，不调用 map start、manual、Nav2、keyboard pulse、
delivery complete 或 `/cmd_vel`。

2026-06-25 22:35 起，普通首屏地图 caption 新增 `雷达点口径`：雷达运行且有地图位姿时显示“实时雷达已贴到地图”，
雷达运行但缺地图位姿时显示“实时雷达只显示局部轮廓，等定位后再贴地图”，雷达已停但仍有 scan preview 时显示
“这是最近记录，不是实时雷达”。该提示只消费现有 summary/map preview，不刷新雷达、不启动雷达、不发送
manual/keyboard pulse/Nav2/delivery complete/stop 或 `/cmd_vel`。

2026-06-25 23:00 起，普通首屏 `移动/导航` 不再显示 `移动前检查` 按钮。发车前最小预检收敛为勾选
`人在旁边、周围安全、停止手段就绪`；勾选只改变本地 gate，不自动提交 operator report、不发送 manual、
keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。高级诊断中的现场材料提交仍保留给送达和验收材料。

2026-06-25 23:20 起，普通首屏 `行程操作` 会把路线准备和地图可见性分开说清楚：只有真实地图画面上已经画出路线
时才提示 `执行图上路线` 对应地图上的起点、终点和路线；如果只读到路线点数但地图尚未画出路线，则提示先刷新地图画面确认
图上路线。该提示只改变 WYSIWYG 文案，不自动刷新地图、不执行 Nav2、不发送 manual/keyboard pulse/delivery complete/stop
或 `/cmd_vel`。

2026-06-25 23:35 起，普通首屏 `执行图上路线` 按钮也遵循同一 WYSIWYG gate：安全确认已勾但当前路线还没画到地图时，
按钮保持禁用并显示 `先刷新地图画面` 或 `先准备图上路线`；只有当前路线已在地图上画出时才允许点击执行。该 gate
只约束 PC 首屏入口，不自动刷新地图、不自动准备路线、不执行 Nav2、不发送 manual/keyboard pulse/delivery complete/stop
或 `/cmd_vel`；真正执行仍由后端固定 Nav2 execute 代理继续复查定位和路线。

同轮起，Node `GET /api/robot-control/summary` 在缺少 `baseUrl` query 时默认使用固定上位机
`http://192.168.1.11:8787`，与普通首屏默认小车地址保持一致；控制类代理仍要求显式 baseUrl 并继续走原有
fail-closed 校验。PC 工作站仍监听 `0.0.0.0:7001`，该默认值只减少普通访问/直接 curl 的地址配置成本，不改 Clash，
不自动发送 manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。

2026-06-26 00:20 起，普通首屏点击 `启动雷达` 且上位机 lifecycle proxy 明确返回 ok 后，地图上的雷达 marker
会立即从旧 summary 的 `雷达未运行` 切到 `雷达已启动，位置未读到` / `雷达已启动，待刷新`，扫描范围 aria
也标明等待刷新确认。该状态只表达“启动命令已返回，下一步刷新确认”，不把雷达冒充为实时运行、不贴假地图坐标，
不自动刷新 proof、不发送 manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。

2026-06-26 00:35 起，普通首屏“扫地式建图”新增 `扫图状态` 行：未确认时显示小车不会移动，记录未启动时显示键盘扫图锁定，
记录中显示先启用键盘，键盘已启用时提示按住方向键/WASD 低速扫图，按住时显示当前方向和本次连续 pulse 进度，松开并发送
stop 后提示刷新扫图画面或保存地图。该状态只解释现有本地流程和 bounded manual pulse 结果，不自动启用键盘、不自动移动、
不开放自动扫图、不发送 Nav2、delivery complete、stop 之外的隐式控制或 `/cmd_vel`。

2026-06-26 00:50 起，普通首屏“行程操作”新增 `行程状态` 行：未勾安全确认时明确小车不会出发，确认后提示先准备或检查行程，
路线已准备但地图未显示时提示先刷新地图画面，当前路线已画到地图时提示图上路线可执行，执行中/准备中/已完成/旧记录/失败也
给出短状态。该状态只解释现有 gate，不自动勾选、不准备路线、不执行 Nav2、不发送 manual/keyboard pulse/delivery complete/stop
或 `/cmd_vel`。

2026-06-25 20:35 起，普通首屏“实时画面”新增 `画面状态` 行：未打开时明确本页没有显示实时画面，相机在线但未打开时提示点
打开画面，连接中/已打开/画面可见/画面偏暗/失败分别给出普通用户可理解的当前画面结论。该状态只消费现有 camera summary
和本地视频帧采样结果，不自动打开摄像头、不发送 camera offer、不调用 Nav2、不发送 manual/keyboard pulse/delivery
complete/stop 或 `/cmd_vel`。

2026-06-25 20:40 起，普通首屏真实地图画面上新增 `扫地图草图` overlay：地图 preview 已读取且存在可通行区域时，地图上画出
蛇形覆盖草图；如果已有 map-frame 机器人位姿，则额外标出 `扫图起点` 并从当前位置接入。扫地式建图卡片同步显示
`扫地图草图` 状态，明确这是只读计划草图，不会自动移动。该草图不解析为 Nav2 路线、不生成导航目标、不发送 camera offer、
manual/keyboard pulse/Nav2/delivery complete/stop 或 `/cmd_vel`；真实移动仍必须由现场 operator 按安全流程或后续上车端
安全状态机放行。

2026-06-25 20:45 起，普通首屏“行程操作”新增 `行程进度`，地图 caption 新增 `行程执行`：直接读取本轮执行或最近执行结果，
把已到达且有反馈、已到达但缺反馈、旧到达记录、未通过、执行中翻译为普通用户可见文案。该状态只消费
`/api/robot-control/nav2/goal/execute` 或 `/api/robot-control/nav2/goal/execution/latest` 已返回的 key-value，
不自动读取 latest、不自动执行 Nav2、不提交送达确认、不发送 manual/keyboard pulse/stop 或 `/cmd_vel`。

2026-06-25 20:48 起，普通首屏“扫地式建图”在地图记录已启动且键盘扫图 stop 成功后，会自动刷新一次 `扫图画面`，
让 operator 松开方向键后直接看到更新后的地图覆盖并继续保存地图。该刷新只调用只读
`GET /api/robot-control/map/preview`，不自动再次发送 manual/keyboard pulse、不启动 Nav2、不提交 delivery complete、
不发送额外 stop 或 `/cmd_vel`；若地图画面刷新成功，`保存当前地图` 会按原有 gate 变为可用。

2026-06-25 20:52 起，普通首屏“扫地式建图”在按住方向键/WASD 连续扫图达到键盘验证阈值后，会自动刷新一次只读地图画面，
让覆盖条在扫图过程中跟随更新；状态会显示 `地图画面已跟随刷新`。这次按住中的刷新不计入保存 gate，保存仍需松开并完成
stop 后的刷新；因此不会鼓励边移动边保存。该刷新不新增 manual/keyboard pulse、不执行 Nav2、不提交 delivery complete、
不发送 stop 或 `/cmd_vel`。

2026-06-25 20:58 起，普通首屏“自动扫图准备”会读取 `safe_command_boundary.free_roam_autonomy_gates` 并显示逐项门禁：
上车端自动停止、雷达避障、地图刷新、停止按钮兜底、自动扫图真车验证。状态只显示 `已满足/未满足/待验证` 和下一步提示，
用于解释为什么自动扫图按钮仍锁定。该门禁展示不开放自动扫图、不自动开始记录、不发送 manual/keyboard pulse/Nav2/
delivery complete/stop 或 `/cmd_vel`。

2026-06-25 21:07 起，上车端 nav 包新增 `free_roam_autonomy` 策略内核和离线 JSON 入口。PC 首屏暂时不调用该入口，
但“自动扫图准备”的五项门禁已对应策略内核的安全输入：现场确认、地图记录、停止兜底、雷达新鲜、障碍距离。下一步需要把
上车端 `/scan`、`/map` 覆盖变化和 stop fallback 接入 artifact，再由 summary 把策略状态回传给 PC；在此之前自动扫图按钮
继续禁用，不发送 `/cmd_vel`。

2026-06-25 21:18 起，上车端 nav 包新增 `free_roam_autonomy_node`：订阅 `/scan` 和 `/map`，写
`trashbot.free_roam_autonomy.runtime.v1` runtime artifact，并在策略要求停止时调用 `/trashbot/stop` 兜底。该节点默认
`enable_cmd_vel_publish=false`、`motion_hil_unlocked=false`，即使策略输出可前进也不会发布 `/cmd_vel`。PC 首屏仍只显示
自动扫图门禁，等 summary 读取 artifact 和真车 HIL 后再讨论开放按钮。

2026-06-25 21:24 起，PC summary 增加只读 `free_roam_autonomy_latest` 读回。新上位机提供
`/api/free-roam/autonomy/latest` 时，普通首屏“自动扫图准备”会优先显示 runtime artifact 中的 `decision.gates`，
例如现场安全确认、地图记录、雷达新鲜、前方障碍和真车低速放行；旧上位机没有该 endpoint 时按 optional missing 处理，
继续显示默认锁定门禁。该读回不开放自动扫图按钮，不发送 `/cmd_vel`。

2026-06-25 21:34 起，普通首屏 `执行图上路线` 成功返回后，会自动追加一次只读
`/api/robot-control/nav2/goal/execution/latest` 和 `/api/robot-control/delivery/latest` 同步，并用本轮
Nav2 execution `evidence_ref` 预填送达 `route/map` 材料。这样执行按钮、行程进度、送达材料入口和页面刷新后的 latest
读回保持同一证据口径。该同步只发生在 operator 已显式点击执行且后端 execute proxy 已返回后；不会自动确认送达、
不会提交 delivery complete、不发送 manual/keyboard pulse/stop 或 `/cmd_vel`。

2026-06-25 21:40 起，PC summary 的 `safe_command_boundary` 增加只读
`free_roam_autonomy_runtime` 摘要，并在普通首屏“自动扫图准备”里显示 `自动扫图状态`。该状态把上车端
runtime artifact 的 `decision.state/reason/stop_required` 翻译为 `门禁锁定`、`低速直行判断`、`避障换向`、
`原地找新覆盖`、`已完成并要求停止` 等普通文案，同时明确 `节点只写记录，不发布运动` 或运动发布边界。
它只让自动扫图状态机所见即所得，不开放自动扫图按钮，不提交 delivery complete，不发送 manual/keyboard pulse/stop
或 `/cmd_vel`。

2026-06-25 21:44 起，普通首屏地图画面也叠加只读 `自动扫图` runtime 标记：例如 `自动扫图：避障换向`、
`自动扫图：低速直行`、`自动扫图：找新覆盖`。有 map-frame 机器人位姿时标记贴近小车；没有位姿时固定在地图角落，
并明确“不代表坐标”。该标记只把上车端状态机最近判断叠到地图上，不生成路线、不启动自动扫图、不发送 manual/
keyboard pulse/Nav2/delivery complete/stop 或 `/cmd_vel`。

2026-06-25 21:52 起，普通首屏 `执行图上路线` 的请求体坐标绑定到地图上当前可见路线的终点：
`goal_x/goal_y` 来自路线 overlay 最后一个 map-frame 点，高级区 `目标 x/y` 只影响高级 Nav2 表单，不再影响普通用户按钮。
路线预览暂不提供终点朝向，因此 `goal_yaw` 仍沿用显式目标朝向输入。该改动只修正 operator 点击后的 Nav2 goal 请求体，
不自动执行路线、不绕过安全确认、不发送 manual/keyboard pulse/delivery complete/stop 或 `/cmd_vel`。
