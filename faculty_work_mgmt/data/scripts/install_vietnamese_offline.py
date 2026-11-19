# -*- coding: utf-8 -*-
"""
Kịch bản Kích hoạt & Nạp Ngôn ngữ Tiếng Việt 100% Offline cho Odoo 20
Không yêu cầu kết nối Internet. Đọc trực tiếp các file i18n/vi.po có sẵn trên ổ đĩa.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r'C:\Program Files\Odoo 20.0.20260927\server')
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

def install_vietnamese_offline():
    config_file = r'C:\Program Files\Odoo 20.0.20260927\server\odoo.conf'
    odoo.tools.config.parse_config(['-c', config_file, '-d', 'Quantrikhoa'], setup_logging=False)
    
    registry = Registry('Quantrikhoa')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== BẮT ĐẦU CÀI ĐẶT & KÍCH HOẠT TIẾNG VIỆT 100% OFFLINE (KHÔNG CẦN INTERNET) ===")
        
        # 1. Tìm bản ghi ngôn ngữ vi_VN
        Lang = env['res.lang'].with_context(active_test=False)
        vi_lang = Lang.search([('code', '=', 'vi_VN')], limit=1)
        if not vi_lang:
            vi_lang = Lang.create({
                'name': 'Vietnamese / Tiếng Việt',
                'code': 'vi_VN',
                'iso_code': 'vi_VN',
                'direction': 'ltr',
                'date_format': '%d/%m/%Y',
                'time_format': '%H:%M:%S',
                'grouping': '3,3',
                'decimal_point': ',',
                'thousands_sep': '.',
                'active': True,
            })
            print("[1/3] Đã tạo mới bản ghi ngôn ngữ vi_VN.")
        else:
            vi_lang.write({
                'active': True,
                'date_format': '%d/%m/%Y',
                'time_format': '%H:%M:%S',
                'decimal_point': ',',
                'thousands_sep': '.',
            })
            print("[1/3] Đã kích hoạt bản ghi ngôn ngữ vi_VN trong CSDL.")

        # 2. Chạy wizard nạp bản dịch offline từ file có sẵn trong addons/*/i18n/vi.po
        print("[2/3] Đang nạp các file vi.po từ thư mục cài đặt Odoo cục bộ vào CSDL...")
        wiz = env['base.language.install'].create({
            'lang_ids': [(6, 0, [vi_lang.id])],
            'overwrite': True,
        })
        wiz.lang_install()
        print("      -> Nạp bản dịch tiếng Việt offline thành công!")

        # 3. Đặt ngôn ngữ mặc định của Administrator sang Tiếng Việt
        admin_user = env['res.users'].search([('login', '=', 'admin')], limit=1)
        if admin_user:
            admin_user.write({'lang': 'vi_VN'})
            print(f"[3/3] Đã chuyển đổi ngôn ngữ tài khoản '{admin_user.name}' sang Tiếng Việt.")

        cr.commit()
        print("=== HOÀN TẤT: HỆ THỐNG ĐÃ SẴN SÀNG VỚI GIAO DIỆN TIẾNG VIỆT ĐẦY ĐỦ ===")

if __name__ == '__main__':
    install_vietnamese_offline()

