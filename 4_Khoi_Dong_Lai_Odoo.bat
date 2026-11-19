@echo off
chcp 65001 >nul
echo =====================================================================
echo  TIỆN ÍCH 4: KHỞI ĐỘNG LẠI DỊCH VỤ ODOO SERVER (RESTART SERVICE)
echo =====================================================================
echo Đang khởi động lại dịch vụ Odoo 20...
powershell -Command "Restart-Service odoo-server-20.0 -ErrorAction SilentlyContinue; if ($?) { Write-Host '[THÀNH CÔNG] Dịch vụ odoo-server-20.0 đã được khởi động lại!' -ForegroundColor Green } else { Write-Host '[LỖI] Vui lòng nhấp chuột phải chọn Run as Administrator!' -ForegroundColor Red }"
echo.
pause

