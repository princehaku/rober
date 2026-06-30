# PC Keyboard Continuous Proof Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainKeyboardContinuousProofSummary`，把 PC 键盘连续控制验收压成一行普通用户可读事实。
  - 普通键盘卡新增 `data-testid="plain-keyboard-continuous-proof"`，结构化暴露同一次按住窗口、连续 pulse 阈值、当前/最佳连续次数、松开后 stop 收口、轮速 L/R 和固定 manual/stop endpoint。
- `pc-tools/workstation/src/styles.css`
  - 新增 `.plain-keyboard-continuous-proof` 状态样式，用于区分待确认、等待按住、按住中和已验证。
- `pc-tools/workstation/test/App.test.ts`
  - 补默认、等待按住、按住 1 次、同一次按住 2 次、松开后已验证的 DOM 和文案断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏连续手控验收条和只读安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "keyboard"`：通过，21 个键盘相关测试通过。
- `npm test -- --run`：通过，2 个测试文件、391 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BeMIu-8b.js` 与 `dist/assets/index-Ch2TQH3P.css`。
- `git diff --check`：通过。
- 7001 重启：新监听进程为 `node` PID `54621`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `index-BeMIu-8b.js` 和 `index-Ch2TQH3P.css`；JS 资源命中 `plain-keyboard-continuous-proof`、`连续手控验收`、`必须同一次按住窗口`、`data-same-hold-window-required`、`data-stop-required-after-hold`，CSS 资源命中 `.plain-keyboard-continuous-proof`。

## 剩余风险

- 本轮只补 PC Web 显示和只读 DOM 合同，不自动启用键盘，不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 未做真车 HIL；真实连续手控仍需现场按住键盘并观察轮速/停止收口。
