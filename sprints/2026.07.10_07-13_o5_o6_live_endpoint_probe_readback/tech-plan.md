# O5/O6 Live Endpoint Probe Readback Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：O5（约 84%）与 O6（约 84%）并列最低。
2. 本 sprint 针对该最低 Objective：是，主攻 O5 live endpoint / external probe evidence 进入 O6 same-task readback。
3. 选择理由：O5 继续提升不能再依赖 local shadow/smoke；O6 也需要真实或准真实外部材料消费入口。本轮在缺真实资源时只补 fail-closed readback 契约，不越界宣称生产成功。

## 技术方案

Robot Software 在既有 `remote_cloud_relay.py`、`o5_same_task_mission_archive_smoke.py` 和 O6 archive/readback 测试基础上小范围扩展：

- 复用现有 `cloud_external_probe` / `cloud_db_queue_external_probe` artifact 生成与 summary 逻辑。
- 在 O5 same-task smoke 中增加可选 probe artifact 输入或生成路径，把 probe 摘要纳入 same-task summary。
- 必要时把 probe 摘要作为 O6 field evidence 的 additive section 安全回读，字段必须 phone-safe。
- 保持 false safety fields，不允许 probe pass 推导 `delivery_success` 或 `safe_to_control`。

## 文件范围

Robot Software 可改：

- `onboard/scripts/o5_same_task_mission_archive_smoke.py`
- `onboard/tests/test_o5_same_task_mission_archive_smoke.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/artifacts/robot_software_worker_report.md`

Product Owner 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/tech-done.md`
- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/side2side_check.md`
- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md`
- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/artifacts/product_worker_report.md`

## 接口影响

- 只允许 additive fields / additive summary，不破坏既有 command/result/reconciliation、same-task mission gate 或 O6 consumer readback。
- 外部 probe artifact 不得包含真实 URL、token、DB/queue endpoint、raw response body、local path 或 traceback。
- 若 probe artifact 缺失或无真实 endpoint，状态必须 blocked/warning，并写明 next required evidence。

## 验收命令

Robot Software 必须运行：

```bash
python3 -m py_compile onboard/scripts/o5_same_task_mission_archive_smoke.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.tests.test_o5_same_task_mission_archive_smoke
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check
```

Product Owner 必须运行或核对：

```bash
test -f sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/tech-done.md
test -f sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/side2side_check.md
test -f sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md
rg -n "live_endpoint_probe|cloud_external_probe|same_task|software_proof" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback
git diff --check
```

## 风险边界

- 本轮不证明真实 production cloud、production DB/queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实手机/browser、真实 annotation API/export 或真实 delivery success。
- 如果当前环境没有真实 external endpoint，允许通过本地/fixture probe artifact 完成软件契约验证，但 OKR 进度只能保守记录。
