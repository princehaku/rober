# 2026.06.29 17:30 PC 底盘读回格式异常轮速事实

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将普通首屏 `当前事实` 的底盘读回问题从单一“读取超时”拆成三类：读取超时、返回格式异常、读取失败。
  - 当 `base_status:response_json_parse_failed` 或类似 bad JSON 只读问题出现时，显示“当前底盘反馈返回格式异常；旧 L/R 不能当当前轮速结论”，避免误说成超时。
- `pc-tools/workstation/test/App.test.ts`
  - 增加底盘只读 JSON 解析失败回归，断言首屏显示格式异常、不泄露 `response_json_parse_failed`，也不调用 manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录底盘只读端点超时、格式异常、读取失败的普通首屏展示口径。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- -t "base readback|current base feedback read errors|partial timeout|wheel readback"`
  - 结果：1 个测试文件通过，12 个相关用例通过。
- 已通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，370 个用例通过。
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。

## 剩余风险

- 本轮只修 PC 只读展示；未获得本轮现场安全确认，因此没有发送真实底盘试动、键盘手控、Nav2 执行、free-roam、stop 或 `/cmd_vel`。
- 真实底盘反馈返回格式异常仍需继续排查上位机 `/api/base/status` 输出、串口日志和 ESP32 feedback 链路。
