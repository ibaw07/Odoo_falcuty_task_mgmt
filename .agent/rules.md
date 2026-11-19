# DỰ ÁN: MODULE QUẢN LÝ CÔNG VIỆC KHOA ĐÀO TẠO ĐẠI HỌC VN (ODOO 20 COMMUNITY)

## 1. KIẾN TRÚC LÕI & QUY CHUẨN KỸ THUẬT
- Tên module kỹ thuật: `faculty_work_mgmt` (Odoo 20, Python 3.12+, OWL 3).
- Ngôn ngữ hiển thị UI: Tiếng Việt 100%. Không làm Mobile API.
- Các model chính kế thừa `mail.thread` và `mail.activity.mixin` (`tracking=True`).
- Áp dụng mô hình Sổ cái (Ledger Pattern): Tách biệt tờ khai công việc (`faculty.manual.declaration`) và sổ cái giờ chuẩn (`faculty.workload.ledger` với `state = 'staging' | 'posted' | 'cancelled'`).
- Khi Trưởng khoa bấm Duyệt (`approved`), tự động gọi hàm khóa giao dịch `_lock_and_post()` sử dụng `SELECT ... FOR UPDATE SKIP LOCKED` để chuyển bút toán sang `posted`. Khi hủy bản ghi đã duyệt, không xóa mà sinh bút toán đảo (`reversal`).

## 2. CẤU TRÚC NHÂN SỰ, ĐỊNH MỨC & MIỄN GIẢM
- Trục thời gian: Quản lý theo Danh mục Năm học (`faculty.academic.year`).
- Hồ sơ Giảng viên (`faculty.lecturer`):
  + Tách riêng 4 trường độc lập:
    1. Chức vụ (`admin_position`): Chỉ chọn 1 trong 3 (`can_bo`: Cán bộ, `pho_khoa`: Phó Trưởng khoa, `truong_khoa`: Trưởng khoa) hoặc để trống.
    2. Chức danh giảng dạy (`academic_rank`): `tro_giang` (Trợ giảng), `giang_vien` (Giảng viên), `giang_vien_chinh` (Giảng viên chính), `giang_vien_cao_cap` (Giảng viên cao cấp), hoặc không có.
    3. Học vị (`degree`): Cử nhân, Thạc sĩ, Tiến sĩ.
    4. Học hàm (`academic_title`): Không, Phó Giáo sư, Giáo sư (Khi nhập liệu điền luôn Chức danh giảng dạy tương ứng).
  + Checkbox `is_visiting` (Giảng viên thỉnh giảng): Thực hiện chế độ và tính định mức theo chức danh như giảng viên cơ hữu.
- Định mức & Miễn giảm:
  + Menu "Định mức chức danh & miễn giảm" chứa bảng cấu hình định mức chuẩn theo Chức danh (Giờ Giảng dạy, Giờ NCKH, Giờ Hoạt động khác). Không có chức danh/học hàm thì định mức = 0; nếu có nhiều mức thì lấy mức cao nhất. Hồ sơ giảng viên tự động nhảy định mức gốc.
  + Bảng nhập liệu Miễn giảm thủ công (theo Năm học): Lý do miễn giảm (nhập tay có gợi ý), Tỷ lệ giảm (%, trần tối đa 100%), Phạm vi áp dụng (`teaching`, `research`, hoặc `both` - không miễn giảm cho Hoạt động khác), File minh chứng tải lên.
  + Công thức: Định mức sau miễn giảm = Định mức gốc - Tổng giờ miễn giảm.

## 3. BA NHÓM CÔNG VIỆC & THUẬT TOÁN BÙ TRỪ CHÉO (TRÊN `faculty.workload.balance`)
Hệ thống dùng bảng hệ số quy đổi động (`Số lượng * Hệ số = Giờ chuẩn`) cho 3 nhóm:
1. Giảng dạy (`teaching`): Chia làm 2 nhánh:
   - Giờ lên lớp trực tiếp (Lịch giảng học phần).
   - Giờ quy đổi giảng dạy khác (Chương trình ĐT, lịch khảo thí, hồ sơ bài giảng, hướng dẫn khóa luận/luận văn/luận án/NCKH sinh viên, thực hành, thực tập).
