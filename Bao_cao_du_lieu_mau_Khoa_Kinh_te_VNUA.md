# Báo cáo Xây dựng Cơ sở Dữ liệu Mẫu Toàn diện: Khoa Kinh tế - Học viện Nông nghiệp Việt Nam (VNUA)

Cơ sở dữ liệu mẫu thực tế của **Khoa Kinh tế - Học viện Nông nghiệp Việt Nam** đã được khởi tạo thành công 100% vào database `Quantrikhoa`. Toàn bộ các mục trên thanh menu nghiệp vụ và 28 model dữ liệu đã được nạp dữ liệu liên hoàn, phản ánh chân thực đặc thù đào tạo kinh tế nông nghiệp, nông thôn và phát triển bền vững.

---

## 1. Tổng quan Bản ghi Dữ liệu Đã Khởi tạo

| STT | Phân hệ / Trụ cột | Model Kỹ thuật | Số lượng Bản ghi | Mô tả Nghiệp vụ |
|:---:|:---|:---|:---:|:---|
| 1 | **Cấu hình & Thang bậc** | `faculty.rank.config` | **16** | Đầy đủ 16 bậc lương viên chức giảng dạy theo NĐ 204 |
| 2 | **Cấu hình & Thang bậc** | `faculty.title.norm` | **6** | Định mức 3 tiêu chí: GS, PGS, GVC, GV, Trợ giảng |
| 3 | **Cấu hình & Thang bậc** | `faculty.norm.reduction` | **7** | Miễn giảm: Trưởng khoa (30%), Phó khoa (20%), Đi học (50%)... |
| 4 | **Niên giám Học vụ** | `faculty.academic.year` | **3** | Năm học 2025-2026 (Hiện hành), 2024-2025... |
| 5 | **Niên giám Học vụ** | `faculty.academic.semester` | **4** | Học kỳ 1, Học kỳ 2 theo năm học |
| 6 | **Khảo thí & Định mức** | `faculty.norm.config` | **1** | Bảng quy chuẩn giờ chuẩn & ngưỡng lớp đông >= 40 (x 1.2) |
| 7 | **Khảo thí & Định mức** | `faculty.exam.grading.rule` | **3** | Quy tắc chấm kiểm tra động: Cố định 5 bài hoặc 15%, 10% |
| 8 | **Chế độ Tài chính** | `faculty.payment.regulation` | **1** | Quyết định 125/QĐ-HVNN-KT: Định mức thực hành, thực tập |
| 9 | **Hồ sơ Giảng viên** | `faculty.lecturer` | **10** | Giảng viên nòng cốt Khoa Kinh tế (kèm LLKH 15 mục) |
| 10 | **Trụ cột 1: Giảng dạy** | `faculty.curriculum` | **4** | CTĐT: KT Nông nghiệp, QTKD Nông nghiệp, KT Phát triển |
| 11 | **Trụ cột 1: Giảng dạy** | `faculty.course` | **9** | Học phần chuyên ngành (Vi mô NN, KT lượng NN, Chuỗi NS...) |
| 12 | **Trụ cột 1: Giảng dạy** | `faculty.course.syllabus` | **7** | Đề cương chi tiết học phần đã kích hoạt áp dụng |
| 13 | **Trụ cột 1: Giảng dạy** | `faculty.student.class` | **6** | Lớp K67, K68, K69 (sĩ số từ 38 đến 52, tự nhân hệ số 1.2) |
| 14 | **Trụ cột 1: Giảng dạy** | `faculty.class.course` | **5** | Học phần theo lớp (Trục trung tâm điều phối học vụ) |
| 15 | **Trụ cột 1: Giảng dạy** | `faculty.teaching.session` | **33** | Lịch giảng chi tiết: đã giảng, dạy thay, tương lai, trùng lịch |
| 16 | **Trụ cột 1: Giảng dạy** | `faculty.academic.checklist` | **35** | Checklist 7 bước học vụ: Tím (Quá hạn), Đỏ (Khẩn cấp), Xanh (Xong) |
| 17 | **Trụ cột 1: Giảng dạy** | `faculty.thesis.guidance` | **3** | Khóa luận ĐH, Luận văn ThS, Đề tài NCKH Sinh viên |
| 18 | **Trụ cột 1: Giảng dạy** | `faculty.internship.project` | **1** | Đợt Thực tập Nghề nghiệp tại HTX Nông nghiệp CNC Ba Vì |
| 19 | **Trụ cột 2: NCKH** | `faculty.research.work` | **4** | Scopus Q1, Đề tài cấp Bộ NN&PTNT, Sách giáo trình, Tạp chí |
| 20 | **Trụ cột 3: Hoạt động khác** | `faculty.other.work` | **4** | SHCM Bộ môn, Tư vấn tuyển sinh ĐBSH, Hội nghị CBVC, Thể thao |
| 21 | **Quản trị Chức năng** | `faculty.stream.assignment` | **6** | Phân công nhiệm vụ theo 6 mảng chức năng cốt lõi của Khoa |
| 22 | **Thư viện Khoa** | `faculty.library.category` | **3** | Thư mục: Giáo trình, Quy chế đào tạo, Kỷ yếu & Đề tài |
| 23 | **Thư viện Khoa** | `faculty.library.document` | **3** | Tài liệu đính kèm file mẫu trong hệ thống Odoo Filestore |
| 24 | **Tờ khai & Sổ cái** | `faculty.manual.declaration` | **2** | 1 Tờ khai đã duyệt ghi sổ, 1 Tờ khai chờ duyệt |
| 25 | **Sổ cái Giờ chuẩn** | `faculty.hour.ledger` | **49** | Toàn bộ bút toán giờ chuẩn chính thức (`state = 'posted'`) |
| 26 | **Cân đối & Thanh toán** | `faculty.workload.balance` | **6** | Bảng cân đối tính toán tự động 4 kịch bản quy chuẩn |
| 27 | **Lịch Công tác Chung** | `faculty.calendar.event` | **43** | Lịch đồng bộ tự động theo thời gian thực (Google Calendar view) |
| 28 | **Điều hành Thông minh** | `faculty.dashboard` | **23** | Bảng Dashboard KPI giám sát sinh nhật, nâng bậc, cảnh báo |

