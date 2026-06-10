# PC Robot Control Radar/Map Proof Refresh Tech Done

## Sprint Type

- `sprint_type: micro`
- Owner: `full-stack-software-engineer`
- Scope: PC Robot Control 的 Radar/Map proof refresh V2 落地，限定为只读/刷新证据链，不新增任何运动控制。
- 本轮已完成代码、测试、文档和 smoke 留档。

## 设计目标

本轮的目标不是把 Robot Control 做成控制台，而是把 PC 端的 Radar/Map proof refresh contract 写清楚，让运营侧能在同一界面里刷新和复核最新的 `scan` / `map` 证据，同时继续把所有真实控制入口锁住。

设计原则只有三条：

1. 刷新的是 proof，不是 motion。
2. 展示的是 latest evidence，不是可控能力。
3. 任何时候都保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 功能设计

### 1. Radar proof refresh

- 对外只消费 `GET /api/radar/status`、`GET /api/radar/scan-proof/latest` 和 `POST /api/radar/scan-proof/refresh`。
- refresh 只刷新 no-motion 的 LiDAR / TF / raw packet 证据窗，不启动任何底盘动作。
- 典型可见字段：
  - `scan_once_observed`
  - `scan_hz_observed`
  - `raw_packet_once_observed`
  - `tf_observed`
  - `blocked_reasons`
- 设计上允许展示 refresh 后的 latest proof、refresh timestamp、HTTP 状态、失败原因和 guard flags。

### 2. Map proof refresh

- 对外只消费 `GET /api/map/proof/latest` 和 `POST /api/map/proof/refresh`。
- refresh 只刷新 no-motion map proof snapshot，不启动 map server、Nav2、base motion 或任何控制回路。
- 典型可见字段：
  - `map_once_observed`
  - `map_file_observed`
  - `map_metadata_observed`
  - `blocked_reasons`
- 设计上允许展示 latest proof、refresh timestamp、canonical artifact 状态、失败原因和 guard flags。

### 3. 控制边界

- 所有真实控制入口继续默认 disabled 或隐藏。
- 明确禁用 `/cmd_vel` 和 `/api/base/manual`。
- 同时禁用或隐藏 Radar start、Map start、Nav2 goal、keyboard control 和 map click goal。
- 页面只保留 locked placeholder、blocked reason、refresh result 和恢复所需的 safety evidence，不渲染“可控”或“已完成”的暗示。

### 4. 共享状态

- 两个 refresh surface 都必须继续透出统一的 fail-closed 字段：
  - `source`
  - `proof_status`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `refresh_timestamp`
  - `blocked_reasons`
- Node 代理仍是唯一的 Robot API 接入层，Vue 不直接跨域访问上位机。
- 只读代理继续做 URL 白名单、危险字段扫描和 fail-closed 判定，不放宽任何控制面。

## 实际改动

- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts>)，新增 Radar/Map proof refresh proxy 共享契约，并把非运动证据动作与硬危险字段分开建模。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/robotControlSummary.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/server/robotControlSummary.ts>)、[`/Users/m1/apps/rober/pc-tools/workstation/src/server/index.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/server/index.ts>) 和 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/catalog.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/server/catalog.ts>)，落地两个固定 POST 代理：`/api/robot-control/radar/scan-proof/refresh` 与 `/api/robot-control/map/proof/refresh`，固定 body 分别为 `{ timeout_s: 10, runtime_warmup_s: 6, start_runtime: true }` 与 `{ timeout_s: 45 }`，并继续把 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 锁死；`sends_commands=true` / `starts_ros2=true` 现在只进入 `non_motion_evidence_actions_observed`，不会单独触发 fail-closed，真正硬危险字段仍会进入 `hard_dangerous_true_fields` 并阻断。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/client/workstationApi.ts`](</Users/m1/apps/rober/pc-tools/workstation/src/client/workstationApi.ts>) 和 [`/Users/m1/apps/rober/pc-tools/workstation/src/components/RobotControlConsolePanel.vue`](</Users/m1/apps/rober/pc-tools/workstation/src/components/RobotControlConsolePanel.vue>)，把 Robot Control 首屏收回到普通用户可读的简易风格：首屏只保留小车连接、实时画面、雷达、地图和移动/导航五个区域，并把 task_id、O6 base URL、peer/ICE/SDP、readback table、O3 proof summary、route replay、evidence 和更细的刷新字段都下沉到 `<details>` 折叠区；同时保留 `刷新雷达` / `刷新地图` / `打开画面` / `关闭画面` 的既有代理调用和动作后自动回刷 summary。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`](</Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts>) 和 [`/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`](</Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts>)，补齐前端交互测试和后端 fixed POST proxy 测试。
- 更新 [`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`](</Users/m1/apps/rober/docs/product/pc_tools_workstation.md>) 与 [`/Users/m1/apps/rober/pc-tools/README.md`](</Users/m1/apps/rober/pc-tools/README.md>)，把文档同步到已实现状态。
- 生成 smoke artifacts：[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response.json`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response.json>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response.json`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response.json>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/refresh_smoke_summary.txt`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/refresh_smoke_summary.txt>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response_retry.json`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response_retry.json>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response_retry.json`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response_retry.json>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/refresh_smoke_summary_retry.txt`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/refresh_smoke_summary_retry.txt>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response_success.json`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response_success.json>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response_success.json`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response_success.json>)、[`/Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/refresh_smoke_summary_success.txt`](</Users/m1/apps/rober/sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/refresh_smoke_summary_success.txt>)。

## 验收命令

本轮验收覆盖构建、测试、lint、diff 校验、JSON artifact 校验和真实上位机 smoke：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
git diff --check
python3 -m json.tool < sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/radar_refresh_response.json
python3 -m json.tool < sprints/2026.06.10_23-35_pc_radar_map_proof_refresh/artifacts/map_refresh_response.json
# 真实上位机 smoke 通过 workstation proxy 触发：
# POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787
# POST /api/robot-control/map/proof/refresh?baseUrl=http://192.168.1.11:8787
```

