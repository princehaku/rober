# PC 自由移动和建图验收口径拆分

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `自动扫图准备` 新增 `建图验收` 行。
  - 当 `free_roam_autonomy_start_ready=true` 但 camera 无可见画面或 radar 不是 `雷达已运行` 时，明确显示“当前只按自由移动记录，不能按可验收建图收口”。
  - 当画面和雷达都 ready 时，显示“启动后本轮可按建图记录监看”。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 camera 首帧失败 + radar 状态源冲突的回归测试，确认不会触发 free-roam start、manual 或 `/cmd_vel`。
  - 更新 start-ready 成功路径，确认 camera/radar ready 时显示可按建图记录监看。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录“低速自由移动”和“可验收建图”是两层能力。

## 验证结果

- `npm test -- --testNamePattern "start-ready free-roam autonomy|splits free movement from mapping acceptance|starts free-roam autonomy after map recording"`：通过，3 passed。
- `npm test`：通过，2 test files / 259 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 该 sprint 只修 PC 首屏解释和验收口径，不改变上车端 free-roam 状态机、雷达驱动或摄像头首帧状态。
- 真实可建图仍需要现场同时证明画面可见和雷达已运行；当前现场 camera 首帧失败、雷达状态源冲突，因此只能按自由移动/诊断推进。
