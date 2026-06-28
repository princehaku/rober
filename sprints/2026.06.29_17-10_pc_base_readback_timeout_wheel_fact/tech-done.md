# 2026.06.29 17:10 PC 底盘读回超时轮速事实

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当 Robot Control summary 主体仍可读，但 `base_status` 或 `base_feedback_samples_latest` 只读端点超时时，普通首屏 `当前事实` 新增轮速分项提示：“当前底盘反馈读取超时；旧 L/R 不能当当前轮速结论”。
  - 该提示只消费 summary 的只读连接状态，不调用 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 live 形态回归：Nav2/地图可读、底盘只读端点超时时，首屏显示轮速读回超时且不泄露 `fetch_timeout_2400ms`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录 PC 普通首屏对底盘只读超时的分项展示口径。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- -t "partial timeout|base readback timeout|current base feedback read errors|wheel readback"`
  - 结果：1 个测试文件通过，10 个相关用例通过。
- 已通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，369 个用例通过。
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。

## 剩余风险

- 本轮只修 PC 只读展示；未获得本轮现场安全确认，因此未发送真实底盘试动、键盘手控、Nav2 执行、free-roam、stop 或 `/cmd_vel`。
- 当前真实上位机底盘只读端点偶发超时，仍需现场继续排查串口占用、底盘供电、ESP32 模式和反馈链路。
