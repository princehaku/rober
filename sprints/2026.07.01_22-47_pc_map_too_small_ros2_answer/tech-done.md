# PC 地图太小与 ROS2 配套答案

## sprint_type

micro

## 设计口径

- 普通用户解决“地图太小”不切到 RViz2，默认使用 PC 内置 `/map` 大地图；该入口只保留地图画布、缩放和只读刷新。
- ROS2 配套按用途分层：本地工程调试用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web；二者不替代 PC 简易界面。
- 本轮只允许 no-motion 显示和只读合同变更，不启动 ROS2/RViz2/Foxglove/Nav2，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `live_closure_summary` 和 summary 顶层新增：
    - `map_display_too_small_next_action_plain`
    - `map_display_ros2_companion_answer_plain`
    - `map_display_operator_default_surface=pc_big_map_direct_view`
    - `map_display_companion_replaces_pc_ui=false`
  - `map_display_companion_plain` 追加“地图太小先进入 `/map`”和“RViz2/Foxglove 只是工程观察”的明确答案。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步新增上述 API 合同字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图卡、标题 proof、`/map` 入口、地图说明、当前卡点摘要和 ROS2 折叠说明同步暴露同一组 DOM 字段。
  - 首屏文案保持普通用户口径，工程命令仍收在默认关闭的“工程观察：RViz2 / Foxglove”里。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 DOM 和文案断言，确认 `/map` 是普通入口，RViz2/Foxglove 不替代 PC UI。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加 summary 顶层和 `live_closure_summary` 字段一致性断言。
- `pc-tools/README.md`
  - 同步记录本轮只读显示合同和 no-motion 边界。

## 验证结果

- 已通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - `Test Files 2 passed`
  - `Tests 245 passed`
- 已通过：`npm run build`
  - `tsc -p tsconfig.app.json`
  - `vite build`
  - `tsc -p tsconfig.server.json`
  - Vite 仍提示已有大 chunk warning，本轮未新增拆包工作。
- 已通过：`git diff --check`
- 已通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node ... TCP *:7001 (LISTEN)`
- 已通过：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 只读回查
  - `map_display_primary_url=/map`
  - `map_display_too_small_next_action_plain=地图太小先点“进入地图大屏”打开 /map...`
  - `map_display_ros2_companion_answer_plain=ROS2 配套：本地工程调试用 RViz2...Foxglove bridge...`
  - `map_display_operator_default_surface=pc_big_map_direct_view`
  - `map_display_companion_replaces_pc_ui=false`
  - `map_display_starts_ros2=false`
  - `map_display_starts_nav2=false`
  - `map_display_sends_motion_when_clicked=false`

## 剩余风险

- 未执行任何需要现场安全确认的运动命令，因此 wheel raw L/R 非零、delivery success、键盘连续手控和自由移动实车验收仍需 CEO 现场确认后再跑。
