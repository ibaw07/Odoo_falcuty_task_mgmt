# KIẾN TRÚC HỆ THỐNG: MODULE QUẢN LÝ KHOA ĐÀO TẠO ĐẠI HỌC (ODOO 20)
**Tên kỹ thuật:** `faculty_work_mgmt`  
**Phiên bản:** `20.0.4.0.0` (Community Edition / On-Premise LAN)  
**Trạng thái triển khai:** **ĐÃ HOÀN THÀNH GIAI ĐOẠN 1, GIAI ĐOẠN 2, GIAI ĐOẠN 3 & KHUNG GIAI ĐOẠN 4**  
**Tài liệu quy chuẩn:** `@rules.md`

---

## 1. TỔNG QUAN CẤU TRÚC HIỆN TẠI
Hệ thống hiện đã hoàn thiện toàn bộ **7 file models Python cốt lõi**, hệ thống **Wizards**, toàn bộ views XML chuẩn Odoo 20 (`<list>`, `<calendar>`, `<chatter/>`, không dùng `<tree>`), phân quyền 5 nhóm, bảo mật access CSV và các báo cáo QWeb A4 chuẩn hành chính.

```
d:/odoo_faculty_workspace/
├── .agent/
│   └── rules.md
├── ARCHITECTURE_STATE.md
└── faculty_work_mgmt/
    ├── __init__.py                      # Nạp models và wizards
    ├── __manifest__.py                  # Phiên bản 20.0.4.0.0 & danh mục data/views/security đầy đủ
    ├── models/
    │   ├── __init__.py
    │   ├── faculty_config.py            # Giai đoạn 1: Cấu hình, 16 Bậc lương, Định mức, Quy chuẩn, Quy trình
    │   ├── faculty_hour_ledger.py       # Giai đoạn 1: Sổ cái Giờ chuẩn trung tâm (_read_group)
    │   ├── faculty_lecturer.py          # Giai đoạn 1: Giảng viên, 3 Ô Tiêu chí, LLKH 15 mục, Chữ ký số
    │   ├── faculty_teaching.py          # Giai đoạn 2: CTĐT, Học phần, Lớp, Lịch giảng, Ra đề, Checklist 7 bước
    │   ├── faculty_exam_internship.py   # Giai đoạn 2: Khảo thí dọc, Hướng dẫn tốt nghiệp, Thực tập, Dự toán
    │   ├── faculty_research.py          # Giai đoạn 3: 13 loại hình NCKH, Dự toán, Cross-Pillar Sync, Alert Level
    │   └── faculty_other_work.py        # Giai đoạn 3 & 4: Hoạt động khác, 6 Mảng chức năng, Thư viện Offline,
    │                                    #                 Lịch chung (faculty.calendar.event),
    │                                    #                 Dashboard Real-time (faculty.dashboard) & Cron Jobs
    ├── wizards/
    │   ├── __init__.py
    │   ├── faculty_return_wizard.py     # Wizard Trả lại việc / Yêu cầu chỉnh sửa đích danh
    │   ├── faculty_schedule_wizard.py   # Wizard Gợi ý lịch trống giảng viên & Báo cáo thi
    │   └── faculty_excel_report_wizard.py # Giai đoạn 4: Khung Wizard Xuất Excel 2 Sheet (Ký tươi & Chữ ký số)
    ├── security/
    │   ├── faculty_security.xml         # Phân quyền 5 nhóm, alias group_faculty_lecturer, Record Rules 1-hop
    │   └── ir.model.access.csv          # Khai báo quyền truy cập 100% các model nghiệp vụ & wizards
    ├── data/
    │   └── faculty_cron_data.xml        # Giai đoạn 4: 3 Cron Job tự động (Nâng bậc lương, Nhắc việc, Đồng bộ lịch)
    ├── views/
    │   ├── faculty_menus.xml            # Menu Khoa, Bảng Điều hành Real-time, Lịch chung, Sổ cái, Cấu hình
    │   ├── faculty_dashboard_calendar_views.xml # Giai đoạn 4: View Dashboard Real-time & View Calendar Popover
    │   ├── faculty_excel_wizard_views.xml       # Giai đoạn 4: Form View Wizard Xuất Excel 2 Sheet
    │   ├── faculty_config_views.xml
    │   ├── faculty_hour_ledger_views.xml
    │   ├── faculty_lecturer_views.xml
    │   ├── faculty_teaching_views.xml
    │   ├── faculty_exam_internship_views.xml
    │   ├── faculty_research_views.xml
    │   ├── faculty_other_work_views.xml
    │   ├── faculty_schedule_wizard_views.xml
    │   └── faculty_return_wizard_views.xml
    └── reports/
        ├── faculty_reports.xml
        ├── faculty_lecturer_llkh_report.xml
        ├── faculty_exam_semester_report.xml
        └── faculty_stream_assignment_report.xml
```

