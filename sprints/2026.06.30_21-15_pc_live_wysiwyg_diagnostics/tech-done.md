# PC Live WYSIWYG Diagnostics

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `live_closure_summary` 中新增相机、雷达、地图雷达的所见即所得诊断字段。
  - 普通文案把底层原因映射为中文，例如读取首帧超时、雷达频率未确认、地图缺雷达点；原始原因数组继续保留给 API/DOM 自动化。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏当前卡点下新增 `plain-live-closure-wysiwyg-diagnostics`，显示当前画面/雷达/地图雷达的只读诊断。
  - 暴露 `data-camera-probe-failure-reason`、`data-radar-scan-missing-observations`、`data-map-radar-blocked-reasons` 和 `data-sends-motion-when-clicked=false`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 `RobotControlLiveClosureSummary` 类型。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加普通文案不暴露底层字段、API/DOM 保留原始诊断字段的回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 PC 大地图/RViz2/Foxglove 口径，以及本轮 live WYSIWYG 诊断合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，3 tests。
- `npm test -- App.test.ts`：通过，225 tests。
- `npm test -- --run`：通过，402 tests。
- `npm run lint`：通过，保留既有 4 个 Vue multiline warning，无 error。
- `npm run build`：通过，Vite 仍提示单包超过 500 kB 的既有 chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮没有发送任何 live motion/control POST，也没有启动 ROS2/RViz2/Foxglove。
- 真实相机仍返回首帧超时，雷达贴图仍需上车端提供当前点位/定位后才能完成所见即所得验收。
- PC 地图已经有大图和地图大屏入口；工程调试建议用 RViz2，远程浏览器共享观察建议后续接 Foxglove bridge。
