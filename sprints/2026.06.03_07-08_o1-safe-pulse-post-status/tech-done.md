# O1 Safe Pulse Post-Status Micro Sprint

## sprint_type

micro

## 目标

本轮推进 O1 最低 Objective 的现场短 pulse 证据采集能力，但不执行无人运动命令、不打开真实串口、不引入 pyserial、不发送 `T=130/T=131/cmd_vel`。目标是让 `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py` 在未来人工看护执行模式下能把 manual、extra stop 和后置 status 放进同一份机器 artifact，并用 `acceptance_verdict` fail-closed 收口。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 已证实的硬件结论

- WAVE ROVER vendor reference 使用 UART、UTF-8 JSON、每行一个 JSON object 并以 `\n` 结束。
- `T=1` 是左右轮速度命令，`T=130` 是 base feedback request，`T=131` 是 feedback flow 控制，`T=1001` 是 base feedback。
- vendor Raspberry Pi reference 的 `/dev/ttyAMA0 @115200` 不能直接外推到 Orange Pi；本项目当前现场控制口结论仍以已记录的 `/dev/ttyS5 @115200` 为边界。
- 本轮没有新增真实串口事实，不能证明 ACK、`T=1001`、真实 `/odom`、`/imu/data`、`/battery` 或 HIL pass。

## 实际改动

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
  - 执行模式在 `/api/base/manual` 与额外 `/api/base/stop` 后新增一次 `GET /api/status`。
  - 新增 `post_status_request`、`post_status_summary`、`post_t1001_feedback_status`。
  - 新增 `acceptance_verdict`，区分 `dry_run_only`、`blocked_before_motion`、`motion_posted_without_ack`、`motion_posted_with_t1001`。
  - 初始 status 失败会在 motion 前阻断；manual/stop/post-status 任一步失败都会 fail-closed 并保留 `failed_step`。
  - 全程保持 `safe_to_control=false`、`hil_pass=false`、`delivery_success=false`。
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
  - 增加 fake HTTP 覆盖 post-status、T=1001 verdict、初始 status 失败阻断、stop 失败 fail-closed。
  - 更新执行模式调用序列断言：`GET status -> POST manual -> POST stop -> GET status`。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 增加 O1 safe pulse post-status acceptance 字段、顺序和 verdict 边界。
- `docs/interfaces/o7_upper_robot_api.md`
  - 更新 O1 Safe Pulse Acceptance Runner 的执行后 status 和 `acceptance_verdict` contract。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 更新 O1 90% 边界：post-status 和 verdict 只能作为 HIL packet 前置材料，不能替代真实 HIL。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
```

结果：exit 0。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
```

结果：

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.063s

OK
```

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --once-json | python3 -m json.tool >/tmp/o1_safe_pulse_post_status_dryrun.json
```

结果：exit 0。本机默认 8787 不可达，artifact fail-closed：

```text
schema=trashbot.o1.ttyS5_safe_pulse_acceptance.v1
acceptance_verdict.status=blocked_before_motion
acceptance_verdict.failed_step=status_request
safe_to_control=false
sends_commands=false
manual_request=null
stop_request=null
```

```bash
git diff --check -- onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o7_upper_robot_api.md docs/interfaces/o1_o5_90_evidence_boundary.md sprints/2026.06.03_07-08_o1-safe-pulse-post-status/tech-done.md
```

结果：exit 0，无输出。

## 是否发送运动命令

否。本轮未 POST `/api/base/manual`，未 POST `/api/base/stop` 到远端，未打开 `/dev/ttyS5`，未发送 `T=1/T=13/T=130/T=131/cmd_vel`。

## 剩余风险和下一步

- `acceptance_verdict.status=motion_posted_with_t1001` 仍不是 HIL pass，只能作为 HIL packet 前置材料。
- 真实 HIL 仍缺至少两帧同源 `T=1001`、ROS `/odom`、`/imu/data`、`/battery`、operator report、急停/停车路径证据。
- 下一步必须在现场人工看护、物理净空、急停/断电路径可用时，再由 operator 明确授权执行短 pulse，并保存同源 artifact；缺 ACK 时仍保持 `safe_to_control=false`。

## Product closeout / OKR verdict

用户价值：本轮把 O1 的受控短 pulse 验收从“可以发 manual/stop”推进到“执行前 status、manual、stop、执行后 post-status 和 verdict 同源归档”，降低现场人工看护执行时漏采 ACK/`T=1001` 或误判安全状态的风险。产品北极星仍是普通手机用户可用的垃圾投递机器人；O1 的价值不是单次点动，而是底盘控制证据可被现场安全、PC/ROS 状态和后续 HIL 验收复用。

OKR 映射和方向判断：Objective 1 继续，仍是当前最低 Objective，进度保持约 93%，不上调 HIL。`post_status_request`、`post_status_summary`、`post_t1001_feedback_status` 和 `acceptance_verdict` 是 watched execution 前置材料，不是 HIL pass、不是 `safe_to_control=true`、不是真实 ROS `/cmd_vel` 接入，也不是 delivery success。

KR 拆解和历史归档：本轮增强 O1 KR3/KR4/KR5 的验收证据合同和 fail-closed 逻辑，但没有完成真实反馈/ACK KR，因此没有 KR 进入完成历史归档。历史记录位置为本文件、`OKR.md` 第 4/4.1/5 节，以及可选追加的 `docs/process/okr_progress_log.md`。

本轮核心抓手：把下一轮现场短 pulse 的验收口径固定为 `GET status -> POST manual -> POST stop -> GET post-status`，并用 `acceptance_verdict` 区分 `dry_run_only`、`blocked_before_motion`、`motion_posted_without_ack`、`motion_posted_with_t1001`。初始 status 失败必须阻断 motion；manual/stop/post-status 任一步失败必须 fail-closed。

需要做什么：下一轮由 Hardware Infra Engineer 在现场人工看护、物理净空、急停/断电路径可用时，明确授权后经 8787 `/api/base/manual` 执行低速短 pulse，并保存同源 artifact；若缺 ACK 或 `T=1001`，仍保持 `safe_to_control=false` 并记录为 feedback not_proven。

优先级和验收口径：P0 继续 O1 watched field pulse execution + ACK/`T=1001` capture。可接受证据至少包括 status/manual/stop/post-status 同源 artifact、自动 stop 或人工 stop 复位证据、operator report、急停路径说明，以及 ACK 或 `T=1001` 观察结论；没有这些证据不得写 HIL pass。

对应责任 Engineer：Hardware Infra Engineer 主责下一轮现场短 pulse 与反馈采集；Robot Software Engineer 只在需要把真实反馈接入 ROS `/odom`、`/imu/data`、`/battery` 或 `/cmd_vel` 验证时介入。

风险、阻塞和证据链缺口：本轮未发送运动命令，未 POST 远端 `/api/base/manual` 或 stop，未打开 `/dev/ttyS5`，未发送 `T=1/T=13/T=130/T=131/cmd_vel`。真实 `T=1001`、ACK、HIL packet、真实 ROS topic、自动停车/急停现场演练和完整 delivery success 仍 `not_proven`。

需要创建或更新的 sprint 文档：本 micro sprint 已更新 `tech-done.md`；本轮不需要补 epic 六文档。OKR 收口同步更新 `OKR.md`，并可在 `docs/process/okr_progress_log.md` 追加历史摘要以保持 OKR 主体可读。
