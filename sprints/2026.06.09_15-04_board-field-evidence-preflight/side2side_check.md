# Board Field Evidence Preflight Sprint Side-by-side Check

## 对照结论

| 验收项 | 结果 | 状态 |
| --- | --- | --- |
| 设计完成后再进入代码 | 已完成 `pre_start.md`、`prd.md`、`tech-plan.md` 后实现 | 完成 |
| 功能点完整性 | CLI 参数、schema、检查项、失败分层、安全边界均已实现 | 完成 |
| 本地 dry-run 可验证 | `/tmp/trashbot_field_preflight.json` 生成并通过 `json.tool` | 完成 |
| SSH 不可达不纯阻塞 | `/tmp/trashbot_field_preflight_ssh.json` 生成，状态 `blocked_ssh_unreachable` | 完成 |
| 产品代码实现 | 新增 `field_route_evidence_preflight.py` | 完成 |
| 测试覆盖 | `python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py` 通过 5 项 | 完成 |
| 文档同步 | 新增 `docs/navigation/field_route_evidence_preflight.md` | 完成 |
| commit/push | 待本轮最终 stage 后提交推送 | 待最终记录 |

## 用户要求对照

用户要求“设计好才能开始写功能点”：满足，已先复核 PRD/tech-plan 完整。

用户要求“功能点不完善不允许开始写代码”：满足，按既有 tech-plan 范围实现，没有扩大到硬件协议或无关 surface。

用户要求“即使 SSH 不可达也必须交付 local/dry-run 可验证软件证据入口”：满足，dry-run JSON 与 SSH blocked JSON 均已生成并通过 JSON 格式化。

用户要求“代码不完美不允许提交”：已完成 py_compile、unittest、dry-run、json.tool 和 SSH 分层验证，提交前只 stage 本轮允许文件。

## 下一步

真实上位机网络恢复后，运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

若状态进入 `ready_for_live_route_capture_not_proven`，再按 JSON `commands.learning` 中模板采集 map、route、keyframe、rosbag 或 replay。
