# PRD：O1 轮速反馈根因诊断

## 产品问题

当前真实链路已证明键盘/Upper/bridge 能把非零意图送成 `T=11 L=164 R=164`，但同窗 `T=1001` 的 `L/R` 仍为
`0/0`。继续运动重采会重复消费已封存的 v8 slice；直接修改 service、UART 或 firmware 又超出本轮授权。需要一个可复验的
诊断能力，把 vendor firmware 分支、项目 bridge/parser、v8 证据与当前只读 runtime inventory 合并为明确的假设排序和下一
维护动作。

## 北极星与 OKR 映射

- 北极星：可信、安全、可解释的真实底盘控制与反馈闭环。
- Objective：O1，当前约 95%。
- 本轮抓手：关闭“为何真实 command 非零而 `T=1001 L/R=0/0`”的诊断盲区。
- 进度口径：本轮默认是 supporting diagnostic capability，主百分比保持 flat；只有新增当前外部事实类别并经 Product 验收，
  才能另行判断，不得由 Engineer 自行加分。
- KR：不归档；`hil_pass=false`、`safe_to_control=false`、route/delivery/Mission Objective 0 均保持 false。

## 功能需求

1. 提供 Python 模块/CLI，读取 v8 `acceptance_summary.json`、`during_motion_t1001.json`、
   `live_bridge_command_delta.jsonl`、`live_bridge_feedback_delta.jsonl` 与 vendor source roots。
2. 明确验证 vendor facts：`FEEDBACK_BASE_INFO=1001`、`T=11` PWM、`T=13` encoder 限制、`T=130/131` feedback、
   `mainType` 分支、`speedGetA/speedGetB` 的赋值/采样来源；事实必须带 source path 与行/符号定位。
3. 输出 schema `trashbot.wave_rover.feedback_root_cause_diagnostic.v1`，至少包含输入 hash/计数、已证事实、未证事实、
   parser/transport 一致性、root-cause candidates、优先级、maintenance requirement 与 next action。
4. 分类必须 fail closed：至少区分 `runtime_main_type_not_observed`、`runtime_firmware_identity_not_observed`、
   `encoder_update_path_not_observed`、`feedback_sampling_alignment_not_proven`、`bridge_parser_consistent_with_vendor_frame` 与
   `artifact_inconsistent_or_invalid`。不得把源码推断写成当前板已验证。
5. 输入缺失、hash/identity 冲突、非法 JSON/JSONL、危险真值或 v8 count 不一致必须返回非零；诊断成功可以返回 `0`，但
   顶层仍固定 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`。
6. 若上位机可达，生成严格只读 inventory，记录现有 service/process 启动参数、bridge 相关 ROS 参数/日志或已部署源码 hash；
   只读证据不足时保留 `not_observed`，禁止尝试修复或重启。
7. 更新硬件文档，解释 vendor 分支、诊断命令、结果边界和下一维护窗口所需动作。

## 非功能需求

- 全部技术注释为中文，新增代码有意义中文注释比例超过 20%。
- 输出不得泄露凭证、完整主机路径、环境变量或 raw secret；artifact 引用使用安全相对路径或 basename/hash。
- CLI 对同一输入输出稳定；排序固定；不得依赖网络才能完成离线回归。
- 不引入新第三方依赖；优先标准库。

## 验收口径

- vendor-source fixture 与 v8 artifacts 能生成诊断 JSON，schema/安全字段/候选顺序稳定。
- hostile/missing/inconsistent fixtures fail closed 且 exit 非零。
- 只读上位机 inventory 若执行，写清命令类别和零 mutation 计数；不可达也要留下真实 transport 结果。
- 目标单测、py_compile、CLI smoke、JSON/JSONL parse、中文注释比例和 scoped diff check 全部通过。
- `tech-done.md` 必须记录实际改动、命令输出、首次失败与修复、剩余风险；不得复用 v8 motion authorization。

## 风险与拒绝项

- vendor 源码只能说明参考固件行为，不能证明板上实际 binary 与源码相同。
- 只读 runtime 参数可能无法暴露 `mainType` 或 firmware build identity；此时结论必须停在需要维护窗口的具体 probe/patch。
- `bridge_debug_serial_derived` 不是 byte-for-byte raw UART；parser 一致性不等于 firmware/encoder 正确。
- 本轮拒绝任何运动、服务变更、UART 抢占、固件写入、自动重试和 OKR 百分比包装。
