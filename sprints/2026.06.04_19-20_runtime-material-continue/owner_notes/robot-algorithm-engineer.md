# Robot Algorithm Engineer Owner Note

## sprint_type

sprint_type: epic

## 目标

推进 O2 `KR-O2-Real-Image-Manifest-Eval`。本轮没有找到真实或受控电梯图片，因此不运行 field eval、不建议 O2 涨分；改为补齐可执行采集模板、manifest readiness checker 和 blocker artifact，避免下一轮继续手工口头描述缺材料。

## 实际改动

- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/elevator_opencv_baseline.py`
  - 新增 `--check-template` 模式。
  - 新增 `trashbot.elevator_image_manifest_template_check.v1` 输出。
  - 校验 manifest schema、必填字段、taxonomy tags、placeholder image refs、fixture-only 图片和真实/受控图片引用。
  - 输出 `blocked_missing_real_or_controlled_images`、`blocked_fixture_only_not_o2_material`、`needs_image_file_backfill`、`ready_for_eval_needs_more_labeled_samples`、`ready_for_opencv_eval` 等状态。
- `onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py`
  - 覆盖 placeholder 模板 fail-closed。
  - 覆盖 fixture-only manifest 不能作为 O2 field material。
- `docs/vision/elevator_opencv_baseline.md`
  - 增加真实/受控 manifest checker 用法、状态语义、not_proven 边界和下一步 eval 命令。
- `pc-tools/evidence/templates/elevator_image_manifest_collection_template.json`
  - 新增 O2 现场/受控图片采集模板。
- `pc-tools/evidence/fixtures/elevator_real_image_manifest_blocker/blocked_missing_manifest.json`
  - 记录本轮 root cause、不可计分材料、checker 命令和下一步所需证据。

## 验证结果

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline --check-template pc-tools/evidence/templates/elevator_image_manifest_collection_template.json
```

结果摘要：

```text
schema=trashbot.elevator_image_manifest_template_check.v1
status=blocked_missing_real_or_controlled_images
evidence_type=blocked_with_root_cause
can_run_opencv_eval=false
field_eval_ready=false
template_placeholders=8
image_kinds.real_or_controlled=0
next_required_evidence=collect real or controlled elevator images and replace template image_dir/image refs
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test
```

结果：

```text
Ran 20 tests in 1.170s
OK
```

```bash
python3 -m compileall -q onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/elevator_opencv_baseline.py onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py
```

结果：通过，无输出。

## 失败定位

`blocked_missing_real_or_controlled_images`。仓库当前仍没有真实或受控电梯 JPEG/PNG/WebP manifest；模板中的 8 个 sample 全部是 placeholder，不能运行 OpenCV field eval，也不能作为 O2 涨分材料。

## 剩余风险

- 不证明真实相机电梯识别、楼层 OCR、目标楼层确认、安全驶出、跨楼层送达或 delivery success。
- 模板只有最小类别骨架，现场采集仍需回填真实 `image_dir`、图片文件和足够样本数。
- O2 只有在真实/受控图片回填并通过 checker 后，才可以运行 OpenCV eval。
