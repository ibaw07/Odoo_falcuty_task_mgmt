# DỰ ÁN: MODULE QUẢN LÝ CÔNG VIỆC KHOA ĐÀO TẠO ĐẠI HỌC VN (ODOO 20)

## 1. MỤC TIÊU & PHẠM VI NGHIỆP VỤ CỐT LÕI
Module `faculty_work_mgmt` chạy trên Odoo 20 Community (Offline/LAN On-Premise), quản lý toàn diện công việc của một Khoa đào tạo tại trường đại học Việt Nam:

### 1.1. Quản lý Giảng viên & Lý lịch Khoa học (LLKH 15 Mục)
- Kế thừa ủy quyền `_inherits = {'res.partner': 'partner_id'}` (tận dụng sẵn họ tên, điện thoại, email, địa chỉ, ảnh đại diện). Hỗ trợ đồng bộ LAN với Web App nội bộ (`http://192.168.100.98:5000/users`).
- **Phân quyền 4 cấp & Cờ ủy quyền trực quan:** Gồm Admin, Trưởng khoa, Phó khoa, Cán bộ/Giảng viên; tích hợp 5 cờ phân quyền nhanh trên hồ sơ (`can_edit_subjects`, `can_edit_classes`, `can_edit_exams`, `can_edit_faculty_tasks`, `can_manage_hr`) tự động đồng bộ sang `res.groups`.
- **Phát triển đội ngũ & Lãnh đạo quản lý:** Theo dõi quy hoạch chức danh, lộ trình cử đi học/bồi dưỡng (đi học >= 4 tuần tự động tính giảm trừ định mức theo công thức `Số tuần / 44`), theo dõi 16 bậc lương và **tự động tạo nhiệm vụ nhắc cán bộ Quản lý nhân sự trước 60 ngày** đến hạn nâng bậc.
- **Giao diện Hồ sơ cá nhân tinh gọn:**
  + BỎ các ô định mức/miễn giảm/thực tế rời rạc ở đầu trang; BỎ ô "Cơ chế bù trừ chéo" khỏi hồ sơ cá nhân; TẮT hoàn toàn popup "Danh sách giảng viên" hiện thừa khi đưa chuột (hover).
  + Chỉ hiển thị **3 Ô Tiêu chí (1. Giảng dạy - 2. NCKH - 3. Hoạt động khác)**: Cả 3 ô đều có mục **Định mức** ở đầu ô và **Bảng liệt kê các nhiệm vụ/hoạt động thực tế được quy đổi** ở bên dưới (lấy trực tiếp từ Sổ cái Giờ chuẩn `faculty.hour.ledger`).
  + Trong **Ô Tiêu chí 1 (Giảng dạy)**: Hiển thị rõ *Định mức sau giảm*, *Giờ giảng định mức (= 50% định mức giảng dạy sau giảm)*, *Giờ giảng thực tế (chỉ tính giờ đứng lớp thuần túy)*, và *Tổng số giờ thực tế (= Giờ giảng đứng lớp + Coi thi + Chấm thi + Chấm kiểm tra + Ra đề mới)*.
- **Tab Lý lịch Khoa học (Đủ 15 mục chuẩn + Nút In/Xuất LLKH):**
  + Gồm thông tin cá nhân, cấp bậc/chức vụ (hiển thị dạng `"Bậc 12/16 - Trưởng khoa"`), quá trình đào tạo, thời gian công tác, văn bằng SHTT & công trình áp dụng thực tiễn, nhiệm vụ KH&CN, giải thưởng, thành tựu.
  + Mục **Công trình khoa học đã công bố**: Cho phép tích chọn **tối đa 5 công trình tiêu biểu** (`is_top_selected`) khi xuất LLKH. Cuối trang in có Ngày tháng năm, "Cá nhân giảng viên lập" (ký nháy) và "Đại diện lãnh đạo xác nhận".

### 1.2. Quản lý 3 Nhóm Công việc Chính (3 Trụ cột Nghiệp vụ)

