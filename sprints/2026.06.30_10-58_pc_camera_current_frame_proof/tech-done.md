# PC Camera Current Frame Proof Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏实时画面卡新增 `plain-camera-current-frame-proof` 当前出帧验收条。
  - 该验收条只读取本页 MJPEG `<img>` / 浏览器 video 是否已经绘出帧、共享预览是否单上游、是否存在浏览器独占说法和固定 MJPEG/status endpoint。
  - 文案明确区分“共享流已有最近帧但本页未确认显示”和“本页已显示 MJPEG/video 实时帧”。
- `pc-tools/workstation/src/styles.css`
  - 为当前出帧验收条补齐等待、接入中、待打开和本页已显示状态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认首屏、MJPEG load 和 video loadeddata 三种状态下的 DOM 字段。
  - 确认该验收条固定 `data-sends-motion-when-clicked=false`，不泄漏 `/cmd_vel` 文案。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明这只是 PC 当前页面显示验收，不新建相机 reader、不触发 camera offer 或任何运动接口。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- test/App.test.ts -t "camera"`：通过，35 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、391 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-l4-4ZcO7.js` 与 `dist/assets/index-prhEZqNH.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧监听进程，新监听进程为 `node` PID `85316`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `index-l4-4ZcO7.js` 和 `index-prhEZqNH.css`，资源内命中 `plain-camera-current-frame-proof`、`画面验收`、`本页已显示 MJPEG 实时帧`、`data-current-frame-visible`、`data-shared-preview-single-upstream` 等新合同。

## 剩余风险

- 本轮只改 PC Web 当前页面显示验收和只读 DOM 合同，不打开真实相机、不执行 camera offer、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未做真实上车摄像头 HIL 出帧验证；真实画面能否显示仍取决于上车相机源、MJPEG relay 和网络状态。
