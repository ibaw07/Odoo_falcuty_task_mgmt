# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import math


class DepartmentBackToListMixin(models.AbstractModel):
    """
    Mixin dùng chung cung cấp nút 'Quay lại danh sách' cho các Form view
    """
    _name = 'department.back.to.list.mixin'
    _description = 'Department Back To List Mixin'

    def action_back_to_list(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self._description or 'Danh sách',
            'res_model': self._name,
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current',
            'context': self.env.context,
        }


class FacultyAcademicYear(models.Model):
    _name = 'faculty.academic.year'
    _description = 'Năm học'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'date_start desc, name desc'

    name = fields.Char(string='Tên năm học', required=True, tracking=True, placeholder='VD: 2025 - 2026')
    code = fields.Char(string='Mã năm học', required=True, copy=False, index=True, placeholder='VD: 2025-2026')
    date_start = fields.Date(string='Ngày bắt đầu', required=True, default=lambda self: date(date.today().year, 8, 1), tracking=True)
    date_end = fields.Date(string='Ngày kết thúc', required=True, default=lambda self: date(date.today().year + 1, 7, 31), tracking=True)
    is_current = fields.Boolean(string='Năm học hiện tại', default=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('active', 'Đang hoạt động'),
        ('closed', 'Đã khóa sổ/Đóng'),
    ], string='Trạng thái', default='active', tracking=True)
    semester_ids = fields.One2many('faculty.academic.semester', 'academic_year_id', string='Các học kỳ')
    notes = fields.Text(string='Ghi chú')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã năm học đã tồn tại! Vui lòng chọn mã khác.'),
    ]

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start >= rec.date_end:
                raise ValidationError(_('Ngày bắt đầu năm học phải trước ngày kết thúc (Chu kỳ chuẩn 01/08 đến 31/07)!'))

    @api.constrains('is_current')
    def _check_is_current(self):
        for rec in self:
            if rec.is_current:
                others = self.search([('id', '!=', rec.id), ('is_current', '=', True)])
                if others:
                    others.write({'is_current': False})

    def action_close_year(self):
        self.ensure_one()
        self.state = 'closed'
        # Tự động chốt toàn bộ các dòng sổ cái trong năm học này
        ledgers = self.env['faculty.hour.ledger'].search([
            ('academic_year_id', '=', self.id),
            ('is_locked', '=', False)
        ])
        ledgers.write({'is_locked': True})
        return True


class FacultyAcademicSemester(models.Model):
    _name = 'faculty.academic.semester'
    _description = 'Học kỳ'
    _order = 'academic_year_id desc, sequence, date_start'

    name = fields.Char(string='Tên học kỳ', required=True, placeholder='VD: Học kỳ 1, Học kỳ 2')
    code = fields.Char(string='Mã học kỳ', required=True, placeholder='VD: HK1, HK2, HK_HE')
    sequence = fields.Integer(string='Thứ tự', default=10)
    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, ondelete='cascade', index=True)
    date_start = fields.Date(string='Từ ngày', required=True)
    date_end = fields.Date(string='Đến ngày', required=True)
    is_current = fields.Boolean(string='Học kỳ hiện tại', default=False)

    @api.constrains('date_start', 'date_end')
    def _check_semester_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start >= rec.date_end:
                raise ValidationError(_('Ngày bắt đầu học kỳ phải trước ngày kết thúc!'))


class FacultyRankConfig(models.Model):
    _name = 'faculty.rank.config'
    _description = 'Cấu hình 16 Bậc lương & Niên hạn'
    _order = 'sequence asc, id asc'

    sequence = fields.Integer(string='Bậc (1-16)', required=True, default=1)
    name = fields.Char(string='Tên bậc lương', compute='_compute_name', store=True)
    salary_coefficient = fields.Float(string='Hệ số lương', digits=(4, 2), required=True, default=2.34)
    promotion_interval_months = fields.Integer(string='Niên hạn nâng bậc (tháng)', default=36, required=True,
                                              help='Mặc định 36 tháng đối với ngạch Giảng viên, 24 tháng đối với ngạch chuyên viên/cán sự.')
    notes = fields.Text(string='Ghi chú')

    _sql_constraints = [
        ('sequence_unique', 'unique(sequence)', 'Thứ tự bậc lương phải là duy nhất (từ 1 đến 16)!'),
    ]

    @api.depends('sequence', 'salary_coefficient')
    def _compute_name(self):
        for rec in self:
            rec.name = f"Bậc {rec.sequence}/16 (Hệ số {rec.salary_coefficient:.2f})"


