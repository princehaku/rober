# Side2Side Check - Board Live Route Preflight and Capture

## 验收口径对照

| PRD/Tech-Plan 要求 | 本轮结果 | 状态 |
| --- | --- | --- |
| 本机尝试 `ssh root@192.168.1.11 -p 37878` | 直接命令返回 `No route to host`（退出 255） | 失败 |
| 脚本落地为可复用预检入口 | 已新增 `onboard/scripts/board_live_route_preflight.sh`，支持 `--help/--dry-run/--local-only/--skip-capture` | 完成 |
| 本机预检检查 `git status` | 已执行并落库 | 完成 |
| 默认网关/ping 检查 | 已执行并在日志保留（允许失败） | 完成 |
| nc/ssh 检查 | 已执行；ping/nc/ssh 失败时仍可记录并继续 | 完成 |
| SSH 成功后检查 `hostname/date/ros2/setup.bash/ros2 pkg/topic list/topic hz` | 本轮因 ssh 不达未能进入有效执行分支 | 未完成 |
| 产出 capture 模板（learn/save_map/route_csv_to_yaml/fixed_route_autonomy/ros2 bag） | `--dry-run` 与 `--local-only` 下输出模板并写入日志 | 完成 |
| 真实路线和地图产物（map.yaml / route.csv / keyframe / bag） | 未产出 | 未完成 |
| 失败时可复跑/下一步动作被写入 sprint 文档 | 已在 tech-done/final 写清 blocker 与复跑动作 | 完成 |
| 不修改硬件/底盘运动链路 | 命令模板仅打印，无直接下发 | 完成 |
| 可选 `run_smoke_tests`（环境回归） | 通过率 95%，存在 1 项既有失败（与本 sprint 非同路径） | 部分完成 |

## 关键对账

- 本 sprint 关键差距不是脚本能力，而是网络层阻塞。  
- 脚本已把证据从“是否尝试”切换为“如何复试”：`run_id`、日志文件、失败分桶、下一步动作明确写入。
- `tech-done.md`、`final.md` 与 `docs/navigation/fixed_route_workflow.md` 已形成同一闭环口径。
