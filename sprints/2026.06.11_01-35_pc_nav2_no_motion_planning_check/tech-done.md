# PC Nav2 No-Motion Planning Check V1

## sprint_type

micro

## 本轮目标

在 PC 工作站 `Robot Control` 首屏增加 Nav2 no-motion 规划检查入口，让 operator 可以通过 PC 后端固定代理触发上位机 `/api/nav2/proof/refresh` 的路径生成证明，同时继续保持普通用户首屏简洁和所有运动控制 fail-closed。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlProofRefreshKind` 为 `nav2_no_motion_proof_refresh`。
  - 扩展 `remote_endpoint` union，允许固定 `/api/nav2/proof/refresh`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `NAV2_NO_MOTION_PROOF_REFRESH_CONFIG`，固定 body 为 no-motion path generation proof：
    - `managed_runtime_opt_in=false`
    - `initialpose_opt_in=false`
    - `path_generation_opt_in=true`
    - `path_goal_frame_id=map`
    - `path_goal_x=0.8`
    - `path_goal_y=0`
    - `path_goal_yaw=0`
  - 新增 `buildNav2NoMotionProofRefreshProxy(baseUrl)`。
  - `computeRobotProofRefreshTimeoutMs` 计入 `path_generation_timeout_s`，Nav2 proxy 当前等待预算为 46s，仍有 60s cap。
- `pc-tools/workstation/src/server/catalog.ts`
  - 导出 `buildNav2NoMotionProofRefreshProxy`。
- `pc-tools/workstation/src/server/index.ts`
  - 新增固定 POST 路由 `POST /api/robot-control/nav2/proof/refresh?baseUrl=...`。
  - 路由只读取 `baseUrl`，不读取前端 body，不暴露 Nav2 start/stop、goal 或任意 endpoint。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postRobotControlNav2ProofRefresh(baseUrl)`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `移动/导航` 卡片新增 `检查路径` 按钮。
  - 首页只显示 `路径未证明`、`检查中`、`路径可生成`、`检查失败` 短状态。
  - 新增 `Nav2 规划详情` 高级诊断块，展示 endpoint、key values、blocked reasons、hard dangerous fields、last refresh time 和 no-motion 边界。
- `pc-tools/workstation/src/styles.css`
  - 复用既有 status chip 色阶，增加 Nav2 规划检查状态。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 UI fixture 和组件断言，覆盖 `检查路径` 按钮、首页不出现 proof 噪声、高级诊断展示 Nav2 细节。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 Nav2 固定 body、非法 baseUrl fail-closed、危险 true 字段 fail-closed、timeout 预算。
- `docs/product/pc_tools_workstation.md`
  - 补充 Nav2 no-motion 规划检查入口、固定 body、首屏边界和 fail-closed 规则。
- `sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/`
  - 保存本地 fail-closed smoke、真实上位机 smoke、只读 summary 和浏览器 DOM smoke 证据。

## 安全边界

- PC 后端只新增固定代理：
  - PC endpoint：`POST /api/robot-control/nav2/proof/refresh?baseUrl=<robot-api-base-url>`
  - 上位机 endpoint：`/api/nav2/proof/refresh`
- 前端不能传任意 body；Node 后端固定生成 no-motion body。
- 本轮没有暴露：
  - `/api/nav2/start`
  - `/api/nav2/stop`
  - NavigateToPose goal
  - map click goal
  - keyboard control
  - `/cmd_vel`
  - `/api/base/manual`
- 即使 `path_generated=true` 或 `path_generation_succeeded=true`，PC 响应顶层仍固定：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
- 如果远端返回 `starts_nav2=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`safe_to_control=true`、`robot_control_executed=true` 等硬危险字段，PC proxy 返回 blocked / failed。

## 验证结果

运行时间：2026-06-11 01:34:31 CST。

通过：

```bash
cd pc-tools/workstation && npm run build
```

结果摘要：

```text
✓ 33 modules transformed.
✓ built in 1.34s
```

通过：

```bash
cd pc-tools/workstation && npm run test
```

结果摘要：

```text
Test Files  2 passed (2)
Tests  74 passed (74)
```

通过：

```bash
cd pc-tools/workstation && npm run lint
```

结果摘要：

```text
eslint .
```

通过：

```bash
git diff --check
```

结果：无 whitespace error。

## 安全 smoke

本地空 baseUrl：

- 命令：`POST http://127.0.0.1:8791/api/robot-control/nav2/proof/refresh`
- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/nav2_proxy_empty_baseurl.json`
- 结果：
  - HTTP 400
  - `proxy_status=refresh_rejected`
  - `remote_endpoint=/api/nav2/proof/refresh`
  - `failure_reason=baseUrl_not_provided`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`

本地非法 baseUrl：

