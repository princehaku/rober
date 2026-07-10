# O1 Free-Cell Map Material Bundle Tech Done

## sprint_type

sprint_type: epic

## 已读资料

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/README.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/tech-plan.md`

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
  - 在现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1` 中新增 33-38 free-cell map material 默认输入和 CLI override。
  - 新增 free-cell lifecycle/list/YAML/PGM/pixel review/PC summary 解析和 fail-closed gates。
  - 新增 additive summary 字段：`free_cell_map_material_present`、`free_cell_map_lifecycle_present`、`free_cell_map_list_present`、`free_cell_map_yaml_present`、`free_cell_map_pgm_present`、`free_cell_pixel_review_present`、`free_cell_pixel_count=394`、`free_cell_has_free_cells=true`、`free_cell_usable_map_count=1`、`map_navigation_material_ready=true`。
  - 保持 `status=motion_map_hil_material_bundle_ready_not_hil_pass`、`proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`，并继续固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`map_navigation_ready=false`。
  - 输出层继续禁止 `source_base_url`、endpoint、absolute path、camera refs、raw runtime context、`/dev/tty`、baudrate、token/secret/password、traceback 和长 base64。
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
  - 新增正例断言覆盖 33-38 free-cell fields。
  - 新增缺失 free-cell pixel review、map list 不 usable、free count 不是 394、YAML/PGM basename mismatch、unsafe allowlisted value、dangerous true 的 fail-closed 回归。
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
  - 同步 free-cell material 输入、合同字段、fail-closed 规则、CLI negative override 和证据边界。

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
# pass, no output
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
................
----------------------------------------------------------------------
Ran 16 tests in 0.051s

OK
```

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
```

关键 positive 字段：

- `status=motion_map_hil_material_bundle_ready_not_hil_pass`
- `blocked_reasons=[]`
- `free_cell_map_material_present=true`
- `free_cell_map_lifecycle_present=true`
- `free_cell_map_list_present=true`
- `free_cell_map_yaml_present=true`
- `free_cell_map_pgm_present=true`
- `free_cell_pixel_review_present=true`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `free_cell_usable_map_count=1`
- `map_navigation_material_ready=true`
- `map_navigation_ready=false`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

负向 smoke 使用 `/tmp` 临时文件把 `37_fixed_free_cells_map_pixel_review.json` 的 free count 改为 `393` 后覆盖 CLI 参数：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle --free-cell-pixel-review-json /tmp/free-cell-review.XXXXXX.json
{
  "status": "blocked_invalid_motion_map_hil_material_bundle",
  "blocked_reasons": [
    "free_cell_pixel_review_count_sum_mismatch",
    "free_cell_pixel_count_not_394",
    "free_cell_pixel_review_counts_free_not_394"
  ],
  "free_cell_pixel_count": null,
  "free_cell_has_free_cells": false,
  "map_navigation_material_ready": false
}
EXIT_CODE=4
```

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle
# pass, no output
```

## 失败定位和修复

- 实现验证中没有出现单测或正例 CLI 失败。
- 首次尝试用 zsh wrapper 捕获负向 smoke 管道退出码时，`PIPESTATUS` 为空；定位为 shell wrapper 写法问题，不是模块行为问题。改用 `bash -lc` 后负向 smoke 正确返回 `EXIT_CODE=4`。
- 负向 smoke 检查时发现 rejected free-cell review 仍在顶层输出 bad count `393`；已修复为只有 valid pixel review 才输出顶层 `free_cell_pixel_count` 和 `free_cell_has_free_cells`。

## 剩余风险

- 本轮仍是 historical same-run software proof，只证明 2026-06-22 free-cell map materials 33-38 被安全接入。
- 不证明 current live HIL、hardware safe-to-control、delivery success、wheel direction、IMU/battery calibration、Nav2 route execution success、production cloud 或 current live map navigation readiness。
- 下一步 O1 需要 current live 同 run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance record，并用 free-cell map material 接 Nav2/定位路线 proof。

## 完成时间

- 2026-07-10 19:43:35 CST
