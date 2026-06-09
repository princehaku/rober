# Final - Field Evidence Artifact Gate

## 收口状态

状态：completed_software_artifact_gate。

本轮已交付现场 evidence manifest / artifact gate。真实 SSH preflight 已按 `ssh root@192.168.1.11 -p 37878` 入口尝试，当前仍是 `blocked_ssh_unreachable`；本轮没有第三次只以 SSH blocker 收口，而是用本地完整 fixture 和缺失 fixture 完成 manifest 功能、fail-closed 和文档验证。

## 实际产出

- `onboard/scripts/field_route_evidence_manifest.py`：新增 `trashbot.field_evidence_manifest.v1` CLI。
- `onboard/tests/test_field_route_evidence_manifest.py`：新增 5 个单元测试。
- `docs/navigation/field_route_evidence_manifest.md`：新增 manifest contract 与复跑文档。
- `docs/navigation/field_route_evidence_preflight.md`：补充 preflight 到 manifest 的下游入口。
- `tech-done.md` / `side2side_check.md`：记录实现、验证和对照结果。

## 验证结论

已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_manifest_complete.json
python3 -m json.tool /tmp/trashbot_field_manifest_missing.json
rg -n "field_evidence_manifest|ssh root@192.168.1.11 -p 37878|not_proven|delivery_success=false|不再次只消费同一 SSH blocker" docs/navigation sprints/2026.06.09_17-03_field-evidence-artifact-gate
git diff --check
```

关键结果：

```text
SSH preflight: status=blocked_ssh_unreachable
complete fixture: gate_pass=true, status=field_evidence_manifest_ready_not_delivery_proof, not_proven=true, delivery_success=false
missing fixture: gate_pass=false, status=blocked_artifacts_missing, blocked_reason=missing_required_artifact
unittest: preflight Ran 5 OK; manifest Ran 5 OK
git diff --check: passed
```

## OKR 影响

本轮服务于临时激活的 O3 现场验证 lane：现在已有可复跑的 artifact gate，可以在 SSH 恢复后统一校验真实 `map.yaml`、`route.csv`、keyframes、rosbag 和 fixed-route replay JSONL。

因为真实 SSH 仍不可达，本轮不能提升真实路线采集、Nav2 实跑、O7 真实 PC 回放或 O6 真实 archive 的完成度。

## 未完成事项与风险

- 未登录真实上位机，未校验远端真实 artifact。
- 未证明 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` topic smoke。
- 未产出真实 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。
- 未执行 Docker/Humble `colcon build`；本轮验收范围是独立 Python CLI、unittest、fixture 和文档。
- 当前工作区存在上一轮未提交改动，未执行 commit / push，避免混入范围外文件。

## 下一步

恢复 `192.168.1.11:37878` 网络/SSH 后，直接对真实 `$HOME/.ros/trashbot_runs/<RUN_ID>` 运行 manifest SSH 模式；若 gate 通过，再把 manifest 交给 O6 archive 或 O7 PC route replay 后续 sprint 消费。
