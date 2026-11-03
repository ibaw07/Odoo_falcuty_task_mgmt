# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class FacultyExamAssignment(models.Model):
    _name = 'faculty.exam.assignment'
    _description = 'Phân công Khảo thí Học phần'
    _order = 'class_course_id, role, id'

    class_course_id = fields.Many2one('faculty.class.course', string='Học phần', required=True, ondelete='cascade', index=True)
    academic_year_id = fields.Many2one('faculty.academic.year', related='class_course_id.academic_year_id', store=True)
    semester_id = fields.Many2one('faculty.academic.semester', related='class_course_id.semester_id', store=True)

    lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ Khảo thí', required=True, index=True)
    role = fields.Selection([
        ('invigilator', 'Cán bộ coi thi'),
        ('grader_1', 'Cán bộ chấm thi 1'),
        ('grader_2', 'Cán bộ chấm thi 2'),
        ('checker_1', 'Cán bộ chấm kiểm tra 1'),
        ('checker_2', 'Cán bộ chấm kiểm tra 2'),
    ], string='Vai trò Khảo thí', required=True)

    paper_count = fields.Integer(string='Số bài / Số buổi', default=0, required=True)
    unit_rate = fields.Float(string='Đơn giá quy chuẩn (giờ/đơn vị)', compute='_compute_rates', store=True)
    standard_hours = fields.Float(string='Số giờ chuẩn quy đổi', compute='_compute_rates', store=True)
    notes = fields.Char(string='Ghi chú')

    @api.depends('role', 'paper_count', 'class_course_id.exam_format', 'class_course_id.total_student_count')
    def _compute_rates(self):
        norm_config = self.env['faculty.norm.config'].search([('active', '=', True)], limit=1)
        for rec in self:
            c = rec.class_course_id
            fmt = c.exam_format if c else 'essay'

            # 1. Coi thi
            if rec.role == 'invigilator':
                rate = norm_config.proctoring_rate if norm_config else 1.5
                if not rec.paper_count:
                    rec.paper_count = 1  # 1 buổi coi thi
                rec.unit_rate = rate
                rec.standard_hours = round(rec.paper_count * rate, 2)

            # 2. Chấm thi 1 & 2 (100% sĩ số, không chia đôi)
            elif rec.role in ('grader_1', 'grader_2'):
                if fmt == 'essay':
                    rate = norm_config.grading_rate_essay if norm_config else 0.05
                elif fmt == 'multiple_choice':
                    rate = norm_config.grading_rate_multiple_choice if norm_config else 0.02
                elif fmt == 'essay_paper':
                    rate = norm_config.grading_rate_report if norm_config else 0.08
                elif fmt == 'oral':
                    rate = norm_config.grading_rate_oral if norm_config else 0.1
                else:
                    rate = 0.05

                if not rec.paper_count and c and c.total_student_count:
                    rec.paper_count = c.total_student_count
                rec.unit_rate = rate
                rec.standard_hours = round(rec.paper_count * rate, 2)

            # 3. Chấm kiểm tra (Tra cứu theo Bảng quy tắc khảo thí động)
            elif rec.role in ('checker_1', 'checker_2'):
                if fmt == 'essay':
                    rate = norm_config.grading_rate_essay if norm_config else 0.05
                elif fmt == 'multiple_choice':
                    rate = norm_config.grading_rate_multiple_choice if norm_config else 0.02
                elif fmt == 'essay_paper':
                    rate = norm_config.grading_rate_report if norm_config else 0.08
                elif fmt == 'oral':
                    rate = norm_config.grading_rate_oral if norm_config else 0.1
                else:
                    rate = 0.05

                if not rec.paper_count and c:
                    total_st = c.total_student_count or 0
                    rec.paper_count = self.env['faculty.exam.grading.rule'].calculate_audit_count(total_st)
                rec.unit_rate = rate
                rec.standard_hours = round(rec.paper_count * rate, 2)
            else:
                rec.unit_rate = 0.0
                rec.standard_hours = 0.0


