#!/usr/bin/env bash
echo Starting FastSD CPU please wait...
set -e
PYTHON_COMMAND="python3"

if ! command -v python3 &>/dev/null; then
    if ! command -v python &>/dev/null; then
        echo "Error: Python not found, please install python 3.8 or higher and try again"
        exit 1
    fi
fi

if command -v python &>/dev/null; then
   PYTHON_COMMAND="python"
fi

echo "Found $PYTHON_COMMAND command"

python_version=$($PYTHON_COMMAND --version 2>&1 | awk '{print $2}')  
echo "Python version : $python_version"

BASEDIR=$(pwd)
# shellcheck disable=SC1091
source "$BASEDIR/env/bin/activate"

# Prefer the Qt platform plugins bundled with PyQt5.
# This avoids loading OpenCV's Qt plugin first, which can crash on Linux/WSL.
PYQT5_PLATFORM_PLUGIN_PATH=$($PYTHON_COMMAND -c "import os; import PyQt5; print(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins', 'platforms'))" 2>/dev/null || true)
if [ -n "$PYQT5_PLATFORM_PLUGIN_PATH" ] && [ -d "$PYQT5_PLATFORM_PLUGIN_PATH" ]; then
    export QT_QPA_PLATFORM_PLUGIN_PATH="$PYQT5_PLATFORM_PLUGIN_PATH"
    export QT_PLUGIN_PATH="$(dirname "$PYQT5_PLATFORM_PLUGIN_PATH")"
    echo "Using Qt platform plugins from PyQt5: $QT_QPA_PLATFORM_PLUGIN_PATH"
fi

if [ -z "$DISPLAY" ]; then
    echo "Error: DISPLAY is not set. Desktop GUI requires an X/Wayland display."
    if grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
        echo "       WSL/WSLg detected. Use './start-webui.sh' or enable a working X server/WSLg display."
    else
        echo "       Start an X server or use './start-webui.sh' to run the web UI."
    fi
    exit 1
fi

QT_XCB_PLUGIN=""
if [ -n "$QT_QPA_PLATFORM_PLUGIN_PATH" ]; then
    QT_XCB_PLUGIN="$QT_QPA_PLATFORM_PLUGIN_PATH/libqxcb.so"
fi
if [ ! -f "$QT_XCB_PLUGIN" ]; then
    QT_XCB_PLUGIN=$(find "$BASEDIR/env/lib/python3.11/site-packages" \( -path '*Qt5/plugins/platforms/libqxcb.so' -o -path '*cv2/qt/plugins/platforms/libqxcb.so' \) | head -n 1)
fi
if [ -n "$QT_XCB_PLUGIN" ]; then
    MISSING_LIBS=$(ldd "$QT_XCB_PLUGIN" 2>/dev/null | grep 'not found' || true)
    if [ -n "$MISSING_LIBS" ]; then
        echo "Warning: Qt xcb plugin has unresolved dependencies:"
        echo "$MISSING_LIBS"
        echo "Install the required system library (for Debian/Ubuntu: libxcb-xinerama0) and retry, or use './start-webui.sh'."
    fi
fi

$PYTHON_COMMAND src/app.py --gui