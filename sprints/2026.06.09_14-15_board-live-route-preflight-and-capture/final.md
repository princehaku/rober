# Final - Board Live Route Preflight and Capture

## 结论

本 sprint 未进入真实现场上位机 ROS2 topic/map/route 采集阶段，但已交付可复用的 `board_live_route_preflight` 执行入口与复跑文档化闭环。该 sprint 结果是：  
- **脚本交付完成**（闭环可复跑入口已建立）  
- **路线证据仍不可产出**（`ssh` 网络 blocker 持续存在）

## 本轮完成项

- 读取并落地了本轮要求的本机/网络/SSH 实现链路：  
  - `onboard/scripts/board_live_route_preflight.sh` 新增且可配置 host/port
  - `docs/navigation/fixed_route_workflow.md` 增加现场 preflight/capture 流程
- 执行并记录了关键命令：`bash -n`、`--help`、`--dry-run --local-only`、`--skip-capture`、`ssh ... echo board_live_ssh_ok`。
- 统一日志路径写入：`~/.ros/trashbot_live_preflight/<run_id>.log`。
- 额外执行的 `bash onboard/scripts/run_smoke_tests.sh` 中，核心 smoke 全部通过，发现 1 项既有回归：
  - `test_launches_default_elevator_assist_off_and_pass_to_orchestrator` 因默认值变更不满足当前断言失败（与本 sprint 目标链路不直接相关）。
- 后续同轮 micro sprint 已修复 launch contract 漂移，并恢复 `pc-tools/evidence/evidence_crosscheck.py` 入口；最新 `bash onboard/scripts/run_smoke_tests.sh` 结果为 `Ran 863 tests ... OK`。

## OKR 影响与边界

- 本 sprint 服务于 O3 现场材料 unblock，不改变 O5/O7 的软件比例边界定义，只降低了“无法重试”的执行阻塞成本。
- 因仍未拿到真实上位机连接，本轮不具备 `map.yaml/route.csv/keyframe/route_replay` 的新现场证据，无法上提 O3 真实路线闭环。

## 未完成与风险

- 未完成：`route_csv_to_yaml`、`fixed_route_autonomy`、`ros2 topic hz` 的成功远端 smoke；`/trashbot/save_map` 未执行；`map/route` 未产出。  
- 已补齐：`run_smoke_tests` 发现的 launch contract 与 `evidence_crosscheck.py` 缺口已在后续 micro sprint 中修复，当前全量 onboard smoke 通过。
- 风险：如 `192.168.1.11:37878` 仍处于路由/ARP/端口层不可达状态，下轮仍会卡在同一 blocker。

## 下一步（明确可执行）

1. 优先恢复上位机网络与端口可达（主机 IP、DHCP、路由、防火墙、SSH 服务状态）。  
2. 网络恢复后，优先运行：  
   - `bash onboard/scripts/board_live_route_preflight.sh --skip-capture`  
3. 若 SSH 仍不达，继续记录 `run_id` + blocker，直接更新 `tech-done` 的 next owner 和重跑动作，不做 closed blocker 直接结束。