#### A. Nhóm 1 - Giảng dạy (Ghi vào Ô Tiêu chí 1):
1. **Chương trình đào tạo (`faculty.curriculum`):** Bỏ nút "Chuyển dự thảo" (đã duyệt là một chiều). Khi bấm nút **"Hết hiệu lực"** (`state = 'expired'`), khóa cứng CTĐT và **tự động ẩn toàn bộ các Học phần thuộc CTĐT đó** khỏi mục Học phần và Môn học.
2. **Học phần & Đề cương chi tiết (`faculty.course` & `faculty.course.syllabus`):**
   - Giao diện danh sách Học phần có cột **Số thứ tự (STT)** đánh số tự động.
   - Cửa sổ Form Học phần: Đổi nhãn thành **"Số tiết BT, TL, KT, BCTT"**; bỏ cụm từ "(tối thiểu 2 giảng viên)" và **cho phép lưu khi chỉ có 1 giảng viên**; hỗ trợ học phần đơn và học phần tích hợp nhiều môn con (`is_composite`).
   - Đề cương chi tiết: Đổi thành **"Năm áp dụng"** (chọn năm ban hành thực tế), bỏ nhóm biên soạn, bỏ nút gửi phê duyệt, thay bằng nút **"Áp dụng"** (bấm là áp dụng ngay).
3. **Danh sách lớp (`faculty.student.class`) & Học phần theo Kỳ (`faculty.class.course`):**
   - Đổi tên "Mở lớp học phần" thành **"Danh sách lớp"**: Nhập Mã CTĐT, Tên lớp, Tổng số học viên (sĩ số >= 40 tự nhân hệ số `1.2`), Phân loại lớp (Chính khóa / Học bù / Học cải thiện), Phòng học, Năm học.
   - Bên dưới chọn **Học kỳ 1** (hoặc thêm **Học kỳ 2**) và chọn các Học phần của kỳ đó: Thông tin môn học tự nhảy sang, người dùng chỉ điền **Từ ngày (`start_date`) - Đến ngày (`end_date`)** và **Số học viên học bù/ghép thêm (nếu có)**.
   - Hỗ trợ tạo đợt Học phần Học bù / Cải thiện riêng biệt (chọn GV dạy bù, lịch dạy bù, chạy quy trình như lớp nguyên bản) và Wizard gợi ý lịch trống giảng viên.
4. **Lịch giảng chi tiết (`faculty.teaching.session`):**
   - Hiển thị các học phần từ Danh sách lớp và **sắp xếp theo thứ tự Ngày bắt đầu học (`start_date`)**.
   - Giảng viên quản lý học phần nhập tại đây:
     + Ngày học từng buổi (Sáng/Chiều, 1-4 tiết) và **GV đứng lớp từng buổi** (hỗ trợ báo bận/dạy thay tự chuyển giờ cho người dạy thay; cảnh báo vàng trùng lịch `has_conflict` không chặn lưu). **Không tính giờ riêng cho soạn giáo án**.
     + **Báo cáo viên thực tế (nếu có)**: Nhập thủ công thông tin báo cáo viên, ngày báo cáo (liên kết sang Dự toán mời báo cáo thực tế).
     + **Ngày thi, Hình thức thi** (Tự luận, Vấn đáp, Trắc nghiệm, Tiểu luận) và Nguồn đề (**"Ra đề mới"** hoặc **"Ngân hàng đề thi"** cho mọi hình thức thi).
   - **Cơ chế tích "Đã ra đề" độc quyền:** Mặc định tất cả GV giảng dạy môn đó đều thấy ô tích "Đã ra đề". Ngay khi **1 giảng viên tự giác tích "Đã ra đề"**, hệ thống tự động: (1) Khóa cứng ô tích của các GV còn lại, (2) Gửi thông báo cho các GV còn lại biết, và (3) Chỉ khi nguồn đề là **"Ra đề mới"** mới tính giờ chuẩn ra đề vào Ô Tiêu chí 1 (theo định mức cấu hình Khoa: 3 đề tự luận/học phần, 5 câu vấn đáp/tín chỉ, 2 chủ đề tiểu luận/tín chỉ...).
5. **Lịch thi & Khảo thí (`faculty.exam.assignment`):**
   - Tự động hiển thị lịch thi từ Lịch giảng chi tiết sang.
   - **Giáo vụ khoa** nhập: **Ngày/Hạn chấm thi và chấm kiểm tra** (nếu lịch bị lùi, Giáo vụ sửa ngày tại đây thì tự động cập nhật theo ngày mới, không sinh bản ghi mới).
   - Phân công nhân sự bằng nút linh hoạt: **"Thêm cán bộ coi thi"** (tự động ẩn hoàn toàn nếu hình thức thi là **Tiểu luận**), **"Thêm cán bộ chấm thi"** (Chấm 1, Chấm 2 hưởng 100% theo sĩ số bài thi, không chia đôi), và **"Thêm cán bộ chấm kiểm tra"** (2 người chấm thẩm định random lại một số bài, tính theo **Bảng quy tắc khảo thí động `faculty.exam.grading.rule`** tại Cấu hình Khoa).
   - Quy trình khảo thí: Đầu năm Trưởng khoa duyệt kế hoạch tổng thể; đầu mỗi tháng Giáo vụ nhập lịch chấm thi không cần duyệt lại -> Tự động liên kết thành Nhiệm vụ (gom theo học phần) và thông báo cho các giảng viên có tên; GV quản lý học phần theo dõi và bấm Hoàn thành. Hỗ trợ **Xuất danh sách Coi thi, Chấm thi học kỳ** (chỉ liệt kê danh sách GV tham gia và hoạt động tham gia theo mẫu hành chính).
