# PC Tools Node/Vue Workstation Final

## sprint_type

epic

## 收口结论

本轮完成 `pc-tools/workstation/` 第一阶段 PC-only Node.js + Vue 工作站。工作站提供 Route Debug、Evidence Tools、Training/Labeling、Proof Boundary 四个统一入口，并保持所有 API/UI fail closed。

当前本地服务已启动：

```text
http://127.0.0.1:8787
```

该入口只代表 PC 本地软件证明，不代表机器人在线、可控制或真实交付成功。

## 验证证据

- `npm install`：通过。
- `npm run build`：通过，Vite 产出 `dist/index.html`、CSS、JS，server TypeScript 编译通过。
- `npm run test`：通过，2 个 test file、5 个 test。
- `npm run lint`：通过。
- `python -m unittest discover pc-tools/route -p "test_*.py"`：通过，7 tests OK。
- `GET http://127.0.0.1:8787/api/health`：返回 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。

## OKR 回顾

本轮响应 CEO 指定的 PC tools 工作站重构，主要对齐 Objective 3 的 PC route debug、路径学习工具和训练/标注入口骨架。Objective 5 仍未产生外部真实材料、云端、4G、OSS/CDN 或真实手机证明，因此不得提升 Objective 5 完成度。

## 流程说明

本轮实现范围集中在 `pc-tools/workstation/**`、`docs/product/pc_tools_workstation.md` 和本 sprint 收口文档；其他 owner 没有独立可改文件面。实现阶段按单 owner 闭环执行，未改动旧 Python gate、硬件、ROS2 或云端目录。

## 剩余风险

- 未证明真实 ROS2、Nav2/fixed-route、真实路线采集、关键帧实景、真实电梯、WAVE ROVER、serial/UART feedback、HIL pass、dropoff/cancel completion、delivery success 或安全控制。
- 未证明真实手机/browser、4G、云端、OSS/CDN 生产链路。
- Training/Labeling 仍为占位，后续需要新 sprint 接真实数据集、标注 UI 或训练流水线。
- Route Debug 当前只做旧 gate 字段映射与文件存在性说明，未读取现场 live route JSON。
