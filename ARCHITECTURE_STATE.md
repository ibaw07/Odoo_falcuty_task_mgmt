# KIẾN TRÚC HỆ THỐNG: MODULE QUẢN LÝ KHOA ĐÀO TẠO ĐẠI HỌC (ODOO 20)
**Tên kỹ thuật:** `faculty_work_mgmt`  
**Phiên bản:** `20.0.1.0.0` (Community Edition / On-Premise LAN)  
**Trạng thái triển khai:** **ĐÃ HOÀN THÀNH GIAI ĐOẠN 1** (Core Models, Ledger, Profiles, Security & Reports)  
**Tài liệu quy chuẩn:** `@rules.md`

---

## 1. TỔNG QUAN GIAI ĐOẠN 1
Giai đoạn 1 đã khởi tạo nền tảng cốt lõi của hệ thống, bao gồm cấu trúc module, 3 file models Python quan trọng nhất, toàn bộ hệ thống phân quyền 5 nhóm, giao diện XML views chuẩn Odoo 20 (dùng `<list>`, `<chatter/>`, không dùng `<tree>`), và mẫu in QWeb Lý lịch Khoa học (LLKH) 15 mục.

```
d:/odoo_faculty_workspace/
├── .agent/
│   └── rules.md
├── ARCHITECTURE_STATE.md
└── faculty_work_mgmt/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   ├── faculty_config.py
    │   ├── faculty_hour_ledger.py
    │   └── faculty_lecturer.py
    ├── security/
    │   ├── faculty_security.xml
    │   └── ir.model.access.csv
    ├── views/
    │   ├── faculty_menus.xml
    │   ├── faculty_config_views.xml
    │   ├── faculty_hour_ledger_views.xml
    │   └── faculty_lecturer_views.xml
    └── reports/
        ├── faculty_reports.xml
        └── faculty_lecturer_llkh_report.xml
```

---

## 2. CHI TIẾT CÁC THÀNH PHẦN ĐÃ TRIỂN KHAI

### 2.1. Cấu hình Module (`__manifest__.py`)
- **Dependencies:** `['base', 'mail']`.
- **Ngôn ngữ:** 100% Tiếng Việt, chuẩn thể thức giáo dục đại học Việt Nam.
- **Tải đầy đủ:** Security XML, Access CSV, Views (Menus, Config, Hour Ledger, Lecturer), và QWeb Reports.

### 2.2. Python Models Cốt lõi (`models/`)
1. **`models/faculty_config.py`**:
   - `DepartmentBackToListMixin`: Cung cấp nút `"Quay lại danh sách"` đồng bộ trên mọi Form view chính qua `action_back_to_list()`.
   - `faculty.academic.year`: Năm học theo chu kỳ chuẩn từ 01/08 đến 31/07. Nút `action_close_year()` chốt sổ cuối năm.
   - `faculty.academic.semester`: Các học kỳ trong năm học (HK1, HK2, HK Hè).
   - `faculty.rank.config`: 16 bậc lương với niên hạn nâng bậc (mặc định 36 tháng cho ngạch giảng viên).
   - `faculty.title.norm`: Định mức chuẩn 3 tiêu chí theo chức danh (Giảng dạy: 270 tiết; NCKH: 600 giờ; Khác: 100 giờ).
   - `faculty.norm.reduction`: Chế độ miễn giảm kiêm nhiệm & đi học (>= 4 tuần tự động tính giảm theo công thức `Số tuần / 44`).
   - `faculty.norm.config`: Bảng quy chuẩn giờ chuẩn động:
     + Hệ số lớp đông >= 40 HV là `1.2`.
     + Đơn giá coi thi, chấm thi Tự luận, Trắc nghiệm, Tiểu luận, Vấn đáp.
     + Định mức ra đề thi mới (Tự luận: 5h/đề, Vấn đáp: 1h/câu, Tiểu luận: 2h/chủ đề).
   - `faculty.exam.grading.rule`: Bảng quy tắc khảo thí động: Từ sĩ số X đến Y -> Số bài chấm kiểm tra random = cố định hoặc % sĩ số. Có hàm `calculate_audit_count(student_count)`.
   - `faculty.payment.regulation` & `faculty.payment.regulation.line`: Quy định thanh toán (List view đúng 4 cột: STT, Loại thanh toán, Căn cứ [Số văn bản - Ngày], Ghi chú; Form view có Tên hoạt động, Căn cứ pháp lý, File đính kèm `attachment=True`, và bảng Các mục chi/Đơn giá áp dụng).
   - `faculty.workflow.process` & `faculty.workflow.step`: Quy trình & Biểu mẫu quy định Khoa (upload Word/PDF qua `ir.attachment`, luồng duyệt `draft -> waiting_dean -> approved`).

