# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time, timedelta


class FacultyBudgetLine(models.Model):
    """Kế thừa bảng Dự toán dùng chung cho Hoạt động khác / Lớp bồi dưỡng"""
    _inherit = 'faculty.budget.line'

    other_work_id = fields.Many2one('faculty.other.work', string='Hoạt động khác', ondelete='cascade', index=True)


class FacultyOtherWork(models.Model):
    _name = 'faculty.other.work'
    _description = 'Hoạt động khác của Khoa (Trụ cột 3)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'academic_year_id desc, deadline asc, id desc'

    name = fields.Char(string='Tên hoạt động / Nhiệm vụ', required=True, tracking=True,
                       placeholder='VD: Tổ chức Tọa đàm Chuyên môn Bộ môn, Hội thao Chào mừng 20/11...')
    code = fields.Char(string='Mã hoạt động', copy=False, index=True, tracking=True,
                       placeholder='VD: HDK-2026-01')

    # 8 loại hoạt động khác chuẩn nghiệp vụ Khoa
    activity_type = fields.Selection([
        ('professional_meeting', '1. Sinh hoạt chuyên môn'),
        ('thematic_activity', '2. Sinh hoạt chuyên đề'),
        ('sports_culture', '3. Thể dục thể thao - Văn hóa'),
        ('party_union', '4. Công tác Đảng - Đoàn thể'),
        ('admissions', '5. Công tác Tuyển sinh'),
        ('recruitment', '6. Tuyển dụng / Phát triển nhân sự'),
        ('training_course_org', '7. Tổ chức lớp bồi dưỡng'),
        ('general_task', '8. Công việc hành chính / Đột xuất khác'),
    ], string='Phân loại hoạt động', default='professional_meeting', required=True, tracking=True)

    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, tracking=True,
                                       default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)
    semester_id = fields.Many2one('faculty.academic.semester', string='Học kỳ',
                                  domain="[('academic_year_id', '=', academic_year_id)]")

    # Người phụ trách chính & Người giao việc
    lead_lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ phụ trách chính', required=True, tracking=True)
    assigner_id = fields.Many2one('faculty.lecturer', string='Lãnh đạo giao việc / Phụ trách', tracking=True)

    # Cơ chế: Lãnh đạo giao việc hoặc Giảng viên tự khai báo
    is_self_declared = fields.Boolean(
        string='Giảng viên tự khai báo',
        default=False,
        tracking=True,
        help='Tích chọn nếu đây là hoạt động do giảng viên tự giác thực hiện và kê khai để Lãnh đạo phê duyệt.'
    )

    # Nhóm tiêu chí ghi giờ chuẩn: Mặc định 'other' (Tiêu chí 3).
    # Nếu tự khai báo, có thể chọn nhóm tiêu chí (1. Giảng dạy, 2. NCKH, 3. Hoạt động khác)
    category = fields.Selection([
        ('teaching', '1. Giảng dạy'),
        ('research', '2. Nghiên cứu khoa học'),
        ('other', '3. Hoạt động khác (Không quy đổi bù trừ)'),
    ], string='Ghi nhận vào Ô Tiêu chí', default='other', required=True, tracking=True,
       help='Quy định công việc này khi được duyệt sẽ kết chuyển giờ chuẩn vào Sổ cái thuộc nhóm tiêu chí nào.')

    start_date = fields.Date(string='Ngày bắt đầu', default=fields.Date.context_today, tracking=True)
    deadline = fields.Date(string='Hạn chót hoàn thành', required=True, tracking=True,
                           default=lambda self: fields.Date.today() + timedelta(days=7))
    completion_date = fields.Date(string='Ngày hoàn thành thực tế', tracking=True)

    # Cảnh báo hạn chót: store=False kèm search='_search_alert_level'
    alert_level = fields.Selection([
        ('normal', 'Bình thường'),
        ('urgent', 'Khẩn cấp (<= 3 ngày)'),
        ('overdue', 'Quá hạn'),
    ], string='Cảnh báo tiến độ', compute='_compute_alert_level', search='_search_alert_level', store=False)

    standard_hours = fields.Float(string='Định mức giờ chuẩn', default=0.0,
                                  help='Số giờ chuẩn quy định cho hoạt động này.')

    participant_ids = fields.One2many('faculty.other.participant', 'work_id', string='Danh sách Thành viên tham gia')
    total_participant_hours = fields.Float(string='Tổng giờ phân bổ', compute='_compute_total_hours', store=True)

    # Tab Dự toán (Áp dụng cho Tổ chức lớp bồi dưỡng / sự kiện)
    payment_regulation_id = fields.Many2one('faculty.payment.regulation', string='Quy định thanh toán áp dụng',
                                            domain=[('payment_category', 'in', ['class_org', 'other'])])
    budget_line_ids = fields.One2many('faculty.budget.line', 'other_work_id', string='Dự toán kinh phí')
    total_budget = fields.Float(string='Tổng kinh phí dự toán (VNĐ)', compute='_compute_total_budget', store=True)

    # Đính kèm file sản phẩm / kế hoạch / báo cáo
    attachment_file = fields.Binary(string='File kế hoạch / Báo cáo kết quả', attachment=True)
    attachment_filename = fields.Char(string='Tên tệp đính kèm')

    # Cờ trạng thái đưa vào Thư viện Khoa
    library_review_state = fields.Selection([
        ('not_required', 'Không yêu cầu'),
        ('pending', 'Chờ Admin duyệt Thư viện'),
        ('approved', 'Đã lưu vào Thư viện'),
    ], string='Trạng thái Thư viện', default='not_required', tracking=True)

    # Luồng duyệt chuẩn
    state = fields.Selection([
        ('draft', 'Dự thảo / Chưa gửi'),
        ('waiting_dean', 'Chờ Trưởng khoa duyệt'),
        ('approved', 'Đã duyệt / Hoàn thành'),
    ], string='Trạng thái', default='draft', tracking=True, required=True)

    notes = fields.Text(string='Ghi chú nội dung & Yêu cầu')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã hoạt động đã tồn tại! Vui lòng chọn mã khác.'),
    ]

    @api.depends('deadline', 'state', 'completion_date')
    def _compute_alert_level(self):
        today = fields.Date.today()
        for rec in self:
            if rec.state == 'approved' or rec.completion_date:
                rec.alert_level = 'normal'
            elif rec.deadline:
                if rec.deadline < today:
                    rec.alert_level = 'overdue'
                elif rec.deadline <= today + timedelta(days=3):
                    rec.alert_level = 'urgent'
                else:
                    rec.alert_level = 'normal'
            else:
                rec.alert_level = 'normal'

    def _search_alert_level(self, operator, value):
        today = fields.Date.today()
        three_days = today + timedelta(days=3)
        if operator == '=':
            if value == 'overdue':
                return [('state', '!=', 'approved'), ('completion_date', '=', False), ('deadline', '<', today)]
            elif value == 'urgent':
                return [('state', '!=', 'approved'), ('completion_date', '=', False), ('deadline', '>=', today), ('deadline', '<=', three_days)]
            elif value == 'normal':
                return ['|', ('state', '=', 'approved'), ('deadline', '>', three_days)]
        return []

    @api.depends('participant_ids.standard_hours')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_participant_hours = sum(p.standard_hours for p in rec.participant_ids)

    @api.depends('budget_line_ids.subtotal')
    def _compute_total_budget(self):
        for rec in self:
            rec.total_budget = sum(line.subtotal for line in rec.budget_line_ids)

    @api.onchange('lead_lecturer_id')
    def _onchange_lead_lecturer_id(self):
        """Tự động thêm Cán bộ phụ trách chính vào bảng thành viên nếu chưa có"""
        if self.lead_lecturer_id and not self.participant_ids:
            self.participant_ids = [(0, 0, {
                'lecturer_id': self.lead_lecturer_id.id,
                'role': 'Chủ trì / Phụ trách chính',
                'standard_hours': self.standard_hours or 0.0,
            })]

    @api.onchange('payment_regulation_id')
    def _onchange_payment_regulation_id(self):
        """Tự động nạp các mục chi từ Quy định thanh toán khi chọn"""
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
        """Nút bấm thủ công nạp các mục chi từ Quy định thanh toán"""
        self.ensure_one()
        if not self.payment_regulation_id:
            raise UserError(_('Vui lòng chọn Quy định thanh toán áp dụng trước khi nạp mục chi!'))
        BudgetLine = self.env['faculty.budget.line']
        for line in self.payment_regulation_id.line_ids:
            BudgetLine.create({
                'other_work_id': self.id,
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

    def action_submit_dean(self):
        """Gửi Lãnh đạo Khoa duyệt"""
        for rec in self:
            rec.state = 'waiting_dean'
            rec.message_post(body=_("Đã gửi hồ sơ hoạt động đến Trưởng khoa phê duyệt."))

    def action_reset_draft(self):
        """Chuyển về Dự thảo"""
        for rec in self:
            # Xóa các dòng sổ cái liên quan nếu có
            ledgers = self.env['faculty.hour.ledger'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id),
                ('is_locked', '=', False),
            ])
            if ledgers:
                ledgers.unlink()
            rec.state = 'draft'
            rec.message_post(body=_("Đã chuyển hoạt động về trạng thái Dự thảo."))

    def action_approve(self):
        """
        DUYỆT HOÀN THÀNH HOẠT ĐỘNG (state = 'approved'):
        1. Ghi giờ chuẩn vào Sổ cái faculty.hour.ledger theo đúng nhóm tiêu chí đã chọn (category).
        2. Nếu có file đính kèm và cờ rà soát Thư viện, tự động tạo hồ sơ chờ duyệt tại Thư viện nhỏ của Khoa.
        """
        self.ensure_one()
        Ledger = self.env['faculty.hour.ledger']
        LibDoc = self.env['faculty.library.document']

        acc_date = self.completion_date or fields.Date.context_today(self)
        acc_year = acc_date.year if acc_date else date.today().year

        # Map activity_type cho Sổ cái
        act_map = {
            'professional_meeting': 'faculty_meeting',
            'thematic_activity': 'faculty_meeting',
            'sports_culture': 'sports_culture',
            'party_union': 'party_union',
            'admissions': 'admissions',
            'recruitment': 'admissions',
            'training_course_org': 'course_org',
            'general_task': 'other',
        }
        ledger_act_type = act_map.get(self.activity_type, 'other')

        # 1. Ghi Sổ cái cho các thành viên có standard_hours > 0
        participants = self.participant_ids
        if not participants and self.lead_lecturer_id and self.standard_hours > 0:
            # Nếu chưa có dòng chi tiết nhưng có giờ trên tổng thể, ghi cho lead_lecturer
            Ledger.post_ledger_entry({
                'lecturer_id': self.lead_lecturer_id.id,
                'academic_year_id': self.academic_year_id.id,
                'semester_id': self.semester_id.id or False,
                'date': acc_date,
                'category': self.category,
                'activity_type': ledger_act_type,
                'name': f"[{self.code or 'HĐK'}] {self.name} (Phụ trách chính)",
                'raw_hours': self.standard_hours,
                'coefficient': 1.0,
                'standard_hours': self.standard_hours,
                'res_model': self._name,
                'res_id': self.id,
                'notes': f"Hoạt động: {dict(self._fields['activity_type'].selection).get(self.activity_type, '')}",
            })
        else:
            for p in participants:
                if p.standard_hours > 0:
                    Ledger.post_ledger_entry({
                        'lecturer_id': p.lecturer_id.id,
                        'academic_year_id': self.academic_year_id.id,
                        'semester_id': self.semester_id.id or False,
                        'date': acc_date,
                        'category': self.category,
                        'activity_type': ledger_act_type,
                        'name': f"[{self.code or 'HĐK'}] {self.name} ({p.role or 'Thành viên'})",
                        'raw_hours': p.standard_hours,
                        'coefficient': 1.0,
                        'standard_hours': p.standard_hours,
                        'res_model': self._name,
                        'res_id': self.id,
                        'notes': f"Hoạt động: {dict(self._fields['activity_type'].selection).get(self.activity_type, '')}",
                    })

        # 2. Đẩy vào Thư viện Khoa nếu có file và yêu cầu rà soát
        if self.attachment_file and self.library_review_state in ('pending', 'not_required'):
            self.library_review_state = 'pending'
            existing_doc = LibDoc.search([
                ('source_model', '=', self._name),
                ('source_id', '=', self.id),
            ], limit=1)
            if not existing_doc:
                default_cat = self.env['faculty.library.category'].search([], limit=1)
                LibDoc.create({
                    'name': self.name,
                    'code': self.code or f"LIB-OTHER-{self.id}",
                    'category_id': default_cat.id if default_cat else False,
                    'document_type': 'regulation' if self.activity_type in ('professional_meeting', 'thematic_activity') else 'other',
                    'attachment_file': self.attachment_file,
                    'attachment_filename': self.attachment_filename or f"{self.name}.pdf",
                    'author_id': self.lead_lecturer_id.id,
                    'year': acc_year,
                    'security_level': 'internal',
                    'review_state': 'pending_review',
                    'source_model': self._name,
                    'source_id': self.id,
                })

        self.state = 'approved'
        if not self.completion_date:
            self.completion_date = acc_date
        self.message_post(body=_("Hoạt động đã được Trưởng khoa phê duyệt hoàn thành và tự động kết chuyển giờ chuẩn vào Sổ cái."))
        return True

    @api.model
    def cron_check_salary_promotions(self):
        """
        Quét hàng ngày: Nếu phát hiện giảng viên có days_to_promotion <= 60
        và chưa có phiếu việc nhắc nâng bậc trong kỳ đó -> Tự động tạo 1 Nhiệm vụ
        trong faculty.other.work (activity_type = 'recruitment') giao cho cán bộ
        có cờ can_manage_hr = True (Quản lý nhân sự).
        """
        today = fields.Date.today()
        hr_managers = self.env['faculty.lecturer'].search([('can_manage_hr', '=', True)])
        if not hr_managers:
            hr_managers = self.env['faculty.lecturer'].search([('position_title', 'in', ['dean', 'vice_dean'])], limit=1)
        if not hr_managers:
            hr_managers = self.env['faculty.lecturer'].search([], limit=1)

        default_hr_id = hr_managers[0].id if hr_managers else False
        academic_year = self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1)

        lecturers = self.env['faculty.lecturer'].search([('next_rank_date', '!=', False)])
        created_count = 0
        for lec in lecturers:
            if not lec.next_rank_date:
                continue
            days_left = (lec.next_rank_date - today).days
            if days_left <= 60:
                reminder_code = f"REM-PROM-{lec.id}-{lec.next_rank_date.strftime('%Y%m%d')}"
                existing = self.search([('code', '=', reminder_code)], limit=1)
                if not existing:
                    rank_str = lec.rank_position_display or (f"Bậc {lec.rank_id.sequence}/16" if lec.rank_id else "Chưa rõ")
                    self.create({
                        'name': f"[Nhắc nâng bậc lương] {lec.name} ({rank_str}) - Hạn {lec.next_rank_date.strftime('%d/%m/%Y')}",
                        'code': reminder_code,
                        'activity_type': 'recruitment',
                        'academic_year_id': lec.active_academic_year_id.id or (academic_year.id if academic_year else False),
                        'lead_lecturer_id': default_hr_id or lec.id,
                        'category': 'other',
                        'start_date': today,
                        'deadline': lec.next_rank_date,
                        'notes': f"Hệ thống tự động phát hiện Giảng viên {lec.name} (Mã: {lec.lecturer_code}) còn {days_left} ngày nữa là đến hạn nâng bậc lương ({lec.next_rank_date.strftime('%d/%m/%Y')}). Đề nghị cán bộ nhân sự tiến hành thủ tục và hướng dẫn nộp hồ sơ xét nâng ngạch/bậc lương theo quy định.",
                        'state': 'draft',
                    })
                    created_count += 1
        return created_count

    @api.model
    def cron_periodic_task_reminders(self):
        """
        Tự động nhắc việc định kỳ theo Quy trình thống kê giờ hoạt động của Khoa
        cho cán bộ có cờ can_edit_faculty_tasks = True.
        """
        today = fields.Date.today()
        task_officers = self.env['faculty.lecturer'].search([('can_edit_faculty_tasks', '=', True)])
        if not task_officers:
            task_officers = self.env['faculty.lecturer'].search([('position_title', 'in', ['dean', 'vice_dean'])], limit=1)
        if not task_officers:
            return 0

        academic_year = self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1)
        reminder_code = f"REM-STAT-HOURS-{today.year}-{today.month}"
        existing = self.search([('code', '=', reminder_code)], limit=1)
        if not existing:
            lead_id = task_officers[0].id
            self.create({
                'name': f"[Định kỳ] Rà soát & Thống kê Giờ hoạt động Khoa Tháng {today.month}/{today.year}",
                'code': reminder_code,
                'activity_type': 'general_task',
                'academic_year_id': academic_year.id if academic_year else False,
                'lead_lecturer_id': lead_id,
                'category': 'other',
                'start_date': today,
                'deadline': today + timedelta(days=7),
                'notes': f"Nhắc việc định kỳ theo quy trình Khoa: Đề nghị cán bộ phụ trách nhiệm vụ tiến hành rà soát tiến độ giảng dạy, các công trình NCKH và tổng hợp số liệu giờ chuẩn công tác của toàn thể CBGV Khoa trong tháng {today.month}/{today.year}.",
                'state': 'draft',
            })
            return 1
        return 0

    @api.model
    def cron_sync_calendar_events(self):
        """Cron tự động đồng bộ sự kiện vào Lịch Công tác Chung Toàn Khoa"""
        CalendarEvent = self.env['faculty.calendar.event']
        return CalendarEvent.action_sync_all_events()


