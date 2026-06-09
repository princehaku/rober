# Final - Board Live Evidence Capture

## 最终状态

本轮状态：`blocked_live_ssh_unreachable_with_fallback_evidence_ready`。

真实上位机入口：

```bash
ssh root@192.168.1.11 -p 37878
```

从当前开发机不可达，直接 SSH 返回 `No route to host`；`board_live_route_preflight.sh --skip-capture` 也确认 ping、nc、ssh 均失败。因此本轮没有产出真实 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL，不能重新激活 O3 现场完成证据。

## 已完成内容

- 执行真实 SSH preflight，失败分层为 `blocked_ssh_unreachable`。
- 生成 SSH 模式 preflight JSON：`/tmp/trashbot_field_preflight_ssh.json`。
- 执行 `board_live_route_preflight.sh` 的语法检查、help、local-only dry-run 和 skip-capture preflight。
- 生成 local dry-run fallback JSON：`/tmp/trashbot_field_preflight_local.json`。
- 构造 manifest fixture 并验证 manifest gate；追加 `replay.jsonl` 后输出 `field_evidence_manifest_ready_not_delivery_proof`。
- 运行 py_compile 和 unittest，`10` 个测试通过。
- 更新本 sprint 收口文档，不改产品代码、测试代码、launch、硬件配置、`OKR.md` 或业务 docs。

## 验证证据摘要

关键 live 失败证据：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

关键 preflight 状态：

```text
status=blocked_ssh_unreachable
```

关键 fallback 状态：

```text
status=dry_run_template_only_not_proven
```

关键 manifest 状态：

```text
gate_pass=true
status=field_evidence_manifest_ready_not_delivery_proof
delivery_success=false
safe_to_control=false
primary_actions_enabled=false
```

关键测试结果：

```text
Ran 10 tests in 0.042s
OK
```

## OKR 与产品判断

本轮继续执行 `OKR.md` 第 5 节指定的 O3 现场验证 lane，而不是新增 O6/O7 surface。结果没有拿到真实现场材料，因此不提升 O3 归档证据，不更新 `OKR.md` 进度。

但本轮没有再次只消费 blocker：已留下标准 fallback evidence packet、manifest gate 证明和明确 CEO 决策点。下一步应该先修正现场网络/入口条件，或改由现场人工导出材料，再让 O6/O7 消费真实数据。

## 剩余风险

- 当前开发机到 `192.168.1.11:37878` 无路由，真实 SSH、ROS2 topic smoke、learn.launch、route recorder、map save、rosbag 均未执行。
- 未验证上位机 ROS2 环境、trashbot packages、`/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`。
- 未执行运动相关命令，也未验证真实固定路线回放。
- 执行中曾发现 tech-plan 原 fixture 命令未创建 `replay.jsonl`，与 manifest required artifact 集合不完全一致；本轮已补正 `tech-plan.md` fallback fixture 命令，并用追加 fixture 复跑通过。后续若调整 manifest required 集合，需同步计划和脚本帮助文本一致性。

## 下一步

CEO 需要确认或提供其中一种条件：

1. 上位机在线、IP 仍为 `192.168.1.11`，开发机在同一局域网或 VPN 内。
2. 端口 `37878` 开放且映射到 SSH。
3. 新的 SSH host/port。
4. 现场人工导出的 `map.yaml`、`route.csv`、keyframes、`route_bag/`、`replay.jsonl`。

入口恢复后，下一轮应直接执行 board runtime/topic smoke 和非运动 capture；只有现场安全条件明确时，再启动 learn.launch route recorder。
