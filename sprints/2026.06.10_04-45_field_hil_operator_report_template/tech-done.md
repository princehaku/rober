# Field HIL Operator Report Template

sprint_type: micro

## 实际改动

- 新增 `docs/hardware/field_hil_operator_report_template.md`，把现场 operator report
  的填写项、JSON payload、`curl` 提交命令、readback 命令和 fail-closed 回包要求整理成
  可执行模板。
- 更新 `docs/hardware/field_hil_execution_pack.md`，把 `/api/operator/report`
  明确接入现场 HIL artifacts intake，并声明它只收人工材料，不能替代 stop、ACK、
  `T=1001`、HIL 或 motion proof。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，删除重复且路径过粗的
  WAVE ROVER Min Actuation Probe 复跑补证段，并新增 operator report 模板入口。

## 验证结果

- 已只读核对 `AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 和
  `onboard/scripts/upper_robot_api.py`。
- 已确认 `upper_robot_api.py` 中 `/api/operator/report` 只写
  `runtime/operator_report_latest.json` 或配置路径，返回
  `operator_report_material_only=true`、`sends_motion_commands=false`、
  `opens_serial=false`、`hil_pass=false`、`delivery_success=false` 等 guard。
- JSON 示例已用 `python3 -m json.tool` 通过解析；临时文件写在 `/tmp`，未留在仓库。
- `git status --short --branch` 输出：

```text
## master...origin/master
 M docs/hardware/board_sensor_stack_smoke.md
 M docs/hardware/field_hil_execution_pack.md
?? docs/hardware/field_hil_operator_report_template.md
?? sprints/2026.06.10_04-45_field_hil_operator_report_template/
```

- 指定 `rg` 验收命令已覆盖 `operator report`、`/api/operator/report`、
  `visible_content_proven`、`physical_motion_lidar_delta_proven`、
  `wheel_feedback_lr_nonzero_proven`、`delivery_success` 和
  `operator_report_material_only`，命中本轮新增模板、execution pack、sensor smoke、
  micro sprint 留档和 `onboard/scripts/upper_robot_api.py`。
- JSON 示例解析命令通过：

```text
python3 -m json.tool /tmp/field_hil_operator_report_payload.json
```

- 只读 SSH 检查通过，未运行运动命令：

```text
op-z3-b6.home
Wed Jun 10 04:17:13 AM CST 2026
active
```

- 额外运行 `git diff --check`，无输出，表示本轮改动未发现 whitespace error。

## 剩余风险

- 本轮只做文档和 micro sprint 留档，未执行真实 HIL、未发送 `/cmd_vel`、未发送 direct
  `T=1`，也未修改远端系统配置。
- 当前 `/api/operator/report` normalizer 只持久化核心字段；细分布尔值必须写入
  `operator_notes` 的结构化文本。后续若要把这些布尔值作为一等字段查询，需要另起软件任务修改 API schema。
- operator report 仍是人工材料入口，不能单独证明 `visible_content_proven`、
  `physical_motion_lidar_delta_proven`、`wheel_feedback_lr_nonzero_proven`、
  `real_route_map_proven` 或 `delivery_success`。
