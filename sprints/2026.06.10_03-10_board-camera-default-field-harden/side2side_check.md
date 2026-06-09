# Board Camera Default Field Harden Side-By-Side Check

- sprint_type: epic
- time: 2026-06-10 03:24 Asia/Shanghai
- checker: main-node acceptance
- safe_to_control=false
- delivery_success=false
- visible_content_proven=false
- deployed_field_smoke_proven=true
- default_camera_device_smoke_proven=true

## 对照目标

本轮 PRD 的目标不是证明画面可见或送达完成，而是把真实上位机已验证的 UVC camera `/dev/video1` 固化为 `bringup.launch.py` 与 `learn.launch.py` 的默认 `camera_device`，避免后续现场启用相机时继续误绑 `/dev/video0` Cedrus decoder。

## PRD 对照

| 功能点 | 验收结果 | 证据 |
| --- | --- | --- |
| FP1：bringup 默认相机设备固化 | 通过 | `bringup.launch.py` 中 `camera_device` 默认值为 `/dev/video1`，`camera_enabled` 仍默认 `false` |
| FP2：learn 默认相机设备固化 | 通过 | `learn.launch.py` 中 `camera_device` 默认值为 `/dev/video1`，相机节点仍受 `IfCondition(camera_enabled)` 控制 |
| FP3：验证口径和文档边界同步 | 通过 | `docs/vision/board_camera_publisher.md` 已写明 `/dev/video1` 是当前现场默认，`visible_content_proven=false` 仍成立 |
| FP4：contract 测试或最小静态验证 | 通过 | `python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过，Docker/Humble build 通过，真实上位机部署后 no-motion smoke 通过 |

## 验证对照

本轮实现后的关键验证结果：

```text
python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
Ran 16 tests in 0.025s
OK
```

```text
bash onboard/scripts/docker_humble_build.sh
Finished <<< ros2_trashbot_interfaces [44.9s]
Finished <<< ros2_trashbot_bringup [6.22s]
Summary: 6 packages finished [55.4s]
```

部署前，真实上位机 `/root/rober/onboard` 仍是旧默认 `/dev/video0`；不显式传
`camera_device` 的 no-motion smoke 失败，复现了本 sprint 要消除的现场风险：

```text
RuntimeError: Failed to open camera device /dev/video0; camera_publisher fails closed and will not fabricate frames
```

随后仅同步本轮两个 launch 文件到远端并最小重建 `ros2_trashbot_bringup`。部署后再次不显式传
`camera_device` 运行 no-motion smoke，通过：

```text
/camera/image_raw
Type: sensor_msgs/msg/Image
Publisher count: 1
image_message_observed=true
height=480
width=640
encoding=bgr8
step=1920
data_len=921600
camera_publisher streaming /dev/video1 to /camera/image_raw
```

## 边界核对

- 未发送 `/cmd_vel`，未启动底盘运动。
- 未修改 WAVE ROVER、ESP32、UART、速度映射或 feedback 代码。
- 未修改 Nav2、任务编排、手机端或云端。
- 未把 `ros_camera_topic_proven=true` 扩大解释为 `visible_content_proven=true`。
- 未更新 `OKR.md` 完成度；本轮只是 O3 现场验证 lane 的前置硬化。

## 结论

本轮软件侧验收和真实上位机部署后 no-motion smoke 均通过，可以提交。
剩余缺口不是默认设备链路，而是 `visible_content_proven=false`：画面仍近黑，需要继续排查镜头盖、遮挡、朝向、光照或 USB 摄像头本体。
