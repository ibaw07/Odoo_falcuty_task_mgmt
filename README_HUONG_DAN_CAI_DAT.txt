========================================================================================
   GÓI CÀI ĐẶT HOÀN CHỈNH: ODOO 20 COMMUNITY & PHẦN MỀM QUẢN LÝ KHOA ĐÀO TẠO
   Khoa Kinh tế - Học viện Nông nghiệp Việt Nam (VNUA)
========================================================================================

📁 THƯ MỤC: D:\Hoan chinh\

DANH SÁCH CÁC THÀNH PHẦN TRONG GÓI:
----------------------------------------------------------------------------------------
1. odoo_setup_20.0.20260927.exe
   -> Bộ cài đặt phần mềm Odoo 20 Community chính thức (kèm PostgreSQL).

2. faculty_work_mgmt (Thư mục) & faculty_work_mgmt.zip (Gói nén)
   -> Module Quản lý Khoa Đào tạo tích hợp 3 Trụ cột: Giảng dạy, NCKH và Hoạt động khác.

3. Huong_dan_cai_dat_va_trien_khai_Odoo_20_LAN.docx
   -> File Word tài liệu hướng dẫn hoàn chỉnh, định dạng đẹp, sẵn sàng in ấn/gửi nội bộ.

4. Huong_dan_cai_dat_va_trien_khai_Odoo_20_LAN.md
   -> File văn bản Markdown chi tiết đầy đủ kỹ thuật.

5. Bao_cao_du_lieu_mau_Khoa_Kinh_te_VNUA.md
   -> Báo cáo kiểm thử 28 bảng dữ liệu và 4 kịch bản quy chuẩn tính giờ chuẩn toán học.

6. Các tiện ích chạy tự động (Click đúp chuột):
   - 1_Mo_Cong_Firewall_8069.bat  : Mở cổng 8069 trên Tường lửa Windows cho mạng LAN.
   - 2_Nap_Tieng_Viet_Offline.bat : Nạp 100% tiếng Việt từ ổ cứng (Không cần Internet).
   - 3_Nap_Du_Lieu_Mau_Khoa.bat   : Nạp dữ liệu mẫu Khoa Kinh tế - HVNN.
   - 4_Khoi_Dong_Lai_Odoo.bat     : Khởi động lại dịch vụ Odoo 20.

========================================================================================
QUY TRÌNH CÀI ĐẶT 5 BƯỚC NHANH (QUICK START):
========================================================================================

BƯỚC 1: CÀI ĐẶT ODOO 20 COMMUNITY
- Nhấp chuột phải vào file "odoo_setup_20.0.20260927.exe" -> Chọn "Run as administrator".
- Chọn cài đặt cả 2 thành phần: "Odoo Server" và "PostgreSQL Database".
- Cấu hình tài khoản CSDL: User là 'odoo', tự đặt mật khẩu (ghi nhớ mật khẩu này).
- Sau khi cài xong, Odoo sẽ nằm tại: C:\Program Files\Odoo 20.0.xxxxxxxx\server.

BƯỚC 2: CẤU HÌNH CHO PHÉP MẠNG LAN VÀ COPY MODULE KHOA ĐÀO TẠO
- Mở file: C:\Program Files\Odoo 20.0.xxxxxxxx\server\odoo.conf bằng Notepad.
- Sửa hoặc thêm dòng:
    http_interface = 0.0.0.0
    http_port = 8069
- Copy toàn bộ thư mục "faculty_work_mgmt" vào thư mục Addons của Odoo:
    C:\Program Files\Odoo 20.0.xxxxxxxx\server\odoo\addons\faculty_work_mgmt

BƯỚC 3: MỞ CỔNG 8069 TRÊN TƯỜNG LỬA WINDOWS
- Nhấp chuột phải vào file "1_Mo_Cong_Firewall_8069.bat" -> Chọn "Run as administrator".
- Mở cửa sổ dòng lệnh gõ "ipconfig" để xem địa chỉ IP máy chủ (ví dụ: 192.168.1.105).
- Các máy khác trong cùng mạng LAN truy cập vào: http://192.168.1.105:8069

BƯỚC 4: KÍCH HOẠT MODULE TRÊN GIAO DIỆN WEB
- Truy cập vào Odoo bằng trình duyệt (http://localhost:8069).
- Đăng nhập tài khoản Administrator.
- Vào menu "Cài đặt (Settings)" -> Cuộn xuống dưới cùng chọn "Kích hoạt chế độ nhà phát triển (Activate the developer mode)".
- Vào menu "Ứng dụng (Apps)" -> Chọn "Cập nhật danh sách ứng dụng (Update Apps List)" -> Bấm Cập nhật.
- Xóa chữ "Apps" trên ô tìm kiếm, gõ từ khóa "faculty".
- Bấm nút "Kích hoạt (Activate / Install)" trên module "Quản trị & Phân công Công tác Khoa Đào tạo".

BƯỚC 5: NẠP TIẾNG VIỆT VÀ DỮ LIỆU MẪU OFFLINE
- Nhấp đúp vào file "2_Nap_Tieng_Viet_Offline.bat" để nạp tiếng Việt mà không cần Internet.
- Nhấp đúp vào file "3_Nap_Du_Lieu_Mau_Khoa.bat" để nạp dữ liệu mẫu Khoa Kinh tế.
- Nhấp chuột phải vào "4_Khoi_Dong_Lai_Odoo.bat" chọn "Run as administrator" để hoàn tất.

========================================================================================
Mọi thắc mắc và xử lý lỗi chi tiết, xin xem file:
"Huong_dan_cai_dat_va_trien_khai_Odoo_20_LAN.docx" trong thư mục này.
========================================================================================