6. **Hồ sơ bài giảng & Chuỗi Checklist 7 bước học vụ tự động:**
   - Gắn với từng học phần của lớp (do GV quản lý học phần xử lý, mỗi bước kèm tên mẫu báo cáo/giấy tờ và ghi chú): *(1) Làm Kế hoạch giảng dạy [tính vào Hoạt động khác cho GV quản lý], (2) Điền GV lịch giảng & Giáo án, (3) Làm giấy mời báo cáo thực tế [chỉ hiện nếu có BCV], (4) Nhắc đón báo cáo viên [nếu có BCV], (5) Nộp bảng điểm tổng hợp, (6) Tổ chức Coi thi [ẩn nếu Tiểu luận], (7) Hoàn thành Chấm thi & Chấm kiểm tra*.
7. **Hướng dẫn & Thực hành, Thực tập (`faculty.internship.project`):**
   - Quản lý hướng dẫn khóa luận, luận văn, luận án, NCKH sinh viên.
   - Mục **"Thực hành & thực tập"**: Học phần liên quan chọn nhiều (`Many2many`), Đơn vị tiếp nhận không bắt buộc (`required=False`), thêm trường **Địa bàn**. Khu vực **"Nội dung"** gồm 3 Tab: **Thành phần - Tài liệu - Dự toán**.

#### B. Nhóm 2 - Nghiên cứu khoa học (Ghi vào Ô Tiêu chí 2):
- Quản lý 12 loại hình (`faculty.research.work`): **(1) Bài báo (WoS/Scopus/Trong nước), (2) Đề tài (Cấp Trường/Bộ/Nhà nước), (3) Đề tài lý luận, (4) Tổ chức hội thảo, (5) Tổ chức tọa đàm, (6) Bài tham luận khoa học, (7) Sáng kiến, (8) Biên soạn học liệu, (9) Ngân hàng câu hỏi thi, (10) Sách (Chuyên khảo/Tham khảo/Hướng dẫn), (11) Xây dựng CTĐT, (12) Xây dựng đề cương chi tiết học phần**.
- **Quy tắc tính giờ Hội thảo / Tọa đàm:** Ban tổ chức, chủ tọa, báo cáo viên, tác giả viết tham luận được tính giờ NCKH; **Đại biểu chỉ tham dự không tính giờ NCKH**.
- **Cơ chế Liên kết chéo tự động (Cross-Pillar Sync):**
  + Khi nghiệm thu (`Đã duyệt`) công việc *Xây dựng CTĐT, Xây dựng đề cương chi tiết, Biên soạn học liệu, Ngân hàng câu hỏi thi* ở Nhóm 2 -> Hệ thống tự động tạo/cập nhật sang danh mục tương ứng ở Nhóm 1 (Giảng dạy) và lưu vào Thư viện Khoa.
  + Khi nghiệm thu *Bài báo, Đề tài, Sách, Sáng kiến* -> Hệ thống tự động đẩy sang mục **Công trình công bố** hoặc **Nhiệm vụ KH&CN** trong **Lý lịch Khoa học 15 mục** của các giảng viên tham gia.

#### C. Nhóm 3 - Hoạt động khác (Ghi vào Ô Tiêu chí 3 - Không dùng để quy đổi bù trừ):
- Quản lý các hoạt động (`faculty.other.work`): **(1) Sinh hoạt chuyên môn, (2) Sinh hoạt chuyên đề, (3) Thể dục thể thao, (4) Công tác Đảng - Đoàn, (5) Tuyển sinh, (6) Tuyển dụng, (7) Tổ chức lớp bồi dưỡng**, và **Bảng phân công nhiệm vụ Khoa theo 6 mảng chức năng** (hỗ trợ in biểu A4 chuẩn thể thức).
- Mọi công việc do Lãnh đạo giao hoặc Giảng viên tự khai báo thuộc nhóm tiêu chí nào thì tự động cộng giờ vào đúng nhóm tiêu chí đó.

