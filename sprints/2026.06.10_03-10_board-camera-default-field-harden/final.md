# Board Camera Default Field Harden Final

- sprint_type: epic
- time: 2026-06-10 03:26 Asia/Shanghai
- owner: robot-software-engineer
- safe_to_control=false
- delivery_success=false
- visible_content_proven=false
- software_proof_only=true

## 复盘结论

本轮完成了“现场相机默认设备固化”的代码闭环：`bringup.launch.py` 与 `learn.launch.py` 在启用相机且未显式传 `camera_device` 时，默认使用当前真实上位机已验证的 `/dev/video1`，不再默认误绑 `/dev/video0` Cedrus decoder。

这提升的是现场采集入口稳定性，不代表画面已经可见、路线关键帧可用、Nav2 可运行或垃圾送达闭环完成。

## 实际交付

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`：`camera_device` 默认改为 `/dev/video1`。
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`：`camera_device` 默认改为 `/dev/video1`，并更新中文注释说明原因。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：新增默认设备防回退测试。
- `docs/vision/board_camera_publisher.md`：同步当前现场默认、覆盖方式和 `visible_content_proven=false` 边界。
- `sprints/2026.06.10_03-10_board-camera-default-field-harden/tech-done.md`：记录实现、验证、失败定位和风险。

## 验证结果

- launch contract 单测通过：`Ran 16 tests ... OK`。
- Docker/Humble 构建通过：`Summary: 6 packages finished [55.4s]`。
- 构建不稳定点复核通过：`Patrol.idl` 存在，PythonLibs 探测输出 `PythonLibs found.`。
- 真实上位机 SSH 可达，但远端仍是旧代码；不显式传 `camera_device` 的 smoke 失败于旧默认 `/dev/video0`，因此不能作为本轮新默认值的上车通过证据。

## OKR 回顾

`OKR.md` 当前最低完成度 Objective 是 O7，但第 5 节要求优先推进现场 O3 验证 lane。该选择在本轮仍成立：O7 的历史回放和标注需要真实 route/keyframe 输入，本轮减少后续真实采集的默认参数错误。

本轮不更新 OKR 百分比，不归档 KR。证据边界是 `software_proof_only=true`。

## 剩余风险

- 真实上位机尚未部署本轮代码；部署后必须复跑 no-motion camera smoke。
- `visible_content_proven=false` 仍未解决，后续需要 Hardware 现场检查镜头盖、遮挡、朝向、光照和 USB 摄像头本体。
- `/dev/video1` 是当前实板枚举事实，不是量产稳定命名方案；后续需要 udev 规则或设备探测机制。
- 本轮没有 HIL、运动控制、Nav2 实跑或送达任务证据。

## 下一步

部署本轮代码到 `root@192.168.1.11:37878` 后，优先运行不显式传 `camera_device` 的 no-motion smoke；若 `/camera/image_raw` 发布成功，再继续排查画面黑场，目标是为后续 `route.csv`、keyframe 和 replay JSONL 采集恢复可用视觉输入。
