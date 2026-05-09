# Sprint 2026.05.10_00-01 Tech Done

## 状态

- 当前阶段：TECH DONE。
- 完成时间：2026-05-10T01:14:44+08:00。
- Owner：`Autonomy Algorithm Engineer` 主责，`Product Manager / OKR Owner` 做 OKR 对齐。

## 实际改动

| 文件 | 改动 |
| --- | --- |
| `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py` | 移除 dry-run 对 visual gate 的直接绕过；启用 visual gate 时必须检查 keyframe、live frame、live descriptor 和匹配数量；状态 JSON 新增 `visual_gate_status`、`visual_gate_detail`、`visual_gate_checkpoint`。 |
| `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py` | 扩展 fixed-route dry-run 离线测试：visual gate disabled 仍可 completed；缺 keyframe 等待；keyframe 存在但缺 camera frame 等待；匹配通过后才推进 checkpoint。 |
| `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py` | 固化 visual gate 诊断字段必须进入 debug status 契约。 |

## 行为变化

- `enable_visual_gate=false`：保持原路线解析 dry-run，checkpoint 可直接推进到 `completed`。
- `enable_visual_gate=true`：dry-run 不再假成功；缺少 keyframe、camera frame、descriptor 或匹配不足时写出 `waiting_visual_gate` 和明确失败原因。
- 调试/行为消费方可以直接读取 visual gate 状态，而不是只能解析 `last_error` 字符串。

## 验证结果

| 命令 | 结果 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_fixed_route_dry_run_offline.py'` | passed，6 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test*.py'` | passed，20 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | passed，interfaces 4 + hardware 14 + nav 20 + bringup 7 + behavior 91 + vision 1 tests OK |
| `git diff --check -- src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_fixed_route_status_static.py` | passed |

## OKR 影响

| OKR | 本轮推进 |
| --- | --- |
| Objective 3 KR3 | fixed route dry-run 现在能验证路线读取、关键帧存在、camera frame 准入和匹配通过后的状态推进。 |
| Objective 3 KR5 | debug status 增加 visual gate 状态、详情和 checkpoint，调试页面/行为层可展示失败原因。 |
| Objective 2 KR4 | 送达路径不再把 visual gate 未满足误报为 completed，失败/等待原因可机器读取。 |

## 剩余风险

- 本轮仍是离线 dry-run 和软件 smoke；未声明 Nav2 实机、摄像头实拍、Docker Humble build 或 HIL 通过。
- `_load_keyframes()` 仍按现有策略静默跳过不可读或 descriptor 为空的 keyframe；当前 checkpoint 会报告 missing keyframe，但尚未做 route-wide 预检。
- 下轮高价值方向：补 route-wide keyframe coverage 预检，或推进 Objective 2 的 patrol `waypoints_total = 5` 占位债务。
