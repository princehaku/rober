# PC 全局键盘连续手控

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 保留 `启用键盘` 作为显式安全窗口，但启用后允许全页面 W/A/S/D 和方向键进入连续手控。
  - 输入框、文本域、下拉框和 contenteditable 内的按键仍被忽略，避免填表时误发车。
  - 焦点离开键盘面板去看地图/雷达/画面不会自动退出；进入可编辑控件、窗口失焦或页面隐藏仍退出/停止。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展键盘连续手控测试：启用前全局按键不发车，启用后全局按住触发重复 manual pulse，输入框内按键不触发 manual。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏全局键盘手控口径和安全边界。

## 验证结果

- 通过：`npm test -- -t "keeps non-stop motion disabled|lacks the bounded pulse contract|enables non-stop motion"`（3 passed，169 skipped）
- 通过：`npm run lint`
- 通过：`npm test`（172 passed）
- 通过：`npm run build`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`（`node` 监听 `*:7001`，未使用 Clash 端口）

## 剩余风险

- 本轮验证仍是 PC/mock 层；没有触发真实小车 HIL、真实连续手控或真实 `/cmd_vel`。
- 真实上车连续手控仍依赖 operator 现场安全确认、固定 `base/manual` 代理、松开 stop 转发和真实底盘反馈。