class FacultyOtherParticipant(models.Model):
    _name = 'faculty.other.participant'
    _description = 'Thành viên tham gia Hoạt động khác'
    _order = 'work_id, sequence, id'

    work_id = fields.Many2one('faculty.other.work', string='Hoạt động', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='STT', default=10)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên tham gia', required=True, index=True)
    role = fields.Char(string='Vai trò / Nhiệm vụ cụ thể', default='Thành viên', placeholder='VD: Trưởng đoàn, Báo cáo viên, Hỗ trợ...')
    standard_hours = fields.Float(string='Giờ chuẩn phân bổ', default=0.0, required=True)
    need_revision = fields.Boolean(string='Cần chỉnh sửa', default=False, tracking=True)
    notes = fields.Char(string='Ghi chú')

    _sql_constraints = [
        ('check_hours_positive', 'CHECK(standard_hours >= 0)', 'Số giờ chuẩn phải lớn hơn hoặc bằng 0!'),
    ]


class FacultyStreamAssignment(models.Model):
    _name = 'faculty.stream.assignment'
    _description = 'Phân công Nhiệm vụ theo 6 Mảng Chức năng Khoa'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'academic_year_id desc, work_stream asc, sequence asc, id asc'

    sequence = fields.Integer(string='STT', default=10)

    # 6 Mảng Chức năng cốt lõi của Khoa Đào tạo Đại học VN
    work_stream = fields.Selection([
        ('training', '1. Mảng Đào tạo & Quản lý Học vụ'),
        ('research', '2. Mảng Nghiên cứu Khoa học & Hợp tác'),
        ('cadre_personnel', '3. Mảng Cán bộ, Nhân sự & Phát triển Đội ngũ'),
        ('student_affairs', '4. Mảng Công tác Sinh viên & Khảo thí'),
        ('party_union', '5. Mảng Đảng, Đoàn thể & Văn thể mỹ'),
        ('facilities_admin', '6. Mảng Cơ sở vật chất & Hành chính Tổng hợp'),
        ('other', '7. Mảng Bổ sung / Đặc thù khác'),
    ], string='Mảng công tác chức năng', required=True, default='training', tracking=True)

    name = fields.Char(string='Tên nhiệm vụ thường xuyên / Đầu việc', required=True, tracking=True,
                       placeholder='VD: Theo dõi lịch giảng, tiến độ học tập và đề cương chi tiết...')

    lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ thực hiện chính', required=True, tracking=True,
                                  help='Giảng viên / Cán bộ phụ trách đầu mối mảng công việc này.')
    assistant_ids = fields.Many2many('faculty.lecturer', 'faculty_stream_assignment_assistant_rel',
                                    'assignment_id', 'lecturer_id', string='Cán bộ phối hợp thực hiện')

    supervisor_id = fields.Many2one('faculty.lecturer', string='Lãnh đạo Khoa phụ trách', required=True, tracking=True,
                                    help='Trưởng khoa hoặc Phó Trưởng khoa trực tiếp chỉ đạo, giám sát mảng.')

    task_nature = fields.Selection([
        ('regular', 'Thường xuyên'),
        ('ad_hoc', 'Đột xuất / Theo kế hoạch chuyên đề'),
    ], string='Tính chất công việc', default='regular', required=True, tracking=True)

    cycle = fields.Selection([
        ('weekly', 'Hàng tuần'),
        ('monthly', 'Hàng tháng'),
        ('semester', 'Học kỳ'),
        ('annual', 'Năm học'),
    ], string='Chu kỳ báo cáo / Thực hiện', default='annual', required=True, tracking=True)

    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học áp dụng', required=True, tracking=True,
                                       default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)
    semester_id = fields.Many2one('faculty.academic.semester', string='Học kỳ',
                                  domain="[('academic_year_id', '=', academic_year_id)]")

    auto_grant_permission = fields.Boolean(
        string='Tự động cấp quyền tương ứng',
        default=True,
        tracking=True,
        help='Khi bật, hệ thống sẽ tự động cập nhật cờ phân quyền thao tác trên hồ sơ giảng viên (Đào tạo, Khảo thí, Nhân sự...).'
    )

    standard_hours = fields.Float(string='Giờ chuẩn quy đổi / năm', default=0.0,
                                  help='Định mức giờ chuẩn chức năng được ghi nhận cho cán bộ thực hiện chính.')

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('active', 'Đang thực hiện'),
        ('done', 'Đã hoàn thành / Tổng kết'),
    ], string='Trạng thái', default='active', tracking=True)

    notes = fields.Text(string='Ghi chú nhiệm vụ & Yêu cầu kết quả')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(FacultyStreamAssignment, self).create(vals_list)
        for rec in records:
            if rec.auto_grant_permission:
                rec._apply_stream_permissions()
        return records

    def write(self, vals):
        res = super(FacultyStreamAssignment, self).write(vals)
        if 'auto_grant_permission' in vals or 'work_stream' in vals or 'lecturer_id' in vals:
            for rec in self:
                if rec.auto_grant_permission:
                    rec._apply_stream_permissions()
        return res

    def _apply_stream_permissions(self):
        """Tự động bật cờ phân quyền trên faculty.lecturer tương ứng với mảng chức năng phụ trách"""
        self.ensure_one()
        lecturer = self.lecturer_id
        if not lecturer:
            return

        perm_updates = {}
        if self.work_stream == 'training':
            perm_updates.update({'can_edit_subjects': True, 'can_edit_classes': True})
        elif self.work_stream == 'student_affairs':
            perm_updates.update({'can_edit_exams': True})
        elif self.work_stream == 'cadre_personnel':
            perm_updates.update({'can_manage_hr': True, 'can_edit_faculty_tasks': True})
        elif self.work_stream in ('research', 'facilities_admin', 'party_union'):
            perm_updates.update({'can_edit_faculty_tasks': True})

        if perm_updates:
            lecturer.write(perm_updates)

    def action_print_assignment_report(self):
        """In Biểu Phân công Nhiệm vụ 6 Mảng Chức năng Khoa khổ A4 chuẩn hành chính"""
        return self.env.ref('faculty_work_mgmt.action_report_faculty_stream_assignment').report_action(self)


