# Board Camera Default Field Harden PRD

## 产品目标

把真实上位机相机设备路径固化为 ROS2 学习和 bringup 主链路默认值，减少现场采集时的人工参数依赖，服务后续真实 keyframe、route、rosbag 和 replay JSONL 采集。

本 PRD 的成功不是“画面可用”或“送达完成”，而是“后续现场启动默认不会误绑 `/dev/video0` Cedrus decoder”。

## 用户价值

面向现场执行者：

- 启动 `learn.launch.py` 或 `bringup.launch.py` 时，默认相机路径贴合当前实板事实。
- 少记一个 `camera_device:=/dev/video1` 覆盖参数，降低现场烟测和采集命令出错概率。
- 一旦相机仍不可见，可以把问题聚焦到镜头盖、遮挡、光照、朝向或摄像头本体，而不是先排查错误设备。

面向后续产品链路：

- O3 可继续推进真实路线素材采集。
- O7 可消费更稳定的 keyframe/route/replay 输入。
- O6 可消费更稳定的 evidence artifact，而不是反复归档误绑失败。

## OKR 映射和方向判断

- 主要映射：归档 O3 现场验证 lane 临时激活。
- 间接服务：O7 历史路线回放和数据标注，O6 事件/evidence 存档。
- 不提升：O1 底盘协议、O5 云中转控制面。

方向判断：继续。

当前 `OKR.md` 明确把现场 O3 验证 lane 排为最高优先级。上轮已证明 ROS2 camera topic path，但默认 launch 仍留有误绑风险；因此本轮应补齐默认和验收口径，而不是继续做只读 handoff 或状态面板。

## 功能点

### FP1：bringup 默认相机设备固化

`bringup.launch.py` 的 `camera_device` 默认值应从 `/dev/video0` 调整为 `/dev/video1`。

验收口径：

- `ros2 launch ros2_trashbot_bringup bringup.launch.py --show-args` 能看到 `camera_device` 默认 `/dev/video1`。
- `camera_enabled:=false` 时不强制打开相机。
- `camera_enabled:=true` 且现场存在 `/dev/video1` 时，仍发布 `/camera/image_raw`。

### FP2：learn 默认相机设备固化

`learn.launch.py` 的 `camera_device` 默认值应从 `/dev/video0` 调整为 `/dev/video1`。

验收口径：

- `ros2 launch ros2_trashbot_bringup learn.launch.py --show-args` 能看到 `camera_device` 默认 `/dev/video1`。
- 学习链路的 camera topic 默认仍是 `/camera/image_raw`。
- 不改变 SLAM、route recorder、waypoint 或底盘运动默认策略。

### FP3：验证口径和文档边界同步

`docs/vision/board_camera_publisher.md` 应同步说明新默认值和证据边界。

验收口径：

- 文档明确 `/dev/video1` 是当前实板 UVC camera 默认。
- 文档明确 `/dev/video0` 是 Cedrus decoder，不应作为当前实板现场采样设备假设。
- 文档保留 `visible_content_proven=false`，不把默认设备固化误写成视觉内容可用。

### FP4：contract 测试或最小静态验证

后续实现需要用自动化或静态验证防止默认值回退。

验收口径：

- 能用现有 bringup launch contract 测试覆盖默认参数，或新增聚焦测试。
- Docker/Humble `colcon build --symlink-install` 通过。
- 若无法上车复验，必须在 `tech-done.md` 明确说明缺少实板 smoke 的影响和剩余风险。

## 非目标

- 不解决黑场或低亮度问题。
- 不新增自动设备探测、udev 规则或相机健康评分。
- 不修改 `camera_publisher.py` 的节点级默认值，除非 Engineer 判断 launch 默认无法覆盖主链路风险。
- 不改底盘、LiDAR、Nav2、任务编排、手机端或云端。
- 不宣称 `safe_to_control=true`、`primary_actions_enabled=true`、`delivery_success=true`。

## 优先级和验收口径

优先级：P0 field hardening。

进入实现的 gate：

- 功能点仅限 FP1-FP4。
- 后续 Engineer 必须先读本 PRD 和 `tech-plan.md`，不得扩大到视觉内容修复。

完成验收：

- launch 默认值和文档边界完成。
- 相关 contract/构建验证通过。
- `tech-done.md` 写清实际改动、命令输出、失败定位和剩余风险。
- 若有真实上位机可用，优先补 no-motion camera smoke；若不可用，不阻塞软件默认固化，但必须标为 `software_proof_only`。

## 责任 Engineer

- 主责：`robot-software-engineer`
- 只读咨询：必要时可让 `rober-hardware-engineer` 确认设备枚举证据，但本轮已有上一轮 sprint 证据，默认不需要并行启动。
- 不涉及：`full-stack-software-engineer`、`robot-algorithm-engineer`

## 证据链缺口

- 尚未证明可见环境内容，`visible_content_proven=false`。
- 尚未证明默认改动后的真实上位机 launch smoke。
- 尚未证明后续 keyframe 可用于路线识别或远程可视确认。
- 尚未形成量产级稳定设备命名方案。

## 已完成 KR 历史记录

本轮不归档新的 KR，也不更新 `OKR.md`。历史进度仍以 `docs/process/okr_progress_log.md` 和既有 sprint final/tech-done 为准。

