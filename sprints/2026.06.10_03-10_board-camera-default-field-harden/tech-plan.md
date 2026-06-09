# Board Camera Default Field Harden Tech Plan

## 执行结论

本轮产品设计完成后，进入实现阶段时应派 `robot-software-engineer` 单线闭环。不要并行拆分，因为改动集中在 ROS2 bringup/learn launch 默认值、launch contract 测试和视觉文档。

本计划不要求当前 Product Owner 修改产品代码。后续 Engineer 实现前必须遵守本文件的文件范围、接口影响和验收命令。

## 文件范围

Product Owner 本轮已允许改动：

- `sprints/2026.06.10_03-10_board-camera-default-field-harden/pre_start.md`
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/prd.md`
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/tech-plan.md`

后续 `robot-software-engineer` 实现建议允许改动：

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/` 下聚焦 launch contract 的测试文件
- `docs/vision/board_camera_publisher.md`
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/tech-done.md`

后续实现不得改动：

- 底盘串口、WAVE ROVER、ESP32、UART、速度映射、feedback 协议文件
- Nav2 行为逻辑、任务编排、手机端、云端
- `OKR.md`
- 与本默认固化无关的格式化或重构

## 技术方案

1. 将 `bringup.launch.py` 的 `camera_device` launch argument 默认值改为 `/dev/video1`。
2. 将 `learn.launch.py` 的 `camera_device` launch argument 默认值改为 `/dev/video1`。
3. 保持 `camera_enabled` 语义不变：默认是否启动相机由既有参数控制，不能因为默认设备变化而强制启动相机。
4. 保持 topic、frame、width、height、fps 参数语义不变。
5. 更新或新增 launch contract 测试，防止 `camera_device` 默认值回退到 `/dev/video0`。
6. 更新 `docs/vision/board_camera_publisher.md`：说明当前现场默认已固化为 `/dev/video1`，但 `visible_content_proven=false` 仍成立。
7. 完成后更新 `tech-done.md`，写清验证证据、失败定位和剩余风险。

## 接口影响

- ROS topic 接口不变：默认仍是 `/camera/image_raw`，消息类型仍是 `sensor_msgs/msg/Image`。
- Launch 参数名不变：`camera_device`、`camera_topic`、`camera_frame_id`、`camera_width`、`camera_height`、`camera_fps` 均保持兼容。
- 行为影响：启用相机但未显式传 `camera_device` 时，默认使用 `/dev/video1`。
- 本地开发影响：没有 `/dev/video1` 的环境在 `camera_enabled:=true` 时会 fail closed，这是预期；开发者可显式覆盖为本地设备。
- 安全影响：不涉及运动控制，不改变 `/cmd_vel`、底盘串口或 stop 语义。

## 验收命令

Product Owner 本轮只读核对命令：

```bash
sed -n '1,220p' OKR.md
sed -n '1,220p' sprints/2026.06.10_03-00_ros-camera-topic-path-diagnostic/tech-done.md
sed -n '1,160p' docs/vision/board_camera_publisher.md
```

后续 `robot-software-engineer` 实现后至少运行：

```bash
rg "camera_device|/dev/video[01]" onboard/src/ros2_trashbot_bringup/launch docs/vision/board_camera_publisher.md
bash onboard/scripts/docker_humble_build.sh
```

如果真实上位机可用，补充 no-motion smoke：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  camera_enabled:=true \
  camera_width:=640 \
  camera_height:=480 \
  camera_fps:=2.0
```

随后采样：

```bash
ros2 topic info /camera/image_raw
ros2 topic echo --once /camera/image_raw
```

真实上位机 smoke 的通过口径：

- `/camera/image_raw` 出现在 ROS graph。
- `topic info` 类型为 `sensor_msgs/msg/Image`，publisher count 至少为 `1`。
- `topic echo --once` 能看到 `height=480`、`width=640`、`encoding=bgr8` 或等价完整图像元数据。
- 不发送 `/cmd_vel`，不启动底盘运动。

如果真实上位机不可用：

- 不能阻塞 launch 默认固化。
- `tech-done.md` 必须写明 `software_proof_only=true` 和缺少实板复验的风险。

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节中完成度最低的当前 Objective 是：

- O7：PC 端运营调试平台，约 12%。

但 `OKR.md` 第 5 节把“现场 O3 验证 lane（归档 Objective 临时激活）”列为当前最高优先级，因为 CEO 已提供真实上位机 SSH，必须优先产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。

本 sprint 不直接实现 O7 UI。理由是：O7 当前最缺真实路线材料输入，本 sprint 固化 `/dev/video1` 默认能降低后续 keyframe/route/replay 采集失败率，属于 O7 可消费证据链的前置现场硬化。O6 作为次低 Objective 也会间接受益于更稳定的 evidence artifact 输入，但不是本 sprint 的直接交付对象。

方向判断：继续。不得把本轮产物包装成 O7/O6 功能完成，只能作为真实素材入口稳定性的前置证据。

## 风险和回滚策略

- 风险：不同设备批次的 UVC camera 枚举可能不是 `/dev/video1`。
  - 处理：保留 `camera_device` 参数可覆盖；后续量产另开 udev 稳定命名任务。
- 风险：默认改为 `/dev/video1` 后，部分本地开发机没有该设备。
  - 处理：相机节点 fail closed；开发者显式传本地设备，不改变 CI 默认不启相机策略。
- 风险：画面仍不可见。
  - 处理：不在本 sprint 验收中要求 `visible_content_proven=true`；下一轮由现场硬件/视觉排查镜头盖、遮挡、朝向、光照和 USB 摄像头本体。
- 回滚：如果真实上位机证明 `/dev/video1` 不再是 UVC capture，应先补证据并调整文档/默认值；不要无证据回退到 `/dev/video0`。

## 输出要求

后续 `robot-software-engineer` 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果或关键日志片段。
3. 失败定位，如有。
4. 剩余风险。
5. `tech-done.md` 中明确 `visible_content_proven`、`safe_to_control`、`delivery_success` 的边界。