- 命令：`POST http://127.0.0.1:8791/api/robot-control/nav2/proof/refresh?baseUrl=https://example.com/api?token=secret`
- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/nav2_proxy_illegal_baseurl.json`
- 结果：
  - HTTP 400
  - `proxy_status=refresh_rejected`
  - `remote_endpoint=/api/nav2/proof/refresh`
  - `failure_reason=baseUrl_protocol_not_allowed`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`

真实上位机 no-motion proxy smoke：

- 命令：`POST http://127.0.0.1:8791/api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`
- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/nav2_proxy_real_upper_robot_192_168_1_11.json`
- 结果：
  - HTTP 502
  - `proxy_status=refresh_failed`
  - `remote_endpoint=/api/nav2/proof/refresh`
  - `failure_reason=fetch_timeout_46000ms`
  - `hard_dangerous_true_fields=[]`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`

真实上位机只读 summary after timeout：

- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/robot_control_summary_after_nav2_timeout.json`
- 结果摘要：
  - `o3_proof_summary.path_generated=true`
  - `o3_proof_summary.path_generation_succeeded=true`
  - `o3_proof_summary.path_point_count=31`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`

解释：PC proxy 没有在 46s 内等到上位机 POST 响应，因此本轮不能把真实 POST refresh 代理标记为成功；但只读 latest 摘要显示上位机侧 no-motion path generation proof 已更新成功。该问题不在本轮允许修改的 onboard 范围内。

## 浏览器 / DOM smoke

- 本地 URL：`http://127.0.0.1:8791`
- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/browser_dom_smoke.json`
- 结果：
  - 标题为 `Rober 小车控制台`
  - 首屏五卡片齐全：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`
  - `检查路径` 入口存在
  - 首屏默认显示 `路径未证明`
  - 首屏未出现 proof/raw/HIL/速度/四向点动/保存地图等工程噪声
  - 高级诊断包含 `Nav2 规划详情`
  - 高级诊断包含 `/api/nav2/proof/refresh`
  - 高级诊断包含 no-motion 边界：no Nav2 start/stop、no `/cmd_vel`、no `/api/base/manual`

## 失败定位

真实上位机 no-motion proxy smoke 初次 16s timeout；已修复 PC proxy timeout 预算，纳入 `path_generation_timeout_s`。

修复后真实上位机 no-motion proxy smoke 仍在 46s timeout。只读 summary 证明 latest path generation 已更新成功，因此当前剩余问题更像是上位机 `POST /api/nav2/proof/refresh` 在完成后没有及时返回 HTTP response，或完成时间超过 PC proxy 当前 46s 等待预算。由于本轮禁止改 onboard 上位机代码，未继续修改上位机。

## 剩余风险

- 真实上位机 `POST /api/nav2/proof/refresh` 通过 PC proxy 仍未返回 200；当前 UI 会显示“检查失败”，高级诊断显示 `fetch_timeout_46000ms`。
- 只读 latest 显示路径生成成功，但这不等于 PC POST proxy smoke 通过，也不等于可以发车。
- 本轮没有做 Nav2 start/stop、NavigateToPose、map click goal、keyboard control、`/cmd_vel`、`/api/base/manual` 或真实运动验证。
- 本轮不修改 onboard；后续需要 Robot/Algorithm owner 排查上位机 refresh endpoint 为什么在 path generation 成功后不及时返回。

## OKR 说明

本轮推进 O7 PC 端运营调试平台：新增普通用户可见的 Nav2 no-motion 规划检查入口，并保持控制面 fail-closed。O3 现场验证 lane 获得了只读 latest path generation 证据，但因 PC POST proxy timeout，不能宣称 Nav2 no-motion refresh 代理真实成功。

## 验收修复追加：Nav2 latest fallback 与文档事实

运行时间：2026-06-11 01:41:20 CST。

### 修复项

- 修正 `docs/product/pc_tools_workstation.md` 中 Map Lifecycle 段的首屏描述：
  - 当前事实是首屏地图卡片只提供 `刷新地图 / 查看地图列表` 和短状态。
  - `保存地图` 只保留在高级诊断，不进入普通用户首屏。
- 为 `nav2_no_motion_proof_refresh` 增加 POST 失败后的固定 latest GET 兜底：
  - 仅当 Nav2 no-motion refresh 的 POST fetch timeout/failed 时触发。
  - 固定读取 `GET /api/nav2/proof/latest`。
  - 不接受前端提供任意 latest path。
  - latest 成功且没有 hard dangerous true fields 时，把 `path_generated`、`path_generation_succeeded`、`path_point_count` 等 key values 写入 PC proxy response。
  - `proxy_status` 仍保持 `refresh_failed`，`failure_reason` 仍保留 POST timeout。
  - `blocked_reasons` 追加 `post_timeout_latest_readback_loaded`。
  - 顶层 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 不变。
