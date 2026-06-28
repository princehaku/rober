# PC free-roam split motion and mapping next action

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 的 `readback_summary.free_roam` 新增：
  `motion_next_action_plain`、`mapping_next_action_plain`。
- free-roam 只读区块现在能直接把两层事实拆开：
  - 自由移动：勾安全确认后可先低速自由移动；相机和雷达只影响建图验收。
  - 建图验收：列出画面首帧、雷达新鲜、地图记录、地图画面等缺口，并说明不影响先低速自由移动。
- 前端 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "summary"`
  - `Test Files 1 passed (1)`
  - `Tests 44 passed | 114 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仅输出 chunk size warning，构建成功。
- 通过：7001 本地只读 summary 验证。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001 (LISTEN)`。
  - `curl -sS --max-time 22 http://127.0.0.1:7001/api/robot-control/summary` 显示
    `free_roam.status=start_ready`、`motion_start_ready=true`、`motion_ready=false`、
    `mapping_ready=false`、`mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`。
  - 只读 summary 输出 `motion_next_action_plain=当前处于停止请求；开始自由移动会先解除停止请求。勾选现场安全确认后可先自由移动；相机和雷达只影响建图验收。`
  - 只读 summary 输出 `mapping_next_action_plain=建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动。`
  - `safe_to_control=false`，`robot_control_executed=false`，确认本轮验证未执行真实控制动作。

## 剩余风险

- 本轮只补只读 summary 文案，不启动自由移动、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实自由移动或建图 HIL 验证。