class FacultyThesisGuidance(models.Model):
    _name = 'faculty.thesis.guidance'
    _description = 'Hướng dẫn Khóa luận, Luận văn & NCKH Sinh viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'academic_year_id desc, id desc'

    name = fields.Char(string='Tên đề tài / Nội dung hướng dẫn', required=True, tracking=True,
                       placeholder='VD: Xây dựng hệ thống quản lý học vụ thông minh')
    code = fields.Char(string='Mã đề tài / Quyết định giao nhiệm vụ', placeholder='VD: KL-2025-01')
    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, tracking=True,
                                      default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)

    guidance_level = fields.Selection([
        ('bachelor', 'Khóa luận Tốt nghiệp Đại học'),
        ('master', 'Luận văn Thạc sĩ'),
        ('doctor', 'Luận án Tiến sĩ'),
        ('student_research', 'NCKH Sinh viên'),
    ], string='Cấp độ hướng dẫn', default='bachelor', required=True, tracking=True)

    student_names = fields.Char(string='Họ tên Sinh viên / Học viên / NCS', required=True, placeholder='VD: Nguyễn Văn Nam, Trần Thị Hoa')
    student_code = fields.Char(string='Mã sinh viên / học viên', placeholder='VD: SV2021001')
    student_count = fields.Integer(string='Số lượng sinh viên', default=1, required=True)

    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên hướng dẫn', required=True, tracking=True)
    role = fields.Selection([
        ('main', 'Hướng dẫn chính / Độc lập'),
        ('sub', 'Đồng hướng dẫn'),
    ], string='Vai trò hướng dẫn', default='main', required=True)

    standard_hours = fields.Float(string='Số giờ chuẩn quy đổi', required=True, default=20.0, tracking=True,
                                 help='Định mức giờ chuẩn theo quy định đào tạo (Đại học: ~20-25h, Thạc sĩ: ~35-40h).')
    defense_date = fields.Date(string='Ngày bảo vệ / Nghiệm thu')

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('waiting_dean', 'Chờ Trưởng khoa duyệt'),
        ('approved', 'Đã duyệt / Hoàn thành'),
    ], string='Trạng thái', default='draft', tracking=True)
    notes = fields.Text(string='Ghi chú')

    def action_submit(self):
        for rec in self:
            rec.state = 'waiting_dean'

    def action_approve(self):
        """Phê duyệt và tự động ghi giờ vào Sổ cái faculty.hour.ledger"""
        for rec in self:
            rec.state = 'approved'
            lvl_label = dict(rec._fields['guidance_level'].selection).get(rec.guidance_level)
            self.env['faculty.hour.ledger'].post_ledger_entry({
                'lecturer_id': rec.lecturer_id.id,
                'academic_year_id': rec.academic_year_id.id,
                'date': rec.defense_date or fields.Date.today(),
                'category': 'teaching',
                'activity_type': 'thesis_guidance',
                'name': f"Hướng dẫn {lvl_label}: {rec.name} ({rec.student_names})",
                'raw_hours': rec.standard_hours,
                'coefficient': 1.0,
                'standard_hours': rec.standard_hours,
                'res_model': 'faculty.thesis.guidance',
                'res_id': rec.id,
            })
            rec.message_post(body=_("Đã phê duyệt hướng dẫn và kết chuyển %s giờ chuẩn vào Sổ cái.") % rec.standard_hours)
        return True

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'


