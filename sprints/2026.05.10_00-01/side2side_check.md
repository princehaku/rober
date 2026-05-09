# Sprint 2026.05.10_00-01 Side2Side Check

## 验收对照

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| `enable_visual_gate=true` 时缺 keyframe 不直接 completed | passed | `test_dry_run_waits_for_visual_gate_when_no_camera_or_keyframes_exist` |
| `enable_visual_gate=true` 时缺 camera frame 不直接 completed | passed | `test_dry_run_waits_for_camera_frame_when_keyframe_exists` |
| visual gate 匹配通过后 dry-run 才推进 checkpoint | passed | `test_dry_run_advances_after_visual_gate_passes` |
| `enable_visual_gate=false` 时 route-only dry-run 仍可 completed | passed | `test_dry_run_does_not_create_basic_navigator_and_writes_contract_status` |
| status JSON 展示 checkpoint 和视觉门控原因 | passed | `visual_gate_status/detail/checkpoint` 断言 |
| 行为层 fixed-route reader 不被误喂 completed | mitigated | nav 端未满足门控时写 `waiting_visual_gate`，behavior 会继续等待直到终态或 timeout |

## 剩余风险

- 本轮只验证 missing keyframe 这类准入失败；真实 live frame 与 ORB match pass/fail 仍缺样例图测试。
- 无 Docker/Humble build 和 HIL 证据。
- 学习阶段模拟完成、legacy sleep server 仍需后续清理。
