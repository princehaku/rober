# sprint_type: micro

## 实际改动

- PC 普通首屏“轮速记录”接入 `/api/robot-control/base/feedback-samples` 顶层只读 alias：
  - `wheel_raw_left`
  - `wheel_raw_right`
  - `wheel_feedback_plain_hint`
  - `wheel_feedback_next_action`
- 普通用户摘要优先展示后端统一生成的 `wheel_feedback_plain_hint`，让现场直接看到“只读反馈采样读到 wheel raw L/R=0/0”或“没有读到可用 wheel raw L/R”，并明确这不是运动命令。
- 普通用户下一步提示接入 `wheel_feedback_next_action`，在只读采样后直接给出“勾安全确认后低速试动/键盘复验”或“先确认底盘反馈链路”的动作。
- 高级诊断 `base feedback raw L/R` 改为优先显示顶层 `wheel_raw_left/right`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_source` 和 `wheel_feedback_plain_hint`，旧响应仍回退到 `sample_key_values`。
- 本轮只改 PC 前端解释层和对应测试；没有触发 manual、keyboard、Nav2、free-roam、cmd_vel 或 delivery complete。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "raw wheel L/R from base feedback samples|current wheel L/R and frame count"`：通过，2 passed。
- `npm --prefix pc-tools/workstation test`：通过，367 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- 只读 live `POST http://127.0.0.1:7001/api/robot-control/base/feedback-samples?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，返回 `wheel_raw_left=not_observed`、`wheel_raw_right=not_observed`、`wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_source=vendor_t1001_L_R`、`wheel_feedback_plain_hint=只读反馈采样没有读到可用 wheel raw L/R；这不是运动命令。`、`wheel_feedback_next_action=先确认上位机底盘反馈链路，再勾安全确认做低速试动。`，并确认 `sends_motion_commands=false`、`robot_control_executed=false`。
- 只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，返回 base 当前 `wheel_raw_left=0`、`wheel_raw_right=0`、`wheel_feedback_lr_nonzero_proven=false`、`latest_feedback_status=fresh`；camera 为 `source_first_frame_failed` 且 `source_diagnosis_status=uvc_no_frame_not_exclusive`、`shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本轮只解决 PC 端“只读 wheel raw L/R 看不懂”的易用性问题；没有现场安全确认，所以没有执行低速试动、键盘连续控制、Nav2 执行或自由移动。
- live 当前相机问题不是独占结论，摘要显示 `uvc_no_frame_not_exclusive`，更像 UVC 源没有产出首帧；需要现场检查摄像头输入、电源、线缆或换已知可用 UVC。
- live 只读底盘反馈采样仍可能在 `0/0` 与 `not_observed` 间波动；小车能否真正自己动，仍需要在安全确认后做低速试动或键盘连续控制验证。
