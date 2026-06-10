# PC Map Lifecycle Controls

## sprint_type

micro

## 实现前设计

- Owner：`full-stack-software-engineer`。
- 目标：把 PC Robot Control 的地图卡片从 proof refresh 推进到固定 map lifecycle endpoint 代理，但继续保持首页普通用户简易风格。
- 固定代理：
  - `GET /api/robot-control/map/list?baseUrl=...` 只转发上位机 `GET /api/map/list`。
  - `POST /api/robot-control/map/save?baseUrl=...` 只转发上位机 `POST /api/map/save`。
  - `POST /api/robot-control/map/start?baseUrl=...` 只转发上位机 `POST /api/map/start`，UI 默认放入高级诊断且禁用，真实 smoke 不执行。
  - `POST /api/robot-control/map/reset?baseUrl=...` 只转发上位机 `POST /api/map/reset`，UI 默认放入高级诊断且禁用，真实 smoke 不执行。
- 请求体白名单：仅允许短 `map_name`、`artifact_path` 字段；不实现通用 body 透传，不开放任意 endpoint。
- 响应边界：PC 合同继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`；上位机响应中如出现危险 true 字段，代理 fail closed 并写入 blocked reasons。
- 首页约束：地图卡片最多新增“地图列表”和“保存地图”，start/reset 不进入普通用户首屏可点操作。
- 高级诊断：展示最近 map lifecycle action、HTTP 状态、map_count、command_result mode/executed、failure_reason、blocked reasons。
- 验证边界：真实上位机 smoke 只允许 `map/list` 和 guarded `map/save`；本轮不执行真实 `map/start`，不触碰底盘运动，不发送 `/cmd_vel` 或 `/api/base/manual`。

## 实际改动

- 时间：2026-06-11 01:11:02 CST。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlMapLifecycle*` 请求/响应合同。
  - 固定响应字段包含 `action`、`remote_endpoint`、`remote_method`、`remote_http_status`、`map_count`、`map_names`、`command_result`、`blocked_reasons`、`hard_dangerous_true_fields`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `buildMapLifecycleProxy()`。
  - 只支持 `list/start/save/reset` 四个固定 action。
  - `GET list` 不发送 body；`POST start/save/reset` 只允许短 `map_name`、`artifact_path`。
  - 未知字段、非 object、超长或不安全字符会本机拒绝。
  - 复用 Robot API baseUrl 围栏和危险 true 字段扫描；`command_result.executed=true` 会在 PC 响应中标记 blocked。
- `pc-tools/workstation/src/server/index.ts`
  - 新增：
    - `GET /api/robot-control/map/list?baseUrl=...`
    - `POST /api/robot-control/map/start?baseUrl=...`
    - `POST /api/robot-control/map/save?baseUrl=...`
    - `POST /api/robot-control/map/reset?baseUrl=...`
  - 没有新增任意 endpoint 代理。
- `pc-tools/workstation/src/server/catalog.ts`
  - 导出 map lifecycle proxy helper。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 map lifecycle client 封装。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图卡片保持普通用户简易风格，只新增“地图列表”“保存地图”两个首屏按钮。
  - `start/reset` 只在高级诊断中以 disabled 的“受控/高级”按钮展示。
  - 高级诊断展示最近 lifecycle action、HTTP、map_count、map names、command_result mode/executed/ok、request body、failure 和 blocked reasons。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 UI fixture 和断言：首屏不出现 Start/Reset，可触发 map list/save 固定代理，高级诊断显示 lifecycle 字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加后端代理测试：固定 endpoint、body 白名单、未知字段拒绝、start/reset 路由存在、危险 true 和 executed command fail-closed。
- `docs/product/pc_tools_workstation.md`
  - 同步 Map Lifecycle Controls V1 产品和接口边界。
- `sprints/2026.06.11_01-05_pc_map_lifecycle_controls/artifacts/`
  - `real_map_list_smoke.json`
  - `real_map_save_guarded_smoke.json`

## 验证结果

主节点复核时间：2026-06-11 01:12:48 CST。复核重点是固定代理边界、真实 smoke 是否只执行 `map/list` 与 guarded `map/save`、首页是否保持普通用户简易风格。

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - 关键输出：`✓ built in 921ms`。
  - 主节点复跑通过，关键输出：`✓ built in 1.43s`。
