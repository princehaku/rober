# Side-to-side Check - O5 Provider Runtime Preflight Stage Diagnostics

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/`
- Product owner：`product-okr-owner`
- Delivery owner：`full-stack-software-engineer`
- Product status：`accepted_offline_stage_diagnostics_contract_no_okr_credit`
- Proof boundary：`software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`

## 用户价值与 Product 判断

部署/验收人员现在能用脱敏 stage 前缀定位 download、SHA、chmod、version 的离线失败边界，不再只能看到整体 exit `1`。这降低了下一次决策靠盲目 live 重跑的风险，符合“可验证地可靠交付”的北极星；但它没有改善普通手机用户的真实公网可用性。

Product 接受离线 stage diagnostics contract、18 tests 的有效双入口证据、dry artifact 与稳定接口文档；拒绝把这些事实解释成真实 provider runtime、public HTTPS、production ready、Mission Objective 0 或 OKR credit。

## 事实源核对

已核对本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、实现、18 个 `test_*` 列表、dry artifact、`docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md`，并参考上一轮 09-04 `final.md`。Product artifact 为 `artifacts/product_acceptance_provider_runtime_preflight_stage_diagnostics.json`。

## 计划与实绩对照

| Gate | 计划口径 | 当前事实 | Product 判断 |
| --- | --- | --- | --- |
| schema | 固定 v1 schema 与白名单 | `trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1`，白名单字段稳定 | accepted |
| stage 顺序 | 七阶段单调、有序前缀 | `download_started -> download_completed -> sha_command_completed -> sha_matched -> chmod_completed -> version_executed -> version_matched` | accepted |
| failure matrix | 六个步骤失败 + invalid transition fail closed | 18 tests 覆盖逐阶段失败、hostile metadata、runner/path、危险 true claim 与脱敏 | accepted |
| offline dry gate | 本地 fixture/stub，无外部动作 | status=`passed_offline_dry_gate`，7 stages 完成，official contract checked=true | accepted as offline-only |
| stable docs | schema/stage/failure/脱敏/proof boundary 同步 | 接口文档完整，明确 offline-only 与禁止 SSH/tunnel/public/robot control | accepted |
| test command | 计划 unittest 命令通过 | 原计划含点路径命令 exit `1`，`ModuleNotFoundError: No module named 'sprints.2026'`，测试文件未加载 | deviation retained |
| effective tests | 实际加载全部测试 | 直接文件入口和 `unittest discover` 均 `Ran 18 tests ... OK` | accepted as sufficient regression evidence |
| comments | 两个 Python 文件中文注释严格 `>20%` | 实现 `21.5%`，测试 `21.1%` | accepted |
| external/live | 不得执行 | SSH/network/tunnel/public/control 均未执行，所有计数/delta/safety false | accepted boundary, not mission evidence |

## 计划命令偏差

原计划命令 `python3 -m unittest <含点 sprint 路径/test.py>` 的真实结果是 exit `1`，错误类型为 `ModuleNotFoundError`。根因是 unittest 在加载测试文件前把 `sprints/2026.07...` 转换成非法模块路径 `sprints.2026...`，不是 18 个 test case 中任一用例失败。

Product 不掩盖该 exit `1`，也不把失败命令改写为通过。接受测试证据的依据是两个有效入口都实际加载同一测试文件并分别输出 `Ran 18 tests ... OK`：直接文件入口与 canonical `unittest discover`。未来含点 sprint 路径的计划不得继续使用该 `-m unittest <path>` 形态。

## Product 接受项

1. accepted：七阶段单调状态机、固定 failure enums、白名单 artifact、local runner 与 offline dry gate。
2. accepted：dry artifact schema/status/proof boundary、七个 stages、全部 delta/control=false。
3. accepted：稳定接口文档与实现/测试一致。
4. accepted：py_compile exit `0`、两个有效入口各 18 tests、CLI/JSON/结构脱敏断言、中文注释 `21.5%/21.1%`、rg/diff check。

## Product 拒绝项

- 拒绝真实 official binary download/SHA/chmod/version、上一轮 live exit `1` 已定位、SSH/remote runtime、tunnel/public URL、TLS/certificate、GET/HEAD 或公网负向矩阵。
- 拒绝 `current_run_artifact_delta=true`、`external_artifact_delta=true`、`live_control_delta=true`、`user_action_delta=true`。
- 拒绝 production ready、Mission Objective 0、route execution、delivery、HIL、safe-to-control、O5 score lift 或 KR 归档。

固定结论：四个 delta=false，`production_ready=false`、`mission_objective_0_satisfied=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

## OKR / KR 与 blocker 决策

- O5 保持约 `85%`，O1 约 `94%`、O6/O7 各约 `93%` 保持；本轮 `okr_credit=false`。
- KR `不归档`；没有已完成 KR 移入历史区。证据只进入当前 OKR 记录与进度日志。
- 本轮是同一 `provider_runtime_preflight` blocker 的第二轮、最后一轮消费。
- 下一轮必须切换 Objective，或升级 CEO 决策；禁止第三轮 O5 wrapper、diagnostic 或 live 重跑。只有 CEO 明确决策才能重新定义后续方向，不能由本 sprint 自动授权。