### 1.3. Dự toán & Thanh toán Tự động (`faculty.payment.regulation` & `faculty.budget.line`)
- Áp dụng cho: **Mời giảng, Mời báo cáo thực tế, Tổ chức lớp, Tổ chức thực hành, thực tập**, Đề tài NCKH, Hội thảo/Tọa đàm, Viết tài liệu dạy học.
- Tại Cấu hình Khoa có mục **"Quy định thanh toán"**:
  + **List View** gồm đúng 4 cột: `STT | Loại thanh toán | Căn cứ (Hiển thị: Số văn bản - Ngày ban hành) | Ghi chú`.
  + **Form View** (khi click vào tên loại thanh toán): Tên hoạt động, Căn cứ pháp lý (Số văn bản, Ngày ban hành, File đính kèm), Ghi chú, và Bảng **Các khoản thanh toán** (Tên mục chi, Định mức/Đơn giá, Công thức tính, nút "Thêm mục chi").
- Tại tab **Dự toán** của các hoạt động: Người dùng chỉ nhập **Số lượng**, hệ thống tự nhân Đơn giá/Định mức ở Cấu hình Khoa thành từng dòng tiền và tổng cộng.

### 1.4. Quy trình, Biểu mẫu, Quy định & Luồng duyệt
- Quản lý quy định, quy trình làm việc của Khoa và Nhà trường về Đào tạo, NCKH, Hoạt động khác (upload file Word/PDF qua `ir.attachment` để tra cứu, tham khảo và cập nhật phiên bản khi thay đổi quy định). Mỗi bước quy trình gắn kèm **Tên mẫu báo cáo/giấy tờ** và **Ghi chú công việc**.
- **Luồng duyệt chuẩn:** `Dự thảo (draft) -> Chờ Trưởng khoa duyệt (waiting_dean) -> Đã duyệt (approved)` (Hỗ trợ Popup trả lại chọn đích danh người cần sửa; riêng Đề cương đã ban hành bấm "Áp dụng" ngay; lịch chấm thi cập nhật hàng tháng không cần duyệt lại).

### 1.5. Dashboard Real-time & Xuất Báo cáo Excel 2 Sheet (.xlsx)
- **Dashboard & Lịch chung:** Cảnh báo Quá hạn **Màu Tím (`#800080`)**, Khẩn cấp <= 3 ngày **Màu Đỏ** (Giảng viên chỉ thấy cảnh báo của mình; Lãnh đạo/Giáo vụ thấy toàn Khoa). Phần thông tin chung toàn Khoa cùng thấy: Nhắc sinh nhật (trước 7 ngày), Nhắc nâng bậc (trước 60 ngày), Bảng Thừa/Thiếu giờ Real-time (chỉ cộng buổi giảng/nhiệm vụ đã diễn ra tính đến ngày hiện tại). Lịch chung có **Popup khi đưa chuột vào (Hover)**.
- **Xuất Excel 2 Sheet + Chữ ký số:**
  + **Sheet 1 (Thống kê Giờ chuẩn & Bù trừ):** Chỉ gồm 3 phần: **(1) Giảng dạy** (`Giờ định mức | Giờ miễn giảm | Định mức sau giảm | Giờ giảng định mức [50%] | Giờ thực tế [Tổng số giờ & Giờ giảng] | Thừa/Thiếu | Bù trừ [thiếu để +, thừa đem bù để -]`); **(2) NCKH** (`Định mức | Miễn giảm | Sau giảm | Giờ thực tế | Thừa/Thiếu | Bù trừ [+/-]`); **(3) Hoạt động khác** (`Giờ định mức | Giờ thực tế | Ghi chú` - Không quy đổi bù trừ).
  + **Sheet 2 (Tổng hợp Tất cả Công việc Đã làm):** Phục vụ đánh giá, xếp loại cuối năm.
  + Tự động xuất bản ký tươi (GV ký nháy, Trưởng khoa xác nhận) và bản lưu hệ thống gắn chữ ký số (`signature_image`) của từng giảng viên.

---

