# PC Camera Action Card Failure Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `action_status_cards[].evidence` 增加相机失败诊断字段：上游活跃、content-type、失败原因、远端 HTTP 状态和格式尝试摘要。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `camera_preview` action card 直接带出 `source_failure_reason`、`shared_preview_last_failure_reason`、`last_offer_format_attempts_summary` 等只读证据。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-action-status-card-camera_preview` DOM 暴露相机失败诊断 `data-*` 字段，并兼容旧 summary 缺 evidence 的情况。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 锁定前端 DOM 和后端 action card 证据。
- `docs/product/pc_tools_workstation.md`
  - 同步相机 WYSIWYG action card 合同。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-DZbtBIQV.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `git diff --check`：通过。
- 7001 重启：新监听进程为 `node` PID `96707`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `assets/index-DZbtBIQV.js` 和 `assets/index-1TFDR4Wy.css`；JS bundle 命中 `data-source-failure-reason` 与 `data-last-offer-format-attempts-summary`。
- live summary 检查：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 200；相机 action card evidence 显示 `source_failure_reason=first_frame_total_timeout`、`shared_preview_upstream_active=true`、`shared_preview_content_type_loaded=false`、`shared_preview_last_remote_http_status=502`，格式尝试为 `MJPG@640x480@30(/dev/video1)`、`MJPG@480x320@30(/dev/video1)`、`YUYV@320x240@25(/dev/video1)` 均无首帧。

## 剩余风险

- 本轮只补 PC 首屏相机失败诊断的只读结构化证据，不修复物理摄像头无首帧问题。
- 真实摄像头恢复仍需要现场检查 USB、摄像头输入、供电或换 known-good UVC 设备复测。
