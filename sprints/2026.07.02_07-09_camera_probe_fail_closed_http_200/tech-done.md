# sprint_type: micro

## 实际改动

- PC 相机首帧复测代理 `POST /api/robot-control/camera/first-frame/probe` 对上车 503、首帧 timeout 和 PC fetch timeout 改为 HTTP 200 fail-closed JSON。
- 保留 body 内 `proxy_status=probe_failed`、`remote_http_status`、`failure_reason`、硬件恢复提示和所有 no-motion flags，避免 `curl -fsS` 隐藏诊断。
- 更新 `catalog.test.ts`、`docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- --run catalog.test.ts robotControlSummary.test.ts App.test.ts`，3 个测试文件、428 个用例通过。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：重启 PC Node 后输出 `pc-tools workstation API listening on http://0.0.0.0:7001`，`lsof` 确认 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS -X POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe` 成功返回 HTTP `200 OK`，body 为 `proxy_status=probe_failed`、`remote_http_status=503`、`failure_reason=deadline_expired`、`readback_only=true`、`camera_probe_readback_only=true`、所有运动/控制 flags 为 false，且继续提示 `camera_usb_speed=12M`、`camera_hardware_action_label=换高速USB后复测`。

## 剩余风险

- 本轮只修复画面 WYSIWYG 失败诊断的 PC HTTP 层可读性；真实相机首帧仍需要按当前诊断更换高速 USB 口/线后复测。