class FacultyTitleNorm(models.Model):
    _name = 'faculty.title.norm'
    _description = 'Định mức 3 Tiêu chí theo Chức danh'
    _inherit = ['department.back.to.list.mixin']
    _order = 'teaching_norm desc'

    name = fields.Char(string='Chức danh / Vị trí', required=True, placeholder='VD: Giảng viên, Giảng viên chính, Giáo sư...')
    code = fields.Char(string='Mã chức danh', required=True, index=True)
    academic_title = fields.Selection([
        ('none', 'Không'),
        ('assoc_prof', 'Phó Giáo sư'),
        ('prof', 'Giáo sư'),
    ], string='Học hàm', default='none')
    academic_degree = fields.Selection([
        ('bachelor', 'Cử nhân/Kỹ sư'),
        ('master', 'Thạc sĩ'),
        ('doctor', 'Tiến sĩ'),
        ('doctor_science', 'Tiến sĩ khoa học'),
    ], string='Học vị', default='master')
    teaching_norm = fields.Float(string='Định mức Giảng dạy (tiết/năm)', default=270.0, required=True,
                                help='Giờ chuẩn giảng dạy tối thiểu hàng năm theo quy định của Bộ GD&ĐT.')
    research_norm = fields.Float(string='Định mức NCKH (giờ/năm)', default=600.0, required=True,
                                help='Giờ chuẩn Nghiên cứu khoa học tối thiểu hàng năm.')
    other_norm = fields.Float(string='Định mức Hoạt động khác (giờ/năm)', default=100.0, required=True,
                             help='Giờ chuẩn tham gia công tác chuyên môn, Đảng, đoàn thể, tuyển sinh...')
    notes = fields.Text(string='Găn chú / Căn cứ pháp lý')


class FacultyNormReduction(models.Model):
    _name = 'faculty.norm.reduction'
    _description = 'Quy định Miễn giảm Định mức'
    _inherit = ['department.back.to.list.mixin']
    _order = 'reduction_type, id'

    name = fields.Char(string='Tên chế độ miễn giảm', required=True, placeholder='VD: Trưởng bộ môn, Đi học thạc sĩ/tiến sĩ >= 4 tuần...')
    reduction_type = fields.Selection([
        ('position', 'Chức vụ lãnh đạo / Kiêm nhiệm'),
        ('study', 'Cử đi học / Bồi dưỡng (>= 4 tuần)'),
        ('maternity', 'Nghỉ thai sản / Ốm đau dài hạn'),
        ('special', 'Đặc cách / Miễn giảm khác'),
    ], string='Loại miễn giảm', required=True, default='position')
    position_title = fields.Char(string='Chức danh kiêm nhiệm')
    percent_teaching = fields.Float(string='% Giảm Giảng dạy', default=0.0)
    percent_research = fields.Float(string='% Giảm NCKH', default=0.0)
    percent_other = fields.Float(string='% Giảm HĐ khác', default=0.0)
    study_weeks = fields.Integer(string='Số tuần đi học (>= 4 tuần)', default=0,
                                 help='Nếu đi học >= 4 tuần, tỷ lệ giảm tự động = (Số tuần / 44) * 100%')
    notes = fields.Text(string='Ghi chú / Căn cứ')

    @api.onchange('study_weeks', 'reduction_type')
    def _onchange_study_weeks(self):
        if self.reduction_type == 'study' and self.study_weeks >= 4:
            calc_ratio = min((self.study_weeks / 44.0) * 100.0, 100.0)
            self.percent_teaching = round(calc_ratio, 2)
            self.percent_research = round(calc_ratio, 2)
            self.percent_other = round(calc_ratio, 2)


