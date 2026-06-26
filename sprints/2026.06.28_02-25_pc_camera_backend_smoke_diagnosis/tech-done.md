# PC 相机主动后端矩阵诊断

## Sprint 类型

sprint_type: micro

## 实际改动

- PC 端 `/api/robot-control/camera/first-frame/probe` 增加 `backendSmoke=1/true` 只读诊断开关；默认仍保持快速首帧探针，只有用户主动检查画面时才请求上位机执行 v4l2/ffmpeg 后端矩阵。
- 普通用户界面的“检查画面（只读）/记录当前画面”会带 `backendSmoke=1`，用于现场确认摄像头失败是否来自页面独占、浏览器播放，还是底层 UVC 无帧。
- 普通界面新增 `backend_no_frame_observed` 人话提示：摄像头能打开，但 v4l2/ffmpeg 底层也没有取到视频帧；优先检查 USB、摄像头输入、格式或供电。
- 回归测试覆盖默认不跑后端矩阵、显式后端矩阵透传、普通首屏失败提示和不发送运动命令。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_camera_probe_parses_subprocess_json_without_control_enable`
- 已通过：`npm test -- --testNamePattern "camera first-frame probe|read-only WYSIWYG|current camera probe failure|not exclusive access"`
- 已通过：`npm test`
- 已通过：`npm run lint`
- 已通过：`npm run build`
- 已通过：`git diff --check`

## 剩余风险

- 真实板端 `/dev/video1` 仍可能继续无首帧；本轮只把“非独占 + 底层无帧”的证据做成 PC 可见诊断，不宣称修复摄像头硬件/驱动输出。
- `backendSmoke=1` 会短时间打开摄像头并运行 v4l2/ffmpeg；已限制为用户主动检查触发，不放入轮询路径。
