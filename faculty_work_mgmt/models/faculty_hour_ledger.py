# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FacultyHourLedger(models.Model):
    _name = 'faculty.hour.ledger'
    _description = 'Sổ cái Giờ chuẩn Trung tâm'
    _order = 'date desc, id desc'

    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên', required=True, index=True, ondelete='cascade')
    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, index=True, ondelete='restrict')
    semester_id = fields.Many2one('faculty.academic.semester', string='Học kỳ', index=True, ondelete='set null')
    date = fields.Date(string='Ngày thực hiện', default=fields.Date.context_today, required=True, index=True)

    category = fields.Selection([
        ('teaching', '1. Giảng dạy'),
        ('research', '2. Nghiên cứu khoa học'),
        ('other', '3. Hoạt động khác'),
    ], string='Nhóm tiêu chí', required=True, index=True,
       help='Ghi thẳng vào 3 nhóm tiêu chí chuẩn.')

    activity_type = fields.Selection([
        # Giảng dạy
        ('lecture', 'Giờ giảng đứng lớp'),
        ('exam_proctoring', 'Coi thi'),
        ('exam_grading', 'Chấm thi'),
        ('exam_audit', 'Chấm kiểm tra'),
        ('exam_creation', 'Ra đề thi mới'),
        ('thesis_guidance', 'Hướng dẫn Khóa luận / Luận văn'),
        ('internship', 'Hướng dẫn Thực hành / Thực tập'),
        # NCKH
        ('research_paper', 'Bài báo khoa học (WoS/Scopus/Trong nước)'),
        ('research_project', 'Đề tài KH&CN (Trường/Bộ/Nhà nước/Lý luận)'),
        ('research_book', 'Sách / Giáo trình / Tài liệu tham khảo'),
        ('research_workshop', 'Hội thảo / Tọa đàm khoa học'),
        ('curriculum_dev', 'Biên soạn CTĐT / Đề cương / Ngân hàng đề'),
        ('initiative', 'Sáng kiến / Giải pháp khoa học'),
        # Hoạt động khác
        ('faculty_meeting', 'Sinh hoạt chuyên môn / Chuyên đề'),
        ('party_union', 'Công tác Đảng - Đoàn thể'),
        ('sports_culture', 'Thể dục thể thao / Văn hóa'),
        ('admissions', 'Công tác Tuyển sinh / Tuyển dụng'),
        ('course_org', 'Tổ chức lớp bồi dưỡng'),
        ('functional_task', 'Phân công 6 mảng chức năng Khoa'),
        ('other', 'Hoạt động hành chính khác'),
    ], string='Loại nhiệm vụ', required=True, index=True)

    name = fields.Char(string='Diễn giải chi tiết nhiệm vụ', required=True)
    raw_hours = fields.Float(string='Số giờ/tiết gốc', default=0.0)
    coefficient = fields.Float(string='Hệ số quy đổi', default=1.0)
    standard_hours = fields.Float(string='Số giờ chuẩn quy đổi', required=True, default=0.0)

    # Nguồn gốc phát sinh (Cross-link)
    res_model = fields.Char(string='Model nguồn', index=True, help='Model phát sinh giờ chuẩn, VD: faculty.teaching.session')
    res_id = fields.Integer(string='ID nguồn', index=True, help='ID bản ghi phát sinh')

    is_locked = fields.Boolean(string='Đã chốt sổ', default=False, index=True,
                               help='Khi đã chốt sổ cuối năm, không được chỉnh sửa hoặc xóa dòng này.')
    notes = fields.Text(string='Ghi chú')

    _sql_constraints = [
        ('check_standard_hours', 'CHECK(standard_hours >= 0)', 'Số giờ chuẩn phải lớn hơn hoặc bằng 0!'),
    ]

    def unlink(self):
        for rec in self:
            if rec.is_locked:
                raise UserError(_('Không thể xóa dòng sổ cái đã chốt cuối năm: "%s"!') % rec.name)
        return super(FacultyHourLedger, self).unlink()

    def write(self, vals):
        for rec in self:
            if rec.is_locked and not (len(vals) == 1 and 'is_locked' in vals):
                raise UserError(_('Dòng sổ cái này đã chốt cuối năm, không được phép chỉnh sửa: "%s"!') % rec.name)
        return super(FacultyHourLedger, self).write(vals)

    @api.model
    def post_ledger_entry(self, vals):
        """
        Ghi sổ hoặc cập nhật dòng sổ cái tự động từ các phân hệ Giảng dạy, NCKH, Hoạt động khác.
        Chống trùng lặp dựa trên res_model + res_id + (tùy chọn activity_type + lecturer_id).
        """
        res_model = vals.get('res_model')
        res_id = vals.get('res_id')
        lecturer_id = vals.get('lecturer_id')
        activity_type = vals.get('activity_type')

        if res_model and res_id and lecturer_id:
            domain = [
                ('res_model', '=', res_model),
                ('res_id', '=', res_id),
                ('lecturer_id', '=', lecturer_id),
            ]
            if activity_type:
                domain.append(('activity_type', '=', activity_type))

            existing = self.search(domain, limit=1)
            if existing:
                if existing.is_locked:
                    raise UserError(_('Không thể ghi đè vì dòng sổ cái liên kết đã bị khóa sổ cuối năm!'))
                existing.write(vals)
                return existing

        # Nếu chưa có bản ghi, tạo mới
        return self.create(vals)

    def action_lock_year_ledger(self, academic_year_id=None):
        """
        Nút khóa chốt sổ cuối năm cho toàn bộ hoặc một năm học cụ thể
        """
        domain = [('is_locked', '=', False)]
        if academic_year_id:
            domain.append(('academic_year_id', '=', academic_year_id))
        elif self:
            domain.append(('id', 'in', self.ids))

        unlocked_entries = self.search(domain)
        unlocked_entries.write({'is_locked': True})
        return True

    def action_unlock_year_ledger(self):
        """
        Mở khóa sổ cái (Dành riêng cho Ban Chủ nhiệm Khoa / Admin)
        """
        self.ensure_one()
        self.write({'is_locked': False})
        return True