2. **`models/faculty_hour_ledger.py`**:
   - `faculty.hour.ledger`: Sổ cái Giờ chuẩn trung tâm tập trung toàn bộ dữ liệu giờ của Khoa.
   - Các trường: `lecturer_id`, `academic_year_id`, `semester_id`, `date`, `category` (`teaching`, `research`, `other`), `activity_type`, `name`, `raw_hours`, `coefficient`, `standard_hours`, `res_model`, `res_id`, `is_locked`.
   - Hàm `post_ledger_entry(vals)`: Tự động ghi/cập nhật dòng sổ cái theo `res_model` + `res_id` + `lecturer_id` chống trùng lặp dữ liệu; chặn sửa xóa nếu dòng sổ đã chốt.
   - Hàm `action_lock_year_ledger()` & `action_unlock_year_ledger()`: Khóa/mở khóa sổ cái.

3. **`models/faculty_lecturer.py`**:
   - `_inherits = {'res.partner': 'partner_id'}` và `['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']`.
   - Các trường: `lecturer_code`, `user_id`, Học hàm (+ năm bổ nhiệm), Học vị (+ năm công nhận), Chức vụ, `rank_id`, `rank_date`, `next_rank_date`, `days_to_promotion` (non-stored + search method), `is_promotion_soon` (cảnh báo <= 60 ngày), `signature_image`.
   - **5 Cờ phân quyền trực quan:** `can_edit_subjects`, `can_edit_classes`, `can_edit_exams`, `can_edit_faculty_tasks`, `can_manage_hr` (tự động đồng bộ sang `res.groups`).
   - **Giao diện Hồ sơ cá nhân tinh gọn:**
     + Bỏ các ô định mức/miễn giảm rời rạc ở đầu trang, bỏ ô bù trừ chéo khỏi hồ sơ cá nhân.
     + Không sử dụng widget hover gây popup thừa.
     + **3 Ô Tiêu chí (1. Giảng dạy - 2. NCKH - 3. Hoạt động khác):**
       * Ô 1 (Giảng dạy): Hiển thị rõ Định mức sau giảm, Giờ giảng định mức (= 50% định mức sau giảm), Giờ giảng đứng lớp thực tế, Tổng số giờ thực tế Giảng dạy, Thừa/Thiếu + Bảng dòng sổ cái giờ giảng dạy.
       * Ô 2 (NCKH): Định mức sau giảm, Tổng số giờ thực tế NCKH, Thừa/Thiếu + Bảng dòng sổ cái NCKH.
       * Ô 3 (Hoạt động khác): Định mức sau giảm, Tổng số giờ thực tế HĐ khác, Thừa/Thiếu + Bảng dòng sổ cái HĐ khác.
       * Tối ưu hóa hiệu năng: Tổng hợp dữ liệu từ `faculty.hour.ledger` thông qua `_read_group`, chống triệt để lỗi N+1 SQL queries.
   - **Tab Quy hoạch & Phát triển cán bộ:** Chức danh quy hoạch, giai đoạn, kế hoạch đào tạo bồi dưỡng. Hàm quét nhắc nâng bậc `action_check_promotion_reminders()` tạo `mail.activity` trước 60 ngày.
   - **Tab Lý lịch Khoa học (Đủ 15 mục chuẩn):**
     + Cấp bậc/Chức vụ hiển thị dạng `"Bậc 12/16 - Trưởng khoa"`.
     + Model `faculty.lecturer.resume.line`: Quá trình đào tạo, Quá trình công tác, Đề tài KH&CN, SHTT, Giải thưởng.
     + Model `faculty.lecturer.publication`: Công trình khoa học công bố, kèm cờ `is_top_selected` (ràng buộc validation tối đa 5 công trình tiêu biểu).

