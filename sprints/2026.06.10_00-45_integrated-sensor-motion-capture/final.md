# Integrated Sensor Motion Capture Final

## 本轮结论

本轮在真实上位机 `root@192.168.1.11:37878` 完成了 integrated sensor + motion capture：

- 雷达：同轮成功。
- 摄像头：同轮成功。
- map：同轮保存成功。
- motion：同轮成功。
- stop：同轮成功。
- route / keyframe：同轮成功。
- API：结束后已恢复成功。

唯一未补齐的是底盘 feedback 新鲜样本：`/battery`、`/imu/data` 未拿到，恢复后的 `/api/base/status` 仍显示 `feedback_ack.t1001_observed=false`。

## 对 OKR 最低优先级核对回顾

`tech-plan.md` 中“不直接开发 O7，而先补真实 route/map/keyframe/motion 素材包”的理由在本轮仍然成立。

本轮新增的真实素材包包括：

- `/scan` 样本
- `/camera/image_raw` 样本
- `/odom` 前后对比样本
- `route.csv`
- `manifest.json`
- `keyframes/001..010`
- `trashbot_integrated_sensor_motion_map.yaml/.pgm`

这些都能直接服务 O7 的地图历史回放、标注、手控与寻路界面联调。

## 阻塞与风险

### 未闭环项

1. `/battery` 样本为空。
2. `/imu/data` 样本为空。
3. `/api/base/status` 可恢复访问，但其新鲜 feedback 仍未证明来自本轮 `T=130/T=131` 请求。

### 证据边界

- `no_motion_static_odom_tf:=true` 仅为 smoke-only TF 拓扑，不代表动态 TF 正确。
- `/odom` 仍是 ROS-side command integration，不是实测编码器里程计。
- 本轮不能据此宣称 Nav2-ready 或导航级 SLAM 标定完成。

### 执行风险

- 本轮远端 capture 脚本需要手工 cleanup 才完全恢复 API，说明脚本收尾逻辑仍需修正。
- `ros2 run ros2_trashbot_hardware esp32_bridge --ros-args --help` 目前会抛 `UnknownROSArgsError`，不影响本轮联跑，但影响可维护性和诊断体验。

## 下一步建议

1. 下一轮优先补 `T=130/T=131` feedback 新鲜样本闭环，明确 bridge 是否发布 `/battery`、`/imu/data`。
2. 将本轮 artifact 脚本的 cleanup 改成确定性收尾，避免 orphan 进程再次占用 `/dev/ttyS5`、`/dev/ttyACM0`、`/dev/video1`。
3. 如需提升到导航级证据，必须补动态 `odom -> base_link` TF、真实轮速/编码器来源与运动中 SLAM 质量验证。
