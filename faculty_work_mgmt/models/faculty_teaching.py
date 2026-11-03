# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta
import math


class FacultyCurriculum(models.Model):
    _name = 'faculty.curriculum'
    _description = 'Chương trình Đào tạo'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'code asc, name asc'

    name = fields.Char(string='Tên chương trình đào tạo', required=True, tracking=True, placeholder='VD: Cử nhân Công nghệ Thông tin')
    code = fields.Char(string='Mã CTĐT', required=True, copy=False, index=True, tracking=True, placeholder='VD: CNTT-2025')
    academic_level = fields.Selection([
        ('bachelor', 'Đại học chính quy'),
        ('postgraduate', 'Sau đại học (ThS/TS)'),
        ('work_study', 'Vừa làm vừa học'),
        ('short_course', 'Đào tạo ngắn hạn / Bồi dưỡng'),
    ], string='Trình độ / Bậc đào tạo', default='bachelor', required=True, tracking=True)
    decision_number = fields.Char(string='Số Quyết định ban hành', tracking=True, placeholder='VD: 256/QĐ-ĐH')
    decision_date = fields.Date(string='Ngày ban hành', tracking=True)
    total_credits = fields.Integer(string='Tổng số tín chỉ', default=130, tracking=True)
    course_ids = fields.One2many('faculty.course', 'curriculum_id', string='Danh mục Học phần thuộc CTĐT')
    total_courses = fields.Integer(string='Tổng số học phần', compute='_compute_total_courses', store=True)

    # Luồng trạng thái một chiều: draft -> approved -> expired. BỎ nút Chuyển dự thảo.
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('approved', 'Đang áp dụng'),
        ('expired', 'Hết hiệu lực'),
    ], string='Trạng thái', default='draft', tracking=True, required=True)
    notes = fields.Text(string='Ghi chú CTĐT')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã Chương trình đào tạo đã tồn tại! Vui lòng chọn mã khác.'),
    ]

    @api.depends('course_ids')
    def _compute_total_courses(self):
        for rec in self:
            rec.total_courses = len(rec.course_ids)

    def action_approve(self):
        """Phê duyệt áp dụng CTĐT (Một chiều)"""
        for rec in self:
            rec.state = 'approved'
            rec.message_post(body=_("Chương trình đào tạo đã được phê duyệt áp dụng chính thức."))
        return True

    def action_set_expired(self):
        """
        Khi bấm 'Hết hiệu lực':
        1. Khóa cứng bản ghi CTĐT (state = 'expired').
        2. Tự động ẩn toàn bộ các Học phần thuộc CTĐT đó khỏi danh mục học phần (active = False).
        """
        for rec in self:
            rec.state = 'expired'
            # Tự động ẩn toàn bộ các học phần thuộc CTĐT này
            courses = rec.course_ids.filtered(lambda c: c.active)
            if courses:
                courses.write({'active': False})
            rec.message_post(body=_(
                "Chương trình đào tạo đã chuyển sang Hết hiệu lực. "
                "Toàn bộ %d học phần thuộc CTĐT đã được ẩn khỏi danh mục hoạt động."
            ) % len(courses))
        return True


