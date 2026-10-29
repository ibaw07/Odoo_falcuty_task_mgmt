# -*- coding: utf-8 -*-
{
    'name': 'Quản lý Công việc Khoa Đào tạo Đại học (Giai đoạn 1)',
    'version': '20.0.1.0.0',
    'summary': 'Quản lý Hồ sơ Giảng viên, Lý lịch Khoa học 15 mục, Sổ cái Giờ chuẩn trung tâm và Cấu hình Khoa',
    'description': """
Module Quản lý Công việc Khoa Đào tạo Đại học Việt Nam (Odoo 20)
================================================================
Giai đoạn 1 bao gồm:
--------------------
* Cấu hình Năm học, Học kỳ, 16 Bậc lương & Niên hạn nâng bậc (nhắc trước 60 ngày).
* Định mức 3 tiêu chí theo Chức danh & Quy định miễn giảm công tác/đi học (>= 4 tuần tính theo công thức Số tuần/44).
* Bảng Quy chuẩn giờ chuẩn động & Bảng Quy tắc khảo thí chấm kiểm tra động.
* Quy định thanh toán & Biểu mẫu/Quy trình làm việc (lưu file đính kèm Word/PDF qua ir.attachment).
* Sổ cái Giờ chuẩn trung tâm (faculty.hour.ledger) tổng hợp bằng _read_group chống N+1 query.
* Hồ sơ Giảng viên (kế thừa res.partner, mail.thread), Giao diện 3 Ô Tiêu chí tinh gọn.
* Quản lý Quy hoạch cán bộ & Lý lịch Khoa học (LLKH 15 mục) xuất in QWeb chuẩn với tối đa 5 công trình tiêu biểu.
    """,
    'category': 'Education/Faculty Management',
    'author': 'Senior Odoo Developer',
    'website': 'http://192.168.100.98:5000',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/faculty_security.xml',
        'security/ir.model.access.csv',
        'views/faculty_menus.xml',
        'views/faculty_config_views.xml',
        'views/faculty_hour_ledger_views.xml',
        'views/faculty_lecturer_views.xml',
        'reports/faculty_reports.xml',
        'reports/faculty_lecturer_llkh_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