---

## 2. Minh họa 4 Kịch bản Bù trừ Giờ chuẩn Toán học Chuẩn xác

Dữ liệu của 4 Giảng viên nòng cốt minh chứng 100% cho 4 kịch bản quy chuẩn được quy định trong nghiệp vụ:

### 🟢 Kịch bản 1: Hoàn thành Nhiệm vụ & Tính Tiền Vượt giờ
- **Giảng viên**: **PGS.TS. Trần Đình Thao** (`GV_VNUA_01` - Trưởng khoa)
- **Định mức sau miễn giảm 30%**:
  - Giảng dạy: $A = 320 \times (1 - 0.3) = 224$ tiết
  - Sàn lên lớp tối thiểu: $B = 0.5 \times A = 112$ tiết
  - NCKH: $C = 240 \times (1 - 0.3) = 168$ giờ
- **Thực tế đạt được**:
  - Lên lớp trực tiếp: $b = 178.0$ tiết $\rightarrow$ Giờ vượt lên lớp: $n = 178 - 112 = 66.0$ tiết
  - Giờ quy đổi khác: $110.0$ tiết $\rightarrow$ Tổng giờ giảng: $a = 288.0$ tiết ($> 224$)
  - NCKH thực tế: $c = 200.0$ giờ ($> 168$)
- **Kết luận**: **Hoàn thành nhiệm vụ**
  - Giờ vượt thanh toán: **$66.0$ giờ**
  - Tiền vượt giờ ($66 \times 150.000$đ): **9.900.000 VNĐ**

---

### 🔵 Kịch bản 4: Thiếu Giờ Giảng dạy ($a < A$), Thừa NCKH $\rightarrow$ Bù trừ NCKH sang Giảng dạy
- **Giảng viên**: **TS. Nguyễn Thị Minh Hiền** (`GV_VNUA_02` - Phó Trưởng khoa)
- **Định mức sau miễn giảm 20%**:
  - Giảng dạy: $A = 240$ tiết, Sàn $B = 120$ tiết
  - NCKH: $C = 160$ giờ
- **Thực tế ban đầu**:
  - Lên lớp trực tiếp: $b = 170.0$ tiết (thừa lên lớp $n = 50.0$ tiết)
  - Tổng giờ giảng: $a = 205.0$ tiết (thiếu $35.0$ tiết so với $A = 240$)
  - NCKH thực tế: $c = 220.0$ giờ (thừa $o = 60.0$ giờ so với $C = 160$)
- **Cơ chế Bù trừ chéo**:
  - Trích $35.0$ giờ NCKH dư thừa bù sang Giảng dạy ($NCKH \rightarrow GD = 35.0$).
  - Sau bù trừ: $a_{sau} = 240.0$ tiết ($= A$), $c_{sau} = 185.0$ giờ ($> C$).
- **Kết luận**: **Hoàn thành nhiệm vụ**
  - Giờ vượt thanh toán: **$50.0$ giờ**
  - Tiền vượt giờ ($50 \times 150.000$đ): **7.500.000 VNĐ**

---

### 🟡 Kịch bản 3: Thừa Giờ Giảng dạy ($m > 0$), Thiếu NCKH Đạt Sàn 25% $\rightarrow$ Bù trừ Giảng dạy sang NCKH
- **Giảng viên**: **TS. Bùi Thị Nga** (`GV_VNUA_03` - Trưởng Bộ môn Phân tích KT & Kinh tế lượng)
- **Định mức sau miễn giảm 30%**:
  - Giảng dạy: $A = 210$ tiết, Sàn $B = 105$ tiết
  - NCKH: $C = 140$ giờ (Sàn 25%: $35$ giờ)
