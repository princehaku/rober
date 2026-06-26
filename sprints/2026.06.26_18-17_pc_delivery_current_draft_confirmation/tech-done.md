# PC delivery current draft confirmation

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通用户送达收口新增 `currentRunDeliveryMaterialReady` 判定。
  - 当最新 Nav2 行程已成功、送达草稿中的 route/map ref 与本轮 Nav2 evidence ref 对齐、且视频/画面 ref 已恢复时，首页明确提示“本轮行程和送达材料已在，只差现场逐项确认；最终确认不会发车”。
  - 送达材料卡改为提示草稿已和本轮行程对齐，最终确认卡改为提示按顺序勾现场确认，不再让用户误以为还要重新准备材料或重新发车。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 matching latest draft + fresh Nav2 的普通首页测试，确认 UI 直接引导现场确认。
  - 测试确认在点击最终确认前不会调用 operator report、delivery complete、manual 或 `/cmd_vel`。
  - 同步更新旧草稿保存后的文案断言。

## 验证结果

- `npm test -- --run test/App.test.ts -t "latest draft material"` 通过：1 passed。
- `npm test` 通过：2 files, 227 tests passed。
- `npm run build` 通过；Vite 仍有单 chunk 大于 500 kB 的既有提示。
- 只读现场 API 核对：
  - `http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`，`safe_to_control=false`，`delivery_success=false`。
  - `/api/robot-control/nav2/goal/execution/latest?baseUrl=http://192.168.1.11:8787` 返回 `status=goal_succeeded`，`evidence_ref=o11-nav2-goal-execution-1782099547218`，`feedback_sample_count=8`，`robot_control_executed=true`。
  - `/api/robot-control/delivery/latest?baseUrl=http://192.168.1.11:8787` 返回 `delivery_success=false`，草稿材料 ref 已有，`route_map_ref=o11-nav2-goal-execution-1782099547218`，缺口仍是现场确认报告、观察到移动、观察到停止、确认已投放/送达、最后点击确认送达。
  - 本轮只读核对未调用发车、手控、delivery complete 或 operator report 写入接口。

## 剩余风险

- `delivery_success` 仍未完成，必须由现场人员观察到达/停止/投放后显式勾选并点击“确认送达（不发车）”。
- 当前底盘只读 T1001 仍显示 wheel L/R 为 `0/0`，非零轮速证明还没完成。
- summary 中雷达最近 proof 显示 stale while lifecycle running；自动扫图仍是 `artifact_only=true` 且 `cmd_vel_publish_enabled=false`，未做无人值守真实移动验证。
- 本轮没有触发真实运动，自动驾驶“为何不动”的硬件/运行时根因仍需下一轮继续定位。