## 2. QUY CHUẨN KỸ THUẬT ODOO 20 (GUARDRAILS BẮT BUỘC)
- Tên module kỹ thuật: `faculty_work_mgmt` (Depends: `['base', 'mail']`). Giao diện 100% Tiếng Việt.
- Các model nghiệp vụ chính PHẢI kế thừa `mail.thread`, `mail.activity.mixin` và `DepartmentBackToListMixin` (có nút **"Quay lại danh sách"** đồng bộ trên mọi Form).
- **Kiến trúc Tinh gọn 7 File Models:** Toàn bộ models được tổ chức gọn vào đúng 7 file trong `models/`:
  1. `faculty_config.py` (Năm học, 16 Bậc lương, Định mức, Quy chuẩn giờ, Quy tắc khảo thí động, Quy định thanh toán, Quy trình & Biểu mẫu).
  2. `faculty_hour_ledger.py` (Sổ cái Giờ chuẩn trung tâm `faculty.hour.ledger` + Chốt sổ cuối năm).
  3. `faculty_lecturer.py` (Giảng viên `_inherits res.partner`, 3 Ô Tiêu chí, Quy hoạch cán bộ, LLKH 15 mục).
  4. `faculty_teaching.py` (CTĐT, Học phần, Đề cương, Danh sách lớp, Học phần theo kỳ, Lịch giảng chi tiết, Ra đề độc quyền, Checklist 7 bước).
  5. `faculty_exam_internship.py` (Phân công Khảo thí dọc, Hướng dẫn tốt nghiệp, Thực hành & Thực tập + Dự toán).
  6. `faculty_research.py` (12 loại hình NCKH/Học liệu/Hội thảo + Dự toán + Liên kết chéo sang Giảng dạy & LLKH).
  7. `faculty_other_work.py` (7 loại Hoạt động khác, Phân công 6 mảng chức năng, Thư viện nhỏ dùng `ir.attachment` Offline).
- **Hiệu năng & Cú pháp Odoo 20:**
  + Tổng hợp giờ từ `faculty.hour.ledger` bắt buộc dùng `_read_group` (tuyệt đối không dùng vòng lặp truy vấn gây lỗi N+1 query).
  + Các trường phụ thuộc `Date.today()` (`alert_level`, `days_to_promotion`, `is_promotion_soon`) bắt buộc để `store=False` kèm hàm `search='_search_*'`.
  + Lưu trữ tệp 100% qua `ir.attachment` (`attachment=True`) trong `filestore` nội bộ.
  + XML View chuẩn Odoo 20: Dùng `<list>` (không dùng `<tree>`), `<chatter/>`, `invisible="..."`, `readonly="..."`.

---

## 3. QUY CHẾ PHÂN VAI 4 AI & TIẾT KIỆM TOKEN TRONG ANTIGRAVITY IDE
Để tránh hết token giữa chừng, bất kỳ AI nào đang thực thi nhiệm vụ phải tuân thủ nghiêm ngặt vai trò sau:
1. **Gemini 3.8 Flash High (Tổng thầu Thi công - 85% khối lượng):** Chịu trách nhiệm tạo cấu trúc thư mục, viết toàn bộ code khung Python của 7 file models, viết 100% các file XML Views, Menus, Security (`ir.model.access.csv`, Record Rules), QWeb PDF Reports và cập nhật `ARCHITECTURE_STATE.md`.
2. **Claude Opus 4.6 Thinking (Chuyên gia Thuật toán Lõi - 5% khối lượng):** Chỉ thực hiện rà soát và tối ưu hóa logic phức tạp bên trong các hàm Python chỉ định (`_read_group` Sổ cái, Quy tắc khảo thí động, Liên kết chéo NCKH -> Giảng dạy/LLKH). **Quy tắc khóa Token cho Opus:** Chỉ sửa trực tiếp hàm được yêu cầu bằng diff ngắn gọn, không viết lại toàn bộ file, không tạo/sửa file XML, không giải thích dài dòng.
3. **Claude Sonnet 4.6 Thinking (Chuyên gia Excel & OWL - 5% khối lượng):** Chỉ tập trung viết logic xuất báo cáo Excel 2 Sheet (`openpyxl` + chèn chữ ký số) và hiệu ứng Hover Popup trên Lịch Dashboard. **Quy tắc khóa Token cho Sonnet:** Đi thẳng vào code của file được chỉ định, không giải thích lý thuyết.
4. **GPT-OSS 120B Medium (Trợ lý Wizard & Báo cáo Phụ - 5% khối lượng):** Viết các Wizard độc lập (Gợi ý lịch trống, Xuất danh sách khảo thí học kỳ, Popup trả lại việc).

## 4. QUY TRÌNH CẬP NHẬT & GIÁM SÁT LIÊN TỤC
- Tuyệt đối cấm **tự ý sửa đổi mã nguồn đã triển khai** nếu chưa có xác nhận từ người dùng và chưa cập nhật tệp `ARCHITECTURE_STATE.md`.
- Mỗi thay đổi cần tuân theo chu trình **Tư vấn (O1) → Phản biện (O2) → Cập nhật (O3)**, đảm bảo tính ổn định hệ thống (Stability First).