- `cd pc-tools/workstation && npm run test`
  - 通过。
  - 关键输出：`Test Files  2 passed (2)`，`Tests  71 passed (71)`。
  - 主节点复跑通过，关键输出：`Test Files  2 passed (2)`，`Tests  71 passed (71)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
  - 关键输出：`eslint .` 无报错。
  - 主节点复跑通过，无 error/warning。
- `git diff --check`
  - 通过，无输出。
  - 主节点复跑通过，无 whitespace error。
- JSON artifact 校验：
  - `python3 -m json.tool sprints/2026.06.11_01-05_pc_map_lifecycle_controls/artifacts/real_map_list_smoke.json` 通过。
  - `python3 -m json.tool sprints/2026.06.11_01-05_pc_map_lifecycle_controls/artifacts/real_map_save_guarded_smoke.json` 通过。
  - 主节点复核两个 artifact 均可解析。
  - `real_map_list_smoke.json`：`action=list`、`remote_endpoint=/api/map/list`、`remote_method=GET`、`remote_http_status=200`、`map_count=2`、`map_names=["trashbot_map.yaml","trashbot_map.pgm"]`、`command_result.mode=read_only_local_files`、`command_result.executed=false`、安全字段全为 false。
  - `real_map_save_guarded_smoke.json`：`action=save`、`remote_endpoint=/api/map/save`、`remote_method=POST`、`remote_http_status=200`、`command_result.mode=dry_run_stub`、`command_result.executed=false`、`failure_reason=command_not_configured`、安全字段全为 false。
- 本地 workstation API smoke：
  - 启动 `PORT=8791 npm run api`。
  - 使用本地假上位机 `http://127.0.0.1:8792`。
  - `GET /api/robot-control/map/list?baseUrl=http://127.0.0.1:8792` 返回 `proxy_status=lifecycle_forwarded`、`remote_endpoint=/api/map/list`、`map_count=1`、`robot_control_executed=false`。
  - `POST /api/robot-control/map/save?...` 带未知字段返回 `proxy_status=lifecycle_rejected`、`failure_reason=request_body_unknown_fields:ignored`，未转发给假上位机。
  - `POST /api/robot-control/map/save?...` 带白名单 body 返回 `proxy_status=lifecycle_forwarded`、`request_body.map_name=local_test`、`request_body.artifact_path=maps/local_test.yaml`、`robot_control_executed=false`。
- 真实上位机 smoke：
  - 目标：`http://192.168.1.11:8787`。
  - 只执行允许的 `map/list` 与 guarded `map/save`。
  - 未执行真实 `map/start`。
  - 未发送 `/cmd_vel`。
  - 未发送 `/api/base/manual`。
  - `map/list` 结果：`proxy_status=lifecycle_forwarded`、`remote_http_status=200`、`map_count=2`、`map_names=["trashbot_map.yaml","trashbot_map.pgm"]`、`command_result.mode=read_only_local_files`、`command_result.executed=false`。
  - `map/save` 结果：`proxy_status=lifecycle_forwarded`、`remote_http_status=200`、`command_result.mode=dry_run_stub`、`command_result.executed=false`、`failure_reason=command_not_configured`、`robot_control_executed=false`。

## 浏览器验收

- 主节点使用 `PORT=8793 npm run api` 打开 `http://127.0.0.1:8793/`。
- 默认首页仍是 `Rober 小车控制台` / `机器人` 页。
- 第一屏仍是五块简易卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- 地图卡片首屏包含 `刷新地图`、`地图列表`、`保存地图`，不包含 `Start` / `Reset` / `开始建图` / `重置` 可点击入口。
- 浏览器 console warning/error 为空。
- 截图 artifact：[`/Users/m1/apps/rober/sprints/2026.06.11_01-05_pc_map_lifecycle_controls/artifacts/browser_map_lifecycle_first_screen.png`](</Users/m1/apps/rober/sprints/2026.06.11_01-05_pc_map_lifecycle_controls/artifacts/browser_map_lifecycle_first_screen.png>)。

## 剩余风险

- `map/save` 当前真实 smoke 是 software guard / dry-run stub，不代表真实地图保存命令已经配置或产物已刷新。
- `map/start`、`map/reset` 后端固定代理已实现并有本地 mock 测试，但本轮真实 smoke 明确未执行。
- PC 首页仍保持简洁；高级诊断包含工程字段，普通用户默认需要展开才能看到。
- 本轮没有改 onboard，也没有触碰 WAVE ROVER、UART、底盘运动、launch 或硬件配置。
