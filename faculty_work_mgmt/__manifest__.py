# -*- coding: utf-8 -*-
{
    'name': 'Faculty Work Management - Quản lý Công việc Khoa Đào tạo Đại học',
    'version': '20.0.4.0.0',
    'summary': 'Faculty Work Management - Dashboard Điều hành Real-time, Lịch chung, Giờ chuẩn & Báo cáo Excel 2 Sheet',
    'description': """
Module Quản lý Công việc Khoa Đào tạo Đại học Việt Nam (Odoo 20)
================================================================
Giai đoạn 1:
------------
* Cấu hình Năm học, Học kỳ, 16 Bậc lương & Niên hạn nâng bậc (nhắc trước 60 ngày).
* Định mức 3 tiêu chí theo Chức danh & Quy định miễn giảm công tác/đi học (>= 4 tuần tính theo công thức Số tuần/44).
* Bảng Quy chuẩn giờ chuẩn động & Bảng Quy tắc khảo thí chấm kiểm tra động.
* Quy định thanh toán & Biểu mẫu/Quy trình làm việc (lưu file đính kèm Word/PDF qua ir.attachment).
* Sổ cái Giờ chuẩn trung tâm (faculty.hour.ledger) tổng hợp bằng _read_group chống N+1 query.
* Hồ sơ Giảng viên (kế thừa res.partner, mail.thread), Giao diện 3 Ô Tiêu chí tinh gọn.
* Quản lý Quy hoạch cán bộ & Lý lịch Khoa học (LLKH 15 mục) xuất in QWeb chuẩn với tối đa 5 công trình tiêu biểu.

Giai đoạn 2 (Trụ cột 1 - Giảng dạy & Khảo thí):
-----------------------------------------------
* Chương trình đào tạo (faculty.curriculum): Luồng 1 chiều, khi Hết hiệu lực tự động ẩn toàn bộ học phần liên quan.
* Học phần & Môn học (faculty.course): Cột STT tự động, nhãn 'Số tiết BT, TL, KT, BCTT', hỗ trợ môn con tích hợp, cho phép 1 giảng viên.
* Đề cương chi tiết (faculty.course.syllabus): 'Năm áp dụng', nút 'Áp dụng' kích hoạt tức thì.
* Danh sách lớp (faculty.student.class) & Học phần theo Lớp (faculty.class.course - Trục trung tâm): Sĩ số >= 40 nhân hệ số 1.2, học bù/ghép thêm.
* Lịch giảng chi tiết (faculty.teaching.session): Sắp xếp theo Ngày bắt đầu học, đổi GV dạy thay, cảnh báo trùng lịch, ghi giờ tự động khi đã diễn ra, không tính giờ giáo án.
* Báo cáo viên thực tế & Cơ chế tích 'Đã ra đề' độc quyền (khóa đồng nghiệp, gửi thông báo, tính giờ ra đề mới).
* Chuỗi Checklist 7 bước học vụ tự động cho từng học phần (cảnh báo quá hạn Tím, khẩn cấp Đỏ).
* Lịch thi & Khảo thí dọc: Phân công Coi thi (ẩn nếu Tiểu luận), Chấm 1 & 2 (100% sĩ số), Chấm kiểm tra (random theo quy tắc động), duyệt kế hoạch đầu năm, kết chuyển giờ khi hoàn thành.
* Hướng dẫn Khóa luận, Luận văn, Luận án, NCKH Sinh viên (faculty.thesis.guidance).
* Thực hành & Thực tập (faculty.internship.project) với 3 Tab (Thành phần - Tài liệu - Dự toán kinh phí theo quy định).

Giai đoạn 3 (Trụ cột 2 - NCKH & Trụ cột 3 - Hoạt động khác + Thư viện nhỏ Offline):
-----------------------------------------------------------------------------------
* Nghiên cứu Khoa học (faculty.research.work): Quản lý đủ 13 loại hình NCKH, tính giờ hội thảo/tọa đàm (đại biểu tham dự không tính giờ), Tab Dự toán kinh phí.
* Cơ chế Liên kết chéo tự động (Cross-Pillar Sync) khi duyệt nghiệm thu:
  + Ghi Sổ cái giờ chuẩn trung tâm (faculty.hour.ledger) phân hệ NCKH.
  + Đẩy sang Trụ cột Giảng dạy (tạo CTĐT, cập nhật Đề cương chi tiết, gắn học liệu môn học).
  + Đẩy tự động vào Lý lịch Khoa học 15 mục (Mục 10 Công trình công bố hoặc Mục 11/13 Nhiệm vụ KH&CN).
* Hoạt động khác của Khoa (faculty.other.work): Quản lý 8 loại hoạt động, phân bổ giờ, hỗ trợ Lãnh đạo giao việc và Giảng viên tự khai báo, cảnh báo hạn chót (Màu Đỏ/Tím store=False).
* Bảng Phân công Nhiệm vụ theo 6 Mảng Chức năng Khoa (faculty.stream.assignment): Tự động cấp quyền tương ứng trên hồ sơ cán bộ, hỗ trợ in Biểu phân công A4 chuẩn thể thức hành chính.
* Thư viện nhỏ của Khoa (faculty.library.category & faculty.library.document): Lưu trữ 100% offline nội bộ qua ir.attachment, phân quyền 4 cấp độ tiếp cận và Cổng Admin rà soát duyệt tài liệu.

Giai đoạn 4 (Dashboard Điều hành Real-time, Lịch chung Hover Popover, Cron Job & Wizard Xuất Excel):
----------------------------------------------------------------------------------------------------
* Dashboard Điều hành Thông minh Real-time (faculty.dashboard):
  + Phân tách cảnh báo theo vai trò: Giảng viên cá nhân (chỉ thấy việc của mình); Lãnh đạo/Giáo vụ (thấy toàn Khoa).
  + Cảnh báo Quá hạn (Màu Tím #800080), Khẩn cấp <= 3 ngày / Bị trả lại sửa (Màu Đỏ #dc3545).
  + Thông tin chung toàn Khoa: Nhắc sinh nhật (7 ngày), Cảnh báo nâng bậc lương (60 ngày).
  + Bảng Theo dõi Thừa / Thiếu Giờ chuẩn Real-time: Truy vấn faculty.hour.ledger bằng _read_group date <= today, so sánh trực tiếp định mức sau giảm.
* Lịch Công tác Chung Toàn Khoa (faculty.calendar.event):
  + Đồng bộ/tổng hợp 5 nhóm sự kiện màu: teaching (Xanh dương), exam (Cam), guest_speaker (Xanh lá), dept_event_task (Đỏ/Tím), birthday (Vàng).
  + Popover / Hover Popup hiển thị tóm tắt đầy đủ thông tin sự kiện trên giao diện Google Calendar Odoo 20.
* Cron Job Tự động: Quét nâng bậc lương <= 60 ngày tự tạo nhiệm vụ cho can_manage_hr; Nhắc việc định kỳ cho can_edit_faculty_tasks; Tự động đồng bộ lịch chung.
* Khung Wizard Xuất Báo cáo Excel 2 Sheet (faculty.excel.report.wizard): Sheet 1 Giờ chuẩn & Bù trừ, Sheet 2 Tổng hợp Công việc, tùy chọn Ký tươi và Chữ ký số.
    """,
    'category': 'Education/Faculty Management',
    'author': 'Senior Odoo Developer',
    'website': 'http://192.168.100.98:5000',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/faculty_security.xml',
        'security/ir.model.access.csv',
        'data/faculty_cron_data.xml',
        'views/faculty_dashboard_calendar_views.xml',
        'views/faculty_excel_wizard_views.xml',
        'views/faculty_menus.xml',
        'views/faculty_config_views.xml',
        'views/faculty_hour_ledger_views.xml',
        'views/faculty_lecturer_views.xml',
        'views/faculty_teaching_views.xml',
        'views/faculty_exam_internship_views.xml',
        'views/faculty_research_views.xml',
        'views/faculty_other_work_views.xml',
        'views/faculty_schedule_wizard_views.xml',
        'views/faculty_return_wizard_views.xml',
        'reports/faculty_reports.xml',
        'reports/faculty_lecturer_llkh_report.xml',
        'reports/faculty_stream_assignment_report.xml',
        'reports/faculty_exam_semester_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