class FacultyCourse(models.Model):
    _name = 'faculty.course'
    _description = 'Học phần & Môn học'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'stt asc, code asc'

    # Số thứ tự đánh số tự động trên List view
    stt = fields.Integer(string='STT', compute='_compute_stt', store=False)
    name = fields.Char(string='Tên học phần / Môn học', required=True, tracking=True, placeholder='VD: Lập trình Hướng đối tượng')
    code = fields.Char(string='Mã học phần', required=True, copy=False, index=True, tracking=True, placeholder='VD: IT201')
    curriculum_id = fields.Many2one('faculty.curriculum', string='Chương trình đào tạo',
                                    domain=[('state', 'in', ['draft', 'approved'])], required=True, tracking=True, ondelete='restrict')
    curriculum_state = fields.Selection(related='curriculum_id.state', string='Trạng thái CTĐT', store=True)

    credit_count = fields.Float(string='Số tín chỉ', default=3.0, required=True, tracking=True)
    lecture_hours = fields.Float(string='Số tiết Lý thuyết (LT)', default=30.0, required=True, tracking=True)
    # Đổi nhãn chuẩn: Số tiết BT, TL, KT, BCTT
    practice_hours = fields.Float(string='Số tiết BT, TL, KT, BCTT', default=15.0, required=True, tracking=True,
                                 help='Bao gồm tiết Bài tập (BT), Thảo luận (TL), Kiểm tra (KT), Báo cáo thực tế (BCTT).')
    total_hours = fields.Float(string='Tổng số tiết học phần', compute='_compute_total_hours', store=True)

    head_lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên quản lý học phần', required=True, tracking=True)
    # XÓA cụm từ '(tối thiểu 2 giảng viên)' và cho phép Lưu bình thường khi chỉ nhập 1 giảng viên
    lecturer_ids = fields.Many2many('faculty.lecturer', 'faculty_course_lecturer_rel', 'course_id', 'lecturer_id',
                                    string='Giảng viên tham gia giảng dạy', required=True)

    # Học phần tích hợp nhiều môn con
    is_composite = fields.Boolean(string='Học phần tích hợp nhiều môn con', default=False, tracking=True)
    sub_module_ids = fields.One2many('faculty.course.sub.module', 'course_id', string='Danh sách Môn con tích hợp')

    # Đề cương chi tiết
    syllabus_ids = fields.One2many('faculty.course.syllabus', 'course_id', string='Đề cương chi tiết')
    active_syllabus_id = fields.Many2one('faculty.course.syllabus', string='Đề cương đang áp dụng', compute='_compute_active_syllabus', store=True)

    active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    notes = fields.Text(string='Ghi chú môn học')

    _sql_constraints = [
        ('code_curriculum_unique', 'unique(code, curriculum_id)', 'Mã học phần đã tồn tại trong Chương trình đào tạo này!'),
    ]

    def _compute_stt(self):
        """Đánh số thứ tự tự động để biết tổng số môn học Khoa đang quản lý"""
        all_courses = self.search([], order='code asc, id asc')
        stt_map = {cid: idx + 1 for idx, cid in enumerate(all_courses.ids)}
        for rec in self:
            rec.stt = stt_map.get(rec.id, 1)

    @api.depends('lecture_hours', 'practice_hours')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = (rec.lecture_hours or 0.0) + (rec.practice_hours or 0.0)

    @api.depends('syllabus_ids.state')
    def _compute_active_syllabus(self):
        for rec in self:
            applied = rec.syllabus_ids.filtered(lambda s: s.state == 'applied')
            rec.active_syllabus_id = applied[0] if applied else False


class FacultyCourseSubModule(models.Model):
    _name = 'faculty.course.sub.module'
    _description = 'Môn con Tích hợp trong Học phần'
    _order = 'sequence asc, id asc'

    course_id = fields.Many2one('faculty.course', string='Học phần cha', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên môn con', required=True, placeholder='VD: Phần 1: Kiến trúc phần mềm')
    code = fields.Char(string='Mã môn con', placeholder='VD: IT201-P1')
    lecture_hours = fields.Float(string='Số tiết LT', default=15.0)
    practice_hours = fields.Float(string='Số tiết BT, TL, KT', default=15.0)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên phụ trách môn con')
    notes = fields.Char(string='Ghi chú')


class FacultyCourseSyllabus(models.Model):
    _name = 'faculty.course.syllabus'
    _description = 'Đề cương Chi tiết Học phần'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'apply_year desc, id desc'

    course_id = fields.Many2one('faculty.course', string='Học phần', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Tên đề cương chi tiết', required=True, tracking=True, placeholder='VD: Đề cương chi tiết HP Lập trình Hướng đối tượng')
    # Đổi thành "Năm áp dụng", BỎ "Nhóm giảng viên biên soạn"
    apply_year = fields.Integer(string='Năm áp dụng', default=lambda self: date.today().year, required=True, tracking=True)
    decision_number = fields.Char(string='Số Quyết định ban hành', tracking=True)
    decision_date = fields.Date(string='Ngày ban hành thực tế', tracking=True)

    # Đính kèm file qua attachment=True
    attachment_file = fields.Binary(string='File Đề cương chi tiết (Word/PDF)', attachment=True)
    attachment_filename = fields.Char(string='Tên tệp đính kèm')

    # BỎ nút Gửi phê duyệt, thay bằng nút Áp dụng (bấm là áp dụng ngay)
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('applied', 'Đang áp dụng'),
        ('superseded', 'Đã thay thế'),
    ], string='Trạng thái', default='draft', tracking=True, required=True)
    notes = fields.Text(string='Ghi chú đề cương')

    def action_apply(self):
        """Bấm Áp dụng là chuyển trạng thái sang Đang áp dụng ngay lập tức"""
        for rec in self:
            # Chuyển các đề cương cũ của học phần này sang Đã thay thế
            others = self.search([
                ('course_id', '=', rec.course_id.id),
                ('id', '!=', rec.id),
                ('state', '=', 'applied')
            ])
            if others:
                others.write({'state': 'superseded'})
            rec.state = 'applied'
            rec.message_post(body=_("Đề cương chi tiết năm áp dụng %d đã được kích hoạt áp dụng.") % rec.apply_year)
        return True