- **Thực tế ban đầu**:
  - Lên lớp trực tiếp: $b = 179.0$ tiết (thừa lên lớp $n = 74.0$ tiết)
  - Tổng giờ giảng: $a = 259.0$ tiết (thừa $m = 49.0$ tiết)
  - NCKH thực tế: $c = 120.0$ giờ (thiếu $20.0$ giờ, nhưng $120 \ge 35$ đạt điều kiện sàn)
- **Cơ chế Bù trừ chéo**:
  - Trích $20.0$ tiết Giảng dạy bù đắp sang NCKH ($GD \rightarrow NCKH = 20.0$).
  - Sau bù trừ: $c_{sau} = 140.0$ giờ ($= C$), $a_{sau} = 239.0$ tiết ($> A$).
- **Kết luận**: **Hoàn thành nhiệm vụ**
  - Giờ vượt thanh toán: **$74.0$ giờ**
  - Tiền vượt giờ ($74 \times 150.000$đ): **11.100.000 VNĐ**

---

### ⚪ Kịch bản 2: Đạt Tổng Giờ Giảng ($a \ge A$), Đủ NCKH, Nhưng Thiếu Lên Lớp ($b < B$)
- **Giảng viên**: **ThS. Vũ Ngọc Huyên** (`GV_VNUA_04` - Bí thư Đoàn khoa / Giảng viên)
- **Định mức**:
  - Giảng dạy: $A = 280$ tiết, Sàn lên lớp: $B = 140$ tiết
  - NCKH: $C = 160$ giờ
- **Thực tế**:
  - Lên lớp trực tiếp: $b = 118.4$ tiết ($< 140$ tiết $\rightarrow$ Không có giờ vượt lên lớp: $n = 0$)
  - Giờ quy đổi khác: $185.0$ tiết $\rightarrow$ Tổng $a = 303.4$ tiết ($> 280$)
  - NCKH sau bù trừ: $c_{sau} = 160.0$ giờ ($= C$)
- **Kết luận**: **Hoàn thành nhiệm vụ**
  - Giờ vượt thanh toán: **$0.0$ giờ**
  - Tiền vượt giờ: **0 VNĐ** (Quy chế: không đủ sàn lên lớp trực tiếp thì không được thanh toán tiền vượt giờ dù tổng số giờ rất cao).

---

## 3. Các Tính năng Đặc thù Khoa Kinh tế Đã Có Dữ liệu Sẵn sàng

1. **Chuỗi Checklist Học vụ 7 Bước**:
   - Bước 5 (Bảng điểm điều kiện dự thi): Đặt cờ màu **Tím** (Quá hạn) để kiểm tra giao diện cảnh báo.
   - Bước 6 (Coi thi kết thúc học phần): Đặt cờ màu **Đỏ** (Khẩn cấp $\le 3$ ngày).
   - Bước 1 & 2: Trạng thái màu **Xanh** (Đã hoàn thành).
2. **Quy tắc Khảo thí & Lớp đông**:
   - Lớp có sĩ số $\ge 40$ học viên (như K67A: 46 SV, K68KTE: 52 SV) tự động nhân hệ số $1.2$.
   - Tự động chia bài chấm kiểm tra động: Lớp nhỏ 5 bài, lớp trung bình 15%, lớp lớn 10%.
3. **Thực hành, Thực tập Nghề nghiệp**:
   - Đợt thực tế tại HTX Nông nghiệp Công nghệ cao Ba Vì có đầy đủ 3 Tab: Thành phần đoàn (Trưởng đoàn, thành viên), Tài liệu kế hoạch và Bảng dự toán chi phí tự động nạp từ Quyết định 125/QĐ-HVNN-KT.
4. **Lịch Công tác Toàn Khoa (Calendar View)**:
   - 43 sự kiện tự động đồng bộ từ lịch giảng, lịch thi, hạn chấm thi và các sự kiện công tác chung.
5. **Dashboard Điều hành Real-time**:
   - Tự động hiển thị các cảnh báo sinh nhật trong 7 ngày tới (Thầy Thao, Cô Hiền) và cảnh báo đến hạn nâng bậc lương trong 60 ngày tới.

---

## 4. Vị trí File Kịch bản Khởi tạo trong Source Code

- **Script trong module**: [populate_vnua_data.py](file:///d:/odoo_faculty_workspace/faculty_work_mgmt/data/scripts/populate_vnua_data.py)
- **Addons Odoo**: [populate_vnua_data.py](file:///C:/Program%20Files/Odoo%2020.0.20260927/server/odoo/addons/faculty_work_mgmt/data/scripts/populate_vnua_data.py)
- **Gói nén cài đặt**: [faculty_work_mgmt.zip](file:///d:/odoo_faculty_workspace/faculty_work_mgmt.zip)
