# PC 自由移动停止文案 micro sprint

- sprint_type: micro
- owner: mainline-no-subagent
- scope: PC 普通首屏自由移动/自动扫图文案

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增本轮移动模式推导：根据 start 回包 `mapping_active_applied` 和当前建图 readiness 区分 `自由移动` / `自动扫图`。
  - 停止按钮、保存阻塞、下一步和扫图状态文案改为使用本轮模式，避免 camera 或 radar 不满足时仍提示“停止自动扫图”。
- `pc-tools/workstation/test/App.test.ts`
  - 自动扫图 ready 场景显式覆盖 `mapping_active_applied=true`。
  - camera 无首帧的自由移动场景显式覆盖 `mapping_active_applied=false`，并断言停止按钮、状态和下一步均显示 `自由移动`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录自由移动与自动扫图共用固定代理、但普通用户文案按本轮模式分开的设计口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --testNamePattern "free-roam autonomy|free-roam recording"`
  - `Test Files 2 passed (2)`
  - `Tests 15 passed | 245 skipped (260)`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 260 passed (260)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单个 chunk 超过 500 kB；这是既有打包体积警告，本轮未扩大处理范围。
- 通过：`git diff --check`

## 剩余风险

- 本轮只修 PC 普通用户文案，不改变上车端 free-roam 状态机、不新增运动出口。
- 真实相机仍需现场修 `/dev/video1` 首帧失败；真实雷达仍需现场确认 lifecycle running 与 fresh proof。
