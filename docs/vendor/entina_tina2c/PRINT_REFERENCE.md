# ENTINA Tina2C 打印参考

核实日期：2026-11-01。用户提供的国内机型链接为 [Tina2C规格](https://entina3d.cn/tina2c#specs)，以1.75 mm PLA试装现有机器人传感器件/四孔样板。

| 官方来源 | 已读事实与边界 |
|---|---|
| [国内Tina2C页](https://entina3d.cn/tina2c#specs) | 成型100×100×100 mm；1.75 mm PLA；WiFi/USB/TF；网页列最高70 mm/s。web读取失败后用PowerShell Invoke-WebRequest取得HTTP200，去script/tag后核对规格文字；不保存大网页。 |
| [国际Tina2C产品页](https://www.entina3d.com/products/entina-3d-printer-tina2c) | 交叉确认100×100×100 mm、0.4 mm喷嘴、1.75 PLA、WiiBuilder/Cura；FAQ明确无热床，支持切片后的G-code经TF卡（microSD）打印。 |
| [官方软件下载页](https://www.entina3d.com/pages/download-1) | Wiibuilder的Windows下载入口由主节点核实，指向download.entina3d.com；本轮未安装、未核验GUI菜单或机型列表。 |

国际FAQ写最高100 mm/s，与国内70不同；本项目沿用准确Tina2C PLA预设，不据营销上限改打印速度。无热床事实不由国内“自动调平热床”的通用文案推断，采用国际机型FAQ的明确说明。

本轮只做来源核实和既有STL包围尺寸比较：样板70×98×2.5理论可放但98方向仅每侧1 mm；相机座48.870×64×43.392可放；70×110雷达板、50×120底座默认平放超界。实际切片有效区、brim/skirt、支撑和首层质量尚未验证，保持mm/100%避免改孔距。不改CAD，不生成G-code，不启动打印。

## 2026-11-01 官方Windows包下载

由[官方Windows入口](https://download.entina3d.com/download/last_entina_wiibuilder.php?os=win)重定向到`https://download.entina3d.com/download/Wiibuilder2.6.7.0_ENTINA_win64-20251111.zip`，HTTP200、application/zip。保存`E:\rober\tools\wiibuilder\WiiBuilder-Windows-official-20261101.zip`，150815294字节，完整ZIP CRC通过，逐条路径检查后解压。

安装器为`E:\rober\tools\wiibuilder\unpacked\Wiibuilder2.6.7.0_ENTINA_win.exe`，150815096字节，MZ/PE格式确认。版本2.6.7.0取自官方文件名；EXE资源未提供FileVersion/ProductVersion，签名状态NotSigned，未安装确认运行版本。

- ZIP SHA256：`656bb1903e8b7808cbc9d29ba593c75064f4dad53c9a4dbe83957838e7db952c`
- EXE SHA256：`fd7c46023dc3b9dc1dc3bdeded4962e6fd228e9e3b5da20d8e5d56332f74a904`

仅下载/解压并核对完整性，未运行安装器；`/tools/wiibuilder/`精准忽略，第三方文件不提交Git。
