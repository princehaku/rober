# Sprint 2026.05.11 23-24 Top-Level Elevator/Mobile/Cloud Redesign - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-11 23:59 Asia/Shanghai。
- Product Owner：`product-okr-owner`（CEO 明确"本次是顶层设计，无需多个子 agent 干活"，由主节点以 product-owner 视角直接交付文档/OKR）。
- 本轮性质：产品/OKR/产品文档顶层重排。**不改代码、不改硬件配置、不改测试。**

## 背景

CEO 给出新的顶层指令：

1. 把"进出电梯"从 H2/受控可选场景升级为**必须实现的功能**。
2. 手机端**美观** + **能直接使用** 升级为**必须**，不再只是"phone-first dependency-free HTML"。
3. CEO 提供了一台 **4C 8G 无 GPU** 服务端用于 4G 数据通信中转：`ssh root@14.103.37.144 -p 7878`。
4. CEO 提供了**阿里云 OSS**（bucket `bytegallop`，region `oss-cn-hangzhou`）和 **CDN**（`https://cdn.bytegallop.com/rober/`）用于数据中转。

本轮目标是把这些方向变成 OKR、Objective、KR、产品 contract、责任 Engineer 和验收口径，不在本轮写代码。

## 目标

1. `OKR.md` 顶层设计落地：
   - 北极星补"必须能跨楼层送垃圾"和"手机端美观可直接使用"。
   - 战略定位调整"电梯能力是 assisted delivery"段，从 H2/受控可选改为 MVP 必须。
   - Objective 2/4/5 的电梯 KR6 去掉 H2/受控前缀，明确为 MVP 必须。
   - Objective 5 强化手机端美观与开箱即用。
   - 新增 Objective 6：4G 云通信链路 + OSS/CDN 数据中转产品化。
2. 重写 `docs/product/elevator_assisted_delivery.md`：H2/可选 → MVP 必须实现。
3. 更新 `docs/product/mobile_user_flow.md`：把"美观、能直接使用"列为强制 product contract。
4. 更新 `docs/product/remote_4g_mvp.md`：接入真实云服务端（地址保留，不写 root 密码或私密信息）。
5. 新增 `docs/product/cloud_4g_infrastructure.md`：服务端、OSS、CDN 产品 contract。**敏感凭证只放 `.env.example` 占位，不写入文档**。
6. 新增 `docs/product/mobile_ui_quality.md`：手机端美观和可用性验收口径。
7. 新增 `.env.example`、补 `.gitignore` 排除 `.env`，防止 OSS Access Key Secret 进入仓库。

## Owner

- 主责：`product-okr-owner`。
- 后续实现 owner：
  - `robot-software-engineer`：电梯子状态机进入主行为状态机，不再标 H2。
  - `autonomy-engineer`：电梯门/楼层/驶出感知证据 + 真机采集计划。
  - `full-stack-software-engineer`：手机端美观 UI、4G 云端服务、OSS/CDN 接入。
  - `hardware-engineer`：仅在涉及硬件事实、电气、UART 或安装时介入，仍以 `docs/vendor/VENDOR_INDEX.md` 为准。

## 范围

允许改动：

- `OKR.md`
- `docs/product/elevator_assisted_delivery.md`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`（新增）
- `docs/product/mobile_ui_quality.md`（新增）
- `.env.example`（新增）
- `.gitignore`
- `sprints/2026.05.11_23-24_top-level-elevator-mobile-cloud/`

明确不改：

- `src/`
- `docs/vendor/`
- `docs/hardware/`
- `docs/navigation/`
- `docs/interfaces/`
- `docs/acceptance/`
- `docs/vision/`
- `docs/superpowers/`
- `README.md`
- 其他 sprint 目录

## 风险

1. **凭证泄露**：CEO 在 prompt 中直接给出 `OSS_ACCESS_KEY_SECRET`、`CDN` 域名、服务端 SSH 端口。任何 tracked 文件都不得保存 secret；必须用 `.env` + 占位 + `.gitignore` 隔离。
2. **进度被误读**：把电梯能力从 H2 改为 MVP 后，外部容易把"OKR 里写明 MVP 必须"误读为"现在小车已经能进出电梯"。本轮**只升级方向，不抬实机完成度**。
3. **手机美观无证据**：把"美观直接可用"列为必须后，外部容易把"已写入 OKR/contract"误读为"UI 已美观可上线"。本轮**只定义验收口径，不抬手机 UI 完成度**。
4. **云端依赖**：服务端 4C 8G 无 GPU、且公网 IP 暴露，必须明确不直接 expose `/cmd_vel`、不直接转发 ROS2 内部 topic，只承担 outbound 命令/状态/ACK 中转。
5. **OSS/CDN 滥用**：OSS 写入策略必须限定 `rober/` 前缀，避免和其他业务串污；写入对象必须可回收，避免长期占用流量。

## 验收口径

- `OKR.md` 中包含"电梯"+"MVP 必须"+"手机美观"+"4G 云中转"+"OSS"+"CDN" 关键词。
- 产品文档覆盖：电梯流程、手机端美观、4G 中转服务端、OSS/CDN 数据流、敏感凭证保管。
- 无任何 tracked 文件包含 `OSS_ACCESS_KEY_SECRET` 实际值；只允许 `.env.example` 中以占位形式存在。
- `.gitignore` 显式排除 `.env`。
- Sprint 六件套完整存在，无占位符。
- scoped `git diff --check` 通过。
