# Robot Algorithm Engineer Owner Note

## 自主能力目标和本轮抓手

- Objective：O2 可送垃圾任务 + 电梯 assisted delivery。
- 本轮抓手：继续查找真实或受控电梯图片 `trashbot.elevator_image_manifest.v1`，如果存在就运行 manifest checker 和 OpenCV offline eval；如果不存在，只刷新 blocker evidence，不把 PGM fixture 或 UI 截图写成 O2 涨分材料。
- 证据边界：`blocked_with_root_cause`。本轮没有触碰底盘运动、串口、`/cmd_vel`、Nav2 goal 或任何硬件控制路径。

## Manifest / Image 查找结果

本地 manifest 查找：

```bash
find . \( -path './.git' -o -path './build' -o -path './install' -o -path './log' -o -path './pc-tools/workstation/node_modules' -o -path './docs/vendor' \) -prune -o -type f \( -iname '*elevator*manifest*.json' -o -iname '*elevator*manifest*.yaml' -o -iname '*lift*manifest*.json' -o -iname '*lift*manifest*.yaml' -o -path './pc-tools/evidence/templates/elevator_image_manifest_collection_template.json' -o -path './pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json' \) -print | sort
```

输出摘要：

```text
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json
./pc-tools/evidence/templates/elevator_image_manifest_collection_template.json
```

本地图片候选查找：

```bash
find . \( -path './.git' -o -path './build' -o -path './install' -o -path './log' -o -path './pc-tools/workstation/node_modules' -o -path './docs/vendor' \) -prune -o -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.bmp' -o -iname '*.pgm' \) -print | grep -Ei 'elevator|lift|door_open|door_closed|inside_positive|outside_negative|safe_exit|uncertain_or_bad_light|floor_target|opencv_baseline' | sort || true
```

输出摘要：

```text
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/ambiguous_bad_light.pgm
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/closed_outside_unsafe.pgm
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/open_inside_safe_f3.pgm
./sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/evidence/mobile_current_pwa_field_trial_browser_390x844.png
./sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/evidence/mobile_current_pwa_field_trial_browser_768x900.png
```

判定：

- `pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/*.pgm` 是合成 fixture，只能作为 software guard，不能作为 O2 真实/受控电梯图片材料。
- 两张 `mobile_current_pwa_field_trial_browser_*.png` 是移动端 UI 截图，不是电梯相机采集样本，不能进入 OpenCV field eval。

上位机只读 SSH 查找：

```bash
timeout 12s ssh -p 37878 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 root@192.168.1.11 'set -eu; for base in /root/rober /home/orangepi/rober /home/pi/rober /ws /mnt/e/rober; do if [ -d "$base" ]; then echo "BASE=$base"; find "$base" \( -path "$base/.git" -o -path "$base/build" -o -path "$base/install" -o -path "$base/log" -o -path "$base/pc-tools/workstation/node_modules" -o -path "$base/docs/vendor" \) -prune -o -type f \( -iname "*elevator*manifest*.json" -o -iname "*lift*manifest*.json" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.bmp" -o -iname "*.pgm" \) -print | grep -Ei "elevator|lift|door_open|door_closed|inside_positive|outside_negative|safe_exit|uncertain|floor_target|manifest" | head -200 || true; fi; done'
```

输出摘要：

```text
BASE=/root/rober
```

判定：上位机可达且 `/root/rober` 存在，但 pruned search 没有返回真实/受控电梯 manifest 或图片候选。

## Checker / Eval 结果

采集模板 readiness checker：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline --check-template pc-tools/evidence/templates/elevator_image_manifest_collection_template.json
```

关键输出：

```text
schema=trashbot.elevator_image_manifest_template_check.v1
status=blocked_missing_real_or_controlled_images
evidence_type=blocked_with_root_cause
can_run_opencv_eval=false
field_eval_ready=false
image_kinds.fixture=0
image_kinds.real_or_controlled=0
image_kinds.missing_or_invalid=8
template_placeholders=8
next_required_evidence=["collect real or controlled elevator images and replace template image_dir/image refs"]
not_proven=[real_camera_elevator_recognition, real_floor_ocr, real_target_floor_confirmation, real_safe_exit, real_cross_floor_delivery]
```

Fixture manifest 负控 checker：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline --check-template pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json
```

关键输出：

```text
exit_code=1
status=invalid_manifest_template
can_run_opencv_eval=false
field_eval_ready=false
image_kinds.fixture=3
image_kinds.real_or_controlled=0
errors=[
  samples[1] missing required field: expected_floor,
  samples[2] missing required field: target_floor,
  samples[2] missing required field: expected_floor,
  samples[2] missing required field: expected_inside_outside,
  samples[2].expected_inside_outside must be one of ['inside', 'outside', 'uncertain']
]
```

OpenCV offline eval：本轮没有运行真实/受控 manifest eval，因为 checker 明确 `can_run_opencv_eval=false`，且本地和上位机都没有找到可接受的真实/受控电梯图片 manifest。fixture eval 不写入 O2 进度，避免把 software guard 当成 field material。

## 失败定位

- 根因：缺少真实或受控电梯图片 manifest；当前仓库只有采集模板、合成 PGM fixture 和移动端 UI 截图。
- 当前可执行入口已具备：`pc-tools/evidence/templates/elevator_image_manifest_collection_template.json` 和 `--check-template`。
- 当前不可执行项：`trashbot.elevator_image_manifest.v1` 的 OpenCV field eval，因为没有 JPEG/PNG/WebP/BMP 真实或受控图片引用。

## 剩余风险和下一步

- O2 不涨分：本轮只形成 blocker evidence，不证明真实相机电梯识别、楼层 OCR、目标楼层确认、安全驶出或跨楼层送达。
- 下一步 owner：Robot Algorithm Engineer 需要接收一组真实或受控电梯图片 manifest；现场/运营侧需要提供图片目录与标注。
- 最小解除 blocker 条件：把模板中的 `image_dir` 和 `samples[].image` 替换为真实或受控电梯 JPEG/PNG/WebP/BMP，覆盖门开、门关、轿厢内、轿厢外、目标楼层、safe/unsafe exit 和 bad-light/uncertain 类，再先跑 checker，只有 `can_run_opencv_eval=true` 后才跑 OpenCV eval。
- 本轮不提出新 KR；继续执行既有 `KR-O2-Real-Image-Manifest-Eval`，不需要改 `OKR.md`，但需要 Product/CEO 或现场 operator 决策图片采集来源和安全场地。
