# 2026-06-27 12:41 camera no-frame not-exclusive diagnosis

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - `/health` 新增 `source_diagnosis`，把相机选源、首帧失败、占用状态和共享预览合同压成稳定结论。
  - 当 DV20/UVC 已选中、首帧失败且没有其它进程占用时，诊断为
    `uvc_no_frame_not_exclusive`，并明确 `not_exclusive=true`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 增加 health 诊断字段断言，锁住 `source_selected_not_probed` 和
    `uvc_no_frame_not_exclusive` 两条路径。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC summary 透出 `source_diagnosis_status/plain_hint/next_action/not_exclusive`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 summary 合同字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通用户首屏优先展示“不是页面独占，UVC 没有输出视频帧”的自然语言结论。
  - 高级诊断显示 source diagnosis 状态、提示、下一步动作和 not-exclusive 判断。
- `docs/vision/board_camera_publisher.md`
  - 同步记录当前相机结论和本轮诊断合同。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`
  - 通过，`Ran 23 tests in 15.302s`，`OK`。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`
  - 通过。
- `npm test`（`pc-tools/workstation`）
  - 通过，`2 passed (2)`，`287 passed (287)`。
- `npm run build`（`pc-tools/workstation`）
  - 通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`
  - 通过，无 whitespace error。
- 真实上位机部署：
  - 已把 `onboard/scripts/local_webrtc_camera_smoke.py` 部署到
    `root@192.168.1.11:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，
    并通过远端 `python3 -m py_compile`。
  - 8088 camera service 已重启，`0.0.0.0:8088` 监听进程为
    `python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py ...`。
  - `GET http://192.168.1.11:8088/health` 读回
    `status=source_first_frame_failed`、`source_usage.status=not_in_use`、
    `source_diagnosis.status=uvc_no_frame_not_exclusive`、
    `source_diagnosis.not_exclusive=true`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
    读回 `readback_summary.camera.source_diagnosis_status=uvc_no_frame_not_exclusive`、
    `source_diagnosis_not_exclusive=true`、`shared_preview_exclusive_camera_claim=false`。
- 关联只读状态复核：
  - 自由移动 `start_ready=true`，雷达相关 `lidar_fresh` 与 `obstacle_clear` gate 为
    `ready`；当前未启动原因是 `operator_confirmed` 现场安全确认未勾选，不是雷达阻塞。
  - Nav2 上次 `goal_execution_status=goal_succeeded`，但
    `goal_execution_base_feedback_lr_nonzero_proven=false`；
    读回显示下一次执行模式为 `next_execution_base_command_mode=ros`。

## 剩余风险

- 本轮只修正诊断与用户可理解性，不宣称摄像头真实画面已经恢复。
- 如果更换 known-good UVC 后仍无首帧，需要继续查 Orange Pi USB/供电/内核 UVC 链路。
- 本轮不执行任何底盘运动、Nav2 路线或自由移动验证。
- Nav2 “没法动”的剩余硬证据缺口是轮速 L/R 非零反馈；需要现场确认安全后执行下一次
  ROS 模式路线，才能闭环真实运动。
