# PC 自动扫图启动后监看刷新

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `refreshRadarProof` 增加 `focusAfterReady=false` 调用模式，允许后台只读刷新雷达 proof 时不抢走当前操作焦点。
  - 普通首屏 `自动扫图` start 成功后，先刷新 console，再只读刷新一次雷达 proof，最后刷新地图 preview。
  - 该链路只更新地图/雷达所见即所得反馈，不发送 base manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图固定代理用例，验证 start 后额外调用一次 radar proof refresh 和一次 map preview。
  - 同一用例继续验证不会调用 manual、`/cmd_vel` 或 Nav2 execute。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录自动扫图 start 成功后的只读雷达/地图监看刷新。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC workstation 边界，并明确不修改 Clash 或系统代理配置。

## 验证结果

- `npm test -- -t "free-roam autonomy"`：通过，2 files / 3 passed / 173 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- `npm test`：通过，2 files / 176 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node 90259 ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮不触发真实 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 这不是长期后台轮询；它只保证自动扫图 start 成功后立刻拉一次雷达和地图新证据。持续周期刷新仍可作为后续优化，但需要谨慎控制资源和测试 timer。
