# Cloud Phone Command API Mainline Tech Done

## sprint_type: epic

## 实际改动

### Task A：Robot Software Engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `cloud_phone_command_api` 常量和 `software_proof_docker_cloud_phone_command_api_gate` 边界。
  - 新增 `normalize_phone_command()`，将 `/api/commands/collect`、`/api/commands/confirm-dropoff`、`/api/commands/cancel` 的手机请求收敛成既有 `collect` / `confirm_dropoff` / `cancel` command store 合同。
  - 新增 `phone_command_receipt()`，返回 phone-safe queued receipt，固定 `ack_semantics=queued_not_delivery_success`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
  - `do_POST()` 增加 bearer-gated `/api/commands/*` 分支，复用现有 `store.submit_command()`，不破坏 robot polling、status、ACK。
  - 新增 command store 写入失败 fail-closed hardening：当 `store.submit_command()` 不可用或写入失败时，API 返回 `503 command_store_unavailable`，不返回 queued receipt，避免手机端把未入队命令误读为已排队。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖 collect / confirm-dropoff / cancel、auth failed、bad request、receipt not delivery success、command store unavailable fail-closed、敏感/control 字段不外泄。
- `docs/product/remote_4g_mvp.md`、`docs/product/cloud_4g_infrastructure.md`、`cloud-relay/README.md`
  - 同步 phone command API、receipt 语义、false-state 和真实云缺口。

### Task B：User Touchpoint Full-Stack Engineer

- `mobile/web/app.js`
  - 主动作 endpoint 切到 `/api/commands/collect`、`/api/commands/confirm-dropoff`、`/api/commands/cancel`。
  - 提交体新增 `trashbot.cloud_phone_command_api_request.v1` envelope。
  - 新增 `cloudPhoneCommandReceiptPanel`，只展示 sanitized queued receipt，明确“已入队/等待机器人处理，不是送达成功”。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 新增 `cloud_phone_command_api` targeted tests。
- `mobile/web/fixtures/robot_diagnostics_cloud_phone_command_api.json`
  - 新增 phone-safe queued receipt fixture。
- `docs/product/mobile_user_flow.md`
  - 同步手机端 API、receipt 文案和敏感信息边界。

## 验证结果

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# 通过，无输出
```

```text
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_phone_command_api
....
Ran 4 tests in 2.769s
OK
```

```text
node --check mobile/web/app.js
# 通过，无输出
```

```text
PYTHONPATH=mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_phone_command_api
..
Ran 2 tests in 0.048s
OK
```

```text
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md cloud-relay/README.md mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.26_00-01_cloud-phone-command-api-mainline
# 通过，无输出
```

## 偏差

- Product worker 超时前未及时落盘，主节点按白名单先补 sprint `pre_start.md`、`prd.md`、`tech-plan.md`，随后 Product worker 返回同一范围验证通过。
- Full-Stack worker 未改 PC workstation；本轮用户触点落在 `mobile/web`，满足至少一个触点调用任务级 command API 的验收口径。
- Robot Software 在原主链路验收后追加了 command store unavailable hardening，属于同一 `cloud_phone_command_api` 安全边界增强；Product closeout 已把验证证据从 `Ran 3 tests` 更新为 `Ran 4 tests in 2.769s OK`。
- 既有 `.idea/rober.iml` 在本轮开始前已是 dirty，本轮未纳入提交范围。

## 剩余风险

- 本轮仍是 Docker/local software proof，不证明公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery success。
- Queued receipt 只表示命令入队等待机器人轮询，不表示机器人已执行、投放完成或取消完成。
- `command_store_unavailable` 已 fail closed，但真实 production DB/queue 的连接池、持久化、重试、告警和多实例一致性仍未验证。
- 下一轮需要把该 API 接到真实部署和外部证据链，或至少做 command lifecycle result reconciliation。