class FacultyLibraryCategory(models.Model):
    _name = 'faculty.library.category'
    _description = 'Thư mục Tài liệu Thư viện Khoa'
    _order = 'sequence asc, name asc'

    name = fields.Char(string='Tên thư mục', required=True, placeholder='VD: Đề cương chi tiết, Giáo trình & Sách...')
    code = fields.Char(string='Mã thư mục', placeholder='VD: SYLLABUS, BOOKS, REGULATIONS...')
    sequence = fields.Integer(string='Thứ tự hiển thị', default=10)
    parent_id = fields.Many2one('faculty.library.category', string='Thư mục cha', ondelete='cascade', index=True)
    child_ids = fields.One2many('faculty.library.category', 'parent_id', string='Thư mục con')
    description = fields.Text(string='Mô tả danh mục')
    document_ids = fields.One2many('faculty.library.document', 'category_id', string='Tài liệu trong mục')
    document_count = fields.Integer(string='Số lượng tài liệu', compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)


class FacultyLibraryDocument(models.Model):
    _name = 'faculty.library.document'
    _description = 'Tài liệu Thư viện Khoa (Offline Filestore)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'year desc, create_date desc, id desc'

    name = fields.Char(string='Tên tài liệu / Văn bản', required=True, tracking=True,
                       placeholder='VD: Đề cương chi tiết HP Lập trình Hướng đối tượng 2026')
    code = fields.Char(string='Mã tài liệu / Số ký hiệu', copy=False, index=True, tracking=True,
                       placeholder='VD: DC-IT201-2026, QD-12/2026...')

    category_id = fields.Many2one('faculty.library.category', string='Thư mục Thư viện', required=True, tracking=True, index=True)

    document_type = fields.Selection([
        ('syllabus', 'Đề cương chi tiết học phần'),
        ('study_material', 'Học liệu / Bài giảng điện tử'),
        ('question_bank', 'Ngân hàng câu hỏi & đề thi'),
        ('curriculum', 'Chương trình đào tạo'),
        ('book', 'Sách / Giáo trình / Tài liệu tham khảo'),
        ('scientific_paper', 'Bài báo / Tham luận / Kỷ yếu'),
        ('regulation', 'Văn bản quy định / Quy trình'),
        ('other', 'Tài liệu lưu trữ khác'),
    ], string='Phân loại tài liệu', default='syllabus', required=True, tracking=True)

    # Lưu trữ 100% qua ir.attachment / filestore nội bộ Odoo (An toàn backup .zip 100%)
    attachment_file = fields.Binary(string='Tệp tài liệu đính kèm (Word/PDF/ZIP)', attachment=True, required=True)
    attachment_filename = fields.Char(string='Tên tệp gốc', required=True)
    file_size_display = fields.Char(string='Kích thước tệp', compute='_compute_file_size', store=False)

    author_id = fields.Many2one('faculty.lecturer', string='Tác giả / Giảng viên nộp', tracking=True)
    course_id = fields.Many2one('faculty.course', string='Học phần liên quan')
    curriculum_id = fields.Many2one('faculty.curriculum', string='CTĐT liên quan')
    year = fields.Integer(string='Năm ban hành / Xuất bản', default=lambda self: date.today().year, required=True)

    # Nguồn gốc liên kết phát sinh
    source_model = fields.Char(string='Model nguồn', index=True)
    source_id = fields.Integer(string='ID nguồn', index=True)

    # 4 cấp độ tiếp cận bảo mật
    security_level = fields.Selection([
        ('public', '1. Công khai (Toàn bộ người dùng)'),
        ('internal', '2. Nội bộ Khoa (Toàn thể CBGV Khoa)'),
        ('leadership', '3. Lãnh đạo Khoa (Ban Chủ nhiệm & Trưởng BM)'),
        ('restricted', '4. Mật / Chỉ định đích danh'),
    ], string='Mức độ tiếp cận', default='internal', required=True, tracking=True)

    allowed_user_ids = fields.Many2many('res.users', 'faculty_library_doc_user_rel',
                                        'doc_id', 'user_id', string='Tài khoản được xem')
    allowed_lecturer_ids = fields.Many2many('faculty.lecturer', 'faculty_library_doc_lecturer_rel',
                                            'doc_id', 'lecturer_id', string='Giảng viên được chỉ định xem')

    # Cổng Admin Rà soát Tài liệu
    review_state = fields.Selection([
        ('pending_review', 'Chờ Admin duyệt Thư viện'),
        ('approved', 'Đã lưu Thư viện (Chính thức)'),
        ('rejected', 'Từ chối lưu'),
    ], string='Trạng thái rà soát', default='approved', required=True, tracking=True)

    reviewer_id = fields.Many2one('res.users', string='Cán bộ kiểm duyệt', tracking=True)
    review_date = fields.Date(string='Ngày kiểm duyệt', tracking=True)
    review_notes = fields.Text(string='Ý kiến rà soát kiểm duyệt')

    description = fields.Text(string='Tóm tắt / Nội dung tài liệu')

    def _compute_file_size(self):
        for rec in self:
            if rec.attachment_file:
                # Tính kích thước xấp xỉ từ base64
                size_bytes = len(rec.attachment_file) * 3 / 4
                if size_bytes >= 1024 * 1024:
                    rec.file_size_display = f"{size_bytes / (1024 * 1024):.2f} MB"
                elif size_bytes >= 1024:
                    rec.file_size_display = f"{size_bytes / 1024:.1f} KB"
                else:
                    rec.file_size_display = f"{int(size_bytes)} Bytes"
            else:
                rec.file_size_display = "0 KB"

    def action_approve_library(self):
        """Admin bấm phê duyệt lưu chính thức vào Thư viện Khoa"""
        for rec in self:
            rec.write({
                'review_state': 'approved',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Date.context_today(self),
            })
            rec.message_post(body=_("Tài liệu đã được phê duyệt đưa vào Thư viện Khoa chính thức."))
            # Cập nhật ngược lại bản ghi nguồn nếu có
            if rec.source_model and rec.source_id:
                src_obj = self.env[rec.source_model].browse(rec.source_id)
                if src_obj.exists() and hasattr(src_obj, 'library_review_state'):
                    src_obj.library_review_state = 'approved'
        return True

    def action_reject_library(self):
        """Admin từ chối lưu vào Thư viện Khoa"""
        for rec in self:
            rec.write({
                'review_state': 'rejected',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Date.context_today(self),
            })
            rec.message_post(body=_("Tài liệu đã bị từ chối lưu vào Thư viện Khoa."))
            if rec.source_model and rec.source_id:
                src_obj = self.env[rec.source_model].browse(rec.source_id)
                if src_obj.exists() and hasattr(src_obj, 'library_review_state'):
                    src_obj.library_review_state = 'not_required'
        return True


