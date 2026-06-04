# Tech Plan: O9 Narrow Runtime Material Epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低 Objective：O9，当前约 18%。
2. 本 sprint 是否针对最低 Objective：是。本轮直接服务 O9 窄 Epic 真实材料突破，并同步牵引 O3 continuous radar/SLAM、O7 PC 同源、O2 真实/受控电梯、O1 stop-first HIL。
3. 不针对其他 Objective 的理由：O5/O6 当前等待真实生产材料；O8 只做治理护栏，不能替代 O9 真实材料。

## 最近 2 轮 blocker 防重复

- `02-03_o9_radar_status_fresh_proof`：status/readback contract 已做，本轮不得继续 Micro-only status/readback；必须做 PC 同源 refresh 复验和新 runtime material。
- `04-05_okr-six-sprint-state-rewrite`：Product 明确下一轮必须窄 Epic；若图片、HIL、远端权限缺失，必须升级 CEO blocker，不得再拆成 Micro 消费同一缺口。

## 并行边界

四个 owner 并行执行，单 artifact、单命令链、单验收口径：

- Full-stack 写 PC 同源复验证据；不改 Robot Software 的 collector/SLAM。
- Robot Software 写 continuous radar/status 或 SLAM `/map` lifecycle 证据；不改 PC UI。
- Robot Algorithm 写真实/受控电梯图片 manifest/eval 证据；不改 HIL 或 PC。
- Hardware Infra 写 stop-first HIL 决策门证据；不碰算法图片和 SLAM。

后续 `final.md` 必须逐 owner 标记：完成、blocked、timeout、重试策略和是否需要 CEO 决策。

## 四个 owner 单 artifact 验收命令

### Full-stack Software Engineer：PC 同源 refresh 复验

Artifact：`sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/pc_same_origin_refresh.json`

```bash
mkdir -p sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence && cd pc-tools/workstation && npm run build && npm test && (PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api > .workstation-runtime/o9_05_06_pc_api.log 2>&1 & pid=$!; trap 'kill $pid 2>/dev/null || true' EXIT; sleep 3; curl -fsS -X POST http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/refresh) | tee ../../sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/pc_same_origin_refresh.json
```

最低验收：artifact 或日志必须证明 PC 同源链路触发 live 8787 refresh，并读回 `proof_state`、hz、TF、`runtime_summary_fallback_used`、`continuous_scan_status`；若失败，记录 PC parser/UI 或 8787 访问 root cause。

### Robot Software Engineer：continuous radar/status 或 SLAM `/map`

Artifact：`sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/radar_or_slam_lifecycle.log`

```bash
mkdir -p sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence && ssh root@192.168.1.11 -p 37878 'set -eu; source /opt/ros/humble/setup.bash; if [ -f /root/rober/onboard/install/setup.bash ]; then source /root/rober/onboard/install/setup.bash; fi; curl -fsS -X POST http://127.0.0.1:8787/api/radar/scan-proof/refresh; echo; curl -fsS http://127.0.0.1:8787/api/radar/status; echo; ros2 topic list; timeout 5 ros2 topic echo --once /map || true; timeout 5 ros2 topic echo --once /scan || true; timeout 5 ros2 run tf2_ros tf2_echo base_link laser_frame || true' | tee sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/radar_or_slam_lifecycle.log
```

最低验收：不能只重复 01-02 latest full proof；必须让 continuous radar/status blocker 有明确收敛，或形成 SLAM `/map` once/map metadata 的新 evidence ref。失败时记录具体 root cause。

### Robot Algorithm Engineer：真实/受控电梯图片

Artifact：`sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/elevator_real_controlled_eval.json`

```bash
mkdir -p sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence && ELEVATOR_MANIFEST=${ELEVATOR_MANIFEST:-pc-tools/evidence/templates/elevator_image_manifest_collection_template.json} && python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test -p 'test_elevator_opencv_baseline.py' && PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline --check-template "$ELEVATOR_MANIFEST" | tee sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/elevator_real_controlled_eval.json
```

最低验收：后续必须补真实/受控电梯 manifest 和 OpenCV eval 输出；若本地或现场没有图片，记录 `blocked_with_root_cause=missing_real_or_controlled_elevator_images`，列出 CEO 需要提供的图片/场地/授权。

### Hardware Infra Engineer：stop-first HIL 决策门

Artifact：`sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/stop_first_hil_gate.log`

```bash
mkdir -p sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence && { date -Is; python3 onboard/scripts/hil_evidence_packet_gate.py --help | head -40; ssh root@192.168.1.11 -p 37878 'set -eu; curl -fsS http://127.0.0.1:8787/api/base/status || true; echo; curl -fsS http://127.0.0.1:8787/api/radar/status || true'; } | tee sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/evidence/stop_first_hil_gate.log
```

最低验收：有现场看护、净空、急停和 CEO/现场授权才进入低速 pulse；否则只输出 CEO blocker。任何未授权运动、`safe_to_control=true` 越界或 HIL pass 文案都判失败。

## 本轮 Product 验收

Product 只验收计划、证据边界和后续 `tech-done.md/final.md` 是否真实记录；不写产品代码、不运行现场 HIL、不更新 `OKR.md`。

本轮计划文件验收命令：

```bash
test -f sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/pre_start.md && test -f sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/prd.md && test -f sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/tech-plan.md
```

```bash
grep -n "sprint_type: epic\|OKR 最低优先级核对\|root@192.168.1.11\|PC 同源\|continuous radar\|SLAM\|真实/受控电梯\|stop-first" sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic/*.md
```

```bash
git diff --check -- sprints/2026.06.05_05-06_o9-narrow-runtime-material-epic
```

## 剩余风险

- PC 同源可能仍停在 parser/UI 消费失败，不能写成 O7 完成。
- continuous radar/status 或 SLAM `/map` 可能仍 blocked，必须记录新 root cause。
- 没有真实/受控电梯图片时，Algorithm 只能交 CEO blocker，不能涨 O2/O9。
- stop-first HIL 缺现场安全条件时只能 blocker，不得写成 HIL pass。
