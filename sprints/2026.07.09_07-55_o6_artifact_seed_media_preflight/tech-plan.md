# O6 Artifact Seed Media Preflight Tech Plan

## 范围

本轮是 O6 主责、O7 消费的双 owner epic。写集拆分如下，避免并行冲突：

- `robot-software-engineer`：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`、`docs/interfaces/o6_cloud_archive_api.md`。
- `full-stack-software-engineer`：`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`、`pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`、`docs/product/pc_tools_workstation.md`。
- 主节点只整合 sprint 留档，不直接写产品代码、测试代码或业务实现。

## 技术方案

### O6 artifact seed/readback

- 在 O6 local/mock archive 中增加或增强 artifact seed/readback 摘要，输入来源为 field evidence manifest 或同等本地 artifact bundle 摘要。
- 输出必须绑定 `task_id`，保留 trajectory frame count、event/evidence ref count、keyframe/media ref 摘要、artifact accessibility/preflight 状态和 blocked reasons。
- 所有绝对路径、credential URL、token、base64、raw media、串口和控制字段必须脱敏或拒绝。
- 成功响应和 consumer detail 仍固定危险能力为 false。

### O7 media/artifact consumer

- O7 consumer detail 从 O6 detail 主路径读取 artifact/media 状态，派生用于 route replay 与 labeling 的 media preflight section。
- UI 显示 media refs 的可用性摘要、缺口和 next evidence，不把 ref 字符串误报为真实媒体可访问。
- 对危险 true 字段、未知 schema、unsafe copy 继续 fail-closed。

## 接口影响

- 不破坏现有 `/api/o6/archive/field-evidence`、`/api/o6/consumer/tasks/<task_id>`、O7 annotation submit/export 合同。
- 新增字段只能 additive；旧 consumer 缺字段时继续 blocked/not_proven。
- 所有真实能力字段保持 false。

## 验收命令

`robot-software-engineer` 必须运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

`full-stack-software-engineer` 必须运行：

```bash
cd pc-tools/workstation && npm run test -- catalog.test.ts
cd pc-tools/workstation && npm run test -- App.test.ts
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

收口必须验证：

```bash
git diff --check
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节 active Objective 中最低完成度是 O6（约 36%），其次是 O7（约 37%）。本 sprint 直接针对 O6，并让 O7 消费同一条证据链；符合最低优先级推进要求。

## 风险边界

- 本轮仍不证明真实生产 DB/queue、OSS/CDN、TLS/4G、真实隧道、真实机器人数据或生产级查询容量。
- 本轮仍不证明真实 keyframe/media 可访问、真实 annotation API、真实 dataset export、真实 RTC/视频、ASR/TTS、wheel raw 非零或完整送达。
- 如果验证失败，owner 必须定位、修复并复验，不能把第一轮失败作为最终结果。