2. Nghiên cứu khoa học (`research`): Bài báo WoS/Scopus/trong nước, đề tài các cấp/lý luận, tổ chức hội thảo/tọa đàm, tham luận, sáng kiến, biên soạn học liệu, ngân hàng câu hỏi thi, sách, xây dựng CTĐT & đề cương chi tiết.
3. Hoạt động khác (`other`): Sinh hoạt chuyên môn/chuyên đề, TDTT, Đảng - Đoàn, tuyển sinh, tuyển dụng, tổ chức lớp bồi dưỡng. (Mục riêng độc lập, KHÔNG miễn giảm, KHÔNG bù trừ).

* Hệ thống biến số & Thuật toán tính toán (tổng hợp bằng `_read_group` từ các bút toán `posted`):
- A: Định mức giờ giảng dạy sau miễn giảm (`net_teaching_quota`).
- B = 0.5 * A: Định mức lên lớp tối thiểu (`min_classroom_quota`).
- b: Giờ lên lớp thực tế của giảng viên (`actual_classroom_hours`).
- a = b + Giờ quy đổi giảng dạy khác: Tổng số giờ giảng đạt được trong năm (`total_teaching_hours`).
- C: Định mức NCKH sau miễn giảm (`net_research_quota`).
- c: Số giờ NCKH quy đổi thực tế (`actual_research_hours`).
- m = max(0, a - A): Giá trị giờ giảng vượt định mức ban đầu (khi a > A).
- n = max(0, b - B): Số giờ lên lớp thừa so với mốc 50% định mức (khi b > B).
- o = max(0, c - C): Giá trị giờ NCKH vượt định mức ban đầu (khi c > C).
- Hệ số quy đổi động trong `res.config.settings`: `rate_t_to_r` (Giảng dạy -> NCKH) và `rate_r_to_t` (NCKH -> Giảng dạy).

* Quy trình xét bù trừ chéo và tính tiền:
1. Chiều Giảng dạy bù cho NCKH (khi a > A tức m > 0, và c < C):
   - Điều kiện được bù: Giờ NCKH thực tế phải đạt tối thiểu 25% định mức (c >= 0.25 * C).
   - Nếu thỏa điều kiện: Trích từ m nhân với `rate_t_to_r` bù sang c cho đến khi c_sau = C (hoặc dùng hết m). Giờ giảng dạy sau bù trừ là a_sau = a - phần_m_đã_dùng (luôn >= A).
2. Chiều NCKH bù cho Giảng dạy (khi a < A và c > C tức o > 0):
   - Trích từ o nhân với `rate_r_to_t` bù sang a cho đến khi a_sau = A (hoặc dùng hết o). Giờ NCKH sau bù trừ là c_sau = c - phần_o_đã_dùng (luôn >= C).
3. Chốt trạng thái hoàn thành & Tính tiền thừa giờ:
   - Số giờ thừa giảng dạy luôn ghi nhận là `n = max(0, b - B)`.
   - Nếu sau bù trừ mà `a_sau < A`: Đánh dấu "Không hoàn thành nhiệm vụ giảng dạy", Thành tiền = 0.
   - Nếu sau bù trừ mà `c_sau < C`: Đánh dấu "Không đạt giờ NCKH", Thành tiền = 0.
   - Nếu sau bù trừ mà `a_sau >= A` VÀ `c_sau >= C`: Hoàn thành nhiệm vụ. Nếu `n > 0` thì được tính tiền vượt giờ: `Thành tiền = n * số_tiền_1_giờ_giảng` (áp dụng cho cả trường hợp m > 0 ban đầu lẫn trường hợp a < A được o bù lên đủ a_sau = A).
   - Giờ NCKH vượt định mức (o) không được tính tiền như giờ thừa giảng dạy.

## 4. THƯ VIỆN SỐ NỘI BỘ (DMS) & DỰ TOÁN THANH TOÁN
- Thư viện nội bộ (`faculty.research.library` kế thừa `ir.attachment`): Lưu trữ trên máy chủ nội bộ gồm: (1) Minh chứng công trình NCKH (tác giả, năm, tạp chí, DOI, file PDF) liên kết với bút toán sổ cái; (2) Văn bản quy định, quy trình, biểu mẫu của Khoa/Trường (Word/PDF).
- Dự toán & Thanh toán (`faculty.budget`): Quản lý kinh phí mời giảng, mời báo cáo thực tế, tổ chức lớp, thực hành, thực tập và thanh toán tiền vượt giờ (`n * đơn giá`).
- Luồng duyệt chung: Dự thảo (`draft`) -> Chờ Trưởng khoa duyệt (`to_approve`) -> Đã duyệt (`approved` / `posted`).