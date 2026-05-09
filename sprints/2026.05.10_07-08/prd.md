# Sprint 2026.05.10 07-08 PRD

## 需求

学习阶段已经可以通过 `route_recorder:=true` 采集 `route.csv` 和 `keyframes/*.jpg`，但这些关键帧还没有进入统一视觉样本 manifest。远程诊断只能知道 detector 样本，不能证明固定路线学习阶段是否沉淀了路线关键帧证据。

## OKR 对齐

- Objective 4 KR3：视觉样本目录和 manifest contract 保留为可选诊断引用。
- Objective 3 KR1/KR2：学习路线和 route 数据采集流程应形成可复盘产物。
- Objective 5 KR4：远程诊断最小数据包需要摄像头/关键帧引用。

## 用户价值

现场学习路线后，售后或调试同学可以直接通过 `manifest.json` 或 `/api/diagnostics` 判断是否采到了 route keyframe、最新 checkpoint 是哪一个、是否存在可追溯图片和 pose JSON。

## 验收口径

- route keyframe sample 使用 `trashbot.vision_samples.v1` manifest schema。
- 每个样本包含 `sample_ref`、`raw_image`、`json`、`context.route_id`、`context.checkpoint_id`、`context.event_type=route_keyframe`。
- companion JSON 包含 `route_pose` 和空 `detections`。
- manifest append 有边界裁剪和坏 manifest 重建测试。
- launch 参数和文档同步更新。