# =============================================================================
# GIAI ĐOẠN 4: LỊCH CÔNG TÁC CHUNG TOÀN KHOA & DASHBOARD ĐIỀU HÀNH REAL-TIME
# =============================================================================

class FacultyCalendarEvent(models.Model):
    _name = 'faculty.calendar.event'
    _description = 'Lịch Công tác Chung Toàn Khoa (Google Calendar & Popover)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'start_datetime asc, id desc'

    name = fields.Char(string='Tên sự kiện / Buổi công tác', required=True, tracking=True)
    event_category = fields.Selection([
        ('teaching', '1. Giảng dạy (Chính khóa / Bù / Cải thiện)'),
        ('exam', '2. Khảo thí & Lịch thi'),
        ('guest_speaker', '3. Báo cáo thực tế & Báo cáo viên'),
        ('dept_event_task', '4. Sự kiện Khoa & Hạn chót công việc'),
        ('birthday', '5. Sinh nhật Cán bộ Giảng viên'),
    ], string='Phân loại sự kiện', required=True, default='dept_event_task', index=True, tracking=True)

    start_datetime = fields.Datetime(string='Thời gian bắt đầu', required=True, index=True, tracking=True)
    stop_datetime = fields.Datetime(string='Thời gian kết thúc', required=True, tracking=True)
    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True)
    all_day = fields.Boolean(string='Cả ngày', default=False)

    location = fields.Char(string='Địa điểm / Phòng học', tracking=True, placeholder='VD: Phòng A201, Hội trường B...')
    lecturer_id = fields.Many2one('faculty.lecturer', string='Người chủ trì / Giảng viên đứng lớp', index=True, tracking=True)
    partner_id = fields.Many2one('res.partner', related='lecturer_id.partner_id', string='Đối tác liên kết', store=True)

    course_id = fields.Many2one('faculty.course', string='Học phần liên quan')
    student_class_id = fields.Many2one('faculty.student.class', string='Lớp liên quan')
    course_class_display = fields.Char(string='Học phần / Lớp', compute='_compute_course_class_display', store=True)

    notes = fields.Text(string='Ghi chú chi tiết / Nội dung công tác')
    color = fields.Integer(string='Mã màu Odoo', compute='_compute_color', store=True)
    color_hex = fields.Char(string='Mã màu HEX', compute='_compute_color', store=True)

    res_model = fields.Char(string='Model nguồn', index=True)
    res_id = fields.Integer(string='ID bản ghi nguồn', index=True)
    event_key = fields.Char(string='Mã định danh đồng bộ', index=True, copy=False)

    _sql_constraints = [
        ('event_key_unique', 'unique(event_key)', 'Sự kiện đã tồn tại trong lịch công tác chung!'),
    ]

    @api.depends('start_datetime', 'stop_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.stop_datetime:
                diff = rec.stop_datetime - rec.start_datetime
                rec.duration = round(diff.total_seconds() / 3600.0, 2)
            else:
                rec.duration = 0.0

    @api.depends('course_id', 'student_class_id')
    def _compute_course_class_display(self):
        for rec in self:
            parts = []
            if rec.course_id:
                parts.append(rec.course_id.name)
            if rec.student_class_id:
                parts.append(f"Lớp: {rec.student_class_id.name}")
            rec.course_class_display = " - ".join(parts) if parts else ""

    @api.depends('event_category')
    def _compute_color(self):
        # 5 nhóm màu chuẩn:
        # 1. teaching (Xanh dương): color=1, hex=#007bff
        # 2. exam (Cam): color=3, hex=#fd7e14
        # 3. guest_speaker (Xanh lá): color=10, hex=#28a745
        # 4. dept_event_task (Đỏ / Tím): color=9, hex=#800080
        # 5. birthday (Vàng): color=2, hex=#ffc107
        color_map = {
            'teaching': (1, '#007bff'),
            'exam': (3, '#fd7e14'),
            'guest_speaker': (10, '#28a745'),
            'dept_event_task': (9, '#800080'),
            'birthday': (2, '#ffc107'),
        }
        for rec in self:
            c_int, c_hex = color_map.get(rec.event_category, (0, '#6c757d'))
            rec.color = c_int
            rec.color_hex = c_hex

    def action_open_source(self):
        """Mở bản ghi nguồn từ sự kiện trên Lịch"""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise UserError(_('Sự kiện này không có bản ghi nguồn liên kết.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def action_sync_all_events(self):
        """
        ĐỒNG BỘ TOÀN DIỆN 5 NHÓM SỰ KIỆN VÀO LỊCH CÔNG TÁC CHUNG TOÀN KHOA:
        1. Giảng dạy (Xanh dương): Lịch giảng chính khóa, bù, cải thiện (faculty.teaching.session).
        2. Khảo thí (Cam): Lịch thi, coi thi, hạn chấm thi (faculty.class.course, faculty.exam.assignment).
        3. Báo cáo thực tế & Báo cáo viên (Xanh lá): Các buổi mời báo cáo viên thực tế.
        4. Sự kiện Khoa & Hạn chót việc (Đỏ / Tím): Họp Khoa, Hội thảo, Đề tài NCKH, Checklist học vụ.
        5. Sinh nhật Cán bộ Giảng viên (Vàng): Ngày sinh của các giảng viên trong năm.
        """
        today = fields.Date.today()
        current_year = today.year
        created_count = 0
        updated_count = 0

        # -------------------------------------------------------------
        # 1. Nhóm Giảng dạy & 3. Nhóm Báo cáo viên (faculty.teaching.session)
        # -------------------------------------------------------------
        sessions = self.env['faculty.teaching.session'].search([
            ('date', '>=', today - timedelta(days=60)),
            ('date', '<=', today + timedelta(days=180)),
        ])
        for sess in sessions:
            if not sess.date:
                continue
            is_morning = (sess.period == 'Sáng')
            start_t = time(7, 30) if is_morning else time(13, 30)
            stop_t = time(11, 30) if is_morning else time(17, 30)
            start_dt = datetime.combine(sess.date, start_t)
            stop_dt = datetime.combine(sess.date, stop_t)

            lead_lecturer = sess.lecturer_id or (sess.teacher_ids[0] if sess.teacher_ids else False)
            course_name = sess.course_id.name if sess.course_id else 'Học phần'
            class_name = sess.class_id.name if sess.class_id else 'Lớp'
            room = sess.room or (sess.class_id.room if sess.class_id else 'Giảng đường Khoa')

            # Nếu có báo cáo viên thực tế -> Nhóm 3 (guest_speaker)
            if sess.has_guest_speaker or sess.guest_speaker_name:
                key = f"guest_speaker_session_{sess.id}"
                cat = 'guest_speaker'
                name = f"[Báo cáo viên] {sess.guest_speaker_name or 'Chuyên gia thực tế'} - HP {course_name} ({class_name})"
                notes = f"Báo cáo viên thực tế: {sess.guest_speaker_name or ''}. Đơn vị: {sess.guest_speaker_org or ''}. Giảng viên phụ trách: {lead_lecturer.name if lead_lecturer else ''}."
            else:
                key = f"teaching_session_{sess.id}"
                cat = 'teaching'
                name = f"[Giảng dạy] {course_name} - {class_name} ({sess.period})"
                notes = f"Lịch giảng: {sess.name or ''}. Số tiết: {sess.periods}. Giảng viên đứng lớp: {lead_lecturer.name if lead_lecturer else ''}. Trạng thái: {'Đã diễn ra' if sess.is_conducted else 'Sắp tới'}."

            vals = {
                'name': name,
                'event_category': cat,
                'start_datetime': start_dt,
                'stop_datetime': stop_dt,
                'location': room,
                'lecturer_id': lead_lecturer.id if lead_lecturer else False,
                'course_id': sess.course_id.id if sess.course_id else False,
                'student_class_id': sess.class_id.id if sess.class_id else False,
                'notes': notes,
                'res_model': 'faculty.teaching.session',
                'res_id': sess.id,
            }
            existing = self.search([('event_key', '=', key)], limit=1)
            if existing:
                existing.write(vals)
                updated_count += 1
            else:
                vals['event_key'] = key
                self.create(vals)
                created_count += 1

        # -------------------------------------------------------------
        # 2. Nhóm Khảo thí & Lịch thi (faculty.class.course & faculty.exam.assignment)
        # -------------------------------------------------------------
        class_courses = self.env['faculty.class.course'].search([
            ('exam_date', '!=', False),
            ('exam_date', '>=', today - timedelta(days=60)),
            ('exam_date', '<=', today + timedelta(days=180)),
        ])
        for cc in class_courses:
            # Sự kiện 1: Buổi thi chính thức
            key_exam = f"exam_date_cc_{cc.id}"
            start_exam = datetime.combine(cc.exam_date, time(8, 0))
            stop_exam = datetime.combine(cc.exam_date, time(11, 0))
            vals_exam = {
                'name': f"[Khảo thí] Lịch thi HP: {cc.course_id.name} - Lớp {cc.class_id.name}",
                'event_category': 'exam',
                'start_datetime': start_exam,
                'stop_datetime': stop_exam,
                'location': cc.exam_room or cc.class_id.room or 'Phòng thi Khoa',
                'lecturer_id': cc.lecturer_id.id if cc.lecturer_id else False,
                'course_id': cc.course_id.id if cc.course_id else False,
                'student_class_id': cc.class_id.id if cc.class_id else False,
                'notes': f"Hình thức thi: {cc.exam_format or ''}. Nguồn đề: {cc.exam_source or ''}. Sĩ số dự thi: {cc.total_students}.",
                'res_model': 'faculty.class.course',
                'res_id': cc.id,
            }
            exist_exam = self.search([('event_key', '=', key_exam)], limit=1)
            if exist_exam:
                exist_exam.write(vals_exam)
            else:
                vals_exam['event_key'] = key_exam
                self.create(vals_exam)

            # Sự kiện 2: Hạn chấm thi nếu có
            if cc.grading_deadline:
                key_grading = f"grading_deadline_cc_{cc.id}"
                start_gr = datetime.combine(cc.grading_deadline, time(8, 0))
                stop_gr = datetime.combine(cc.grading_deadline, time(17, 0))
                vals_gr = {
                    'name': f"[Hạn chấm thi] HP: {cc.course_id.name} - Lớp {cc.class_id.name}",
                    'event_category': 'exam',
                    'start_datetime': start_gr,
                    'stop_datetime': stop_gr,
                    'location': 'Văn phòng Khoa / Khảo thí',
                    'lecturer_id': cc.lecturer_id.id if cc.lecturer_id else False,
                    'course_id': cc.course_id.id if cc.course_id else False,
                    'student_class_id': cc.class_id.id if cc.class_id else False,
                    'notes': f"Hạn cuối bàn giao bài thi và bảng điểm tổng hợp về Giáo vụ Khoa.",
                    'res_model': 'faculty.class.course',
                    'res_id': cc.id,
                }
                exist_gr = self.search([('event_key', '=', key_grading)], limit=1)
                if exist_gr:
                    exist_gr.write(vals_gr)
                else:
                    vals_gr['event_key'] = key_grading
                    self.create(vals_gr)

        # -------------------------------------------------------------
        # 4. Nhóm Sự kiện Khoa & Hạn chót công việc (faculty.other.work & NCKH)
        # -------------------------------------------------------------
        other_tasks = self.env['faculty.other.work'].search([
            ('deadline', '!=', False),
            ('deadline', '>=', today - timedelta(days=60)),
            ('deadline', '<=', today + timedelta(days=180)),
        ])
        for task in other_tasks:
            key_task = f"other_work_task_{task.id}"
            st_date = task.deadline or task.start_date or today
            start_task = datetime.combine(st_date, time(8, 30))
            stop_task = datetime.combine(st_date, time(16, 30))
            vals_task = {
                'name': f"[Sự kiện Khoa] {task.name}",
                'event_category': 'dept_event_task',
                'start_datetime': start_task,
                'stop_datetime': stop_task,
                'location': 'Khoa Đào tạo / Trực tuyến',
                'lecturer_id': task.lead_lecturer_id.id if task.lead_lecturer_id else False,
                'notes': f"Phân loại: {dict(task._fields['activity_type'].selection).get(task.activity_type, '')}. Hạn chót: {task.deadline.strftime('%d/%m/%Y') if task.deadline else ''}. Trạng thái: {dict(task._fields['state'].selection).get(task.state, '')}.",
                'res_model': 'faculty.other.work',
                'res_id': task.id,
            }
            exist_task = self.search([('event_key', '=', key_task)], limit=1)
            if exist_task:
                exist_task.write(vals_task)
            else:
                vals_task['event_key'] = key_task
                self.create(vals_task)

        # -------------------------------------------------------------
        # 5. Nhóm Sinh nhật Cán bộ Giảng viên (faculty.lecturer)
        # -------------------------------------------------------------
        lecturers = self.env['faculty.lecturer'].search([('birth_date', '!=', False)])
        for lec in lecturers:
            b_date = lec.birth_date
            try:
                bday_this_year = date(current_year, b_date.month, b_date.day)
            except ValueError:
                # Xử lý nhuận 29/02
                bday_this_year = date(current_year, 2, 28)

            key_bday = f"birthday_{lec.id}_{current_year}"
            start_bday = datetime.combine(bday_this_year, time(0, 0))
            stop_bday = datetime.combine(bday_this_year, time(23, 59))

            vals_bday = {
                'name': f"🎂 [Sinh nhật] {lec.name} ({lec.rank_position_display or 'CBGV'})",
                'event_category': 'birthday',
                'start_datetime': start_bday,
                'stop_datetime': stop_bday,
                'all_day': True,
                'location': 'Khoa Đào tạo',
                'lecturer_id': lec.id,
                'notes': f"Chúc mừng sinh nhật Thầy/Cô {lec.name}! Số điện thoại: {lec.phone or 'Chưa cập nhật'}. Email: {lec.email or 'Chưa cập nhật'}.",
                'res_model': 'faculty.lecturer',
                'res_id': lec.id,
            }
            exist_bday = self.search([('event_key', '=', key_bday)], limit=1)
            if exist_bday:
                exist_bday.write(vals_bday)
            else:
                vals_bday['event_key'] = key_bday
                self.create(vals_bday)

        return True


class FacultyDashboard(models.TransientModel):
    _name = 'faculty.dashboard'
    _description = 'Bảng Điều hành Thông minh Real-time'

    name = fields.Char(string='Tên bảng điều hành', default='Bảng Điều hành Thông minh Khoa Đào tạo')
    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học theo dõi',
                                       default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)
    date = fields.Date(string='Thời điểm truy vấn', default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Người dùng hiện tại', default=lambda self: self.env.user)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Hồ sơ giảng viên của bạn')
    is_management = fields.Boolean(string='Là Lãnh đạo / Giáo vụ Khoa', default=False)

    # Thống kê KPI tóm tắt đầu trang
    count_overdue = fields.Integer(string='Số việc Quá hạn (Màu Tím)', default=0)
    count_urgent = fields.Integer(string='Số việc Khẩn cấp / Cần sửa (Màu Đỏ)', default=0)
    count_birthdays = fields.Integer(string='Sinh nhật sắp tới (7 ngày)', default=0)
    count_promotions = fields.Integer(string='Đến hạn nâng bậc (60 ngày)', default=0)
    total_lecturers = fields.Integer(string='Tổng số Giảng viên', default=0)
    total_hours_realtime = fields.Float(string='Tổng giờ thực tế tích lũy', default=0.0)

    # 4 Bảng dữ liệu con
    alert_ids = fields.One2many('faculty.dashboard.alert', 'dashboard_id', string='Danh sách Cảnh báo theo Vai trò')
    birthday_ids = fields.One2many('faculty.dashboard.birthday', 'dashboard_id', string='Nhắc lịch Sinh nhật toàn Khoa')
    promotion_ids = fields.One2many('faculty.dashboard.promotion', 'dashboard_id', string='Cảnh báo Nâng bậc lương toàn Khoa')
    hour_ids = fields.One2many('faculty.dashboard.hour', 'dashboard_id', string='Bảng Theo dõi Thừa / Thiếu Giờ chuẩn Real-time')

    @api.model
    def action_open_dashboard(self):
        """Mở Bảng Điều hành Thông minh Real-time cho người dùng hiện tại"""
        dashboard = self.create({'name': f"Bảng Điều hành Khoa - {fields.Date.context_today(self).strftime('%d/%m/%Y')}"})
        dashboard._populate_dashboard_data()
        return {
            'name': _('Bảng Điều hành Thông minh Real-time'),
            'type': 'ir.actions.act_window',
            'res_model': 'faculty.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_refresh_dashboard(self):
        """Bấm nút Làm mới dữ liệu trên Dashboard"""
        self.ensure_one()
        self._populate_dashboard_data()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'faculty.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_calendar(self):
        """Mở Lịch Công tác Chung Toàn Khoa"""
        action = self.env.ref('faculty_work_mgmt.action_faculty_calendar_event').read()[0]
        return action

    def action_open_excel_wizard(self):
        """Mở Wizard Xuất Báo cáo Excel"""
        return {
            'name': _('Xuất Báo cáo Excel 2 Sheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'faculty.excel.report.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def _populate_dashboard_data(self):
        """
        Nạp dữ liệu thời gian thực cho Bảng Điều hành:
        - Phân tách cảnh báo theo vai trò:
          + Giảng viên thường: Chỉ thấy việc, NCKH, Checklist của chính mình (Quá hạn màu Tím #800080, Khẩn cấp / Cần sửa màu Đỏ #dc3545).
          + Lãnh đạo / Giáo vụ / Admin: Thấy toàn bộ cảnh báo Quá hạn và Khẩn cấp của TOÀN KHOA.
        - Thông tin chung toàn Khoa:
          + Nhắc sinh nhật (trước 7 ngày và hôm nay).
          + Cảnh báo nâng bậc lương (trước 60 ngày).
          + Bảng theo dõi Thừa / Thiếu giờ chuẩn Real-time: _read_group từ faculty.hour.ledger date <= today so với định mức sau giảm.
        """
        self.ensure_one()
        today = fields.Date.today()
        three_days = today + timedelta(days=3)

        # 1. Xác định vai trò người dùng
        is_mgr = (
            self.env.is_admin() or
            self.env.user.has_group('faculty_work_mgmt.group_faculty_dean') or
            self.env.user.has_group('faculty_work_mgmt.group_faculty_training') or
            self.env.user.has_group('faculty_work_mgmt.group_faculty_exam')
        )
        self.is_management = is_mgr

        lec = self.env['faculty.lecturer'].search([('user_id', '=', self.env.user.id)], limit=1)
        if not lec:
            lec = self.env['faculty.lecturer'].search([('partner_id', '=', self.env.user.partner_id.id)], limit=1)
        self.lecturer_id = lec.id if lec else False

        # -------------------------------------------------------------
        # 2. KHU VỰC CẢNH BÁO THEO VAI TRÒ
        # -------------------------------------------------------------
        self.alert_ids.unlink()
        alerts = []

        # 2.1. Cảnh báo từ Hoạt động khác (faculty.other.work)
        ow_domain = [('state', '!=', 'approved'), ('completion_date', '=', False)]
        if not is_mgr and lec:
            ow_domain.extend(['|', ('lead_lecturer_id', '=', lec.id), ('participant_ids.lecturer_id', '=', lec.id)])
        other_works = self.env['faculty.other.work'].search(ow_domain)
        for w in other_works:
            has_rev = any(p.need_revision for p in w.participant_ids if is_mgr or (lec and p.lecturer_id.id == lec.id))
            if w.deadline and w.deadline < today:
                alerts.append((0, 0, {
                    'name': f"[HĐ khác] {w.name}",
                    'source_type': 'other_work',
                    'lecturer_id': w.lead_lecturer_id.id if w.lead_lecturer_id else False,
                    'deadline': w.deadline,
                    'alert_type': 'overdue',
                    'color_hex': '#800080',
                    'res_model': 'faculty.other.work',
                    'res_id': w.id,
                }))
            elif has_rev or (w.deadline and w.deadline <= three_days):
                a_type = 'revision' if has_rev else 'urgent'
                alerts.append((0, 0, {
                    'name': f"[HĐ khác] {w.name}" + (" (Yêu cầu sửa lại)" if has_rev else ""),
                    'source_type': 'other_work',
                    'lecturer_id': w.lead_lecturer_id.id if w.lead_lecturer_id else False,
                    'deadline': w.deadline,
                    'alert_type': a_type,
                    'color_hex': '#dc3545',
                    'res_model': 'faculty.other.work',
                    'res_id': w.id,
                }))

        # 2.2. Cảnh báo từ Đề tài / Công trình NCKH (faculty.research.work)
        rw_domain = [('state', '!=', 'approved')]
        if not is_mgr and lec:
            rw_domain.extend(['|', ('leader_id', '=', lec.id), ('participant_ids.lecturer_id', '=', lec.id)])
        research_works = self.env['faculty.research.work'].search(rw_domain)
        for r in research_works:
            has_rev = any(p.need_revision for p in r.participant_ids if is_mgr or (lec and p.lecturer_id.id == lec.id))
            r_deadline = r.deadline or r.acceptance_date
            if r_deadline and r_deadline < today:
                alerts.append((0, 0, {
                    'name': f"[NCKH] {r.name}",
                    'source_type': 'research',
                    'lecturer_id': r.leader_id.id if r.leader_id else False,
                    'deadline': r_deadline,
                    'alert_type': 'overdue',
                    'color_hex': '#800080',
                    'res_model': 'faculty.research.work',
                    'res_id': r.id,
                }))
            elif has_rev or (r_deadline and r_deadline <= three_days):
                a_type = 'revision' if has_rev else 'urgent'
                alerts.append((0, 0, {
                    'name': f"[NCKH] {r.name}" + (" (Yêu cầu sửa lại)" if has_rev else ""),
                    'source_type': 'research',
                    'lecturer_id': r.leader_id.id if r.leader_id else False,
                    'deadline': r_deadline,
                    'alert_type': a_type,
                    'color_hex': '#dc3545',
                    'res_model': 'faculty.research.work',
                    'res_id': r.id,
                }))

        # 2.3. Cảnh báo từ Checklist 7 bước học vụ (faculty.academic.checklist)
        chk_domain = [('is_done', '=', False), ('deadline', '!=', False)]
        if not is_mgr and lec:
            chk_domain.extend(['|', ('class_course_id.lecturer_id', '=', lec.id), ('class_course_id.class_id.teacher_ids', 'in', [lec.id])])
        checklists = self.env['faculty.academic.checklist'].search(chk_domain)
        for c in checklists:
            c_name = f"[Checklist] Bước {c.step_number}: {c.name} ({c.class_course_id.course_id.name})"
            if c.deadline < today:
                alerts.append((0, 0, {
                    'name': c_name,
                    'source_type': 'checklist',
                    'lecturer_id': c.class_course_id.lecturer_id.id if c.class_course_id.lecturer_id else False,
                    'deadline': c.deadline,
                    'alert_type': 'overdue',
                    'color_hex': '#800080',
                    'res_model': 'faculty.academic.checklist',
                    'res_id': c.id,
                }))
            elif c.deadline <= three_days:
                alerts.append((0, 0, {
                    'name': c_name,
                    'source_type': 'checklist',
                    'lecturer_id': c.class_course_id.lecturer_id.id if c.class_course_id.lecturer_id else False,
                    'deadline': c.deadline,
                    'alert_type': 'urgent',
                    'color_hex': '#dc3545',
                    'res_model': 'faculty.academic.checklist',
                    'res_id': c.id,
                }))

        self.alert_ids = alerts

        # -------------------------------------------------------------
        # 3. THÔNG TIN CHUNG TOÀN KHOA: NHẮC SINH NHẬT (7 NGÀY & HÔM NAY)
        # -------------------------------------------------------------
        self.birthday_ids.unlink()
        birthdays = []
        all_lecturers = self.env['faculty.lecturer'].search([])
        for l in all_lecturers:
            if not l.birth_date:
                continue
            b = l.birth_date
            try:
                b_this = date(today.year, b.month, b.day)
            except ValueError:
                b_this = date(today.year, 2, 28)

            if b_this < today:
                try:
                    b_next = date(today.year + 1, b.month, b.day)
                except ValueError:
                    b_next = date(today.year + 1, 2, 28)
                delta = (b_next - today).days
            else:
                delta = (b_this - today).days

            if 0 <= delta <= 7:
                birthdays.append((0, 0, {
                    'lecturer_id': l.id,
                    'birth_date': l.birth_date,
                    'birthday_display': l.birth_date.strftime('%d/%m'),
                    'days_until': delta,
                    'is_today': (delta == 0),
                    'phone': l.phone or '',
                    'email': l.email or '',
                }))
        # Sắp xếp người có sinh nhật gần nhất lên đầu
        birthdays.sort(key=lambda x: x[2]['days_until'])
        self.birthday_ids = birthdays

        # -------------------------------------------------------------
        # 4. THÔNG TIN CHUNG TOÀN KHOA: CẢNH BÁO NÂNG BẬC LƯƠNG (60 NGÀY)
        # -------------------------------------------------------------
        self.promotion_ids.unlink()
        promotions = []
        for l in all_lecturers:
            if not l.next_rank_date:
                continue
            days_left = (l.next_rank_date - today).days
            if days_left <= 60:
                cur_seq = l.rank_id.sequence if l.rank_id else 0
                next_seq = cur_seq + 1 if cur_seq < 16 else 16
                promotions.append((0, 0, {
                    'lecturer_id': l.id,
                    'current_rank_display': f"Bậc {cur_seq}/16" if cur_seq else "Chưa xếp bậc",
                    'next_rank_display': f"Bậc {next_seq}/16",
                    'next_rank_date': l.next_rank_date,
                    'days_to_promotion': days_left,
                    'is_overdue': (days_left < 0),
                }))
        promotions.sort(key=lambda x: x[2]['days_to_promotion'])
        self.promotion_ids = promotions

        # -------------------------------------------------------------
        # 5. BẢNG THEO DÕI THỪA / THIẾU GIỜ CHUẨN REAL-TIME (_read_group)
        # -------------------------------------------------------------
        self.hour_ids.unlink()
        ledger_domain = [('date', '<=', today)]
        if self.academic_year_id:
            ledger_domain.append(('academic_year_id', '=', self.academic_year_id.id))

        grouped_ledger = self.env['faculty.hour.ledger']._read_group(
            domain=ledger_domain,
            groupby=['lecturer_id', 'category'],
            aggregates=['standard_hours:sum'],
        )
        # Index {lecturer_id: {category: hours}}
        hours_map = {}
        for l_rec, cat, h_sum in grouped_ledger:
            if not l_rec:
                continue
            lid = l_rec.id
            hours_map.setdefault(lid, {})
            hours_map[lid][cat] = h_sum or 0.0

        hour_lines = []
        total_hours_sum = 0.0
        for l in all_lecturers:
            l_hours = hours_map.get(l.id, {})
            t_act = l_hours.get('teaching', 0.0)
            r_act = l_hours.get('research', 0.0)
            o_act = l_hours.get('other', 0.0)

            t_norm = l.teaching_norm_reduced or 0.0
            r_norm = l.research_norm_reduced or 0.0
            o_norm = l.other_norm_reduced or 0.0

            t_bal = round(t_act - t_norm, 2)
            r_bal = round(r_act - r_norm, 2)
            o_bal = round(o_act - o_norm, 2)
            tot_bal = round(t_bal + r_bal + o_bal, 2)

            total_hours_sum += (t_act + r_act + o_act)

            if tot_bal > 0:
                stat = 'surplus'
            elif tot_bal < 0:
                stat = 'deficit'
            else:
                stat = 'balanced'

            hour_lines.append((0, 0, {
                'lecturer_id': l.id,
                'academic_title_display': l.rank_position_display or 'Giảng viên',
                'teaching_norm_reduced': t_norm,
                'teaching_actual': t_act,
                'teaching_balance': t_bal,
                'research_norm_reduced': r_norm,
                'research_actual': r_act,
                'research_balance': r_bal,
                'other_norm_reduced': o_norm,
                'other_actual': o_act,
                'other_balance': o_bal,
                'total_balance': tot_bal,
                'status': stat,
            }))

        self.hour_ids = hour_lines

        # Cập nhật KPI Counters
        self.count_overdue = sum(1 for a in self.alert_ids if a.alert_type == 'overdue')
        self.count_urgent = sum(1 for a in self.alert_ids if a.alert_type in ('urgent', 'revision'))
        self.count_birthdays = len(self.birthday_ids)
        self.count_promotions = len(self.promotion_ids)
        self.total_lecturers = len(all_lecturers)
        self.total_hours_realtime = round(total_hours_sum, 2)


class FacultyDashboardAlert(models.TransientModel):
    _name = 'faculty.dashboard.alert'
    _description = 'Dòng Cảnh báo Dashboard theo Vai trò'
    _order = 'deadline asc, id desc'

    dashboard_id = fields.Many2one('faculty.dashboard', string='Bảng điều hành', required=True, ondelete='cascade')
    name = fields.Char(string='Tên công việc / Đề tài / Bước học vụ', required=True)
    source_type = fields.Selection([
        ('checklist', 'Checklist 7 bước học vụ'),
        ('research', 'Đề tài / Công trình NCKH'),
        ('other_work', 'Nhiệm vụ / Hoạt động khác'),
    ], string='Nguồn công việc', required=True)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ phụ trách')
    deadline = fields.Date(string='Hạn chót')
    alert_type = fields.Selection([
        ('overdue', 'Quá hạn (Màu Tím #800080)'),
        ('urgent', 'Khẩn cấp <= 3 ngày (Màu Đỏ)'),
        ('revision', 'Bị trả lại yêu cầu sửa (Màu Đỏ)'),
    ], string='Mức độ cảnh báo', required=True)
    color_hex = fields.Char(string='Mã màu HEX', default='#dc3545')
    res_model = fields.Char(string='Model nguồn')
    res_id = fields.Integer(string='ID nguồn')

    def action_open_record(self):
        """Mở nhanh bản ghi nguồn để xử lý"""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise UserError(_('Bản ghi này không có liên kết nguồn.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }


class FacultyDashboardBirthday(models.TransientModel):
    _name = 'faculty.dashboard.birthday'
    _description = 'Nhắc Sinh nhật Thành viên Khoa'
    _order = 'days_until asc, id asc'

    dashboard_id = fields.Many2one('faculty.dashboard', string='Bảng điều hành', required=True, ondelete='cascade')
    lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ Giảng viên', required=True)
    birth_date = fields.Date(string='Ngày sinh')
    birthday_display = fields.Char(string='Ngày sinh nhật')
    days_until = fields.Integer(string='Số ngày còn lại')
    is_today = fields.Boolean(string='Hôm nay sinh nhật', default=False)
    phone = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Email liên hệ')


class FacultyDashboardPromotion(models.TransientModel):
    _name = 'faculty.dashboard.promotion'
    _description = 'Cảnh báo Nâng bậc lương Giảng viên'
    _order = 'days_to_promotion asc, id asc'

    dashboard_id = fields.Many2one('faculty.dashboard', string='Bảng điều hành', required=True, ondelete='cascade')
    lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ Giảng viên', required=True)
    current_rank_display = fields.Char(string='Bậc lương hiện tại')
    next_rank_display = fields.Char(string='Bậc lương dự kiến')
    next_rank_date = fields.Date(string='Ngày đến hạn')
    days_to_promotion = fields.Integer(string='Số ngày đến hạn')
    is_overdue = fields.Boolean(string='Đã quá hạn', default=False)


class FacultyDashboardHour(models.TransientModel):
    _name = 'faculty.dashboard.hour'
    _description = 'Theo dõi Thừa / Thiếu Giờ chuẩn Real-time'
    _order = 'total_balance asc, id asc'

    dashboard_id = fields.Many2one('faculty.dashboard', string='Bảng điều hành', required=True, ondelete='cascade')
    lecturer_id = fields.Many2one('faculty.lecturer', string='Cán bộ Giảng viên', required=True)
    academic_title_display = fields.Char(string='Chức danh / Cấp bậc')

    teaching_norm_reduced = fields.Float(string='Định mức Giảng dạy')
    teaching_actual = fields.Float(string='Thực tế Giảng dạy')
    teaching_balance = fields.Float(string='Thừa/Thiếu GD')

    research_norm_reduced = fields.Float(string='Định mức NCKH')
    research_actual = fields.Float(string='Thực tế NCKH')
    research_balance = fields.Float(string='Thừa/Thiếu NCKH')

    other_norm_reduced = fields.Float(string='Định mức HĐ khác')
    other_actual = fields.Float(string='Thực tế HĐ khác')
    other_balance = fields.Float(string='Thừa/Thiếu HĐ khác')

    total_balance = fields.Float(string='Tổng Thừa / Thiếu')
    status = fields.Selection([
        ('surplus', 'Thừa giờ (+ )'),
        ('deficit', 'Thiếu giờ (- )'),
        ('balanced', 'Đạt chuẩn (0)'),
    ], string='Đánh giá sơ bộ')


