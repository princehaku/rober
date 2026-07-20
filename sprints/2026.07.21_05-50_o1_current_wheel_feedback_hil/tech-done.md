# O1 当前轮速反馈 HIL 执行记录

- `sprint_type: epic`
- owner: `robot-hardware-engineer`
- authorization: `ceo_20260721_0651_current_wheel_feedback_hil_v8`
- final authorization status: `consumed_no_retry`
- result: `FAIL_CLOSED_AFTER_SINGLE_NONZERO_ATTEMPT`

## 实际改动与执行

live 执行阶段只创建本 sprint 的 `artifacts/**`、`tech-done.md`、`side2side_check.md`、`final.md`。Product 随后以 `PRODUCT_CLOSEOUT=ACCEPT_REAL_ATTEMPT_HIL_FAIL_CLOSED_FINAL_STOP_PROVEN` 验收；本次 docs sync 仅更新 `docs/hardware/wave_rover_nonzero_feedback_hil_gate.md` 和本文件，把 offline software gate 与 v8 live evidence 的关系、exact slice 退役和下一诊断入口同步到硬件文档。未修改远端文件、service、holder、产品代码、OKR、progress log 或其他 owner WIP。

Phase0 只读执行 `systemctl/ps/ss/lsof/fuser`、GET health/base/latest/Nav2、部署源码 hash/合同读取、`ROS2CLI_NO_DAEMON=1 ros2 topic info /cmd_vel --verbose`。确认 Upper/bridge active、8787 ready、`/dev/ttyS5` 唯一 owner 为 bridge、`/cmd_vel` 唯一 subscriber 为 `/esp32_bridge`、无 publisher/连接、当前 `T=1001 L/R=0/0`、Nav2 stopped。随后按 frozen request 执行：

1. pre-stop `POST /api/base/stop`：1 次，curl exit `0`；
2. nonzero `POST /api/base/manual`：stdin `--data-binary @-`，`0.08m/s`、`300ms`，仅 1 次，curl exit `0`；
3. dedicated post-stop `POST /api/base/stop`：1 次，curl exit `0`；
4. `retry=0`，未重放 nonzero。

Upper nonzero response证明 `/cmd_vel` 6 帧、subscriber count `1`，bridge 同窗记录 6 帧 `T=11 L=164 R=164 sent=true`；但运动窗 3 个直接对齐的 `source=wave_rover_uart_t1001` 帧及 response 80 帧汇总全部 `L/R=0/0`。dedicated stop 后 bridge 最新命令为 `T=11 L=0 R=0 sent=true`，post-stop `T=1001 L/R=0/0`，无 8787 连接。

## Vendor 来源与证实结论

已读 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`uart_ctrl.h`、`ugv_advance.h`、`movtion_module.h`、`ugv_rpi/base_ctrl.py`。采用事实：`T=13=CMD_ROS_CTRL`；`T=130=CMD_BASE_FEEDBACK`；`T=1001 L/R` 来自 `speedGetA/speedGetB`；UART 为 UTF-8 newline JSON。

本次实际 bridge wire-side command debug 是 `T=11`，没有 byte-for-byte raw command capture，因此 `T=13 wire not proven`。反馈证据是 bridge 解析的串口源 debug（`source=wave_rover_uart_t1001`），不是原始字节 dump。由于 bridge 持有 UART，本次走 continuous `T=131` feedback flow，Upper 明确记录 direct `T=130` 未执行，故 `T=130 request not proven`。

## 验证结果与失败定位

- JSON：全部 artifact JSON 可 parse；JSONL 每行可 parse。
- exactly-once：`pre/nonzero/post/retry=1/1/1/0`，authorization=`consumed_no_retry`。
- 计划中的 phase0/response/authorization/post-stop assertions 通过。
- 计划的 during-motion nonzero `T=1001` assertion 真实失败；发生在唯一 nonzero 已发送之后，证据为 `during_motion_t1001.json L=0 R=0`。
- final stopped assertion 通过；`git diff --check` 通过。

## 剩余风险

`hil_pass=false`：当前 encoder wheel feedback 仍未随已发送 PWM 非零。可能是 encoder/firmware mainType/反馈字段链路问题，不能在 v8 下重试。`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`；一次 IMU 变化不替代轮速 HIL。下一轮必须新授权，并先由 Hardware 查清为何实际运动命令存在而 `speedGetA/speedGetB` 始终为零。

本次文档同步没有执行 SSH、HTTP、ROS、串口、control、stop、nonzero 或其它 live 命令；既有 `1/1/1/0` 计数、`consumed_no_retry`、during `T=1001 0/0` 和 final stopped 结论均未改变。
