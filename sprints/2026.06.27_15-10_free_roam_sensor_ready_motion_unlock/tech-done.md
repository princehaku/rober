# 2026.06.27 15:10 Free-Roam Sensor Ready Motion Unlock

sprint_type: micro

## 实际改动

- 上车端 `POST /api/free-roam/autonomy/start` 改为先检查相机 health ready 与雷达 lifecycle running + 最新 scan proof fresh。
- 只有相机和雷达都 ready 时，start 才写 `motion_hil_unlocked=true` 与 `enable_cmd_vel_publish=true`，让 `free_roam_autonomy_node` 可按自身 `/scan`、`/map` 和 watchdog 决策发布 `/cmd_vel`。
- 任一传感器未 ready 时，start 返回 `blocked_sensor_readiness`，不写任何 free-roam ROS 参数。
- stop 固定写回 `enable_cmd_vel_publish=false`、`motion_hil_unlocked=false`，再请求状态机停止；stop 不要求相机或雷达 ready。
- PC 代理合同新增 `motion_unlock_requested` 与 `sensor_readiness` 摘要，不再硬编码“本次不会设置运动解锁”。
- PC 普通首屏自动扫图按钮新增 camera readiness 门禁；键盘连续手控仍不依赖雷达。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，46 tests。
- `npm run build`：通过。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 真机部署：已上传 `upper_robot_api.py` 到 `root@192.168.1.11:37878`，远端 `python3 -m py_compile` 通过，并重启 8787，PID `115623`。
- 真机 `/api/status`：camera `status=ready`、`video_source=/dev/video1`；radar `lifecycle_state=stopped`、`latest_scan_proof_fresh=false`。
- PC 代理 `POST http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/start?baseUrl=http://192.168.1.11:8787`：
  返回 HTTP 400、`proxy_status=autonomy_rejected`、`failure_reason=free_roam_motion_sensors_not_ready`、`blocked_reasons=["radar_not_ready"]`、`motion_unlock_requested=false`、`command_result.executed=false`。
- 上车直连 `POST /api/free-roam/autonomy/start`：
  返回 `status=blocked_sensor_readiness`、`blocked_reasons=["radar_not_ready"]`、`command_result.executed=false`，证明雷达未 ready 时不会写运动解锁参数。

## 剩余风险

- 当前真机雷达 lifecycle 仍显示 stopped / latest scan proof stale，因此真实 `start` 预期会被 `blocked_sensor_readiness` 拦住，不会解锁发车。
- 本轮验证会继续做真机 smoke；若雷达未 ready，只能证明“未 ready 不解锁”的安全路径，不能证明真实自由移动。
- Vendor 依据已复核 `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 控制仍以 JSON/UTF-8/newline 与项目侧 `/dev/ttyS5`、115200 的现有上车配置为边界；本轮没有改串口、波特率或底盘 JSON 协议。
