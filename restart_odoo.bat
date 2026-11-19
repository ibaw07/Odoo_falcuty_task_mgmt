@echo off
echo ==============================================
echo   Dang khoi dong lai dich vu Odoo 20 Server...
echo ==============================================
net stop odoo-server-20.0
net start odoo-server-20.0
echo.
echo Da khoi dong lai Odoo thanh cong!
echo Ban co the mo trinh duyet truy cap: http://localhost:8069
echo.
pause

