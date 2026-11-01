# WiiBuilder Windows 下载

sprint_type: micro

状态：下载/解压与文件校核完成，主节点已审阅通过，按授权交付四份文本。用户明确要求“你帮我下载”，本轮只下载并检查官方Windows安装包，保存到项目tools/wiibuilder，不安装、不启动软件或物理打印。

## 最小计划与范围

robot-hardware-engineer单owner：从ENTINA官方软件下载页的Windows入口下载 → 核对HTTP/真实类型/大小/SHA256 → ZIP完整CRC与逐条安全路径检查后解压 → 读取安装器版本/签名 → 同步本地路径与精准ignore。只改.gitignore、PRINT_PLA、打印参考和本micro；保留模型及其他工具/旧sprint。

## 实际改动与验证

- 实际文件：项目`tools/wiibuilder/WiiBuilder-Windows-official-20261101.zip`与`unpacked/Wiibuilder2.6.7.0_ENTINA_win.exe`。目标原先不存在，未覆盖用户文件。文本仅改.gitignore、PRINT_PLA第一条、vendor打印参考和本文件。
- `Invoke-WebRequest`官方Windows入口返回HTTP200/application/zip；`curl -I -L`核对302最终指向官方`Wiibuilder2.6.7.0_ENTINA_win64-20251111.zip`，Content-Length150815294，与Get-Item一致。下载未禁用TLS校验。
- Python检查PK ZIP魔数、`zipfile.testzip()`完整CRC返回None（通过），1条entry、解压150815096字节；解压前逐条拒绝绝对路径/上级目录/盘符冒号/符号链接/大小写重名，解析目标均在预定unpacked内，使用新文件模式写出。安装器MZ/PE格式确认。
- `Get-FileHash`ZIP SHA256：`656bb1903e8b7808cbc9d29ba593c75064f4dad53c9a4dbe83957838e7db952c`，Python独立计算一致。EXE SHA256：`fd7c46023dc3b9dc1dc3bdeded4962e6fd228e9e3b5da20d8e5d56332f74a904`。
- `Get-AuthenticodeSignature`=NotSigned；VersionInfo的FileVersion/ProductVersion为空。2.6.7.0仅来自官方包名，未安装确认运行版本。
- `git check-ignore -v` ZIP/EXE均命中`/tools/wiibuilder/`；`git diff --check`通过。无CAD验证需求，未改模型、其他工具或旧sprint。下载中首次查看目标时HTTP响应尚未开始落盘，稍后正常完成，未发生需重试的下载错误。

## 剩余边界

本轮未安装、未核实软件GUI/机型配置，未切片、未生成G-code、未实打。第三方包仅留本机项目目录，不进入Git。
