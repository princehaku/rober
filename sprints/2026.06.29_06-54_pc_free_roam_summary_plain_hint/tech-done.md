# Free-roam summary plain hint

- sprint_type: micro
- 时间：2026-06-29 06:54 CST
- Owner：User Touchpoint Full-Stack Engineer（主会话执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.free_roam` 新增 `plain_hint`，把能否先自由移动、建图验收缺口和下一步合成一条只读事实。
  - fail-closed summary 也补齐同名字段，避免读取失败时字段缺失。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 `RobotControlSummaryResponse.readback_summary.free_roam` 类型。
- `pc-tools/workstation/test/App.test.ts`
  - 同步默认 summary fixture 的 free-roam `plain_hint`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖未连接、可先自由移动但建图缺口、建图 ready、自由移动运行中但建图缺口四类 readback。
- `docs/product/pc_tools_workstation.md`
  - 记录 summary free-roam `plain_hint` 的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - 结果：1 个测试文件通过，38 个用例通过，122 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`
  - 结果：1 个测试文件通过，1 个用例通过，214 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 Vite chunk size warning。
- 首轮全量失败后修正两个精确断言，再通过：`npm --prefix pc-tools/workstation test`
  - 初始失败原因：两个 catalog 精确断言未包含新增 `plain_hint` 或期望的下一步来源不准确。
  - 修正后结果：2 个测试文件通过，375 个用例通过。
- 通过：重启 PC API 到 `0.0.0.0:7001`，实际监听 PID `16180`。
  - 只读 `GET /api/robot-control/summary` 结果：`readback_summary.free_roam.status=start_ready`、`start_ready=true`、`mapping_ready=false`、`mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`，`plain_hint` 明确“可先自由移动”和“建图验收还差画面首帧、雷达新鲜、地图记录、地图画面”。

## 剩余风险

- 本轮只补 summary 只读字段，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop。
- live 建图仍缺画面首帧、雷达新鲜、地图记录和地图画面；低速自由移动仍需要现场安全确认后由 operator 显式启动。
