# 2026-06-10 05:50 map lifecycle helper reconcile

sprint_type: micro

## 实际改动

- 新增 `onboard/scripts/o3_map_lifecycle_proof.py`，从真实上位机
  `root@192.168.1.11:37878` 的 `/root/rober/onboard/scripts/o3_map_lifecycle_proof.py`
  只读纳入仓库。
- 新增 `onboard/tests/test_map_lifecycle_proof_helper.py`，覆盖 helper 存在、
  可执行位、CLI help/argparse 和 no-motion guard 静态边界。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，记录 helper 已纳管，以及
  `/map_once_not_observed` 仍是当前 map proof 未 clean 的根因。

## 远端 helper 来源

- path: `/root/rober/onboard/scripts/o3_map_lifecycle_proof.py`
- size: `16083`
- mtime: `2026-06-05 12:24:57.032651159 +0800`
- mode: `755`
- sha256: `f8cffd9830ee66b5344985475c32665184a05a9ed4fb77df3ae21244c184fea3`
- local post-comment sha256: `765adc60686fdf8a0449f2df437278a5605d50a52451dfe0000bf622935f136a`
  （仅补中文 no-motion 说明，保留远端实际运行逻辑）

## 验证结果

`git status --short --branch --untracked-files=all`：

```text
## master...origin/master
 M docs/hardware/board_sensor_stack_smoke.md
?? onboard/scripts/o3_map_lifecycle_proof.py
?? onboard/tests/test_map_lifecycle_proof_helper.py
?? sprints/2026.06.10_05-50_map_lifecycle_helper_reconcile/tech-done.md
```

`python3 -m py_compile onboard/scripts/o3_map_lifecycle_proof.py`：通过，无输出。

`python3 onboard/scripts/o3_map_lifecycle_proof.py --help`：通过，只输出 argparse usage；
包含 `--output`、`--map-dir`、`--timeout-s`，未进入 ROS2/LiDAR runtime。

`python3 -m unittest discover -s onboard/tests -p 'test_map_lifecycle_proof_helper.py'`：

```text
Ran 3 tests in 0.038s

OK
```

`rg -n "o3_map_lifecycle_proof|map lifecycle helper|/map_once_not_observed|no-motion|publishes_cmd_vel|calls_base_manual|safe_to_control|delivery_success" onboard/scripts/o3_map_lifecycle_proof.py docs/hardware/board_sensor_stack_smoke.md sprints/2026.06.10_05-50_map_lifecycle_helper_reconcile/tech-done.md`：

```text
docs/hardware/board_sensor_stack_smoke.md:378:## 2026-06-10 05:50 map lifecycle helper reconcile
docs/hardware/board_sensor_stack_smoke.md:380:`onboard/scripts/o3_map_lifecycle_proof.py` 已从真实上位机
docs/hardware/board_sensor_stack_smoke.md:391:  `publishes_cmd_vel=false`、`calls_base_manual=false`、`safe_to_control=false`、
docs/hardware/board_sensor_stack_smoke.md:392:  `delivery_success=false`。
docs/hardware/board_sensor_stack_smoke.md:396:  `/map_once_not_observed`，因此已有 `trashbot_map.yaml` / `trashbot_map.pgm`
onboard/scripts/o3_map_lifecycle_proof.py:2:"""no-motion LiDAR + SLAM `/map` lifecycle proof 采集器。
onboard/scripts/o3_map_lifecycle_proof.py:46:        "safe_to_control": False,
onboard/scripts/o3_map_lifecycle_proof.py:50:        "publishes_cmd_vel": False,
onboard/scripts/o3_map_lifecycle_proof.py:51:        "calls_base_manual": False,
onboard/scripts/o3_map_lifecycle_proof.py:53:        "delivery_success": False,
onboard/scripts/o3_map_lifecycle_proof.py:265:        causes.append({"layer": "SLAM/TF/topic remap", "reason": "/map_once_not_observed"})
```

`git diff --check`：通过，无输出。

## 剩余风险

- 本轮没有再次运行 `/api/map/proof/refresh`，避免重复触发真实上位机 runtime。
- helper 可复现性已补齐，但 clean map proof 仍未完成；上一轮失败根因仍是
  `/map_once_not_observed`，需要后续定位 SLAM/TF/topic timing。
- 当前验证是本地静态与 CLI help 级别，不等于 LiDAR/SLAM/HIL clean proof。