class FacultyNormConfig(models.Model):
    _name = 'faculty.norm.config'
    _description = 'Bảng Quy chuẩn Giờ chuẩn Động'
    _inherit = ['department.back.to.list.mixin']

    name = fields.Char(string='Tên bảng quy chuẩn', required=True, default='Bảng Quy chuẩn Giờ chuẩn Khoa Đào tạo')
    academic_year_id = fields.Many2one('faculty.academic.year', string='Áp dụng cho Năm học')
    active = fields.Boolean(string='Đang áp dụng', default=True)

    # Hệ số lớp đông
    large_class_threshold = fields.Integer(string='Ngưỡng lớp đông (HV)', default=40, required=True,
                                          help='Lớp có sĩ số từ ngưỡng này trở lên sẽ được nhân hệ số lớp đông.')
    large_class_coeff = fields.Float(string='Hệ số lớp đông (>= 40 HV)', default=1.2, digits=(3, 2), required=True)

    # Đơn giá khảo thí
    proctoring_rate = fields.Float(string='Đơn giá Coi thi (giờ chuẩn/buổi)', default=1.5, required=True)
    grading_rate_essay = fields.Float(string='Đơn giá Chấm thi Tự luận (giờ/bài)', default=0.05, required=True)
    grading_rate_multiple_choice = fields.Float(string='Đơn giá Chấm thi Trắc nghiệm (giờ/bài)', default=0.02, required=True)
    grading_rate_report = fields.Float(string='Đơn giá Chấm Tiểu luận / Báo cáo (giờ/bài)', default=0.08, required=True)
    grading_rate_oral = fields.Float(string='Đơn giá Chấm thi Vấn đáp (giờ/học viên)', default=0.1, required=True)

    # Định mức ra đề mới
    exam_creation_essay_norm = fields.Float(string='Định mức Ra đề Tự luận mới (giờ/đề)', default=5.0, required=True)
    exam_creation_oral_norm = fields.Float(string='Định mức Ra câu hỏi Vấn đáp (giờ/câu)', default=1.0, required=True)
    exam_creation_report_norm = fields.Float(string='Định mức Ra chủ đề Tiểu luận (giờ/chủ đề)', default=2.0, required=True)
    notes = fields.Text(string='Ghi chú cấu hình')


class FacultyExamGradingRule(models.Model):
    _name = 'faculty.exam.grading.rule'
    _description = 'Bảng Quy tắc Khảo thí Chấm kiểm tra Động'
    _order = 'min_students asc'

    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Mô tả quy tắc', compute='_compute_name', store=True)
    min_students = fields.Integer(string='Từ sĩ số (HV)', required=True, default=1)
    max_students = fields.Integer(string='Đến sĩ số (HV)', required=True, default=40)
    audit_type = fields.Selection([
        ('fixed', 'Số lượng bài cố định (bài)'),
        ('percent', 'Tỷ lệ % trên sĩ số (%)'),
    ], string='Cách tính bài kiểm tra', default='fixed', required=True)
    audit_value = fields.Float(string='Giá trị kiểm tra (Bài hoặc %)', default=5.0, required=True)
    notes = fields.Char(string='Ghi chú')

    @api.depends('min_students', 'max_students', 'audit_type', 'audit_value')
    def _compute_name(self):
        for rec in self:
            val_str = f"{rec.audit_value:.0f} bài" if rec.audit_type == 'fixed' else f"{rec.audit_value:.1f}%"
            rec.name = f"Sĩ số {rec.min_students} - {rec.max_students} HV ➔ Chấm kiểm tra: {val_str}"

    @api.model
    def calculate_audit_count(self, student_count):
        """
        Tính số bài chấm kiểm tra ngẫu nhiên dựa trên sĩ số học viên
        """
        if student_count <= 0:
            return 0
        rule = self.search([
            ('min_students', '<=', student_count),
            ('max_students', '>=', student_count),
        ], limit=1)
        if not rule:
            # Quy tắc fallback nếu ngoài dải: 5% sĩ số, tối thiểu 3 bài
            return max(3, int(math.ceil(student_count * 0.05)))
        if rule.audit_type == 'fixed':
            return int(min(rule.audit_value, student_count))
        else:
            return int(math.ceil(student_count * (rule.audit_value / 100.0)))


class FacultyPaymentRegulation(models.Model):
    _name = 'faculty.payment.regulation'
    _description = 'Quy định Thanh toán'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'sequence asc, id asc'

    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên hoạt động / Loại thanh toán', required=True, tracking=True,
                       placeholder='VD: Thanh toán Mời giảng, Mời Báo cáo viên, Tổ chức lớp...')
    payment_category = fields.Selection([
        ('guest_teaching', 'Mời giảng'),
        ('guest_speaker', 'Mời báo cáo viên thực tế'),
        ('class_org', 'Tổ chức lớp'),
        ('internship', 'Tổ chức thực hành, thực tập'),
        ('research', 'Nghiên cứu khoa học & Hội thảo'),
        ('other', 'Nội dung chi khác'),
    ], string='Phân loại thanh toán', required=True, default='guest_teaching', tracking=True)

    # Căn cứ pháp lý: Số văn bản - Ngày ban hành
    document_number = fields.Char(string='Số văn bản', required=True, tracking=True, placeholder='VD: 125/QĐ-ĐH')
    document_date = fields.Date(string='Ngày ban hành', required=True, tracking=True, default=fields.Date.context_today)
    basis_display = fields.Char(string='Căn cứ', compute='_compute_basis_display', store=True,
                                help='Hiển thị cột Căn cứ theo định dạng: Số văn bản - Ngày')

    # File đính kèm quy định
    attachment_file = fields.Binary(string='File đính kèm văn bản', attachment=True)
    attachment_filename = fields.Char(string='Tên file đính kèm')

    line_ids = fields.One2many('faculty.payment.regulation.line', 'regulation_id', string='Các mục chi / Định mức đơn giá')
    notes = fields.Text(string='Ghi chú')

    @api.depends('document_number', 'document_date')
    def _compute_basis_display(self):
        for rec in self:
            if rec.document_number and rec.document_date:
                date_str = rec.document_date.strftime('%d/%m/%Y')
                rec.basis_display = f"{rec.document_number} - {date_str}"
            elif rec.document_number:
                rec.basis_display = rec.document_number
            else:
                rec.basis_display = ''


