# PC Live Closure WYSIWYG Refresh Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-summary` 新增当前所见缺口 DOM 合同：ready、missing surface ids、needs refresh 和固定刷新按钮 test id。
  - 在 `needs_wysiwyg` 卡点内新增 `plain-live-closure-wysiwyg-refresh`，复用已有 no-motion 当前所见刷新链路。
  - 按钮固定声明只刷新 radar scan proof、camera first-frame probe、map preview、radar status 和 camera MJPEG status；不启动 radar lifecycle、map runtime、Nav2、manual、keyboard 或 free-roam。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live closure 卡内 WYSIWYG refresh 的 DOM 合同和请求边界。
  - 覆盖 wheel rerun 卡点下不显示该 WYSIWYG refresh 按钮，避免把可视化缺口误作为轮速复验预检 blocker。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步当前卡点的一键只读 WYSIWYG 复测入口。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|keeps live closure wheel rerun as a focus-only Nav2 action"`：通过，2 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、398 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-CCRRMIEl.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：旧 `node` PID `7831` 已停止，新监听进程为 `node` PID `21307`，地址 `TCP *:7001`。
- 只读 smoke：`GET http://127.0.0.1:7001/` 已引用新 bundle；bundle 内命中 `plain-live-closure-wysiwyg-refresh`、缺口 surface id、camera probe、radar scan proof refresh 和 no-motion 边界字段；`GET /api/robot-control/summary` 返回当前 `live_status=needs_wysiwyg`、camera/map/radar 均 false，本轮未发送任何 motion POST。

## 剩余风险

- 本轮只改 PC Web 显示和只读 DOM 合同；没有执行真实相机 probe / radar scan proof refresh 的 live POST smoke。
- 当前 live 现场仍是 `needs_wysiwyg`，说明真实画面、地图或雷达贴图还需要现场继续刷新/排查。