## 验证结果

- `npm run build` 通过。
- `npm run test` 通过，`66` 个测试全部通过。
- `npm run lint` 通过。
- `git diff --check` 通过。
- `python3 -m json.tool` 已通过 `radar_refresh_response_success.json` 和 `map_refresh_response_success.json`。
- 真实上位机 smoke 通过 workstation proxy 成功触发两轮固定 POST 刷新：
  - Radar 结果是 `proxy_status=refresh_forwarded`、`last_result_status=refreshed`、`hard_dangerous_true_fields=[]`、`non_motion_evidence_actions_observed=["sends_commands","starts_ros2"]`。
  - Map 结果是 `proxy_status=refresh_forwarded`、`last_result_status=map_once_artifact_metadata_observed`、`hard_dangerous_true_fields=[]`、`non_motion_evidence_actions_observed=["sends_commands"]`。
  - 两个响应都保持了 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 旧的 `*_retry.json` / `*_retry.txt` 保留为第三轮前的定位证据，帮助区分“代理预算失败”与“语义误判失败”两类问题。

## 剩余风险

- workstation 代理的 timeout 预算问题已经修掉：Radar 现在按 `timeout_s=10 + runtime_warmup_s=6 + 余量` 计算，Map 按 `timeout_s=45 + 余量` 计算，并分别封顶在 `60s` / `120s` 内。
- `sends_commands=true` / `starts_ros2=true` 现在被解释为允许的非运动 evidence helper，不再触发 fail-closed；真正会阻断的仍然是硬危险字段，例如 `safe_to_control=true`、`primary_actions_enabled=true`、`command_dispatch_enabled=true`、`robot_control_executed=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`opens_base_uart=true`、`uses_base_uart=true` 和 `hil_pass=true`。
- `refresh` 卡片显示的是 workstation 代理合成的 fail-closed 或 forwarded 结果，不等于上位机已经完成真实控制能力开放。
- 若后续要把这轮从 software proof 推到现场可用，仍然需要继续验证 192.168.1.11:8787 的真实 refresh contract 在更复杂场景下是否会返回额外硬危险字段，并确认响应时延长期稳定。

## 本轮补充

### 实际改动

- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/App.vue`](</Users/m1/apps/rober/pc-tools/workstation/src/App.vue>)，把默认 `activePanel` 改成 `robotControl`，让 PC 工作站打开后先落到简易机器人控制页；同时把顶层 `ProofFlagStrip` 从 topbar 下移除，改为只在 `Proof Boundary` 页的“高级安全信息”里展示。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/components/WorkstationTabs.vue`](</Users/m1/apps/rober/pc-tools/workstation/src/components/WorkstationTabs.vue>)，把标签改成更适合普通用户/运营的短中文标签：`机器人`、`路线`、`控制台`、`预览`、`证据`、`硬件`、`数据`、`安全边界`，并把 `机器人` 放到首位。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/components/ProofBoundaryPanel.vue`](</Users/m1/apps/rober/pc-tools/workstation/src/components/ProofBoundaryPanel.vue>)，在安全边界页内补上 `<details>` 高级安全信息区，承载 `source=software_proof`、`proof_status=not_proven` 等 proof flags。
- 更新 [`/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`](</Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts>)，把 Robot Control 相关断言改成默认首屏校验，并为路线、硬件、O7 控制台、O7 预览和 consumer ingest 相关用例补上新的中文 tab 点击。
- 更新 [`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`](</Users/m1/apps/rober/docs/product/pc_tools_workstation.md>) 与 [`/Users/m1/apps/rober/pc-tools/README.md`](</Users/m1/apps/rober/pc-tools/README.md>)，同步说明默认入口已回到 Robot Control，诊断和 proof flags 已下沉到安全边界页。

### 验证结果

- `cd pc-tools/workstation && npm run build` 通过。
- `cd pc-tools/workstation && npm run test` 通过，`66` 个测试全部通过。
- `cd pc-tools/workstation && npm run lint` 通过。
- `git diff --check` 通过。

### 剩余风险

- 首屏默认已经回到 `Robot Control`，但仍依赖本地浏览器加载顺序；如果用户网络或本机资源极慢，短暂的 loading 提示仍可能先闪一下。
- `ProofFlagStrip` 仍然保留在 `Proof Boundary` 页的高级安全信息里，便于安全复核，但普通用户首屏已经不再直接看到这组 proof flags。