class FacultyStudentClass(models.Model):
    _name = 'faculty.student.class'
    _description = 'Danh sách Lớp sinh viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'academic_year_id desc, code asc'

    name = fields.Char(string='Tên lớp', required=True, tracking=True, placeholder='VD: Lớp Đại học CNTT K25A')
    code = fields.Char(string='Mã lớp', required=True, copy=False, index=True, tracking=True, placeholder='VD: D25-CNTT-A')
    curriculum_id = fields.Many2one('faculty.curriculum', string='Mã CTĐT / Chương trình',
                                    domain=[('state', '=', 'approved')], required=True, tracking=True)
    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, tracking=True,
                                      default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)

    # Sĩ số >= 40 tự nhân hệ số 1.2
    student_count = fields.Integer(string='Tổng số học viên (Sĩ số)', default=35, required=True, tracking=True)
    class_factor = fields.Float(string='Hệ số quy mô lớp', compute='_compute_class_factor', store=True)

    class_type = fields.Selection([
        ('regular', 'Chính khóa'),
        ('makeup', 'Học bù'),
        ('improvement', 'Học cải thiện'),
    ], string='Phân loại lớp', default='regular', required=True, tracking=True)
    classroom = fields.Char(string='Phòng học / Địa điểm', placeholder='VD: Phòng 402 - Giảng đường A')

    class_course_ids = fields.One2many('faculty.class.course', 'class_id', string='Các học phần theo kỳ của lớp')
    notes = fields.Text(string='Ghi chú lớp học')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã lớp đã tồn tại! Vui lòng chọn mã khác.'),
    ]

    @api.depends('student_count')
    def _compute_class_factor(self):
        norm_config = self.env['faculty.norm.config'].search([('active', '=', True)], limit=1)
        threshold = norm_config.large_class_threshold if norm_config else 40
        coeff = norm_config.large_class_coeff if norm_config else 1.2
        for rec in self:
            rec.class_factor = coeff if rec.student_count >= threshold else 1.0


