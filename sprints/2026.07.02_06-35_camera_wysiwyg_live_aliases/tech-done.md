# Camera WYSIWYG Live Aliases

## sprint_type

micro

## 目标

- 修复 `GET /api/robot-control/summary` 顶层相机 WYSIWYG live 字段为 `null` 的问题。
- 让现场脚本不用解析 `live_closure_summary`，即可确认相机不是页面独占、USB full-speed 恢复动作和 no-motion 复测链路。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 顶层透出 `live_wysiwyg_camera_source_diagnosis_*`。
  - 顶层透出 `live_wysiwyg_camera_recovery_*`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 summary 顶层相机 WYSIWYG live alias 类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加顶层 alias 与 `live_closure_summary` 同源断言。
  - 增加 USB full-speed 相机场景的顶层 alias 断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录顶层相机 WYSIWYG live alias 合同。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 通过：`Test Files 3 passed (3)`、`Tests 428 passed (428)`。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示既有 bundle 大小 warning。
- 重启 PC Node：
  - 通过；`node` 监听 `*:7001`。
- 只读 smoke：
  - `GET /api/robot-control/summary` 顶层返回 `live_wysiwyg_camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`。
  - 顶层返回 `live_wysiwyg_camera_recovery_sequence=/api/robot-control/camera/first-frame/probe,/api/robot-control/camera/mjpeg/status,/api/robot-control/summary`。
  - `source_nested_same=true`、`recovery_nested_same=true`、`sequence_nested_same=true`。

## 剩余风险

- 本轮只补 summary 顶层相机 WYSIWYG live alias，不改变相机硬件状态；真实画面仍需要现场按提示把摄像头换到高速 USB 口/线或带供电 Hub 后复测。
- 仓库未安装 Playwright，未做真实浏览器 smoke；普通首屏 DOM 由本轮通过的 `App.test.ts` 覆盖。
