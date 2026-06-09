# Side2Side Check - Board Live Evidence Capture

## 验收口径对照

| 验收项 | 期望 | 本轮结果 | 结论 |
| --- | --- | --- | --- |
| Live SSH gate | `ssh root@192.168.1.11 -p 37878` 可达 | 退出码 `255`，`No route to host` | 未通过，失败在网络路由层 |
| SSH preflight JSON | 输出标准 JSON 并分层失败 | `/tmp/trashbot_field_preflight_ssh.json`，`status=blocked_ssh_unreachable` | 通过 |
| Board evidence CLI | 静态检查、help、dry-run、本机 preflight 可执行 | `bash -n`、`--help`、`--dry-run --local-only` 通过；`--skip-capture` 因 SSH 不可达退出 `2` | 通过，非零退出符合 blocker 暴露设计 |
| ROS2/topic smoke | SSH 成功后检查 ROS2、package、topic | SSH 不通，未进入上位机 ROS2 阶段 | 未执行，原因明确 |
| Live artifact | 产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL 中至少一种真实材料 | 未产出真实材料 | 未通过 |
| Fallback preflight | SSH 不通时输出 local dry-run JSON | `/tmp/trashbot_field_preflight_local.json`，`status=dry_run_template_only_not_proven` | 通过 |
| Manifest fixture | fallback artifact root 可被 manifest gate 消费 | 原 tech-plan fixture 缺 `replay.jsonl` 首次失败；追加 fixture 后 `gate_pass=true`，并已补正 `tech-plan.md` fallback 命令 | 通过 |
| Fail-closed | fallback 不误报真实送达或可控 | `delivery_success=false`、`not_proven=true`、`safe_to_control=false`、`primary_actions_enabled=false` | 通过 |
| 单元测试 | preflight/manifest 单测通过 | `Ran 10 tests ... OK` | 通过 |

## 用户验收判断

本轮未满足路径 A（live 成功），因为真实 SSH 入口不可路由，无法进入上位机 ROS2/topic/capture。已满足路径 B（live 失败但 fallback 合格）的核心要求：失败被分层记录，SSH preflight JSON、local dry-run JSON、manifest fixture JSON 均可复跑，并给出下一步 CEO 决策点。

## 与功能点完整性门槛的差距

- Live SSH gate：失败，需 CEO 或现场网络条件修正。
- Board runtime gate：未执行，依赖 SSH 可达。
- Capture gate：未执行 live capture，依赖 SSH 可达和现场安全条件。
- Manifest gate：local fixture 可 gate，但不是 live evidence。
- Fail-closed gate：通过，未把 fallback/mock/preflight-only 状态误报为真实送达。
- Code-write gate：未发现必须由 robot-algorithm-engineer 直接改产品代码的问题；tech-plan fixture 缺 `replay.jsonl` 的文档偏差已在本 sprint 计划中补正。

## CEO 决策点

请优先确认网络条件，而不是继续增加软件 surface：

1. `192.168.1.11` 是否仍是上位机当前 IP。
2. 开发机是否已加入上位机同一局域网或现场 VPN。
3. `37878` 是否开放并指向 SSH 服务。
4. 若现场网络无法恢复，是否由现场人员直接导出 `map.yaml`、`route.csv`、keyframes、`route_bag/`、`replay.jsonl`，再交给 manifest gate。