- 调整 UI `summarizeNav2Planning()`：
  - 当 `refresh_failed` 但 latest key values 显示 `path_generated=true` 或 `path_generation_succeeded=true` 时，首页显示 `路径可生成`。
  - hint 明确为 `刷新请求超时，但 latest 已有 no-motion 路径证据；不会自动发车。`
  - 不把该状态解释为控制成功。
- 补充测试：
  - Nav2 POST timeout 后固定读取 `/api/nav2/proof/latest` 并带回 latest key values。
  - Radar/Map timeout 仍只发一次 POST，不触发 latest fallback。
  - Vue fixture 覆盖 `refresh_failed + latest path proof` 的首页显示。

### 追加验证结果

通过：

```bash
cd pc-tools/workstation && npm run build
```

结果摘要：

```text
✓ 33 modules transformed.
✓ built in 1.32s
```

通过：

```bash
cd pc-tools/workstation && npm run test
```

结果摘要：

```text
Test Files  2 passed (2)
Tests  75 passed (75)
```

通过：

```bash
cd pc-tools/workstation && npm run lint
```

结果摘要：

```text
eslint .
```

### 追加真实上位机 smoke

- 命令：`POST http://127.0.0.1:8791/api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`
- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/nav2_proxy_real_upper_robot_192_168_1_11.json`
- 结果：
  - HTTP 502
  - `proxy_status=refresh_failed`
  - `failure_reason=fetch_timeout_46000ms`
  - `blocked_reasons=["fetch_timeout_46000ms","post_timeout_latest_readback_loaded"]`
  - `last_result_schema=trashbot.upper_robot_api.v1.nav2_runtime_proof_latest`
  - `latest_readback_key_values.path_generated=true`
  - `latest_readback_key_values.path_generation_succeeded=true`
  - `latest_readback_key_values.path_point_count=31`
  - `hard_dangerous_true_fields=[]`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`

### 追加 UI smoke

- artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/nav2_ui_smoke_after_latest_fallback.json`
- 结果：
  - 输入真实上位机 `baseUrl=http://192.168.1.11:8787`
  - 点击 `检查路径`
  - 首屏显示 `路径可生成`
  - 首屏显示 `刷新请求超时，但 latest 已有 no-motion 路径证据；不会自动发车。`
  - 首屏未出现 `path_generation_succeeded`、`path_point_count`、`fetch_timeout_46000ms`、`safe_to_control=false`
  - 高级诊断包含 latest key、`post_timeout_latest_readback_loaded` 和 `fetch_timeout_46000ms`

### 追加剩余风险

- 真实上位机 POST 仍没有在 46s 内返回，PC proxy 继续以 `refresh_failed` 表达该事实。
- latest fallback 只能说明最新 no-motion path proof 已可读，不能说明本次 POST 已正常完成，也不能说明可发车。
- Radar/Map timeout 行为保持原样，没有 latest fallback。

## 主节点验收

- 本地启动 `PORT=8796 npm run api` 后用浏览器验收 `http://127.0.0.1:8796/`。
- 首屏仍是普通用户简易风格：
  - 标题为 `Rober 小车控制台`。
  - 5 个卡片齐全：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
  - `移动/导航` 卡片包含 `检查路径` 和 `停止`。
  - 首屏未出现 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`readback`、HIL checklist、速度/时长、四向点动、`保存地图`、`/cmd_vel` 或 `/api/base/manual`。
  - 高级诊断包含 `Nav2 规划详情` 和 `no Nav2 start/stop; no NavigateToPose; no /cmd_vel; no /api/base/manual`。
  - 浏览器 console `warn/error` 为空。
- 补充 artifact：`sprints/2026.06.11_01-35_pc_nav2_no_motion_planning_check/artifacts/browser_nav2_planning_acceptance.png`。
- `POST http://127.0.0.1:8796/api/robot-control/nav2/proof/refresh` 在缺少 `baseUrl` 时返回 `proxy_status=refresh_rejected`、`failure_reason=baseUrl_not_provided`，且 `remote_endpoint` 固定为 `/api/nav2/proof/refresh`。
- `rg -n "/api/robot-control/nav2/(start|stop)|robotControlNav2(Start|Stop)|nav2/start|nav2/stop" pc-tools/workstation/src pc-tools/workstation/test docs/product/pc_tools_workstation.md` 只命中文档中的禁用说明，没有新增 PC Nav2 start/stop 路由或 client。
- `git diff --check` 通过。
- `python3 -m json.tool` 校验 `nav2_proxy_real_upper_robot_192_168_1_11.json` 与 `nav2_ui_smoke_after_latest_fallback.json` 通过。
