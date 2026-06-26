# PC radar gate obstacle WYSIWYG label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当雷达 proof 仍待刷新、但自动扫图门禁读到最近障碍距离时，地图雷达口径明确说明这是“自动扫图门禁读到的最近障碍”，不是已贴到地图的实时雷达点。
  - 保持原有坐标口径：机器人地图位置未读到时，近障碍只按局部距离显示，不贴到地图。
- `pc-tools/workstation/test/App.test.ts`
  - 更新雷达待刷新 + 最近障碍距离场景的普通地图断言，防止以后再次把门禁距离说成实时地图雷达点。

## 验证结果

- `npm test -- --run test/App.test.ts -t "radar marker|radar refresh|radar points|radar status"` 通过：5 passed。
- `npm test` 通过：2 files, 229 tests passed。
- `npm run build` 通过；Vite 仍有单 chunk 大于 500 kB 的既有提示。
- 只读现场验证：
  - PC Node `http://127.0.0.1:7001/api/health` 正常。
  - 当前 summary 显示相机 ready，地图记录已启动，机器人地图位置仍未读到。
  - 雷达 lifecycle running，但 `latest_scan_proof_fresh=false`；自动扫图门禁读到 `最近障碍 0.04m`，正是本轮文案覆盖的 live 形状。

## 剩余风险

- 这次只修正普通界面的雷达口径，没有刷新雷达 proof 或触发真实运动。
- 当前雷达近障碍 0.04m 是真实现场风险信号；即使自动扫图允许低速降级，现场也必须保持接管。
- 机器人 map-frame pose 仍为 null；雷达点和小车位置无法贴到真实地图坐标。
- wheel raw 仍未证明非零，自动移动的硬件履约仍需下一轮继续验证。
