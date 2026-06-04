# Final: O9 Fresh Scan Proof Runtime

## sprint_type

sprint_type: epic

## 收口结论

本 sprint 没有拿到 O9 所需的完整 fresh `/scan` runtime material。可以记录的真实进展是：O9 blocker 被进一步收窄，Robot Software 形成了 API-managed LiDAR-only runtime hook，本地 unittest/compileall/diff-check 通过，并已部署到 upper；live 8787 refresh/latest 从全缺失推进到 `partially_observed`。

最终 live 结果仍是 `evidence_type=blocked_with_root_cause`：`scan_once=true`、`raw_packet=true`，但 `scan_hz=false`、`tf=false`、`all_required=false`。因此本轮不更新 `OKR.md` 百分比。没有完整远端 fresh proof，就不能把 API hook、HTTP 200、local tests、LiDAR-only smoke 或 PC readback 包装成 O9/O3/O7 完成。

## OKR 判定

| Objective | 本轮判定 | 原因 |
| --- | --- | --- |
| O9：短周期真实材料破局战役 | 不涨分 | live refresh 仅 `partially_observed`；`scan_hz` 和 TF 缺失，`robot_runtime_material` 未成立。 |
| O3：建图、定位、Nav2 与固定路线 | 不涨分 | 未证明完整 `/scan` proof、SLAM `/map`、AMCL、Nav2 消费或固定路线。 |
| O7：PC 运营调试平台 | 不涨分 | 未证明 PC/operator 触发 live runtime refresh 并读回 fresh artifact。 |
| O8：Epic 交付节奏与证据治理 | 可记录过程证据，不改百分比 | 两个 Robot Software worker 超时/中断或未闭环，暴露 owner 验收链路问题。 |

## evidence_type

- `software_guard`：本地 API-managed runtime hook diff、本地测试/diff-check 通过、接口文档边界更新。
- `blocked_with_root_cause`：live refresh/latest 已取证但仅 partial，缺 `scan_hz` 和 TF。
- 未达到 `robot_runtime_material`：没有 live latest artifact 证明 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、collector log、fresh timestamp 和 `safe_to_control=false`。

## 实际改动归档

- 已有 Robot Software 本地 diff：`onboard/scripts/upper_robot_api.py`、`onboard/scripts/test_upper_robot_api.py`、`docs/interfaces/lidar_ros2_closed_loop.md`。
- 已同步 upper：`/root/rober/onboard/scripts/upper_robot_api.py`，并配置 `/etc/systemd/system/trashbot-upper-robot-api.service.d/20-lidar-scan-proof-runtime.conf`。
- Product/OKR 本轮收口更新：`tech-done.md` 延续记录、`side2side_check.md`、`final.md`。
- 未改 `OKR.md` 百分比。

## 剩余 blocker

- Robot Software 需要把下一轮任务拆成两段：先单独证明 `scan_hz=true`，再单独证明 `base_link -> laser_frame` TF。
- 如果 `scan_hz=false` 继续出现，需要区分是 LiDAR driver 生命周期太短、`ros2 topic hz` timeout 采样窗口不足、collector 解析问题，还是 ROS graph 里 topic 发布不连续。
- 如果 `tf=false` 继续出现，需要区分是 static transform 未随 runtime 启动、frame id 不匹配，还是 `tf2_echo` 超时窗口不足。

## CEO 决策

当前不需要 CEO 改产品方向；需要 Robot Software 继续攻坚 `scan_hz=false` 和 TF 缺失。若下一轮仍无法把 partial proof 推到 all_required，则需要 CEO 决策：继续攻坚远端 LiDAR runtime、暂停 O9 fresh scan proof、或切换到不依赖该 blocker 的 Objective。

## 最终风险

- 本轮 Product 收口没有运行测试；测试、diff-check 和远端取证状态来自 Robot Software worker 报告。
- 本轮没有真实底盘运动、没有 HIL、没有 `/cmd_vel`、没有 `/api/base/manual`。
- 本轮没有证明 SLAM/Nav2/固定路线/PC operator runtime 成功。
