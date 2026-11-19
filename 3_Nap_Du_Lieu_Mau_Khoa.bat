@echo off
chcp 65001 >nul
echo =====================================================================
echo  TIỆN ÍCH 3: NẠP DỮ LIỆU MẪU KHOA KINH TẾ - HV NÔNG NGHIỆP VIỆT NAM
echo  (Nạp 10 giảng viên, 4 kịch bản tính giờ chuẩn, 28 bảng dữ liệu)
echo =====================================================================
echo.
set PYTHON_EXE=C:\Program Files\Odoo 20.0.20260927\python\python.exe
set SCRIPT_PATH=%~dp0faculty_work_mgmt\data\scripts\populate_vnua_data.py

if not exist "%PYTHON_EXE%" (
    echo [LỖI] Không tìm thấy Python của Odoo tại: "%PYTHON_EXE%"
    echo Vui lòng kiểm tra lại đường dẫn cài đặt Odoo trên máy của bạn.
    pause
    exit /b 1
)

echo Đang nạp dữ liệu mẫu vào cơ sở dữ liệu Odoo...
"%PYTHON_EXE%" "%SCRIPT_PATH%"
echo.
pause

