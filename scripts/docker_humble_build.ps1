$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

docker build -t ros-rbs-humble:dev (Join-Path $repoRoot "docker\humble")
docker run --rm `
    -v "${repoRoot}:/ws" `
    -w /ws `
    ros-rbs-humble:dev `
    bash -lc "source /opt/ros/humble/setup.bash && rm -rf build install log && colcon build --symlink-install"
