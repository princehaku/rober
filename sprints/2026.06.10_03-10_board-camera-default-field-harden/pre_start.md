# Board Camera Default Field Harden Pre-Start

- sprint_type: epic
- owner: product-okr-owner
- implementation_owner: robot-software-engineer
- time: 2026-06-10 03:10 Asia/Shanghai
- motion_commands_allowed=false
- safe_to_control=false
- delivery_success=false
- target_objective: O3 field validation lane, serving O7/O6 downstream evidence

## 用户价值和产品北极星

北极星仍是让普通手机用户最终能把垃圾交给小车，小车沿固定路线完成可复盘的送达任务。本轮不追求视觉识别、导航成功或送达完成，而是把真实上位机已证明的相机设备路径固化进 ROS2 学习/bringup 主链路，避免后续现场采集再次误绑 Orange Pi 的 Cedrus decoder。

用户价值是降低现场采集失败率：后续 Robot Software Engineer 或现场操作员启动 `learn.launch.py` / `bringup.launch.py` 时，默认相机应指向已验证的 `/dev/video1`，让 `map.yaml`、`route.csv`、keyframe、rosbag/replay JSONL 的采集链路少一个人为参数坑。

## 上轮证据入口

本轮设计采用以下证据，不新增硬件猜测：

- `sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/tech-done.md`
- `docs/vision/board_camera_publisher.md`
- `OKR.md`
- `AGENTS.md`

已确认事实：

- 真实上位机 `/dev/video1` 可以经 `camera_publisher` 发布到 ROS2 `/camera/image_raw`。
- `/camera/image_raw` subscriber 收到 `640x480 bgr8`，`data_len=921600`。
- `ros_camera_topic_proven=true`。
- `visible_content_proven=false`，不能宣称可用视觉路线内容。
- `learn.launch.py` 与 `bringup.launch.py` 默认 `camera_device=/dev/video0`，存在误绑 Cedrus decoder 风险。

## 方向判断

方向：继续。

理由：

- `OKR.md` 当前最高优先级明确要求现场 O3 验证 lane 产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。
- 上轮已经把 `/dev/video1 -> /camera/image_raw` topic 通路打通，但默认 launch 仍要求人工显式覆盖，容易让下一轮真实采集回退到错误设备。
- 本轮只设计默认设备和验收口径固化，不把黑场问题包装成视觉可用，也不提高 `safe_to_control` 或 `delivery_success`。

## 本轮核心抓手

把现场相机默认设备从“文档提醒”推进到“ROS2 bringup/learn 主链路默认行为”，并配套验收口径：

- `bringup.launch.py` 默认 `camera_device:=/dev/video1`。
- `learn.launch.py` 默认 `camera_device:=/dev/video1`。
- 相关文档同步说明 `/dev/video1` 是当前实板真实 UVC camera，`/dev/video0` 是 Cedrus decoder 失败样例。
- 验收仅证明 launch 默认、ROS graph/topic smoke 和文档边界，不证明可见内容、视觉定位、Nav2-ready 或送达完成。

## 范围边界

本阶段只做产品/验收设计，不写产品代码。

后续实现阶段建议由 `robot-software-engineer` 单 owner 闭环，因为文件范围集中在 ROS2 launch、bringup contract 测试和视觉文档；不需要并行拆给多个 Engineer。

不进入范围：

- 不修改底盘串口、WAVE ROVER、ESP32、UART、速度映射、feedback 协议。
- 不修改相机驱动策略，不引入自动枚举或设备探测。
- 不宣称 `visible_content_proven=true`。
- 不启动运动命令，不发送 `/cmd_vel`。
- 不更新 `OKR.md` 完成度。

## 风险和阻塞

- `/dev/video1` 是当前实板事实，不保证所有未来批次设备枚举完全一致；后续量产需要设备稳定命名或 udev 规则，但本轮不扩大范围。
- 画面仍接近黑场，可能是镜头盖、遮挡、朝向、光照或 USB 摄像头本体问题；本轮不解决视觉内容质量。
- 默认改为 `/dev/video1` 会让没有该设备的本地开发环境在启用相机时 fail closed，这是符合现场优先策略的预期行为。
- 后续实现必须补 `tech-done.md`，并把验证结果写清楚，不能只改 launch。

