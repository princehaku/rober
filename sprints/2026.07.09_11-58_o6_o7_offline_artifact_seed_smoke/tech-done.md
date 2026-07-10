# O6/O7 Offline Artifact Seed Smoke Tech Done

## sprint_type: epic

## 实际改动

本轮为产品收口，不改产品代码、不改测试代码、不改 vendor 文件，只补齐 sprint 交付文档与 OKR 留档：

- 新建本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 节与当前最高优先级说明，把 O6/O7 的软件侧进度从约 42% 保守调整到约 45% / 44%。
- 更新 `docs/process/okr_progress_log.md`，追加本 sprint 的证据条目。

对 worker 证据的收口结论如下：

- Algorithm worker 已把离线路线材料整理成 `trashbot.offline_seed_summary.v1`，`route.csv` / `manifest.json` / `derived_replay.jsonl` 形成同一 `task_id=offline-artifact-seed-20260610` 的 seed smoke 摘要。
- 该 seed smoke 的离线 replay 帧数为 `17`，并保留了 `route_bag` 仍参与 gate 的事实，因此路线根 seed 目前仍需临时 bundle 或同类完整 fixture。
- O6 worker 已新增 `trashbot.o6.offline_artifact_seed_smoke.v1`，把同一 `task_id` 的 route / replay / keyframe / evidence / probe 摘要接入 archive detail 与 consumer detail，`test_remote_cloud_relay` 达到 `154 tests OK`。
- O7 worker 已消费同一 `task_id` 下的 O6 摘要，`npm run test` 达到 `473 passed`，并通过 `build`、`lint` 和 `git diff --check`。

## 验证结果

已运行并回报用户要求的验收命令：

```bash
test -f sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/tech-done.md && test -f sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/side2side_check.md && test -f sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/final.md
```

结果：通过。

```bash
rg -n "sprint_type: epic|software_proof_offline_artifact_seed_smoke_only|154 tests|473 tests|17|O6|O7|safe_to_control: false|delivery_success: false|primary_actions_enabled: false|robot_control_executed: false|route_bag" sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke OKR.md docs/process/okr_progress_log.md
```

结果：通过，命中本 sprint 的收口文档、OKR 进度说明、`17` 帧离线 replay、`154 tests`、`473 passed`、`route_bag` gate 以及四个安全旗标。

```bash
git diff --check
```

结果：通过。

## 剩余风险

- 这次只证明 `software_proof_offline_artifact_seed_smoke_only`，不证明真实生产云、真实媒体、真实 annotation API、真实 dataset export、真实机器人运动或 delivery success。
- route-root seed smoke 仍受 `route_bag` gate 影响；当前只完成离线 seed 贯通，不代表 route-only 输入已经足够。
- O6/O7 的新证据仍是 local/mock / offline proof，后续若要进入真实现场材料贯通，必须补 same-task_id live preflight 与真实 route_bag / capture lane。

## 安全旗标

- `safe_to_control: false`
- `delivery_success: false`
- `primary_actions_enabled: false`
- `robot_control_executed: false`

