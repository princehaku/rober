# Tech Done

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 `current_camera_wysiwyg_pack_missing_evidence` 与 `current_camera_wysiwyg_pack_missing_evidence_labels`。
- 当画面 WYSIWYG 未出首帧时，字段固定返回 `["camera_first_frame"]` / `["画面首帧"]`；画面可见时返回空数组。
- 普通首屏 `plain-current-camera-wysiwyg-pack` DOM 同步暴露 `data-missing-evidence` 和 `data-missing-evidence-labels`，与 summary、mapping pack 的缺口 id 对齐。
- 更新产品文档和 API/DOM 回归测试。该改动只补读回 alias，不启动相机独占采集、Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- test/App.test.ts -t "focuses field acceptance WYSIWYG refresh on camera only when radar and map are already visible"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过，无空白错误。
- 已重启 PC 服务到 `0.0.0.0:7001`，进程 PID `81080`。
- Live 只读复验：`GET /api/robot-control/summary` 返回 `current_camera_wysiwyg_pack_status=needs_first_frame`、`current_camera_wysiwyg_pack_missing_evidence=["camera_first_frame"]`、`current_camera_wysiwyg_pack_missing_evidence_labels=["画面首帧"]`、`current_camera_wysiwyg_pack_blocks_mapping_start=true`、`current_camera_wysiwyg_pack_blocks_free_move=false`。

## 剩余风险

- 相机真实首帧仍未恢复，当前 live 原因仍是 `first_frame_total_timeout`，USB speed 为 `12M`；需要现场换高速 USB 口/线或带供电 USB Hub 后复测。
- 本轮未发送任何运动指令；完整 Nav2、键盘连续控制、自由移动和 delivery success 仍需要现场安全确认后的 HIL 证据。
