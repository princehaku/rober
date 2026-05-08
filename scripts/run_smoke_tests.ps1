$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    python -m compileall -q src scripts
    python -m unittest discover -s src\ros2_trashbot_hardware\test -p "test*.py"
    python -m unittest discover -s src\ros2_trashbot_nav\test -p "test*.py"
    python -m unittest discover -s src\ros2_trashbot_bringup\test -p "test*.py"
    python -m unittest discover -s src\ros2_trashbot_behavior\test -p "test*.py"
    if (Test-Path src\ros2_trashbot_vision\test) {
        python -m unittest discover -s src\ros2_trashbot_vision\test -p "test*.py"
    }
}
finally {
    Pop-Location
}
