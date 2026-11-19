@echo off
chcp 65001 >nul
echo =====================================================================
echo  TIỆN ÍCH 2: KÍCH HOẠT VÀ NẠP NGÔN NGỮ TIẾNG VIỆT 100% OFFLINE
echo  (Không cần kết nối Internet - Đọc từ các file vi.po có sẵn trên đĩa)
echo =====================================================================
echo.
set PYTHON_EXE=C:\Program Files\Odoo 20.0.20260927\python\python.exe
set SCRIPT_PATH=%~dp0faculty_work_mgmt\data\scripts\install_vietnamese_offline.py

if not exist "%PYTHON_EXE%" (
    echo [LỖI] Không tìm thấy Python của Odoo tại: "%PYTHON_EXE%"
    echo Vui lòng kiểm tra lại đường dẫn cài đặt Odoo trên máy của bạn.
    pause
    exit /b 1
)

echo Đang nạp tiếng Việt vào cơ sở dữ liệu...
"%PYTHON_EXE%" "%SCRIPT_PATH%"
echo.
pause

