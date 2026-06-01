# O5/O6 External Probe Artifact UI 验收

- sprint_type: micro
- owner: full-stack-software-engineer
- 时间: 2026-06-01 23:00-24:00
- 范围: 只验收和最小修复 O5/O6 external live probe artifact、PC workstation 脱敏摘要 UI/API、Python stdlib runner `--output` 落盘能力。

## 实际改动

- 验收上一轮 full-stack 改动，确认 Python runner 支持 `--output` 输出同一份脱敏 `trashbot.o5_o6.external_live_probe.v1` artifact。
- 验收 PC workstation 新增 `GET /api/o5-o6/external-probe-artifact`，该 API 只读取本地 artifact 摘要，不执行 probe、不联网、不访问 `/robots/*`、不读取硬件、不回显 token/raw URL/path/traceback。
- 验收 O7 Console 中新增 External Probe Artifact 展示，展示最近一次 probe 的 `probe_status`、runner、endpoint reachability、blocked reasons 和 fail-closed safety fields。
- 最小修复 `pc-tools/workstation/test/App.test.ts` 中过宽的泄漏断言：O7 Previews 页本身会展示既有 loopback 只读探针 URL，因此把 `http://127.0.0.1` 不泄漏断言收窄到 `/api/o5-o6/external-probe-artifact` fixture/contract。
- 2026-06-02 00:21 CST 复核时追加收紧 PC artifact API：endpoint 摘要只展示固定 allowlist path，剥离 `?baseUrl=...` query，避免编码后的 raw URL 进入 O7 Console；同时把 PC API 自身的 `no_post`、`no_robot_control`、`no_hardware_read` 策略固定为 true，不再透传 artifact 内部声明。
- 追加 `pc-tools/workstation/test/catalog.test.ts` 覆盖 PC aggregate endpoint 携带编码 `baseUrl` 时不回显 `baseUrl=`、`http%3A%2F%2F` 或 raw host。
- 未修改 `OKR.md`，未覆盖 hardware agent 的 O1 文档/sprint 改动，未新增真实控制、POST、`/robots/*` 访问、硬件读取或 ACK 写入路径。

## 验证结果

1. `python3 -m py_compile cloud-relay/scripts/o5_o6_external_live_probe.py`
   - 结果: 通过，退出码 0。
2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest cloud-relay/tests/test_o5_o6_external_live_probe.py`
   - 结果: 通过，复跑为 `Ran 5 tests in 3.026s`，`OK`。
   - 说明: unittest 期间脚本 stdout 输出一次缺 URL/token 的结构化 `probe_status=fail_closed` JSON，属于测试覆盖的一部分，不代表真实云或真实 4G 已接通。
3. `cd pc-tools/workstation && npm run build`
   - 结果: 通过，Vite 输出 `dist/index.html`、`dist/assets/index-RjWv-c7_.css`、`dist/assets/index-DHOyjc_j.js`，退出码 0。
4. `cd pc-tools/workstation && npm run test`
   - 首轮结果: 失败，`test/App.test.ts` 的 O7 Previews 用例要求页面全文不包含 `http://127.0.0.1`，但该页既有 O7 只读 probe 明确展示 loopback base URL。
   - 修复后结果: 通过，复跑为 `Test Files 2 passed (2)`，`Tests 53 passed (53)`。
5. `cd pc-tools/workstation && npm run lint`
   - 结果: 通过，退出码 0，无 ESLint 输出。
6. scoped `git diff --check`
   - 结果: 通过，退出码 0，无 whitespace error 输出。

## 用户旅程变化和触点收益

- 运维人员能在 PC workstation O7 Console 上直接看到最近一次 O5/O6 external live probe 的脱敏摘要，不需要 SSH 后手工打开 artifact 文件。
- 失败原因以 `blocked_reasons`、endpoint reachability 和 fail-closed safety fields 呈现，能区分未配置、网络/服务不可达、schema drift 和 unsafe true field，不把失败藏成空白页。
- UI 只消费后端产出的脱敏契约，不在浏览器侧拼接 raw base URL、token 或 artifact path，保持普通用户/运维触点和真实控制面隔离。

## 接口影响

- Python CLI: `cloud-relay/scripts/o5_o6_external_live_probe.py` 新增 `--output <path>`，把 stdout 同 schema 的脱敏 JSON 额外写入调用方指定路径。
- PC API: 新增只读 `GET /api/o5-o6/external-probe-artifact`，响应 schema 为 `trashbot.pc_tools_workstation.o5_o6_external_probe_artifact.v1`。
- PC client snapshot: `loadWorkstationSnapshot()` 新增拉取 `o5O6ExternalProbeArtifact`，并在 O7 Console 展示摘要。
- 文档同步: `cloud-relay/README.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/o6_cloud_archive_core_api.md`、`docs/interfaces/o1_o5_90_evidence_boundary.md` 已记录 `--output` 和 PC artifact summary 边界。

## 前后端 / ROS2 联调结果

- 前端: Vitest 覆盖 O7 Console 展示 artifact summary，以及不出现 `Bearer`、`/cmd_vel`、artifact raw URL/path 泄漏。
- 后端: catalog test 覆盖 artifact API 读取 env 指定 JSON、过滤 raw base URL 和本地 path、固定 no-post/no-hardware-read/no-control 字段。
- cloud-relay: Python unittest 覆盖 `--output` 写入同一份 fail-closed 脱敏 artifact。
- ROS2/硬件: 本轮没有接入 ROS2 topic/action/service，没有读取硬件，没有真实发车或 ACK 写入；所有结论仅为 O5/O6 software/fail-closed evidence。

## 剩余风险

- 真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser、机器人 ACK 和 delivery success 仍为 `not_proven`。
- artifact 的可信度取决于调用方是否把 Python runner 的 `--output` 写入 PC workstation 可读取位置；缺文件或坏 JSON 会 fail closed 显示为未加载。
- 本轮仅修正验证发现的测试断言问题，没有扩大 O5/O6 功能范围，也没有推进真实云/真实上车材料。
