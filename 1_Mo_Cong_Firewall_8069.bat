@echo off
chcp 65001 >nul
echo =====================================================================
echo  TIỆN ÍCH 1: MỞ CỔNG 8069 TRÊN TƯỜNG LỬA WINDOWS (FIREWALL)
echo =====================================================================
echo Đang mở cổng TCP 8069 cho Odoo trong mạng LAN...
netsh advfirewall firewall add rule name="Odoo Server Port 8069" dir=in action=allow protocol=TCP localport=8069 profile=any
echo.
if %errorlevel% equ 0 (
    echo [THÀNH CÔNG] Đã mở cổng 8069 trên Tường lửa Windows!
    echo Các máy khác trong mạng LAN có thể truy cập vào máy chủ này qua cổng 8069.
) else (
    echo [LỖI] Vui lòng nhấp chuột phải vào file này và chọn 'Run as administrator'!
)
echo.
pause