class FacultyClassCourse(models.Model):
    _name = 'faculty.class.course'
    _description = 'Học phần theo Lớp (Trục Trung tâm)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'start_date asc, id desc'

    name = fields.Char(string='Tên học phần - Lớp', compute='_compute_name', store=True)
    class_id = fields.Many2one('faculty.student.class', string='Lớp sinh viên', required=True, ondelete='cascade', index=True)
    academic_year_id = fields.Many2one('faculty.academic.year', related='class_id.academic_year_id', store=True, index=True)
    semester_id = fields.Many2one('faculty.academic.semester', string='Học kỳ', required=True, index=True, tracking=True)

    course_id = fields.Many2one('faculty.course', string='Học phần', required=True, tracking=True)
    credit_count = fields.Float(string='Số tín chỉ', related='course_id.credit_count', store=True)
    lecture_hours = fields.Float(string='Số tiết LT', related='course_id.lecture_hours', store=True)
    practice_hours = fields.Float(string='Số tiết BT, TL, KT, BCTT', related='course_id.practice_hours', store=True)
    is_composite = fields.Boolean(related='course_id.is_composite', string='Là học phần tích hợp')

    head_lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên quản lý học phần', required=True, tracking=True)
    lecturer_ids = fields.Many2many('faculty.lecturer', 'faculty_class_course_lecturer_rel', 'class_course_id', 'lecturer_id',
                                    string='Giảng viên tham gia giảng dạy', required=True)

    # Thời gian học
    start_date = fields.Date(string='Từ ngày (Bắt đầu)', required=True, tracking=True, default=fields.Date.context_today)
    end_date = fields.Date(string='Đến ngày (Kết thúc)', required=True, tracking=True)

    # Sĩ số & Học bù/ghép thêm
    base_student_count = fields.Integer(string='Sĩ số lớp cơ sở', related='class_id.student_count', store=True)
    extra_student_count = fields.Integer(string='Số HV học bù / ghép thêm', default=0, tracking=True,
                                        help='Số lượng học viên từ khóa trước học bù hoặc ghép lớp cải thiện điểm.')
    total_student_count = fields.Integer(string='Tổng sĩ số thực tế', compute='_compute_student_stats', store=True)
    class_factor = fields.Float(string='Hệ số lớp thực tế (>= 40 HV là 1.2)', compute='_compute_student_stats', store=True)

    course_type = fields.Selection([
        ('regular', 'Chính khóa'),
        ('makeup', 'Học bù'),
        ('improvement', 'Học cải thiện'),
    ], string='Đợt học phần', default='regular', required=True, tracking=True)
    classroom = fields.Char(string='Phòng học thực tế')

    # Buổi học chi tiết
    session_ids = fields.One2many('faculty.teaching.session', 'class_course_id', string='Lịch giảng chi tiết từng buổi')
    total_session_hours = fields.Float(string='Tổng số tiết đã xếp', compute='_compute_session_hours', store=True)

    # Báo cáo viên thực tế
    has_guest_speaker = fields.Boolean(string='Có mời Báo cáo viên thực tế', default=False, tracking=True)
    guest_speaker_info = fields.Char(string='Họ tên / Đơn vị Báo cáo viên', placeholder='VD: PGS.TS. Trần Văn B - Viện KHCN')
    guest_lecture_date = fields.Date(string='Ngày báo cáo thực tế')

    # Thông tin thi
    exam_date = fields.Date(string='Ngày thi kết thúc HP', tracking=True)
    exam_session = fields.Selection([('morning', 'Sáng'), ('afternoon', 'Chiều')], default='morning', string='Ca thi')
    exam_format = fields.Selection([
        ('essay', 'Tự luận'),
        ('oral', 'Vấn đáp'),
        ('multiple_choice', 'Trắc nghiệm'),
        ('essay_paper', 'Tiểu luận / Bài tập lớn'),
    ], string='Hình thức thi', default='essay', required=True, tracking=True)
    question_source = fields.Selection([
        ('new_paper', 'Ra đề mới'),
        ('question_bank', 'Ngân hàng đề thi'),
    ], string='Nguồn đề thi', default='question_bank', required=True, tracking=True)

    # Bảng phân công ra đề thi độc quyền
    paper_maker_ids = fields.One2many('faculty.exam.paper.maker', 'class_course_id', string='Danh sách Giảng viên Ra đề')
    paper_locked = fields.Boolean(string='Đã có GV ra đề (Khóa ô tích)', default=False, tracking=True)
    paper_created_lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên đã ra đề', tracking=True)

    # Chuỗi Checklist 7 bước học vụ
    checklist_ids = fields.One2many('faculty.academic.checklist', 'class_course_id', string='Chuỗi Checklist 7 bước học vụ')

    # Khảo thí & Chấm thi
    grading_deadline = fields.Date(string='Hạn nộp bài chấm thi & chấm kiểm tra', tracking=True,
                                  help='Giáo vụ khoa cập nhật hạn chấm thi tại đây sẽ tự động đồng bộ sang Lịch thi và Checklist.')
    exam_plan_state = fields.Selection([
        ('draft', 'Dự thảo kế hoạch'),
        ('approved', 'Đã duyệt kế hoạch đầu năm'),
    ], string='Trạng thái Kế hoạch Khảo thí', default='draft', tracking=True)
    exam_done = fields.Boolean(string='Đã hoàn thành Khảo thí', default=False, tracking=True)
    exam_assignment_ids = fields.One2many('faculty.exam.assignment', 'class_course_id', string='Phân công Khảo thí')

    # Bảng Dự toán chi phí (Dùng chung faculty.budget.line)
    budget_line_ids = fields.One2many('faculty.budget.line', 'class_course_id', string='Dự toán Mời giảng & Báo cáo viên')
    total_budget = fields.Float(string='Tổng cộng tiền dự toán (VNĐ)', compute='_compute_total_budget', store=True)

    @api.depends('class_id.name', 'course_id.name')
    def _compute_name(self):
        for rec in self:
            c_name = rec.course_id.name if rec.course_id else ''
            cl_name = rec.class_id.name if rec.class_id else ''
            rec.name = f"{c_name} - {cl_name}" if c_name and cl_name else c_name or cl_name

    @api.onchange('course_id')
    def _onchange_course_id(self):
        """Thông tin môn học tự động nhảy sang khi chọn course_id"""
        if self.course_id:
            self.head_lecturer_id = self.course_id.head_lecturer_id
            self.lecturer_ids = self.course_id.lecturer_ids

    @api.depends('base_student_count', 'extra_student_count')
    def _compute_student_stats(self):
        norm_config = self.env['faculty.norm.config'].search([('active', '=', True)], limit=1)
        threshold = norm_config.large_class_threshold if norm_config else 40
        coeff = norm_config.large_class_coeff if norm_config else 1.2
        for rec in self:
            total = (rec.base_student_count or 0) + (rec.extra_student_count or 0)
            rec.total_student_count = total
            rec.class_factor = coeff if total >= threshold else 1.0

    @api.depends('session_ids.period_count')
    def _compute_session_hours(self):
        for rec in self:
            rec.total_session_hours = sum(s.period_count for s in rec.session_ids)

    @api.depends('budget_line_ids.subtotal')
    def _compute_total_budget(self):
        for rec in self:
            rec.total_budget = sum(line.subtotal for line in rec.budget_line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(FacultyClassCourse, self).create(vals_list)
        for rec in records:
            rec._init_paper_makers()
            rec._init_checklist_steps()
        return records

    def write(self, vals):
        res = super(FacultyClassCourse, self).write(vals)
        if 'lecturer_ids' in vals:
            for rec in self:
                rec._sync_paper_makers()
        if 'has_guest_speaker' in vals or 'exam_format' in vals or 'start_date' in vals or 'exam_date' in vals or 'grading_deadline' in vals:
            for rec in self:
                rec._update_checklist_deadlines()
        return res

    def _init_paper_makers(self):
        """Khởi tạo danh sách các giảng viên có quyền ra đề thi"""
        self.ensure_one()
        Maker = self.env['faculty.exam.paper.maker']
        for lec in self.lecturer_ids:
            Maker.create({
                'class_course_id': self.id,
                'lecturer_id': lec.id,
                'is_paper_created': False,
            })

    def _sync_paper_makers(self):
        self.ensure_one()
        current_lecs = self.paper_maker_ids.mapped('lecturer_id')
        new_lecs = self.lecturer_ids - current_lecs
        Maker = self.env['faculty.exam.paper.maker']
        for lec in new_lecs:
            Maker.create({
                'class_course_id': self.id,
                'lecturer_id': lec.id,
                'is_paper_created': False,
            })

    def _init_checklist_steps(self):
        """Tự động sinh chuỗi Checklist 7 bước học vụ chuẩn cho từng học phần"""
        self.ensure_one()
        Checklist = self.env['faculty.academic.checklist']
        steps = [
            (1, 'Làm Kế hoạch giảng dạy học phần', 'Mẫu 01/KHGD-ĐT', self.start_date - timedelta(days=10) if self.start_date else False),
            (2, 'Điền giảng viên lịch giảng chi tiết & Giáo án', 'Mẫu 02/LG-GA', self.start_date or False),
            (3, 'Làm giấy mời Báo cáo thực tế', 'Mẫu 03/GM-BCV', self.start_date + timedelta(days=5) if self.start_date else False),
            (4, 'Nhắc đón Báo cáo viên thực tế', 'Mẫu 04/ND-BCV', self.guest_lecture_date - timedelta(days=1) if self.guest_lecture_date else False),
            (5, 'Nộp bảng điểm tổng hợp điều kiện dự thi', 'Mẫu 05/BĐ-ĐK', self.end_date - timedelta(days=3) if self.end_date else False),
            (6, 'Tổ chức Coi thi kết thúc học phần', 'Mẫu 06/CT-HP', self.exam_date or False),
            (7, 'Hoàn thành Chấm thi & Chấm kiểm tra', 'Mẫu 07/KQ-CT', self.grading_deadline or False),
        ]
        for seq, name, form_tpl, deadline in steps:
            Checklist.create({
                'class_course_id': self.id,
                'step_number': seq,
                'sequence': seq * 10,
                'name': name,
                'form_template_name': form_tpl,
                'responsible_lecturer_id': self.head_lecturer_id.id,
                'deadline': deadline,
            })

    def _update_checklist_deadlines(self):
        """Cập nhật ngày hạn chót và tính khả kiến của chuỗi checklist khi đổi ngày"""
        for rec in self:
            for chk in rec.checklist_ids:
                if chk.step_number == 1 and rec.start_date:
                    chk.deadline = rec.start_date - timedelta(days=10)
                elif chk.step_number == 2 and rec.start_date:
                    chk.deadline = rec.start_date
                elif chk.step_number == 3 and rec.start_date:
                    chk.deadline = rec.start_date + timedelta(days=5)
                elif chk.step_number == 4 and rec.guest_lecture_date:
                    chk.deadline = rec.guest_lecture_date - timedelta(days=1)
                elif chk.step_number == 5 and rec.end_date:
                    chk.deadline = rec.end_date - timedelta(days=3)
                elif chk.step_number == 6 and rec.exam_date:
                    chk.deadline = rec.exam_date
                elif chk.step_number == 7 and rec.grading_deadline:
                    chk.deadline = rec.grading_deadline

    def action_confirm_paper_created(self, lecturer):
        """
        Xử lý cơ chế độc quyền khi 1 giảng viên tích 'Đã ra đề':
        1. Khóa cứng ô tích của các giảng viên còn lại.
        2. Gửi thông báo cho các giảng viên còn lại biết.
        3. Nếu nguồn đề là 'Ra đề mới', tính giờ chuẩn ghi Sổ cái.
        """
        self.ensure_one()
        self.paper_locked = True
        self.paper_created_lecturer_id = lecturer.id

        # Thông báo cho các giảng viên còn lại
        other_lecs = self.lecturer_ids - lecturer
        lec_names = ", ".join(other_lecs.mapped('name'))
        msg_body = _(
            "Giảng viên <strong>%s</strong> đã hoàn thành ra đề thi cho học phần <strong>%s</strong>. "
            "Hệ thống đã khóa quyền ra đề của các giảng viên còn lại (%s)."
        ) % (lecturer.name, self.name, lec_names or "Không có")
        self.message_post(body=msg_body)

        # Tính giờ chuẩn ra đề nếu nguồn đề là 'Ra đề mới'
        if self.question_source == 'new_paper':
            norm_config = self.env['faculty.norm.config'].search([('active', '=', True)], limit=1)
            standard_hours = 5.0
            if norm_config:
                if self.exam_format == 'essay':
                    standard_hours = norm_config.exam_creation_essay_norm
                elif self.exam_format == 'oral':
                    standard_hours = norm_config.exam_creation_oral_norm
                elif self.exam_format == 'essay_paper':
                    standard_hours = norm_config.exam_creation_report_norm
                else:
                    standard_hours = 5.0

            self.env['faculty.hour.ledger'].post_ledger_entry({
                'lecturer_id': lecturer.id,
                'academic_year_id': self.academic_year_id.id,
                'semester_id': self.semester_id.id,
                'date': fields.Date.today(),
                'category': 'teaching',
                'activity_type': 'exam_creation',
                'name': f"Ra đề thi mới: {self.name} (Hình thức: {dict(self._fields['exam_format'].selection).get(self.exam_format)})",
                'raw_hours': standard_hours,
                'coefficient': 1.0,
                'standard_hours': standard_hours,
                'res_model': 'faculty.class.course',
                'res_id': self.id,
            })
        return True

    def action_approve_exam_plan(self):
        """Trưởng khoa phê duyệt Kế hoạch Khảo thí đầu năm"""
        self.ensure_one()
        self.exam_plan_state = 'approved'
        self.message_post(body=_("Trưởng khoa đã phê duyệt kế hoạch khảo thí đầu năm cho học phần."))
        return True

    def action_finish_exam(self):
        """
        Giảng viên quản lý học phần bấm 'Hoàn thành Khảo thí':
        1. Đánh dấu exam_done = True.
        2. Tự động kết chuyển toàn bộ giờ Coi thi, Chấm thi, Chấm kiểm tra vào Sổ cái faculty.hour.ledger.
        """
        self.ensure_one()
        self.exam_done = True

        # Đồng bộ bước 7 của Checklist sang hoàn thành
        step_7 = self.checklist_ids.filtered(lambda c: c.step_number == 7)
        if step_7 and not step_7.is_done:
            step_7.write({'is_done': True, 'done_date': fields.Date.today()})

        # Kết chuyển các dòng khảo thí vào Sổ cái
        for assign in self.exam_assignment_ids:
            act_type = 'exam_proctoring' if assign.role == 'invigilator' else ('exam_grading' if assign.role in ('grader_1', 'grader_2') else 'exam_audit')
            role_label = dict(assign._fields['role'].selection).get(assign.role)
            self.env['faculty.hour.ledger'].post_ledger_entry({
                'lecturer_id': assign.lecturer_id.id,
                'academic_year_id': self.academic_year_id.id,
                'semester_id': self.semester_id.id,
                'date': self.grading_deadline or self.exam_date or fields.Date.today(),
                'category': 'teaching',
                'activity_type': act_type,
                'name': f"Khảo thí ({role_label}): {self.name} - {assign.paper_count} bài/buổi",
                'raw_hours': assign.paper_count,
                'coefficient': assign.unit_rate,
                'standard_hours': assign.standard_hours,
                'res_model': 'faculty.exam.assignment',
                'res_id': assign.id,
            })

        self.message_post(body=_("Đã hoàn thành khảo thí và kết chuyển giờ chuẩn Coi thi, Chấm thi, Chấm kiểm tra vào Sổ cái."))
        return True


class FacultyTeachingSession(models.Model):
    _name = 'faculty.teaching.session'
    _description = 'Buổi học Chi tiết'
    _order = 'date asc, session_time asc, id asc'

    class_course_id = fields.Many2one('faculty.class.course', string='Học phần lớp', required=True, ondelete='cascade', index=True)
    academic_year_id = fields.Many2one('faculty.academic.year', related='class_course_id.academic_year_id', store=True, index=True)
    semester_id = fields.Many2one('faculty.academic.semester', related='class_course_id.semester_id', store=True, index=True)
    date = fields.Date(string='Ngày học', required=True, default=fields.Date.context_today, index=True)
    session_time = fields.Selection([('morning', 'Sáng'), ('afternoon', 'Chiều')], default='morning', required=True, string='Buổi')
    period_count = fields.Integer(string='Số tiết (1-4)', default=4, required=True)
    sub_module_id = fields.Many2one('faculty.course.sub.module', string='Môn con (nếu tích hợp)')

    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên kế hoạch', required=True)
    is_substituted = fields.Boolean(string='Báo bận / Dạy thay', default=False)
    substitute_lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên dạy thay')
    actual_lecturer_id = fields.Many2one('faculty.lecturer', string='GV đứng lớp thực tế', compute='_compute_actual_lecturer', store=True)

    class_factor = fields.Float(string='Hệ số lớp', related='class_course_id.class_factor', store=True)
    standard_hours = fields.Float(string='Số giờ chuẩn quy đổi', compute='_compute_standard_hours', store=True)

    # Cảnh báo vàng trùng lịch (store=False, KHÔNG dùng _sql_constraints chặn lưu)
    has_conflict = fields.Boolean(string='Trùng lịch', compute='_compute_conflict', store=False)
    conflict_warning = fields.Char(string='Cảnh báo trùng lịch', compute='_compute_conflict', store=False)
    notes = fields.Char(string='Ghi chú buổi giảng')

    @api.depends('lecturer_id', 'is_substituted', 'substitute_lecturer_id')
    def _compute_actual_lecturer(self):
        for rec in self:
            rec.actual_lecturer_id = rec.substitute_lecturer_id if (rec.is_substituted and rec.substitute_lecturer_id) else rec.lecturer_id

    @api.depends('period_count', 'class_factor')
    def _compute_standard_hours(self):
        for rec in self:
            rec.standard_hours = round((rec.period_count or 0.0) * (rec.class_factor or 1.0), 2)

    def _compute_conflict(self):
        """Phát hiện cảnh báo trùng lịch: cùng GV thực tế, cùng ngày và cùng buổi ở lớp khác"""
        for rec in self:
            if rec.actual_lecturer_id and rec.date and rec.session_time:
                domain = [
                    ('actual_lecturer_id', '=', rec.actual_lecturer_id.id),
                    ('date', '=', rec.date),
                    ('session_time', '=', rec.session_time),
                    ('id', '!=', rec.id or 0),
                ]
                conflicts = self.search(domain, limit=1)
                if conflicts:
                    rec.has_conflict = True
                    rec.conflict_warning = f"Trùng lịch với {conflicts.class_course_id.name} ({conflicts.date.strftime('%d/%m/%Y')})!"
                else:
                    rec.has_conflict = False
                    rec.conflict_warning = ''
            else:
                rec.has_conflict = False
                rec.conflict_warning = ''

    @api.model_create_multi
    def create(self, vals_list):
        records = super(FacultyTeachingSession, self).create(vals_list)
        records._post_to_ledger_if_due()
        return records

    def write(self, vals):
        res = super(FacultyTeachingSession, self).write(vals)
        self._post_to_ledger_if_due()
        return res

    def _post_to_ledger_if_due(self):
        """
        Khi buổi học đã diễn ra (date <= today), tự động ghi giờ đứng lớp thuần túy
        (Số tiết * Hệ số lớp) vào Sổ cái faculty.hour.ledger. TUYỆT ĐỐI KHÔNG tính giờ giáo án.
        """
        today = fields.Date.today()
        for rec in self:
            if rec.date and rec.date <= today and rec.actual_lecturer_id and rec.standard_hours > 0:
                self.env['faculty.hour.ledger'].post_ledger_entry({
                    'lecturer_id': rec.actual_lecturer_id.id,
                    'academic_year_id': rec.academic_year_id.id,
                    'semester_id': rec.semester_id.id,
                    'date': rec.date,
                    'category': 'teaching',
                    'activity_type': 'lecture',
                    'name': f"Giảng dạy: {rec.class_course_id.name} - Ngày {rec.date.strftime('%d/%m/%Y')} ({rec.period_count} tiết x hệ số {rec.class_factor})",
                    'raw_hours': rec.period_count,
                    'coefficient': rec.class_factor,
                    'standard_hours': rec.standard_hours,
                    'res_model': 'faculty.teaching.session',
                    'res_id': rec.id,
                })


class FacultyExamPaperMaker(models.Model):
    _name = 'faculty.exam.paper.maker'
    _description = 'Giảng viên Ra đề thi'
    _order = 'class_course_id, lecturer_id'

    class_course_id = fields.Many2one('faculty.class.course', string='Học phần', required=True, ondelete='cascade', index=True)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên', required=True)
    is_paper_created = fields.Boolean(string='Đã ra đề', default=False)
    created_date = fields.Date(string='Ngày ra đề')
    is_locked = fields.Boolean(string='Bị khóa', compute='_compute_is_locked')

    @api.depends('class_course_id.paper_locked', 'is_paper_created')
    def _compute_is_locked(self):
        for rec in self:
            rec.is_locked = rec.class_course_id.paper_locked and not rec.is_paper_created

    def write(self, vals):
        res = super(FacultyExamPaperMaker, self).write(vals)
        if vals.get('is_paper_created'):
            for rec in self:
                if rec.is_paper_created and not rec.class_course_id.paper_locked:
                    if not rec.created_date:
                        rec.created_date = fields.Date.today()
                    rec.class_course_id.action_confirm_paper_created(rec.lecturer_id)
        return res

    def action_toggle_created(self):
        self.ensure_one()
        if self.is_locked:
            raise UserError(_('Học phần này đã có giảng viên khác hoàn thành ra đề thi!'))
        if not self.is_paper_created:
            self.write({
                'is_paper_created': True,
                'created_date': fields.Date.today(),
            })
        return True


class FacultyAcademicChecklist(models.Model):
    _name = 'faculty.academic.checklist'
    _description = 'Checklist Học vụ 7 Bước'
    _order = 'sequence asc, id asc'

    class_course_id = fields.Many2one('faculty.class.course', string='Học phần', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    step_number = fields.Integer(string='Bước (1-7)', required=True)
    name = fields.Char(string='Nội dung công việc', required=True)
    form_template_name = fields.Char(string='Tên mẫu báo cáo / Giấy tờ')
    responsible_lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên phụ trách')
    deadline = fields.Date(string='Hạn chót')
    is_done = fields.Boolean(string='Đã hoàn thành', default=False)
    done_date = fields.Date(string='Ngày hoàn thành')

    # Tính khả kiến (Bước 3, 4 chỉ hiện nếu has_guest_speaker, Bước 6 ẩn nếu thi Tiểu luận)
    is_visible = fields.Boolean(string='Kích hoạt / Hiển thị', compute='_compute_visibility', store=True)

    # Cảnh báo màu Tím (#800080) quá hạn, màu Đỏ khẩn cấp <= 3 ngày (store=False)
    alert_level = fields.Selection([
        ('normal', 'Bình thường'),
        ('urgent', 'Khẩn cấp (<= 3 ngày)'),
        ('overdue', 'Quá hạn'),
    ], string='Mức độ cảnh báo', compute='_compute_alert_level', store=False)
    notes = fields.Text(string='Ghi chú bước việc')

    @api.depends('class_course_id.has_guest_speaker', 'class_course_id.exam_format', 'step_number')
    def _compute_visibility(self):
        for rec in self:
            c = rec.class_course_id
            if rec.step_number in (3, 4):
                rec.is_visible = bool(c.has_guest_speaker)
            elif rec.step_number == 6:
                rec.is_visible = (c.exam_format != 'essay_paper')
            else:
                rec.is_visible = True

    def _compute_alert_level(self):
        today = fields.Date.today()
        for rec in self:
            if rec.is_done or not rec.deadline:
                rec.alert_level = 'normal'
            elif rec.deadline < today:
                rec.alert_level = 'overdue'
            elif (rec.deadline - today).days <= 3:
                rec.alert_level = 'urgent'
            else:
                rec.alert_level = 'normal'

    def action_mark_done(self):
        """Đánh dấu hoàn thành bước việc checklist"""
        self.ensure_one()
        self.is_done = True
        self.done_date = fields.Date.today()

        # Bước 1: Kế hoạch giảng dạy -> Tự ghi giờ Hoạt động khác cho GV quản lý
        if self.step_number == 1 and self.responsible_lecturer_id:
            c = self.class_course_id
            self.env['faculty.hour.ledger'].post_ledger_entry({
                'lecturer_id': self.responsible_lecturer_id.id,
                'academic_year_id': c.academic_year_id.id,
                'semester_id': c.semester_id.id,
                'date': fields.Date.today(),
                'category': 'other',
                'activity_type': 'teaching_plan',
                'name': f"Lập kế hoạch giảng dạy: {c.name}",
                'raw_hours': 5.0,
                'coefficient': 1.0,
                'standard_hours': 5.0,
                'res_model': 'faculty.academic.checklist',
                'res_id': self.id,
            })

        # Bước 7: Hoàn thành Chấm thi -> Tự động kích hoạt hoàn thành Khảo thí
        if self.step_number == 7:
            if not self.class_course_id.exam_done:
                self.class_course_id.action_finish_exam()

        return True