class FacultyPaymentRegulationLine(models.Model):
    _name = 'faculty.payment.regulation.line'
    _description = 'Chi tiết Mục chi Quy định Thanh toán'
    _order = 'sequence, id'

    regulation_id = fields.Many2one('faculty.payment.regulation', string='Quy định thanh toán', ondelete='cascade', index=True)
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên mục chi', required=True, placeholder='VD: Tiết giảng Thạc sĩ, Tiết giảng Giáo sư, Bồi dưỡng đón tiếp...')
    unit = fields.Char(string='Đơn vị tính', default='Tiết/Buổi', required=True)
    standard_rate = fields.Float(string='Định mức / Đơn giá (VNĐ)', required=True, default=0.0)
    formula_desc = fields.Char(string='Công thức tính / Căn cứ áp dụng', placeholder='VD: Số tiết x Đơn giá x Hệ số')
    notes = fields.Char(string='Ghi chú')


class FacultyWorkflowProcess(models.Model):
    _name = 'faculty.workflow.process'
    _description = 'Quy trình & Biểu mẫu Quy định của Trường/Khoa'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'category, sequence, id'

    sequence = fields.Integer(string='Thứ tự', default=10)
    name = fields.Char(string='Tên quy trình / Quy định', required=True, tracking=True,
                       placeholder='VD: Quy trình Tổ chức thi kết thúc học phần, Quy trình Nghiệm thu đề tài...')
    code = fields.Char(string='Mã quy trình', copy=False, placeholder='VD: QT-ĐT-01')
    category = fields.Selection([
        ('training', 'Đào tạo & Quản lý Học vụ'),
        ('research', 'Nghiên cứu khoa học'),
        ('other', 'Hoạt động khác & Quản lý Khoa'),
    ], string='Lĩnh vực áp dụng', default='training', required=True, tracking=True)
    version = fields.Char(string='Phiên bản', default='1.0', required=True, tracking=True)
    effective_date = fields.Date(string='Ngày hiệu lực', default=fields.Date.context_today, tracking=True)

    # File Word/PDF quy định cho phép tra cứu và cập nhật phiên bản
    attachment_file = fields.Binary(string='File quy định (Word/PDF)', attachment=True)
    attachment_filename = fields.Char(string='Tên tệp đính kèm')

    step_ids = fields.One2many('faculty.workflow.step', 'process_id', string='Các bước thực hiện')
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('waiting_dean', 'Chờ Trưởng khoa duyệt'),
        ('approved', 'Đã duyệt / Ban hành'),
    ], string='Trạng thái', default='draft', tracking=True)
    notes = fields.Text(string='Ghi chú')

    def action_submit(self):
        for rec in self:
            rec.state = 'waiting_dean'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'


class FacultyWorkflowStep(models.Model):
    _name = 'faculty.workflow.step'
    _description = 'Bước Quy trình & Biểu mẫu Kèm theo'
    _order = 'sequence, id'

    process_id = fields.Many2one('faculty.workflow.process', string='Quy trình', ondelete='cascade', index=True)
    sequence = fields.Integer(string='Bước số', default=10)
    name = fields.Char(string='Nội dung công việc', required=True, placeholder='VD: Bước 1: Lập kế hoạch giảng dạy...')
    form_template_name = fields.Char(string='Tên biểu mẫu / Mẫu báo cáo', placeholder='VD: Mẫu 01/KHGD-ĐT')
    attachment_template = fields.Binary(string='File biểu mẫu mẫu', attachment=True)
    attachment_template_filename = fields.Char(string='Tên file biểu mẫu')
    responsible_role = fields.Char(string='Vai trò thực hiện', default='Giảng viên / Giáo vụ')
    notes = fields.Text(string='Ghi chú / Yêu cầu chi tiết')
