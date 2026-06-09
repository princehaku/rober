# Side2Side Check - Field Evidence Artifact Gate

## 对照结论

本轮满足 PRD/tech-plan 的软件交付目标：已先尝试真实 SSH preflight，SSH 仍返回 `blocked_ssh_unreachable`；随后没有再次只消费同一 SSH blocker，而是用本地完整 fixture 和缺失 fixture 跑通 `trashbot.field_evidence_manifest.v1` artifact gate。

## 需求对照

| 需求 | 结果 | 证据 |
| --- | --- | --- |
| 先尝试 `ssh root@192.168.1.11 -p 37878` preflight | 通过执行，结果不可达 | `/tmp/trashbot_field_preflight_ssh.json`，`status=blocked_ssh_unreachable` |
| 支持 `--mode local\|ssh`、`--artifact-root`、`--preflight-json`、`--output`、SSH 参数 | 已实现 | `onboard/scripts/field_route_evidence_manifest.py` |
| 校验 map、route、keyframes、rosbag、replay | 已实现 | 完整 fixture 全 present，缺失 fixture fail closed |
| 每项 artifact 记录 required/present/path/size/mtime/sha256/reason | 已实现 | `/tmp/trashbot_field_manifest_complete.json` |
| 顶层包含 schema/run_id/generated_at/source/mode/preflight_status/gate_pass/status/blocked_reason/not_proven/delivery flags | 已实现 | `/tmp/trashbot_field_manifest_complete.json` |
| 缺失或空 artifact fail closed | 已验证 | `status=blocked_artifacts_missing`、单测 `test_empty_keyframes_fail_closed` |
| 本地 fixture 完整时可 `gate_pass=true`，但 SSH 未 ready 时保持 `not_proven=true` | 已验证 | `blocked_reason=blocked_ssh_unreachable`、`delivery_success=false` |
| SSH 模式只读、不发布运动命令、不启动导航 | 已实现并测试 | 单测确认命令不含 `/cmd_vel` 或 `ros2 launch` |
| 文档同步 | 已完成 | `docs/navigation/field_route_evidence_manifest.md` 与 preflight 文档 |

## 证据边界

- 完整 fixture 证明 manifest 软件路径可用，不证明真实上位机路线材料已产生。
- 缺失 fixture 证明 artifact gate 会 fail closed，不会把空目录或模板当成真实现场证据。
- `delivery_success=false` 与 `primary_actions_enabled=false` 保持关闭；本轮没有真实送达、真实 Nav2/fixed-route 或 HIL 证据。

## OKR 回顾

tech-plan 中“不直接针对 O7，先补 O3 现场材料 gate”的理由仍成立。本轮没有真实 SSH 材料，因此不能把 O7 PC 回放切到真实路线数据；但 manifest contract 已为后续 O6 archive / O7 route replay 消费真实材料提供标准入口。