class FacultyInternshipProject(models.Model):
    _name = 'faculty.internship.project'
    _description = 'Thực hành & Thực tập'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(string='Tên đợt Thực hành / Thực tập', required=True, tracking=True,
                       placeholder='VD: Thực tập thực tế chuyên ngành CNTT tại Doanh nghiệp')
    code = fields.Char(string='Mã đợt / Kế hoạch', placeholder='VD: TT-2025-01')
    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, tracking=True,
                                      default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)

    # Học phần liên quan chọn nhiều (Many2many)
    course_ids = fields.Many2many('faculty.course', 'faculty_internship_course_rel', 'internship_id', 'course_id',
                                 string='Học phần liên quan')

    # Đơn vị tiếp nhận không bắt buộc (required=False)
    host_organization = fields.Char(string='Đơn vị tiếp nhận', required=False, placeholder='VD: Tập đoàn FPT / VNPT...')

    # Thêm trường Địa bàn
    area_location = fields.Char(string='Địa bàn', placeholder='VD: TP. Hà Nội / Khu CNC Hòa Lạc...')

    start_date = fields.Date(string='Ngày bắt đầu', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='Ngày kết thúc', required=True)

    # 3 Tab khu vực Nội dung:
    # Tab 1: Thành phần
    participant_ids = fields.One2many('faculty.internship.participant', 'project_id', string='Cán bộ tham gia hướng dẫn')

    # Tab 2: Tài liệu
    document_ids = fields.One2many('faculty.internship.document', 'project_id', string='Tài liệu & Kế hoạch đính kèm')

    # Tab 3: Dự toán
    payment_regulation_id = fields.Many2one('faculty.payment.regulation', string='Quy định thanh toán áp dụng',
                                            domain=[('payment_category', '=', 'internship')])
    budget_line_ids = fields.One2many('faculty.budget.line', 'internship_id', string='Các khoản dự toán kinh phí')
    total_budget = fields.Float(string='Tổng tiền dự toán (VNĐ)', compute='_compute_total_budget', store=True)

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('waiting_dean', 'Chờ Trưởng khoa duyệt'),
        ('approved', 'Đã duyệt / Triển khai'),
    ], string='Trạng thái', default='draft', tracking=True)
    notes = fields.Text(string='Ghi chú kế hoạch thực tập')

    @api.depends('budget_line_ids.subtotal')
    def _compute_total_budget(self):
        for rec in self:
            rec.total_budget = sum(line.subtotal for line in rec.budget_line_ids)

    @api.onchange('payment_regulation_id')
    def _onchange_payment_regulation_id(self):
        """Tự động nạp các mục chi từ Quy định thanh toán khi chọn payment_regulation_id"""
        if self.payment_regulation_id:
            lines = []
            for line in self.payment_regulation_id.line_ids:
                lines.append((0, 0, {
                    'sequence': line.sequence,
                    'payment_regulation_id': self.payment_regulation_id.id,
                    'payment_line_id': line.id,
                    'name': line.name,
                    'unit': line.unit,
                    'standard_rate': line.standard_rate,
                    'quantity': 1.0,
                    'formula_desc': line.formula_desc,
                    'notes': line.notes,
                }))
            self.budget_line_ids = [(5, 0, 0)] + lines

    def action_load_budget_lines(self):
        """Tự động nạp các mục chi từ Quy định thanh toán sang bảng Dự toán"""
        self.ensure_one()
        if not self.payment_regulation_id:
            raise UserError(_('Vui lòng chọn Quy định thanh toán áp dụng trước khi nạp mục chi!'))
        BudgetLine = self.env['faculty.budget.line']
        for line in self.payment_regulation_id.line_ids:
            BudgetLine.create({
                'internship_id': self.id,
                'sequence': line.sequence,
                'payment_regulation_id': self.payment_regulation_id.id,
                'payment_line_id': line.id,
                'name': line.name,
                'unit': line.unit,
                'standard_rate': line.standard_rate,
                'quantity': 1.0,
                'formula_desc': line.formula_desc,
                'notes': line.notes,
            })
        return True

    def action_submit(self):
        for rec in self:
            rec.state = 'waiting_dean'

    def action_approve(self):
        """Phê duyệt và kết chuyển giờ thực hành/thực tập của cán bộ vào Sổ cái"""
        for rec in self:
            rec.state = 'approved'
            for part in rec.participant_ids:
                if part.standard_hours > 0 and part.lecturer_id:
                    role_str = dict(part._fields['role'].selection).get(part.role)
                    self.env['faculty.hour.ledger'].post_ledger_entry({
                        'lecturer_id': part.lecturer_id.id,
                        'academic_year_id': rec.academic_year_id.id,
                        'date': rec.end_date or fields.Date.today(),
                        'category': 'teaching',
                        'activity_type': 'internship',
                        'name': f"Thực tập ({role_str}): {rec.name} ({part.days_count} ngày)",
                        'raw_hours': part.days_count,
                        'coefficient': 1.0,
                        'standard_hours': part.standard_hours,
                        'res_model': 'faculty.internship.participant',
                        'res_id': part.id,
                    })
            rec.message_post(body=_("Đã phê duyệt đợt thực tập và kết chuyển giờ chuẩn cho các cán bộ tham gia."))
        return True

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'


