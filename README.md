# 🎓 Hệ Thống Quản Lý Khối Lượng Giảng Dạy & Công Tác Khoa Đào Tạo (Odoo 20)

[![Odoo Version](https://img.shields.io/badge/Odoo-20.0_Community-714B67?style=flat&logo=odoo)](https://www.odoo.com)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791?style=flat&logo=postgresql)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-LGPL--3-green.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)

Module **faculty_work_mgmt** là giải pháp số hóa toàn diện công tác quản trị đào tạo, quản lý khối lượng giảng dạy, nghiên cứu khoa học và hoạt động chuyên môn của giảng viên tại các Khoa/Viện thuộc trường Đại học, Học viện (được chuẩn hóa theo mô hình thực tế của **Khoa Kinh tế - Học viện Nông nghiệp Việt Nam**).

---

## 📌 Điểm Nổi Bật & Tính Năng Cốt Lõi

### 1. Quản lý Hồ sơ Giảng viên & Chế độ Chính sách
- Quản lý học hàm (GS, PGS), học vị (TS, ThS, CN), chức danh giảng dạy (Trợ giảng, GV, GVC, GVCC) và chức vụ hành chính.
- Tự động theo dõi thâm niên ngạch bậc lương, đếm ngược và cảnh báo hạn nâng bậc lương định kỳ.
- Tự động tính toán tỷ lệ miễn giảm định mức giờ chuẩn theo quy chế (nữ nuôi con nhỏ, kiêm nhiệm quản lý, bồi dưỡng chuyên môn...).
- Cảnh báo sinh nhật và nhắc việc quản trị nhân sự.

### 2. Quản lý Lớp học phần & Kế hoạch Giảng dạy
- Quản lý chi tiết từng lớp học phần: số tín chỉ, hệ số quy đổi (lớp đông, thực hành, địa bàn), giảng viên chính, trợ giảng.
- Lập lịch giảng dạy theo buổi (Teaching Sessions), tích hợp kiểm tra trùng lịch phòng học và giảng viên.
- Wizard tự động tìm slot trống và gợi ý lịch giảng dạy tối ưu.

### 3. Khảo thí, Khóa luận & Thực tập
- **Coi thi & Chấm thi**: Phân công cán bộ coi thi (Cán bộ 1, 2), chấm thi bài thi viết, vấn đáp, thực hành; tự động tính giờ chuẩn theo hệ số.
- **Khóa luận tốt nghiệp**: Quản lý hội đồng, giảng viên hướng dẫn, người phản biện, tự động ghi nhận khối lượng khi nghiệm thu.
- **Thực tập tốt nghiệp / Thực tập nghề nghiệp**: Theo dõi sinh viên tại cơ sở thực tập, phê duyệt khối lượng hướng dẫn.

### 4. Kiến trúc Sổ Cái Giờ Giảng Thời Gian Thực (Workload Ledger)
- Toàn bộ khối lượng phát sinh được ghi nhận theo mô hình **Sổ cái kép (Ledger Entries)** với 3 trạng thái nghiêm ngặt: `Draft` (Dự thảo) -> `Posted` (Đã ghi sổ) -> `Cancel` (Đã hủy).
- Cơ chế **ACID & Anti-Stale Cache**: Tự động recompute và cập nhật bảng tổng hợp cân đối giờ (`faculty.workload.balance`) ngay khi bút toán thay đổi.
- **Xóa bỏ bút toán mồ côi**: Khi xóa buổi giảng hoặc đổi giảng viên, hệ thống tự động hủy/đảo bút toán tương ứng trong sổ cái.
- Hỗ trợ khóa an toàn dòng dữ liệu bằng cơ chế `FOR UPDATE SKIP LOCKED`.

### 5. Kê Khai Khối Lượng Khác & Phê Duyệt Đa Cấp
- Giảng viên tự kê khai các công tác ngoài giảng dạy: NCKH, biên soạn bài giảng, cố vấn học tập, công tác tuyển sinh, công tác Đảng - Đoàn thể.
- Quy trình kiểm duyệt minh bạch: Giảng viên gửi -> Trưởng bộ môn duyệt -> Ban Chủ nhiệm Khoa phê duyệt cuối cùng.

### 6. Báo Cáo Thống Kê & Xuất Dữ Liệu Excel Chuẩn
- **Xuất Báo cáo Excel 2 Sheet**:
  - **Sheet 1**: Bảng tổng hợp thanh toán thừa giờ toàn Khoa (định mức, thực hiện, giờ thanh toán).
  - **Sheet 2**: Chi tiết từng hoạt động cấu thành giờ chuẩn của từng giảng viên.
- **Dashboard Điều Hành**: Biểu đồ trực quan hóa tiến độ giảng dạy, tỷ lệ vượt định mức, phân bổ công tác theo Bộ môn.

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
├── faculty_work_mgmt/                     # Mã nguồn chính của Module Odoo 20
│   ├── __manifest__.py                   # Khai báo metadata, phụ thuộc và dữ liệu nạp
│   ├── models/                           # 6 tệp Models logic nghiệp vụ
│   │   ├── faculty_lecturer.py           # Hồ sơ giảng viên, ngạch bậc, miễn giảm
│   │   ├── faculty_config.py             # Cấu hình danh mục, định mức, hệ số
│   │   ├── faculty_teaching.py           # Học phần, lớp học, buổi giảng
│   │   ├── faculty_exam_internship.py    # Coi thi, chấm thi, khóa luận, thực tập
│   │   ├── faculty_hour_ledger.py        # Kiến trúc sổ cái giờ giảng & cân đối
│   │   └── faculty_other_work.py         # Kê khai công tác khác & Dashboard
│   ├── views/                            # Giao diện Form, Tree, Pivot, Graph, Calendar
│   ├── wizards/                          # Các cửa sổ trợ giúp & xuất báo cáo
│   ├── reports/                          # Mẫu in QWeb PDF / XML
│   ├── security/                         # Phân quyền nhóm người dùng & Access Rights
│   ├── data/                             # Dữ liệu hệ thống, Cron jobs & Scripts
│   │   ├── faculty_cron_data.xml         # Cron quét sổ cái & nâng bậc lương
│   │   └── scripts/                      # Script nạp dữ liệu & Tiếng Việt offline
│   └── tests/                            # Test cases kiểm thử tự động
├── docs/                                 # Tài liệu triển khai & hướng dẫn sử dụng
│   ├── Huong_dan_cai_dat_va_trien_khai_Odoo_20_LAN.docx  # Bản Word đầy đủ
│   ├── Huong_dan_cai_dat_va_trien_khai_Odoo_20_LAN.md    # Bản Markdown tra cứu
│   └── Bao_cao_du_lieu_mau_Khoa_Kinh_te_VNUA.md          # Cơ cấu dữ liệu mẫu VNUA
├── .archify/                             # Sơ đồ kiến trúc & ERD tương tác (HTML)
├── 1_Mo_Cong_Firewall_8069.bat            # Script mở cổng Firewall 8069 cho mạng LAN
├── 2_Nap_Tieng_Viet_Offline.bat           # Script nạp gói ngôn ngữ Tiếng Việt offline
├── 3_Nap_Du_Lieu_Mau_Khoa.bat             # Script nạp dữ liệu mẫu Khoa Kinh tế VNUA
├── 4_Khoi_Dong_Lai_Odoo.bat               # Script khởi động lại Odoo Service
└── README.md                             # Tài liệu tổng quan dự án
```

---

## 🚀 Hướng Dẫn Cài Đặt Nhanh Trong Mạng LAN Nội Bộ

### Bước 1: Chuẩn bị môi trường
1. Tải và cài đặt **Odoo 20.0 Community** (đã bao gồm PostgreSQL).
2. Đường dẫn cài đặt mặc định: `C:\Program Files\Odoo 20.0.xxxxxxxx`.

### Bước 2: Cài đặt Module
1. Sao chép thư mục `faculty_work_mgmt` vào thư mục `custom-addons` của Odoo:
   ```text
   C:\Program Files\Odoo 20.0.xxxxxxxx\server\odoo\custom-addons\faculty_work_mgmt
   ```
2. Khởi động lại dịch vụ Odoo: Chạy file `4_Khoi_Dong_Lai_Odoo.bat` (hoặc vào `services.msc` restart `odoo-server-20.0`).

### Bước 3: Kích hoạt ứng dụng trên Web
1. Mở trình duyệt truy cập: `http://localhost:8069`.
2. Đăng nhập bằng tài khoản Quản trị (`admin`).
3. Vào **Apps (Ứng dụng)** -> Bật **Developer Mode** -> Chọn **Update Apps List (Cập nhật danh sách ứng dụng)**.
4. Tìm kiếm từ khóa `faculty` hoặc `Khoa đào tạo` -> Nhấn **Activate (Kích hoạt)**.

### Bước 4: Cấu hình Mạng LAN & Nạp Dữ Liệu
1. **Mở cổng 8069 cho các máy khác truy cập**: Chuột phải vào `1_Mo_Cong_Firewall_8069.bat` -> Chọn **Run as administrator**.
2. **Kích hoạt Tiếng Việt Offline (Không cần Internet)**: Chạy `2_Nap_Tieng_Viet_Offline.bat`.
3. **Nạp dữ liệu mẫu Khoa Kinh tế VNUA**: Chạy `3_Nap_Du_Lieu_Mau_Khoa.bat`.

---

## 🔒 Cơ Chế Tài Khoản & Mật Khẩu Đăng Nhập Mạng LAN
- Trong mạng LAN không có Internet, hệ thống không gửi được email kích hoạt mật khẩu ra ngoài.
- Quản trị viên (Admin) thiết lập mật khẩu khởi tạo cho giảng viên:
  1. Vào **Cài đặt (Settings) -> Người dùng & Công ty -> Người dùng (Users)**.
  2. Chọn User -> Bấm nút **Hành động (Action)** ⚙️ -> **Đổi mật khẩu (Change Password)**.
  3. Đặt mật khẩu khởi tạo (ví dụ: `123456` hoặc Mã giảng viên).
  4. Người dùng đăng nhập lần đầu truy cập góc trên bên phải màn hình -> **Tùy chọn (Preferences)** để đổi sang mật khẩu riêng.

---

## 📄 Bản Quyền & Giấy Phép
Dự án được phân phối dưới giấy phép **LGPL-3 (GNU Lesser General Public License v3.0)**.
Phát triển cho hệ thống quản trị đào tạo đại học số hóa trên nền tảng Odoo 20.
