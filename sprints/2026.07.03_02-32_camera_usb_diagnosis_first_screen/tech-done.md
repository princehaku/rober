# 相机USB诊断首屏可见

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - PC 首页相机卡改为 flex 顺序布局，保留实时预览，同时把 `plain-camera-usb-recovery-proof` 提到预览框上方。
  - `plain-camera-usb-recovery-proof` 新增醒目的橙色硬件诊断样式，避免 USB 12M/full-speed 结论被普通说明淹没。
- `pc-tools/workstation/test/App.test.ts`
  - 增加样式合同断言，要求普通首页不能隐藏 USB 12M/非独占诊断。
- `docs/product/pc_tools_workstation.md`
  - 记录上位机真实相机排查：DV20 当前在 USB `12M` full-speed，直接 V4L2 STREAMON I/O error，软件重新枚举后仍未恢复。

## 验证结果

- 上位机 SSH：`ssh root@192.168.1.11 -p 7878`
  - `trashbot-local-webrtc-camera.service` active。
  - `lsusb -t` 显示 DV20 UVC interface 在 Bus 06 `12M`。
  - `v4l2-ctl -d /dev/video1 --set-fmt-video=width=480,height=320,pixelformat=MJPG --stream-mmap=3 --stream-count=1` 返回 `VIDIOC_STREAMON returned -1 (Input/output error)`，输出文件 0 字节。
  - 对 `/sys/bus/usb/devices/6-1/authorized` 执行重新枚举并重启 8088 服务后，设备仍为 `12M`，取帧仍失败。
- PC summary
  - `camera_diag=uvc_full_speed_usb_not_exclusive`、`camera_usb=12M`、`camera_hardware_action_required=true`。
  - `camera_blocks_free_move=false`、`keyboard_ready=true`、`free_move_ready=true`。
- Chrome headless 1280x720
  - `plain-camera-usb-recovery-proof` 在首屏可见，坐标 `top=221,bottom=296`。
  - 文案显示：`当前 USB=12M`、`不是页面独占`、`换高速USB后复测`、`不阻塞自由移动`。
  - 截图证据：`/tmp/rober_pc_camera_usb_diagnosis_proof.png`。
- `npm test -- --run test/App.test.ts`
  - 通过：1 个测试文件，237 个测试。
- `npm run build`
  - 通过：TypeScript app/server 编译和 Vite build 完成；仅保留既有 chunk size warning。

## 剩余风险

- 当前摄像头没有被页面独占，也不是 PC relay 问题；内核 V4L2 层已无法 STREAMON。需要把 DV20 接到 Orange Pi 的高速 USB 口/线或带供电 Hub 后复测，软件侧已保留只读复测链路。
- 相机首帧失败仍阻塞建图首帧验收，但不阻塞地图观察、雷达点、键盘手控、自由移动或 Nav2 路线执行。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- 上位机 `lsusb -t` / `v4l2-ctl` / `dmesg` / `camera_mjpeg_status` 只读验证。
