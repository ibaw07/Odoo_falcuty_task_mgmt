# -*- coding: utf-8 -*-
"""Wizard Xuất Báo cáo Excel 2 Sheet (.xlsx)
Phục vụ tổng hợp Giờ chuẩn, Bù trừ chéo, Đánh giá xếp loại & Báo cáo tháng.
Hoàn chỉnh với openpyxl: Header hành chính, 3 Phần bảng, Footer ký số.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64
from datetime import date


class FacultyExcelReportWizard(models.TransientModel):
    _name = 'faculty.excel.report.wizard'
    _description = 'Wizard Xuất Báo cáo Excel 2 Sheet (Giờ chuẩn & Công việc)'

    # 1. Phạm vi xuất báo cáo
    report_scope = fields.Selection([
        ('personal', '1. Cá nhân Giảng viên'),
        ('department', '2. Tổng hợp Toàn Khoa'),
        ('monthly', '3. Báo cáo Kết quả Tháng N & Kế hoạch Tháng N+1'),
    ], string='Phạm vi xuất báo cáo', default='personal', required=True)

    # 2. Tham số thời gian & đối tượng
    academic_year_id = fields.Many2one(
        'faculty.academic.year',
        string='Năm học',
        required=True,
        default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False
    )
    semester_id = fields.Many2one(
        'faculty.academic.semester',
        string='Học kỳ',
        domain="[('academic_year_id', '=', academic_year_id)]"
    )
    month = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string='Tháng báo cáo', default=lambda self: str(date.today().month))

    lecturer_id = fields.Many2one(
        'faculty.lecturer',
        string='Giảng viên',
        default=lambda self: (
            self.env['faculty.lecturer'].search([('user_id', '=', self.env.user.id)], limit=1) or
            self.env['faculty.lecturer'].search([('partner_id', '=', self.env.user.partner_id.id)], limit=1)
        )
    )

    # 3. Tùy chọn bản xuất (Ký tươi hoặc Chữ ký số)
    signature_mode = fields.Selection([
        ('wet_ink', 'Bản in ký tươi (GV ký nháy, Trưởng khoa ký xác nhận)'),
        ('digital_sign', 'Bản gắn chữ ký số (Chèn ảnh chữ ký cá nhân signature_image)'),
    ], string='Chế độ ký duyệt', default='wet_ink', required=True,
       help='Bản ký tươi để in ra giấy trình ký; Bản chữ ký số dùng lưu hành số hóa nội bộ.')

    # 4. Lưu file kết quả xuất
    excel_file = fields.Binary(string='File kết quả (.xlsx)', readonly=True, attachment=True)
    file_name = fields.Char(string='Tên tệp Excel', readonly=True)
    state = fields.Selection([
        ('draft', 'Chọn tham số'),
        ('get', 'Tải file kết quả'),
    ], default='draft', string='Trạng thái')

    @api.onchange('report_scope')
    def _onchange_report_scope(self):
        if self.report_scope != 'personal':
            self.lecturer_id = False
        else:
            if not self.lecturer_id:
                lec = (self.env['faculty.lecturer'].search([('user_id', '=', self.env.user.id)], limit=1) or
                       self.env['faculty.lecturer'].search([('partner_id', '=', self.env.user.partner_id.id)], limit=1))
                self.lecturer_id = lec.id if lec else False

    def action_back_to_draft(self):
        """Quay lại bước chọn tham số để xuất báo cáo khác"""
        self.ensure_one()
        self.write({'state': 'draft', 'excel_file': False, 'file_name': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_export_excel(self):
        """
        Xuất báo cáo Excel 2 Sheet hoàn chỉnh bằng openpyxl:
        - Sheet 1: Thống kê Giờ chuẩn & Bù trừ (3 Phần riêng biệt, header hành chính,
                   merge cells tiêu đề nhóm, border mảnh, Times New Roman)
        - Sheet 2: Tổng hợp chi tiết toàn bộ Công việc Đã làm (phục vụ đánh giá cuối năm)
        - Footer: 3 cột ký duyệt; chế độ digital_sign chèn ảnh chữ ký số từ signature_image
                  và lưu ir.attachment để lưu hành số hóa nội bộ.
        """
        self.ensure_one()
        if self.report_scope == 'personal' and not self.lecturer_id:
            raise UserError(_('Vui lòng chọn Giảng viên cần xuất báo cáo cá nhân!'))

        # ---------- Tên file chuẩn hành chính ----------
        year_name = self.academic_year_id.name.replace('/', '_') if self.academic_year_id else str(date.today().year)
        if self.report_scope == 'personal':
            lec_code = self.lecturer_id.lecturer_code or f"GV{self.lecturer_id.id}"
            file_name = f"Bao_cao_Gio_chuan_Ca_nhan_{lec_code}_{year_name}.xlsx"
        elif self.report_scope == 'department':
            file_name = f"Bao_cao_Tong_hop_Gio_chuan_Khoa_{year_name}.xlsx"
        else:
            file_name = f"Bao_cao_Ket_qua_Thang_{self.month}_Ke_hoach_Thang_Ke_tiep_{year_name}.xlsx"

        # ---------- Sinh nội dung workbook ----------
        excel_bytes = self._generate_excel_content()

        self.write({
            'state': 'get',
            'excel_file': base64.b64encode(excel_bytes),
            'file_name': file_name,
        })

        # ---------- Lưu ir.attachment (bản số hóa nội bộ) ----------
        self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(excel_bytes),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'description': (
                f"Bản lưu trữ số hóa nội bộ – {file_name} – "
                f"Xuất ngày {date.today().strftime('%d/%m/%Y')}"
            ),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ==========================================================================
    # HELPER: SINH NỘI DUNG EXCEL
    # ==========================================================================

    def _generate_excel_content(self):
        """Hàm sinh nội dung nhị phân của tệp Excel 2 Sheet hoàn chỉnh."""
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise UserError(_(
                'Thư viện openpyxl chưa được cài đặt. '
                'Vui lòng chạy: pip install openpyxl'
            ))

        output = io.BytesIO()
        wb = openpyxl.Workbook()

        # Sheet 1: Thống kê Giờ chuẩn & Bù trừ
        ws1 = wb.active
        ws1.title = "1. Thống kê Giờ chuẩn & Bù trừ"
        self._render_sheet1_hours(ws1, openpyxl)

        # Sheet 2: Tổng hợp Tất cả Công việc Đã làm
        ws2 = wb.create_sheet(title="2. Tổng hợp Công việc Đã làm")
        self._render_sheet2_tasks(ws2, openpyxl)

        wb.save(output)
        return output.getvalue()

    # --------------------------------------------------------------------------
    # SHEET 1: THỐNG KÊ GIỜ CHUẨN & BÙ TRỪ
    # --------------------------------------------------------------------------

    def _render_sheet1_hours(self, ws, openpyxl):
        """
        Sheet 1 hoàn chỉnh:
          - Header chuẩn hành chính (Quốc hiệu, Tên Trường/Khoa, Tiêu đề)
          - 3 Phần bảng riêng biệt (Merge Cells tiêu đề nhóm, border mảnh)
          - Footer ký duyệt 3 cột + chèn ảnh chữ ký số nếu digital_sign
        """
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers
        from openpyxl.utils import get_column_letter
        import openpyxl.drawing.image as oxl_img

        TNR = 'Times New Roman'
        thin = Side(style='thin')
        border_thin = Border(left=thin, right=thin, top=thin, bottom=thin)

        def _st(bold=False, size=11, italic=False, color='000000', name=TNR):
            return Font(name=name, size=size, bold=bold, italic=italic, color=color)

        def _al(h='left', v='center', wrap=False):
            return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

        def _fill(hex_color):
            return PatternFill(start_color=hex_color, end_color=hex_color, fill_type='solid')

        def _apply_border(ws, min_row, max_row, min_col, max_col):
            for r in range(min_row, max_row + 1):
                for c in range(min_col, max_col + 1):
                    ws.cell(row=r, column=c).border = border_thin

        # ── Lấy thông tin Trường / Khoa từ cấu hình hệ thống ──────────────────
        ICP = self.env['ir.config_parameter'].sudo()
        school_name = ICP.get_param('faculty_work_mgmt.school_name', default='TRƯỜNG ĐẠI HỌC ...')
        dept_name   = ICP.get_param('faculty_work_mgmt.department_name', default='KHOA ĐÀO TẠO ĐẠI HỌC')
        # Tỷ lệ quy đổi bù trừ GD→NCKH lấy từ cấu hình (mặc định 1.0)
        try:
            cross_ratio = float(ICP.get_param('faculty_work_mgmt.cross_offset_ratio', default='1.0'))
        except (ValueError, TypeError):
            cross_ratio = 1.0

        today = date.today()
        year_label = self.academic_year_id.name if self.academic_year_id else str(today.year)
        sem_label  = self.semester_id.name if self.semester_id else 'Cả năm học'

        # ── PHẦN A: HEADER HÀNH CHÍNH ─────────────────────────────────────────
        # Xác định tổng số cột của bảng để merge hợp lý
        # Phần 1: 10 cột (STT + Họ tên + Chức danh + GD×7)
        # Phần 2: 6 cột (NCKH×6)
        # Phần 3: 3 cột (HĐK×3)
        # Tổng: STT(1) + Info(2) + GD(8) + NCKH(6) + HDK(3) = 20 cột
        TOTAL_COLS = 20
        LAST_COL   = TOTAL_COLS  # alias

        # Hàng 1: Quốc hiệu Tiêu ngữ (bên phải, cột 13–20)
        ws.merge_cells(start_row=1, start_column=13, end_row=1, end_column=LAST_COL)
        c = ws.cell(row=1, column=13,
                    value='CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM')
        c.font = _st(bold=True, size=12)
        c.alignment = _al(h='center')

        ws.merge_cells(start_row=2, start_column=13, end_row=2, end_column=LAST_COL)
        c = ws.cell(row=2, column=13,
                    value='Độc lập – Tự do – Hạnh phúc')
        c.font = _st(bold=True, size=11, italic=True)
        c.alignment = _al(h='center')

        ws.merge_cells(start_row=3, start_column=13, end_row=3, end_column=LAST_COL)
        c = ws.cell(row=3, column=13,
                    value='─────────────────────────')
        c.alignment = _al(h='center')

        # Hàng 1-3: Tên Trường / Khoa bên trái (cột 1–12)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=12)
        c = ws.cell(row=1, column=1, value=school_name.upper())
        c.font = _st(bold=True, size=12)
        c.alignment = _al(h='left')

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=12)
        c = ws.cell(row=2, column=1, value=dept_name.upper())
        c.font = _st(bold=True, size=11)
        c.alignment = _al(h='left')

        # Hàng 4: Tiêu đề báo cáo ở giữa
        ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=LAST_COL)
        c = ws.cell(row=4, column=1,
                    value=f'BẢNG THỐNG KÊ GIỜ CHUẨN VÀ BÙ TRỪ NGHĨA VỤ')
        c.font = _st(bold=True, size=14)
        c.alignment = _al(h='center')

        ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=LAST_COL)
        c = ws.cell(row=5, column=1,
                    value=f'Năm học: {year_label}   |   Học kỳ: {sem_label}')
        c.font = _st(italic=True, size=11)
        c.alignment = _al(h='center')

        # Nếu báo cáo cá nhân: thêm dòng thông tin GV
        data_start_row = 7
        if self.report_scope == 'personal' and self.lecturer_id:
            lec = self.lecturer_id
            ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=LAST_COL)
            c = ws.cell(row=6, column=1,
                        value=(f'Họ và tên: {lec.name}   |   Mã GV: {lec.lecturer_code}'
                               f'   |   Cấp bậc: {lec.rank_position_display or ""}'))
            c.font = _st(italic=True, size=11)
            c.alignment = _al(h='left')
            data_start_row = 8

        # ── PHẦN B: HEADER BẢNG 3 PHẦN (2 hàng tiêu đề) ────────────────────

        # Bố cục cột (1-based):
        # 1=STT, 2=Họ tên, 3=Chức danh
        # PHẦN 1 – GIẢNG DẠY: 4-11 (8 cột)
        #   4=Định mức gốc GD  5=Giờ miễn giảm  6=ĐM sau giảm
        #   7=ĐM Giờ giảng(50%)
        #   8=Tổng số giờ TT GD  9=Giờ giảng TT (đứng lớp thuần)
        #   10=Thừa/Thiếu GD  11=Bù trừ GD
        # PHẦN 2 – NCKH: 12-17 (6 cột)
        #   12=ĐM NCKH  13=Miễn giảm NCKH  14=ĐM sau giảm NCKH
        #   15=Giờ TT NCKH  16=Thừa/Thiếu NCKH  17=Bù trừ NCKH
        # PHẦN 3 – HOẠT ĐỘNG KHÁC: 18-20 (3 cột)
        #   18=ĐM HĐK  19=Giờ TT HĐK  20=Ghi chú HĐK

        H1 = data_start_row        # hàng tiêu đề nhóm lớn
        H2 = data_start_row + 1   # hàng tiêu đề cột

        FILL_GD   = _fill('1F4E79')   # xanh đậm – Giảng dạy
        FILL_NCKH = _fill('375623')   # xanh lá – NCKH
        FILL_HDK  = _fill('7B3F00')   # nâu – Hoạt động khác
        FILL_BASE = _fill('2E4057')   # tối chung cho STT/Info

        def _hdr1(ws, row, col_start, col_end, text, fill):
            ws.merge_cells(start_row=row, start_column=col_start,
                           end_row=row, end_column=col_end)
            c = ws.cell(row=row, column=col_start, value=text)
            c.font = Font(name=TNR, size=10, bold=True, color='FFFFFF')
            c.fill = fill
            c.alignment = _al(h='center', wrap=True)
            c.border = border_thin

        def _hdr2(ws, row, col, text, fill):
            c = ws.cell(row=row, column=col, value=text)
            c.font = Font(name=TNR, size=9, bold=True, color='FFFFFF')
            c.fill = fill
            c.alignment = _al(h='center', v='center', wrap=True)
            c.border = border_thin

        # ─── Hàng H1: tiêu đề nhóm lớn ───────────────────────────────────────
        # STT + Họ tên + Chức danh → merge 2 hàng
        for col in [1, 2, 3]:
            ws.merge_cells(start_row=H1, start_column=col,
                           end_row=H2, end_column=col)
        labels_base = ['STT', 'Họ và tên', 'Chức danh / Cấp bậc']
        for i, lbl in enumerate(labels_base, start=1):
            _hdr2(ws, H1, i, lbl, FILL_BASE)

        # Nhóm PHẦN 1 – GIẢNG DẠY (cột 4–11)
        _hdr1(ws, H1, 4, 11,
              'PHẦN 1 – GIẢNG DẠY', FILL_GD)
        # Sub-header GD: hàng con "Giờ thực tế" span 2 cột (8-9)
        # Merge "Giờ thực tế" lên nhưng cột 8 & 9 là sub-cột → ta làm 2 tầng
        # Cột 4–7 và 10–11 trực tiếp xuống H2
        gd_cols = {
            4:  'Giờ định mức',
            5:  'Giờ miễn giảm',
            6:  'Định mức sau giảm',
            7:  'Giờ giảng ĐM\n(= 50% ĐM sau giảm)',
            10: 'Thừa / Thiếu',
            11: 'Bù trừ',
        }
        for col, lbl in gd_cols.items():
            ws.merge_cells(start_row=H1 + 1 - 1, start_column=col,
                           end_row=H1 + 1 - 1, end_column=col)
            # Sửa: các cột đơn trong PHẦN 1 merge từ H1+1 xuống H2
            # Nhưng H1 đã dùng cho group label, nên sub dùng H2 trực tiếp
            _hdr2(ws, H2, col, lbl, FILL_GD)

        # "Giờ thực tế" gộp 2 cột con 8–9 ở tầng H1+0 (tức H1, nhưng đã merge group)
        # → Ta tạo tầng trung gian bằng cách adjust: header group GD ở H1 cột 4–11
        #   và header trung gian "Giờ thực tế" ở H2 cột 8–9 (merge 2 cột)
        ws.merge_cells(start_row=H2, start_column=8, end_row=H2, end_column=9)
        c = ws.cell(row=H2, column=8, value='Giờ thực tế')
        c.font = Font(name=TNR, size=9, bold=True, color='FFFFFF')
        c.fill = FILL_GD
        c.alignment = _al(h='center', wrap=True)
        c.border = border_thin
        # Thêm hàng phụ H3 cho 2 sub-cột con của "Giờ thực tế"
        H3 = H2 + 1
        ws.merge_cells(start_row=H1, start_column=8, end_row=H1, end_column=9)  # merge lại H1 vì đã merge group
        # Vì _hdr1 đã merge H1 4→11, ta cần split lại ô con: dùng H3
        # → Thực tế ta dùng mô hình: H1=group, H2=sub-group, H3=leaf col
        # Để đơn giản, hạ tầng xuống 1 hàng: dùng H1+H2+H3 cho GD
        # Reset: lấy lại H3 là hàng sub-sub
        sub_gd_cols = {
            8: 'Tổng số giờ\n(Giảng + Coi/Chấm thi + Ra đề...)',
            9: 'Giờ giảng\n(Đứng lớp thuần túy)',
        }
        for col, lbl in sub_gd_cols.items():
            _hdr2(ws, H3, col, lbl, FILL_GD)
        # Các cột đơn GD (4-7, 10-11): merge H2→H3 để căn đều chiều cao
        for col in [4, 5, 6, 7, 10, 11]:
            ws.merge_cells(start_row=H2, start_column=col,
                           end_row=H3, end_column=col)

        # Nhóm PHẦN 2 – NCKH (cột 12–17)
        _hdr1(ws, H1, 12, 17, 'PHẦN 2 – NGHIÊN CỨU KHOA HỌC (NCKH)', FILL_NCKH)
        nckh_hdrs = [
            'Định mức', 'Miễn giảm',
            'ĐM sau miễn giảm', 'Giờ thực tế',
            'Thừa / Thiếu', 'Bù trừ',
        ]
        for i, lbl in enumerate(nckh_hdrs, start=12):
            ws.merge_cells(start_row=H2, start_column=i, end_row=H3, end_column=i)
            _hdr2(ws, H2, i, lbl, FILL_NCKH)

        # Nhóm PHẦN 3 – HOẠT ĐỘNG KHÁC (cột 18–20)
        _hdr1(ws, H1, 18, 20,
              'PHẦN 3 – HOẠT ĐỘNG KHÁC\n(Không dùng để quy đổi bù trừ)',
              FILL_HDK)
        hdk_hdrs = ['Giờ định mức', 'Giờ thực tế', 'Ghi chú']
        for i, lbl in enumerate(hdk_hdrs, start=18):
            ws.merge_cells(start_row=H2, start_column=i, end_row=H3, end_column=i)
            _hdr2(ws, H2, i, lbl, FILL_HDK)

        # STT/Info: merge H1→H3 cho 3 cột đầu
        for col in [1, 2, 3]:
            # Đã merge H1→H2 ở trên, cần extend thêm H3
            ws.merge_cells(start_row=H1, start_column=col,
                           end_row=H3, end_column=col)

        # Chiều cao hàng header
        ws.row_dimensions[H1].height = 22
        ws.row_dimensions[H2].height = 28
        ws.row_dimensions[H3].height = 36

        # ── PHẦN C: DỮ LIỆU ─────────────────────────────────────────────────

        # Lấy danh sách giảng viên cần xuất
        if self.report_scope == 'personal' and self.lecturer_id:
            lecturers = self.lecturer_id
        else:
            lecturers = self.env['faculty.lecturer'].search([])

        # Lấy dữ liệu sổ cái tổng hợp (1 query)
        domain = [('lecturer_id', 'in', lecturers.ids)]
        if self.academic_year_id:
            domain.append(('academic_year_id', '=', self.academic_year_id.id))
        if self.semester_id:
            domain.append(('semester_id', '=', self.semester_id.id))
        domain.append(('date', '<=', today))

        grouped = self.env['faculty.hour.ledger']._read_group(
            domain=domain,
            groupby=['lecturer_id', 'category', 'activity_type'],
            aggregates=['standard_hours:sum'],
        )

        # Index: {lecturer_id: {(category, activity_type): sum_hours}}
        stats = {}
        for l_rec, cat, atype, h_sum in grouped:
            if not l_rec:
                continue
            lid = l_rec.id
            stats.setdefault(lid, {})
            stats[lid][(cat, atype)] = h_sum or 0.0

        # Các activity_type thuộc "Tổng số giờ GD" (cột 8)
        TEACHING_TOTAL_TYPES = {
            'lecture', 'exam_proctoring', 'exam_grading',
            'exam_audit', 'exam_creation', 'thesis_guidance', 'internship',
        }

        cur_row = H3 + 1
        stt = 1

        for lec in lecturers:
            l_stats = stats.get(lec.id, {})

            # ── Tính Giảng dạy ────────────────────────────────────────────────
            t_norm_base    = lec.teaching_norm_base or 0.0
            # Tổng % miễn giảm = base - reduced
            t_reduced      = lec.teaching_norm_reduced or 0.0
            t_exemption    = round(t_norm_base - t_reduced, 2)
            t_lecture_norm = lec.teaching_norm_lecture_50 or 0.0

            t_actual_total  = sum(
                h for (c, a), h in l_stats.items()
                if c == 'teaching' and a in TEACHING_TOTAL_TYPES
            )
            t_actual_lecture = sum(
                h for (c, a), h in l_stats.items()
                if c == 'teaching' and a == 'lecture'
            )
            t_balance = round(t_actual_total - t_reduced, 2)

            # ── Tính NCKH ────────────────────────────────────────────────────
            r_norm_base   = lec.research_norm_base or 0.0
            r_reduced     = lec.research_norm_reduced or 0.0
            r_exemption   = round(r_norm_base - r_reduced, 2)
            r_actual      = sum(h for (c, _), h in l_stats.items() if c == 'research')
            r_balance     = round(r_actual - r_reduced, 2)

            # ── Tính Hoạt động khác ─────────────────────────────────────────
            o_norm    = lec.other_norm_reduced or 0.0
            o_actual  = sum(h for (c, _), h in l_stats.items() if c == 'other')
            o_note    = ''

            # ── Bù trừ chéo GD ↔ NCKH ───────────────────────────────────────
            # Thiếu GD (t_balance < 0): nhận bù từ NCKH → GD Bù trừ = +|t_balance|
            # Thừa GD (t_balance > 0): đem bù sang NCKH (nhân cross_ratio)
            #   → GD Bù trừ = -(giờ thừa đem đi bù)
            # Ngược lại cho NCKH
            gd_offset   = 0.0
            nckh_offset = 0.0

            if t_balance < 0 and r_balance > 0:
                # GD thiếu, NCKH thừa → NCKH bù sang GD
                can_cover = round(r_balance * cross_ratio, 2)
                covered   = min(abs(t_balance), can_cover)
                gd_offset   = round(covered, 2)          # GD nhận +
                nckh_offset = round(-covered / cross_ratio, 2)  # NCKH xuất −
            elif r_balance < 0 and t_balance > 0:
                # NCKH thiếu, GD thừa → GD bù sang NCKH
                can_cover = round(t_balance / cross_ratio, 2)
                covered   = min(abs(r_balance), can_cover * cross_ratio)
                nckh_offset = round(covered, 2)            # NCKH nhận +
                gd_offset   = round(-(covered / cross_ratio), 2)  # GD xuất −

            def _fmt_offset(v):
                if v == 0:
                    return ''
                return f'+{v:.1f}' if v > 0 else f'{v:.1f}'

            # ── Ghi dòng dữ liệu vào sheet ───────────────────────────────────
            row_data = [
                stt,                            # 1  STT
                lec.name,                       # 2  Họ và tên
                lec.rank_position_display or '', # 3  Chức danh
                t_norm_base,                    # 4  Giờ định mức GD
                t_exemption,                    # 5  Giờ miễn giảm GD
                t_reduced,                      # 6  ĐM sau giảm GD
                t_lecture_norm,                 # 7  GG định mức (50%)
                t_actual_total,                 # 8  Tổng số giờ TT GD
                t_actual_lecture,               # 9  Giờ giảng TT (đứng lớp)
                t_balance,                      # 10 Thừa/Thiếu GD
                _fmt_offset(gd_offset),         # 11 Bù trừ GD
                r_norm_base,                    # 12 ĐM NCKH
                r_exemption,                    # 13 Miễn giảm NCKH
                r_reduced,                      # 14 ĐM sau miễn giảm NCKH
                r_actual,                       # 15 Giờ TT NCKH
                r_balance,                      # 16 Thừa/Thiếu NCKH
                _fmt_offset(nckh_offset),       # 17 Bù trừ NCKH
                o_norm,                         # 18 ĐM HĐK
                o_actual,                       # 19 Giờ TT HĐK
                o_note,                         # 20 Ghi chú HĐK
            ]
            ws.append(row_data)

            # Format từng ô dữ liệu
            for col_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=cur_row, column=col_idx)
                cell.font = Font(name=TNR, size=10)
                cell.border = border_thin
                cell.alignment = _al(h='center', v='center', wrap=True)
                # Số thực → định dạng 1 chữ số thập phân
                if isinstance(val, float):
                    cell.number_format = '#,##0.0'
                    # Tô màu Thừa/Thiếu
                    if col_idx in (10, 16):
                        if val < 0:
                            cell.font = Font(name=TNR, size=10, color='C00000', bold=True)
                        elif val > 0:
                            cell.font = Font(name=TNR, size=10, color='375623', bold=True)
                # Cột Bù trừ (11, 17) và text → canh trái
                if col_idx in (2, 3, 11, 17, 20):
                    cell.alignment = _al(h='left', v='center', wrap=True)
                # Cột STT → canh giữa
                if col_idx == 1:
                    cell.alignment = _al(h='center', v='center')

            cur_row += 1
            stt += 1

        # ── Độ rộng cột tự động ───────────────────────────────────────────────
        col_widths = {
            1: 5,   2: 22, 3: 20,
            4: 12,  5: 12, 6: 14, 7: 14, 8: 18, 9: 16, 10: 12, 11: 10,
            12: 10, 13: 12, 14: 14, 15: 14, 16: 12, 17: 10,
            18: 12, 19: 12, 20: 20,
        }
        for col, w in col_widths.items():
            ws.column_dimensions[get_column_letter(col)].width = w

        # ── PHẦN D: FOOTER KÝ DUYỆT ─────────────────────────────────────────
        self._render_signatures(ws, openpyxl, cur_row, TOTAL_COLS)

    # --------------------------------------------------------------------------
    # SHEET 2: TỔNG HỢP CHI TIẾT CÔNG VIỆC ĐÃ LÀM
    # --------------------------------------------------------------------------

    def _render_sheet2_tasks(self, ws, openpyxl):
        """
        Sheet 2: Liệt kê toàn bộ dòng sổ cái chi tiết phục vụ đánh giá cuối năm.
        Cột: STT | Nhóm tiêu chí | Tên công việc | Vai trò | Ngày hoàn thành |
             Số giờ ghi nhận | Kết quả / Ghi chú
        """
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter

        TNR = 'Times New Roman'
        thin = Side(style='thin')
        border_thin = Border(left=thin, right=thin, top=thin, bottom=thin)

        def _al(h='left', v='center', wrap=False):
            return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

        today = date.today()

        ICP = self.env['ir.config_parameter'].sudo()
        school_name = ICP.get_param('faculty_work_mgmt.school_name', default='TRƯỜNG ĐẠI HỌC ...')
        dept_name   = ICP.get_param('faculty_work_mgmt.department_name', default='KHOA ĐÀO TẠO ĐẠI HỌC')
        year_label  = self.academic_year_id.name if self.academic_year_id else str(today.year)

        TOTAL_COLS = 7

        # ── Header hành chính ─────────────────────────────────────────────────
        ws.merge_cells(start_row=1, start_column=5, end_row=1, end_column=TOTAL_COLS)
        c = ws.cell(row=1, column=5, value='CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM')
        c.font = Font(name=TNR, size=12, bold=True)
        c.alignment = _al(h='center')

        ws.merge_cells(start_row=2, start_column=5, end_row=2, end_column=TOTAL_COLS)
        c = ws.cell(row=2, column=5, value='Độc lập – Tự do – Hạnh phúc')
        c.font = Font(name=TNR, size=11, bold=True, italic=True)
        c.alignment = _al(h='center')

        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)
        c = ws.cell(row=1, column=1, value=school_name.upper())
        c.font = Font(name=TNR, size=12, bold=True)

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=4)
        c = ws.cell(row=2, column=1, value=dept_name.upper())
        c.font = Font(name=TNR, size=11, bold=True)

        ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=TOTAL_COLS)
        c = ws.cell(row=3, column=1,
                    value='BẢNG TỔNG HỢP CHI TIẾT CÁC CÔNG VIỆC & HOẠT ĐỘNG ĐÃ THỰC HIỆN')
        c.font = Font(name=TNR, size=13, bold=True)
        c.alignment = _al(h='center')

        ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=TOTAL_COLS)
        c = ws.cell(row=4, column=1,
                    value=f'Năm học: {year_label}   |   Ngày xuất: {today.strftime("%d/%m/%Y")}')
        c.font = Font(name=TNR, size=11, italic=True)
        c.alignment = _al(h='center')

        if self.report_scope == 'personal' and self.lecturer_id:
            lec = self.lecturer_id
            ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=TOTAL_COLS)
            c = ws.cell(row=5, column=1,
                        value=f'Giảng viên: {lec.name}   –   Mã: {lec.lecturer_code}'
                              f'   –   Chức danh: {lec.rank_position_display or ""}')
            c.font = Font(name=TNR, size=11, italic=True)
            hdr_row = 7
        else:
            hdr_row = 6

        # ── Header cột ──────────────────────────────────────────────────────────
        FILL_HDR = PatternFill(start_color='333F48', end_color='333F48', fill_type='solid')
        col_headers = [
            'STT',
            'Nhóm tiêu chí',
            'Tên công việc / Hoạt động',
            'Vai trò',
            'Ngày hoàn thành',
            'Số giờ ghi nhận',
            'Kết quả / Ghi chú',
        ]
        for col_idx, hdr in enumerate(col_headers, start=1):
            c = ws.cell(row=hdr_row, column=col_idx, value=hdr)
            c.font = Font(name=TNR, size=10, bold=True, color='FFFFFF')
            c.fill = FILL_HDR
            c.alignment = _al(h='center', v='center', wrap=True)
            c.border = border_thin
        ws.row_dimensions[hdr_row].height = 28

        # ── Lấy dữ liệu từ sổ cái ────────────────────────────────────────────
        if self.report_scope == 'personal' and self.lecturer_id:
            lecturers = self.lecturer_id
        else:
            lecturers = self.env['faculty.lecturer'].search([])

        domain = [('lecturer_id', 'in', lecturers.ids)]
        if self.academic_year_id:
            domain.append(('academic_year_id', '=', self.academic_year_id.id))
        if self.semester_id:
            domain.append(('semester_id', '=', self.semester_id.id))
        domain.append(('date', '<=', today))

        ledgers = self.env['faculty.hour.ledger'].search(
            domain, order='lecturer_id asc, date asc, id asc'
        )

        cat_label = {
            'teaching': '1. Giảng dạy',
            'research': '2. NCKH',
            'other':    '3. Hoạt động khác',
        }
        activity_label = dict(
            self.env['faculty.hour.ledger']._fields['activity_type'].selection
        )

        # Màu xen kẽ hàng
        FILL_ODD  = PatternFill(start_color='EBF3FB', end_color='EBF3FB', fill_type='solid')
        FILL_EVEN = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

        cur_row = hdr_row + 1
        stt = 1
        prev_lecturer_id = None

        for row in ledgers:
            # Kẻ phân cách khi đổi giảng viên (chế độ toàn Khoa)
            if self.report_scope != 'personal' and row.lecturer_id.id != prev_lecturer_id:
                if prev_lecturer_id is not None:
                    # Thêm 1 dòng trống phân cách
                    cur_row += 1
                prev_lecturer_id = row.lecturer_id.id

            fill = FILL_ODD if stt % 2 == 1 else FILL_EVEN
            row_vals = [
                stt,
                cat_label.get(row.category, row.category),
                # Kết hợp Tên công việc + Loại hình
                f'[{activity_label.get(row.activity_type, row.activity_type)}] {row.name}',
                row.lecturer_id.name if self.report_scope != 'personal' else '',
                row.date.strftime('%d/%m/%Y') if row.date else '',
                row.standard_hours,
                row.notes or '',
            ]
            for col_idx, val in enumerate(row_vals, start=1):
                c = ws.cell(row=cur_row, column=col_idx, value=val)
                c.font = Font(name=TNR, size=10)
                c.fill = fill
                c.border = border_thin
                c.alignment = _al(h='center', v='center', wrap=True)
                if col_idx in (3, 7):
                    c.alignment = _al(h='left', v='center', wrap=True)
                if col_idx == 6 and isinstance(val, float):
                    c.number_format = '#,##0.0'
            cur_row += 1
            stt += 1

        # ── Độ rộng cột ─────────────────────────────────────────────────────────
        col_widths_s2 = {1: 6, 2: 22, 3: 45, 4: 22, 5: 16, 6: 16, 7: 35}
        for col, w in col_widths_s2.items():
            ws.column_dimensions[get_column_letter(col)].width = w

    # --------------------------------------------------------------------------
    # FOOTER: KÝ DUYỆT & CHỮ KÝ SỐ
    # --------------------------------------------------------------------------

    def _render_signatures(self, ws, openpyxl, start_row, total_cols):
        """
        Footer 3 cột ký duyệt:
          - Người lập biểu (cột 1–5 bên trái)
          - Giảng viên ký nháy xác nhận (cột giữa)
          - Trưởng khoa / Lãnh đạo xác nhận (cột 16–20 bên phải)
        Chế độ digital_sign: chèn ảnh chữ ký số từ signature_image (base64).
        Đồng thời người lập biểu tự điền đúng tên & chữ ký số cá nhân GV.
        """
        from openpyxl.styles import Font, Alignment
        from openpyxl.drawing.image import Image as OxlImage
        import io as _io

        TNR = 'Times New Roman'
        today = date.today()
        date_str = f'Ngày {today.day} tháng {today.month} năm {today.year}'

        # Hàng ngày tháng năm (bên phải)
        date_col = max(total_cols - 4, 1)
        ws.merge_cells(start_row=start_row, start_column=date_col,
                       end_row=start_row, end_column=total_cols)
        c = ws.cell(row=start_row, column=date_col, value=date_str)
        c.font = Font(name=TNR, size=11, italic=True)
        c.alignment = Alignment(horizontal='center')

        R1 = start_row + 1  # hàng chức danh ký
        R2 = R1 + 1         # hàng "(Ký và ghi rõ họ tên)"
        R3 = R2 + 1         # hàng để trống cho chữ ký tươi / ký số
        R4 = R3 + 4         # hàng ghi tên người ký

        # ── Xác định cột cho 3 vị trí ký ─────────────────────────────────────
        # Phân chia: cột 1–6 | cột 7–13 | cột 14–total_cols
        col_left_s   = 1
        col_left_e   = min(6, total_cols)
        col_mid_s    = 7
        col_mid_e    = 13
        col_right_s  = 14
        col_right_e  = total_cols

        def _sig_header(row, col_s, col_e, title, subtitle):
            ws.merge_cells(start_row=row, start_column=col_s,
                           end_row=row, end_column=col_e)
            c = ws.cell(row=row, column=col_s, value=title)
            c.font = Font(name=TNR, size=11, bold=True)
            c.alignment = Alignment(horizontal='center')
            ws.merge_cells(start_row=row + 1, start_column=col_s,
                           end_row=row + 1, end_column=col_e)
            c2 = ws.cell(row=row + 1, column=col_s, value=subtitle)
            c2.font = Font(name=TNR, size=10, italic=True)
            c2.alignment = Alignment(horizontal='center')

        _sig_header(R1, col_left_s,  col_left_e,
                    'NGƯỜI LẬP BIỂU',
                    '(Ký và ghi rõ họ tên)')
        _sig_header(R1, col_mid_s,   col_mid_e,
                    'GIẢNG VIÊN XÁC NHẬN',
                    '(Ký nháy xác nhận số liệu)')
        _sig_header(R1, col_right_s, col_right_e,
                    'TRƯỞNG KHOA / LÃNH ĐẠO KHOA',
                    '(Ký, ghi rõ họ tên và đóng dấu)')

        # ── Ghi tên người ký ở hàng R4 ───────────────────────────────────────
        if self.report_scope == 'personal' and self.lecturer_id:
            lec_name = self.lecturer_id.name
        else:
            lec_name = self.env.user.name or ''

        ws.merge_cells(start_row=R4, start_column=col_left_s,
                       end_row=R4, end_column=col_left_e)
        c = ws.cell(row=R4, column=col_left_s, value=lec_name)
        c.font = Font(name=TNR, size=11, bold=True)
        c.alignment = Alignment(horizontal='center')

        # ── Chế độ Chữ ký số ─────────────────────────────────────────────────
        if (self.signature_mode == 'digital_sign'
                and self.report_scope == 'personal'
                and self.lecturer_id
                and self.lecturer_id.signature_image):

            try:
                sig_bytes = base64.b64decode(self.lecturer_id.signature_image)
                sig_stream = _io.BytesIO(sig_bytes)
                img = OxlImage(sig_stream)

                # Giữ tỷ lệ ảnh, tối đa 100×40 px
                max_w, max_h = 100, 40
                orig_w = img.width or max_w
                orig_h = img.height or max_h
                ratio = min(max_w / orig_w, max_h / orig_h)
                img.width  = int(orig_w * ratio)
                img.height = int(orig_h * ratio)

                # Gắn vào ô R3 cột người lập biểu (trái)
                target_cell = ws.cell(row=R3, column=col_left_s)
                from openpyxl.utils import get_column_letter
                img.anchor = f'{get_column_letter(col_left_s)}{R3}'
                ws.add_image(img)

                # Đánh dấu đã gắn chữ ký số
                ws.merge_cells(start_row=R4 + 1, start_column=col_left_s,
                               end_row=R4 + 1, end_column=col_left_e)
                c = ws.cell(row=R4 + 1, column=col_left_s,
                            value='✔ Đã gắn chữ ký số nội bộ')
                c.font = Font(name=TNR, size=9, color='375623', bold=True)
                c.alignment = Alignment(horizontal='center')

            except Exception:
                # Nếu ảnh lỗi, ghi chú thay thế
                ws.merge_cells(start_row=R3, start_column=col_left_s,
                               end_row=R3, end_column=col_left_e)
                c = ws.cell(row=R3, column=col_left_s,
                            value='[Lỗi đọc ảnh chữ ký số – kiểm tra trường signature_image]')
                c.font = Font(name=TNR, size=9, color='C00000', italic=True)
                c.alignment = Alignment(horizontal='center')

