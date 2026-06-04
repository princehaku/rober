# Final: O9 Narrow Runtime Material Epic

## sprint_type

sprint_type: epic

## 收口结论

本轮完成了一个窄 Epic，而不是继续 Micro-only 接口/readback：

- Product/OKR 计划文档已落地：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Robot Software 关闭 02-03 的远端未加载缺口：live 8787 已 restart/curl，`/api/radar/status` 现场返回 latest fresh proof 字段。
- Full-stack 落了 PC App 最小护栏：same-origin refresh 不会把 fresh proof 包装成 continuous ready。
- Algorithm 明确 O2/O9 blocker：缺真实/受控电梯图片 manifest。
- Hardware 明确 O1/O9 blocker：缺 stop-first HIL 安全前提和现场授权。

## OKR 进度判断

| Objective | 本轮判断 |
| --- | --- |
| O1 | 保持约 95.5%；没有 HIL、ACK、ROS feedback topics 或 `safe_to_control=true`。 |
| O2 | 保持约 72%；没有真实/受控电梯图片 manifest 或 field eval。 |
| O3 | 保持约 75%；远端 status readback 已复验，但 continuous radar 和 SLAM `/map` 仍 blocked。 |
| O5 | 保持约 84%；未触达 production live material。 |
| O6 | 保持约 82%；未触达 production archive/query/inference。 |
| O7 | 保持约 91%；PC App 最小护栏通过，但没有 PC live API smoke 和完整 hz/TF/fallback 展示。 |
| O8 | 约 45% -> 约 46%；本轮按要求启动窄 Epic，完成多 owner 事实闭环、blocker 记录和防越界收口。 |
| O9 | 保持约 18%；没有新增 continuous radar、SLAM/map、field/HIL 或 user acceptance material。 |

## 证据边界

新增可计证据：

- `robot_runtime_material/readback`：远端 8787 `/api/radar/status` 和 `/api/radar/scan-proof/latest` 已现场 curl，新字段加载。
- `software_guard`：PC App same-origin refresh 最小护栏，防止 fresh proof 被误读为 continuous ready。
- `blocked_with_root_cause`：`missing_real_or_controlled_elevator_images`、`hil_safety_preconditions_not_met`、`scan_continuity_not_observed`、`map_artifact_dir_missing`。

不可越界：

- 本轮不证明 continuous radar ready、SLAM `/map`、AMCL、Nav2、PC WASD、WAVE ROVER ACK、HIL、真实电梯识别、真实手机用户验收或真实送达。

## 下一步

1. Full-stack：扩大文件范围到 `pc-tools/workstation/src/server/o7DirectUpperApi.ts` 和 `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`，完成 hz、TF、runtime fallback、continuous boundary 全字段解析/展示，并跑 PC 本机 API live smoke。
2. Robot Software + Algorithm：专门推进 SLAM `/map` lifecycle，目标是 `/map` once、map artifact、metadata 和 `runtime/map_lifecycle_latest.json`。
3. Algorithm：采集真实/受控电梯图片并回填 `trashbot.elevator_image_manifest.v1`。
4. Hardware：只有现场看护、净空、急停/断电和授权齐备时才进入 stop-first HIL；否则继续 CEO blocker。
