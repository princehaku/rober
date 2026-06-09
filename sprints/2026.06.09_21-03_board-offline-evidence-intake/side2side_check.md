# Board Offline Evidence Intake Side2Side Check

## 验收对照

| PRD / Tech Plan 要求 | 本轮结果 |
| --- | --- |
| 支持本地目录输入 | 已支持 `--input <dir>`，等价于 `--artifact-root <dir>` |
| 输出 / 复用 `trashbot.field_evidence_manifest.v1` | 继续由 `field_route_evidence_manifest.py` 输出同一 schema |
| 覆盖 present/missing artifact | 既有 artifact 扫描保留，单测覆盖完整、缺失和空 keyframes |
| 覆盖 schema mismatch | 新增已有 manifest schema mismatch fail-closed 单测 |
| 覆盖 unsafe claim | 新增 `delivery_success=true` / `safe_to_control=true` fail-closed 单测 |
| fail-closed | schema mismatch、unsafe claim、missing artifact 均非零退出 |
| 不依赖真实 SSH | P0 验收全部本地运行，SSH 只保留为后续 P1 风险 |
| 不误报成功交付或安全控制 | 所有生成路径固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false` |

## 关键对照结果

本地完整 fixture 运行：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --input /tmp/trashbot_field_evidence_fixture --output /tmp/trashbot_field_evidence_manifest.json
```

输出 `gate_pass=true`，但 manifest 仍为：

- `not_proven=true`
- `blocked_reason=missing_preflight_json`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`

这满足 PRD 的边界：离线 evidence packet intake 只证明 artifact gate，不证明真实 delivery。

## 未覆盖项

- 未做真实 SSH 复测，避免第三次消费同一 `No route to host` blocker。
- 未做 PC 端构建或测试，因为本轮机器人侧未触碰 `pc-tools/**`；PC worker 如有并行结果，应在其自己的输出中补充。
