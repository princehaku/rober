# PC 统一安全确认文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏的扫地式建图、移动/导航、行程操作，以及高级手控区共用的安全确认文案统一追加“勾一次，全页面生效”，避免 operator 误以为每个区块都要单独确认。
- `pc-tools/workstation/test/App.test.ts`：在既有“trip、keyboard、free-roam mapping 复用同一个普通安全确认”的测试里补充文案断言，继续覆盖勾选不会自动触发 manual、stop、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录 2026-06-27 17:01 起普通 PC 界面的最小安全确认文案口径。

## 验证结果

- `npm test -- --run test/App.test.ts -t "reuses one plain safety confirmation"`：通过，1 个用例通过，169 个用例按 filter 跳过。
- `npm test -- --run`：通过，2 个测试文件、298 个用例全部通过。
- `npm run build`：通过，产物为 `dist/assets/index-Br5SB-PE.js` 和 `dist/assets/index-DkzBjvNI.css`；Vite 仍提示主 chunk 超过 500 kB，这是既有体积告警。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `curl -s http://127.0.0.1:7001/`：确认当前 7001 页面引用新构建产物 `assets/index-Br5SB-PE.js`，`lsof` 显示 Node 监听 `*:7001`。

## 剩余风险

- 本轮只改前端文案和测试，不触发真实小车运动，也不修复上位机摄像头 UVC 无首帧、Nav2 真实执行反馈为 0 或雷达 proof stale 的硬件/运行态问题。
