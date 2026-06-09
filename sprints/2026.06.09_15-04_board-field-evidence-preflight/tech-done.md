# Board Field Evidence Preflight Sprint Tech Done

## sprint_type: epic

## 实际完成

本轮完成了 `board_field_evidence_preflight_cli` 的功能设计和工程交接：

- 明确新增 CLI 的目标、输入参数、输出 JSON schema、失败分层和安全边界。
- 明确 dry-run 必须可在无 ROS2、无真实 SSH 的开发机上验证。
- 明确真实 SSH 恢复后用于上位机现场预检，不替代真实 map/route/keyframe/rosbag/replay 证据。
- 明确 Engineer 实现文件范围、测试路径、验收命令、文档同步和提交推送要求。

## 实际改动文件

- `sprints/2026.06.09_15-04_board-field-evidence-preflight/pre_start.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/prd.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/tech-plan.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/tech-done.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/side2side_check.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md`

## 未完成实现

本轮未实现产品代码，原因不是需求不清，而是运行时子 agent 能力不可用。

主节点按仓库 `AGENTS.md` 纪律尝试派发 `product-okr-owner` 子 agent，连续返回：

```text
spawn_agent could not resolve the child model for service tier validation
```

按项目规则，主节点不能在没有子 agent 的情况下越权写产品代码、测试代码或运行实现验证命令。因此本轮停在设计交付和可执行交接，不假装已经完成 CLI。

## 验证结果

已执行只读检查和设计留档：

```bash
git status --short --branch
```

开始时输出：

```text
## master...origin/master
```

未执行以下实现验收命令，因为对应文件尚未由 Engineer 创建：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_field_preflight.json
```

## 失败定位

阻塞点：子 agent 运行时无法启动，错误发生在工具层模型解析，不是仓库代码、设计、测试或 SSH 网络本身。

上一轮真实 SSH 网络 blocker 没有被本轮重复消费；本轮选择了不依赖 SSH 恢复的设计和工程交接。

## 剩余风险

- `board_field_evidence_preflight_cli` 尚未实现，不能作为可运行工具使用。
- 未产生 JSON evidence packet、单元测试日志或 dry-run 输出。
- 下一轮需要在子 agent 恢复后直接按 `tech-plan.md` 派 `robot-algorithm-engineer` 实现，或由用户明确允许主节点降级直接写代码。