---

## 2. CHI TIẾT CÁC THÀNH PHẦN GIAI ĐOẠN 4 ĐÃ TRIỂN KHAI

### 2.1. Bảng Điều hành Thông minh Real-time (`faculty.dashboard`)
Đặt trong `models/faculty_other_work.py` đảm bảo quy tắc **Kiến trúc Tinh gọn 7 File Models**:
1. **Phân tách Cảnh báo theo Vai trò:**
   - **Giảng viên cá nhân (`group_faculty_lecturer` / `group_faculty_user`):**
     + Chỉ hiển thị các công việc, đề tài NCKH và bước Checklist 7 bước học vụ của **chính cá nhân giảng viên đó**.
     + Trạng thái **Quá hạn:** Màu Tím (`#800080`).
     + Trạng thái **Khẩn cấp <= 3 ngày** hoặc **Bị trả lại yêu cầu sửa (`need_revision = True`):** Màu Đỏ (`#dc3545`).
   - **Lãnh đạo Khoa, Giáo vụ, Admin:**
     + Hiển thị toàn bộ cảnh báo Quá hạn (Màu Tím `#800080`) và Khẩn cấp (Màu Đỏ `#dc3545`) của **toàn thể cán bộ giảng viên trong Khoa**.
2. **Khu vực Thông tin chung toàn Khoa (Tất cả thành viên cùng thấy):**
   - **Nhắc lịch Sinh nhật thành viên:** Tự động quét và hiển thị thành viên có ngày sinh trước 7 ngày và trong ngày sinh nhật hôm nay (`is_today = True`).
   - **Cảnh báo Nâng bậc lương:** Quét niên hạn 16 bậc ngạch lương và hiển thị các giảng viên có `days_to_promotion <= 60` (trước 60 ngày).
   - **Bảng Theo dõi Thừa / Thiếu Giờ chuẩn Real-time (Thời gian thực):**
     + Sử dụng `_read_group` trên `faculty.hour.ledger` gom theo `['lecturer_id', 'category']` với điều kiện chỉ cộng các hoạt động/buổi giảng đã thực sự diễn ra tính đến ngày hôm nay (`date <= fields.Date.context_today(self)`).
     + So sánh trực tiếp với Định mức sau giảm của từng giảng viên (Giảng dạy, NCKH, Hoạt động khác) và hiển thị kết quả Thừa / Thiếu theo thời gian thực (Xanh khi thừa `>= 0`, Đỏ khi thiếu `< 0`).
3. **Thao tác nhanh trên Header:**
   - Nút **"Làm mới dữ liệu (Real-time)"** (`action_refresh_dashboard`): Tải lại tức thì số liệu mới nhất.
   - Nút **"Lịch Công tác Chung Toàn Khoa"** (`action_open_calendar`): Chuyển sang giao diện Lịch.
   - Nút **"Xuất Báo cáo Excel 2 Sheet"** (`action_open_excel_wizard`): Bật popup wizard xuất báo cáo.

---

### 2.2. Lịch Công tác Chung Toàn Khoa (`faculty.calendar.event`)
Giao diện chuẩn Google Calendar trên Odoo 20:
1. **5 Nhóm Màu Sự kiện (`event_category`) kèm Bộ lọc (Filter) bên phải:**
   - `teaching` (**Xanh dương**): Lịch giảng dạy chính khóa, dạy bù, học cải thiện (đồng bộ từ `faculty.teaching.session`).
   - `exam` (**Cam**): Lịch thi, coi thi, hạn chấm thi (đồng bộ từ `faculty.class.course` & `faculty.exam.assignment`).
   - `guest_speaker` (**Xanh lá**): Lịch báo cáo thực tế & đón báo cáo viên.
   - `dept_event_task` (**Đỏ / Tím**): Sự kiện chung của Khoa (Họp Khoa, Hội thảo, Bảo vệ) & Hạn chót công việc.
   - `birthday` (**Vàng**): Sinh nhật cán bộ giảng viên trong Khoa.
