# Waveshare WAVE ROVER local reference

Downloaded from the official Waveshare WAVE ROVER wiki for local coding,
wiring, firmware, and mechanical reference.

Source page: https://www.waveshare.net/wiki/WAVE_ROVER

## Local contents

- `WAVE_ROVER.wiki.html` - saved copy of the wiki page.
- `wiki_assets/` - images referenced by the wiki page.
- `downloads/WAVE_ROVER.zip` - ESP32 lower-controller Arduino source package.
- `downloads/WAVE_ROVER_FACTORY.zip` - ESP32 factory firmware and Flash Download Tool.
- `downloads/WAVE_ROVER_DXF.rar` - chassis DXF drawings.
- `downloads/WAVE_ROVER_PDF.rar` - chassis PDF drawings.
- `downloads/WAVE_ROVER-EP_DXF.rar` - extension platform DXF drawings.
- `downloads/WAVE_ROVER-EP_PDF.rar` - extension platform PDF drawings.
- `downloads/WAVE_ROVER_MODEL_STL.rar` - 3D model STL files.
- `extracted/WAVE_ROVER/WAVE_ROVER_V0.9/` - extracted Arduino source.
- `extracted/WAVE_ROVER_FACTORY/WAVE_ROVER_FACTORY/` - extracted factory firmware files.
- `ugv_rpi/` - cloned Raspberry Pi upper-computer sample repo.

## Coding notes

- The Raspberry Pi sample talks to the ESP32 lower controller using newline
  delimited JSON over UART.
- Main Python reference: `ugv_rpi/base_ctrl.py`.
- Default UART in the sample: `/dev/ttyAMA0` at `115200`.
- Alternate UART mentioned in the sample: `/dev/serial0` at `115200`.
- Low-level ESP32 command definitions: `extracted/WAVE_ROVER/WAVE_ROVER_V0.9/json_cmd.h`.
- Speed command used by the sample: `{"T":1,"L":left,"R":right}`.
- ROS-style velocity command defined by the firmware comments:
  `{"T":13,"X":linear_x,"Z":angular_z}`.
- Base feedback related commands in `json_cmd.h`: `T=130` and feedback flow
  enable/disable `T=131`.

## Firmware notes

- Arduino source entry point:
  `extracted/WAVE_ROVER/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`.
- Factory flash tool:
  `extracted/WAVE_ROVER_FACTORY/WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/flash_download_tool_3.9.5.exe`.
- Factory binary files are under:
  `extracted/WAVE_ROVER_FACTORY/WAVE_ROVER_FACTORY/flash_download_tool_3.9.5/bin/`.

## Mechanical and wiring reference

- Use the downloaded PDF/DXF/RAR packages for mounting dimensions and connector
  layout.
- RAR files were kept as original archives because no RAR extractor is currently
  available in this Windows environment.

## Upstream repositories

- Raspberry Pi sample repo: https://github.com/waveshareteam/ugv_rpi
- Local clone commit at download time: `3ae9f20`