### 2.3. Phân quyền & Bảo mật (`security/`)
- `faculty_security.xml`:
  1. `group_faculty_user`: Giảng viên / Cán bộ nhân viên (Quyền cơ sở).
  2. `group_faculty_training`: Quản lý Đào tạo / Giáo vụ.
  3. `group_faculty_exam`: Quản lý Khảo thí.
  4. `group_faculty_research`: Quản lý Nghiên cứu Khoa học.
  5. `group_faculty_dean`: Ban Chủ nhiệm Khoa / Trưởng Khoa (Toàn quyền quản trị).
  - Record rules: Giảng viên chỉ xem/sửa hồ sơ và sổ cái cá nhân; Lãnh đạo Khoa toàn quyền.
- `ir.model.access.csv`: Khai báo quyền CRUD cho toàn bộ 15 models nghiệp vụ.

### 2.4. Giao diện Odoo 20 (`views/`)
- Tuân thủ 100% cú pháp Odoo 20: Thẻ `<list>` thay thế thẻ `<tree>`, `<chatter/>`, `invisible="..."`, `readonly="..."`.
- Cấu hình List view Quy định thanh toán đúng 4 cột: `STT | Loại thanh toán | Căn cứ (Số văn bản - Ngày) | Ghi chú`.
- Card giao diện 3 Ô Tiêu chí có bảng con hiển thị chi tiết các dòng sổ cái đã quy đổi.

### 2.5. Mẫu in QWeb (`reports/`)
- `faculty_reports.xml` & `faculty_lecturer_llkh_report.xml`:
  - Bản in PDF Lý lịch Khoa học 15 mục chuẩn thể thức hành chính giáo dục Việt Nam.
  - Tự động lọc tối đa 5 công trình tiêu biểu đã tích chọn (`is_top_selected`).
  - Cuối trang có phần ngày tháng năm, khối chữ ký nháy của Giảng viên (nhúng ảnh `signature_image`) và khối xác nhận của Trưởng khoa.

---

## 3. LỘ TRÌNH TRIỂN KHAI CÁC GIAI ĐOẠN TIẾP THEO
Theo phân vai quy chế tại `@rules.md`:
- **Giai đoạn 2 (Nhóm 1 - Giảng dạy):** File `models/faculty_teaching.py` (CTĐT `faculty.curriculum`, Học phần `faculty.course`, Đề cương `faculty.course.syllabus`, Danh sách lớp `faculty.student.class`, Lịch giảng chi tiết `faculty.teaching.session` với cơ chế tích "Đã ra đề" độc quyền và chuỗi checklist 7 bước học vụ).
- **Giai đoạn 3 (Khảo thí & Thực hành/Thực tập):** File `models/faculty_exam_internship.py` (Lịch thi & Phân công khảo thí dọc `faculty.exam.assignment`, Hướng dẫn tốt nghiệp, Thực hành & Thực tập `faculty.internship.project` kèm Tab Thành phần - Tài liệu - Dự toán).
- **Giai đoạn 4 (Nhóm 2 - NCKH & Đồng bộ chéo):** File `models/faculty_research.py` (12 loại hình NCKH, Dự toán thanh toán, Cơ chế liên kết chéo tự động Cross-Pillar Sync sang Giảng dạy và LLKH).
- **Giai đoạn 5 (Nhóm 3 - Hoạt động khác & Thư viện):** File `models/faculty_other_work.py` (7 loại hoạt động khác, Bảng phân công 6 mảng chức năng Khoa, Thư viện Offline qua `ir.attachment`).
- **Giai đoạn 6 (Wizards & Tiện ích):** Wizard gợi ý lịch trống giảng viên, Wizard xuất danh sách khảo thí học kỳ, Wizard popup trả lại việc có chọn người.
- **Giai đoạn 7 (Dashboard Real-time & Excel 2 Sheet):** Lịch chung Khoa có hover popup, cảnh báo quá hạn tím/đỏ, xuất Excel 2 sheet kèm chữ ký số bằng `openpyxl`.