2. **Hỗ trợ Popover / Hover Popup:**
   - Cấu hình thẻ `<calendar>` chuẩn Odoo 20 với `event_open_popup="true"`.
   - Popover tóm tắt đầy đủ: Thời gian, Địa điểm / Phòng học, Người chủ trì / Giảng viên đứng lớp, Học phần / Lớp, Ghi chú chi tiết.
   - Nút **"Mở bản ghi gốc"** (`action_open_source`): Nhảy thẳng đến buổi giảng, đợt thi, nhiệm vụ hoặc công trình NCKH tương ứng.
3. **Hàm Đồng bộ Tự động (`action_sync_all_events`):** Quét và tổng hợp dữ liệu từ cả 3 trụ cột vào bảng lịch chung với cơ chế khóa `event_key` chống trùng lặp.

---

### 2.3. Hệ thống Cron Job Tự động (`data/faculty_cron_data.xml`)
3 tác vụ nền tự động định kỳ:
1. `cron_faculty_check_salary_promotions`: Quét hàng ngày, nếu phát hiện giảng viên có `days_to_promotion <= 60` (còn 60 ngày đến hạn nâng bậc) và chưa có phiếu việc nhắc trong kỳ đó -> Tự động tạo 1 Nhiệm vụ trong `faculty.other.work` (`activity_type = 'recruitment'`) giao cho cán bộ có cờ `can_manage_hr = True` (Quản lý nhân sự).
2. `cron_faculty_periodic_task_reminders`: Nhắc việc định kỳ theo quy trình thống kê giờ hoạt động của Khoa cho cán bộ có cờ `can_edit_faculty_tasks = True`.
3. `cron_faculty_sync_calendar_events`: Tự động quét và đồng bộ lịch công tác toàn Khoa hàng ngày.

---

### 2.4. Khung Wizard Xuất Báo cáo Excel 2 Sheet (`wizards/faculty_excel_report_wizard.py`)
Model TransientModel `faculty.excel.report.wizard`:
1. **Tham số cấu hình linh hoạt:**
   - Phạm vi xuất (`report_scope`): `'personal'` (Cá nhân giảng viên), `'department'` (Tổng hợp toàn Khoa), `'monthly'` (Báo cáo tháng N & Kế hoạch tháng N+1).
   - `academic_year_id`, `semester_id`, `month`, `lecturer_id` (mặc định gắn giảng viên đang đăng nhập).
   - Tùy chọn bản xuất (`signature_mode`):
     + `'wet_ink'`: Bản in ký tươi (chừa trống ô ký nháy cá nhân và ô Trưởng khoa xác nhận đóng dấu).
     + `'digital_sign'`: Bản gắn chữ ký số (tự động gắn ảnh chữ ký cá nhân `signature_image`).
2. **Cấu trúc 2 Sheet chuẩn:**
   - **Sheet 1 (Thống kê Giờ chuẩn & Bù trừ):** Gồm 3 phần: (1) Giảng dạy (Định mức, Miễn giảm, Sau giảm, Giờ giảng 50%, Thực tế đứng lớp & tổng, Thừa/Thiếu), (2) NCKH (Định mức, Thực tế, Thừa/Thiếu), Cơ chế Bù trừ chéo, (3) Hoạt động khác (Định mức, Thực tế, Thừa/Thiếu - Không bù trừ).
   - **Sheet 2 (Tổng hợp Tất cả Công việc Đã làm):** Liệt kê chi tiết từng buổi giảng, công trình NCKH, nhiệm vụ phục vụ đánh giá, xếp loại cuối năm.
3. **Sẵn sàng cho Bước 4.2:** Các hook phương thức (`_generate_excel_content`, `_render_sheet1_hours`, `_render_sheet2_tasks`, `_render_signatures`) được cấu trúc dạng module rõ ràng, sẵn sàng để Claude Sonnet 4.6 tinh chỉnh sâu bằng thư viện `openpyxl`.

---

### 2.5. Bảo mật & An toàn Dữ liệu
1. **Quyền đọc `faculty.lecturer`:** Thiết lập `domain_force = "[(1, '=', 1)]"` mở quyền đọc cho `group_faculty_user` đảm bảo 100% không bao giờ bị lỗi trắng dropdown khi chọn giảng viên trên toàn hệ thống.
2. **Record Rules 1-hop:** Áp dụng phân quyền chặt chẽ trên `faculty.calendar.event`, `faculty.other.work`, `faculty.research.work`, `faculty.library.document`.
3. **Danh mục CSV:** Khai báo đầy đủ 100% quyền truy cập của các models mới và wizards trong `security/ir.model.access.csv`.
