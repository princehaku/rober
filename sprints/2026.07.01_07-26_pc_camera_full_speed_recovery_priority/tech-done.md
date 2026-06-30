# PC Camera Full-Speed Recovery Priority

- sprint_type: micro
- owner: Codex mainline (subagent disabled per CEO instruction)
- time: 2026-07-01 07:26 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 调整相机恢复建议优先级：当 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive` 且 `source_diagnosis_not_exclusive=true` 时，`live_wysiwyg_camera_recovery_next_action_plain` 和 `mapping_unblock_camera_recovery_next_action_plain` 优先显示 USB 12M full-speed 的具体处理建议，而不是落入泛化“不独占后检查 USB/换 UVC”文案。
  - 保留“相机不是页面独占”的普通用户提示，并去掉 full-speed action 末尾重复的“共享预览不是页面独占”。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 在 full-speed USB 相机诊断单测中增加 recovery 字段断言，防止普通首屏和建图解锁路径再次丢失 full-speed 具体动作。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC summary / mapping unblock 的 full-speed 恢复合同，并明确该路径只读、不启动建图、不发车。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 6 passed (6)`。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示单 chunk 超过 500 kB，这是既有前端体积提示，不影响本轮功能。
- `npm test`
  - 通过：`Test Files 3 passed (3)`，`Tests 415 passed (415)`。
- `git diff --check`
  - 通过。
- PC 服务重启验证
  - 已重启 `npm run api`，监听 `http://0.0.0.0:7001`，PID `32840`。
- 现场只读 summary 验证
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `200`。
  - `camera_diagnosis_status=uvc_full_speed_usb_not_exclusive`，`camera_diagnosis_not_exclusive=true`。
  - `live_wysiwyg_camera_recovery_next_action_plain` 与 `mapping_unblock_camera_recovery_next_action_plain` 均为“相机不是页面独占；诊断显示 USB full-speed；先复测相机首帧并读取共享预览状态。若仍无画面，摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测。”
  - `live_wysiwyg_camera_recovery_sends_motion=false`，`mapping_unblock_camera_recovery_sends_motion=false`。

## 剩余风险

- 本轮只修 PC 普通用户恢复建议优先级；没有执行相机首帧 probe、MJPEG 状态刷新、建图启动、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实摄像头仍处于 `USB 12M full-speed` 且首帧失败状态，需要现场更换高速 USB 口/线或带供电 USB Hub 后复测。
- 工作区仍保留两份历史 artifact 未提交改动，本轮未触碰、未纳入提交。