class FacultyInternshipParticipant(models.Model):
    _name = 'faculty.internship.participant'
    _description = 'Thành phần tham gia Thực tập'
    _order = 'role, id'

    project_id = fields.Many2one('faculty.internship.project', string='Đợt thực tập', required=True, ondelete='cascade', index=True)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên tham gia', required=True)
    role = fields.Selection([
        ('leader', 'Trưởng đoàn'),
        ('deputy', 'Phó đoàn'),
        ('member', 'Cán bộ hướng dẫn / Thành viên'),
    ], string='Vai trò trong đoàn', default='member', required=True)
    student_count = fields.Integer(string='Số sinh viên phụ trách', default=20)
    days_count = fields.Integer(string='Số ngày thực tế', default=5)
    standard_hours = fields.Float(string='Số giờ chuẩn quy đổi', default=15.0, required=True)
    notes = fields.Char(string='Ghi chú nhiệm vụ')


class FacultyInternshipDocument(models.Model):
    _name = 'faculty.internship.document'
    _description = 'Tài liệu Thực tập đính kèm'
    _order = 'id asc'

    project_id = fields.Many2one('faculty.internship.project', string='Đợt thực tập', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Tên tài liệu / Văn bản', required=True, placeholder='VD: Kế hoạch thực tập chi tiết, Quyết định thành lập đoàn')
    attachment_file = fields.Binary(string='Tệp đính kèm (Word/PDF)', attachment=True, required=True)
    attachment_filename = fields.Char(string='Tên file đính kèm')
    notes = fields.Char(string='Ghi chú')


class FacultyBudgetLine(models.Model):
    """
    Model Dòng Dự toán dùng chung cho:
    - Thực hành / Thực tập (internship_id)
    - Mời giảng / Mời Báo cáo viên thực tế (class_course_id)
    - Lớp bồi dưỡng / NCKH (res_model + res_id)
    """
    _name = 'faculty.budget.line'
    _description = 'Dòng Dự toán Kinh phí'
    _order = 'sequence asc, id asc'

    sequence = fields.Integer(string='STT', default=10)
    class_course_id = fields.Many2one('faculty.class.course', string='Học phần lớp', ondelete='cascade', index=True)
    internship_id = fields.Many2one('faculty.internship.project', string='Đợt thực tập', ondelete='cascade', index=True)

    res_model = fields.Char(string='Model liên kết', index=True)
    res_id = fields.Integer(string='ID bản ghi', index=True)

    payment_regulation_id = fields.Many2one('faculty.payment.regulation', string='Quy định thanh toán')
    payment_line_id = fields.Many2one('faculty.payment.regulation.line', string='Mục chi chuẩn')

    name = fields.Char(string='Nội dung mục chi', required=True, placeholder='VD: Thù lao Báo cáo viên, Hỗ trợ công tác phí...')
    unit = fields.Char(string='Đơn vị tính', default='Tiết / Buổi', required=True)
    standard_rate = fields.Float(string='Định mức / Đơn giá (VNĐ)', default=0.0, required=True)
    quantity = fields.Float(string='Số lượng', default=1.0, required=True)
    subtotal = fields.Float(string='Thành tiền (VNĐ)', compute='_compute_subtotal', store=True)
    formula_desc = fields.Char(string='Công thức tính')
    notes = fields.Char(string='Ghi chú')

    @api.depends('standard_rate', 'quantity')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = round((rec.standard_rate or 0.0) * (rec.quantity or 0.0), 2)

