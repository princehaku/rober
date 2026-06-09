# WAVE ROVER Feedback Smoke 结果

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实结论

1. `root@192.168.1.11:37878` 可访问，目标串口为 `/dev/ttyS5`，波特率 `115200`。
2. 停止 `upper_robot_api.py` 后，直接对 `/dev/ttyS5` 发送 vendor feedback 命令：
   - `{"T":143,"cmd":0}`
   - `{"T":142,"cmd":100}`
   - `{"T":131,"cmd":1}`
   - `{"T":130}`
3. raw UART 在 10 秒窗口内连续返回 `T=1001`，字段稳定包含：
   - `L`
   - `R`
   - `r`
   - `p`
   - `v`
   - `y`
4. `y` 字段本轮返回值是字符串 `"null"`，不是数值 yaw。这与 vendor 固件字段名一致，但当前实机值未形成可用角度数据。
5. raw 层证明下位机 feedback 是活的，问题不在 UART 不通。
6. 启动 `ros2 run ros2_trashbot_hardware esp32_bridge` 后：
   - `/odom` 有样本；
   - `/battery` 无样本；
   - `/imu/data` 无样本。
7. 结束后已恢复 `upper_robot_api.py`，`/api/base/status` 可访问，但仍显示 `feedback_ack.t1001_observed=false`；第二次恢复后 `feedback_samples_latest` 还变为 `missing`。

## 失败定位

- 失败不在底盘 raw feedback 层。
- 失败更接近 ROS2 bridge / parser / publisher 链：
  1. bridge 进程能连上 `/dev/ttyS5`；
  2. 但 10 秒窗口内没有把 `T=1001` 发布成 `/battery` 或 `/imu/data`；
  3. `/odom` 仍然是 ROS 侧积分输出，不依赖实测 `T=1001`。
- `upper_robot_api.py` 恢复后仍未把本轮 fresh `T=1001` 反映到 `/api/base/status`，说明 API 自己的 readback/artifact 刷新链也需要单独排查。

## 工件

- `artifacts/raw_feedback_probe.log`
- `artifacts/esp32_bridge_feedback.log`
- `artifacts/battery_once.txt`
- `artifacts/imu_once.txt`
- `artifacts/odom_once.txt`
