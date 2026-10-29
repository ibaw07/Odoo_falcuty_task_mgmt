# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import date


class FacultyLecturer(models.Model):
    _name = 'faculty.lecturer'
    _description = 'Hồ sơ Giảng viên'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'lecturer_code asc, name asc'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', auto_join=True, string='Thông tin đối tác')
    lecturer_code = fields.Char(string='Mã giảng viên', required=True, copy=False, index=True, tracking=True, placeholder='VD: GV001')
    user_id = fields.Many2one('res.users', string='Tài khoản người dùng Odoo', tracking=True,
                              help='Liên kết với tài khoản hệ thống để phân quyền và tự động lọc công việc cá nhân.')

    # Học hàm & Học vị
    academic_title = fields.Selection([
        ('none', 'Chưa có'),
        ('assoc_prof', 'Phó Giáo sư'),
        ('prof', 'Giáo sư'),
    ], string='Học hàm', default='none', tracking=True)
    title_appointment_year = fields.Integer(string='Năm bổ nhiệm học hàm', placeholder='VD: 2020')

    academic_degree = fields.Selection([
        ('bachelor', 'Cử nhân / Kỹ sư'),
        ('master', 'Thạc sĩ'),
        ('doctor', 'Tiến sĩ'),
        ('doctor_science', 'Tiến sĩ khoa học'),
    ], string='Học vị cao nhất', default='master', tracking=True)
    degree_recognition_year = fields.Integer(string='Năm công nhận học vị', placeholder='VD: 2018')

    position_title = fields.Selection([
        ('lecturer', 'Giảng viên'),
        ('senior_lecturer', 'Giảng viên chính'),
        ('principal_lecturer', 'Giảng viên cao cấp'),
        ('head_dept', 'Trưởng bộ môn'),
        ('vice_head_dept', 'Phó Trưởng bộ môn'),
        ('vice_dean', 'Phó Trưởng khoa'),
        ('dean', 'Trưởng khoa'),
        ('admin_staff', 'Giáo vụ khoa'),
    ], string='Chức vụ / Vị trí công tác', default='lecturer', tracking=True)

    title_norm_id = fields.Many2one('faculty.title.norm', string='Mức chuẩn chức danh áp dụng', tracking=True)

    # 16 Bậc lương & Niên hạn nâng bậc
    rank_id = fields.Many2one('faculty.rank.config', string='Bậc lương hiện tại', tracking=True)
    rank_date = fields.Date(string='Ngày bổ nhiệm bậc lương', default=fields.Date.context_today, tracking=True)
    next_rank_date = fields.Date(string='Ngày dự kiến nâng bậc', compute='_compute_next_rank_date', store=True, tracking=True,
                                 help='Tự động cộng niên hạn (mặc định 36 tháng) từ ngày bổ nhiệm bậc lương.')
    days_to_promotion = fields.Integer(string='Số ngày đến hạn nâng bậc', compute='_compute_days_to_promotion',
                                       search='_search_days_to_promotion', store=False)
    is_promotion_soon = fields.Boolean(string='Sắp đến hạn nâng bậc (<= 60 ngày)', compute='_compute_days_to_promotion',
                                       search='_search_is_promotion_soon', store=False)

    # Hiển thị cấp bậc/chức vụ chuẩn: "Bậc 12/16 - Trưởng khoa"
    rank_position_display = fields.Char(string='Cấp bậc & Chức vụ', compute='_compute_rank_position_display', store=True)

    # Chữ ký số
    signature_image = fields.Binary(string='Chữ ký số / Ảnh chữ ký cá nhân', attachment=True)

    # 5 Cờ phân quyền trực quan (Ủy quyền tác vụ)
    can_edit_subjects = fields.Boolean(string='Quyền sửa CTĐT & Môn học', default=False, tracking=True)
    can_edit_classes = fields.Boolean(string='Quyền mở lớp & Chia học phần', default=False, tracking=True)
    can_edit_exams = fields.Boolean(string='Quyền nhập lịch & Khảo thí', default=False, tracking=True)
    can_edit_faculty_tasks = fields.Boolean(string='Quyền phân công nhiệm vụ Khoa', default=False, tracking=True)
    can_manage_hr = fields.Boolean(string='Quyền quản lý nhân sự & Bậc lương', default=False, tracking=True)

    # Chế độ miễn giảm & Đi học >= 4 tuần
    reduction_ids = fields.Many2many('faculty.norm.reduction', string='Chế độ miễn giảm kiêm nhiệm')
    study_weeks = fields.Integer(string='Số tuần cử đi học/bồi dưỡng trong năm (>= 4 tuần)', default=0, tracking=True,
                                 help='Nếu đi học từ 4 tuần trở lên, tự động tính giảm định mức theo công thức Số tuần / 44.')

    # Năm học đang theo dõi trên Dashboard hồ sơ cá nhân
    active_academic_year_id = fields.Many2one(
        'faculty.academic.year',
        string='Năm học theo dõi',
        default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False
    )

    # =========================================================================
    # 3 Ô TIÊU CHÍ TINH GỌN (1. GIẢNG DẠY - 2. NCKH - 3. HOẠT ĐỘNG KHÁC)
    # =========================================================================
    # Tiêu chí 1: Giảng dạy
    teaching_norm_base = fields.Float(string='Định mức gốc Giảng dạy (tiết)', compute='_compute_norms', store=True)
    teaching_norm_reduced = fields.Float(string='Định mức sau giảm (tiết)', compute='_compute_norms', store=True)
    teaching_norm_lecture_50 = fields.Float(string='Giờ giảng định mức (50%)', compute='_compute_norms', store=True,
                                            help='Giờ giảng định mức = 50% định mức giảng dạy sau giảm.')
    teaching_actual_lecture = fields.Float(string='Giờ giảng thực tế (đứng lớp)', compute='_compute_criteria_stats', store=False)
    teaching_actual_total = fields.Float(string='Tổng số giờ thực tế Giảng dạy', compute='_compute_criteria_stats', store=False,
                                         help='Tổng = Giờ giảng đứng lớp + Coi thi + Chấm thi + Chấm kiểm tra + Ra đề mới + Hướng dẫn...')
    teaching_balance = fields.Float(string='Thừa / Thiếu Giảng dạy', compute='_compute_criteria_stats', store=False)

    # Tiêu chí 2: Nghiên cứu khoa học
    research_norm_base = fields.Float(string='Định mức gốc NCKH (giờ)', compute='_compute_norms', store=True)
    research_norm_reduced = fields.Float(string='Định mức sau giảm NCKH (giờ)', compute='_compute_norms', store=True)
    research_actual_total = fields.Float(string='Tổng số giờ thực tế NCKH', compute='_compute_criteria_stats', store=False)
    research_balance = fields.Float(string='Thừa / Thiếu NCKH', compute='_compute_criteria_stats', store=False)

    # Tiêu chí 3: Hoạt động khác
    other_norm_base = fields.Float(string='Định mức gốc HĐ khác (giờ)', compute='_compute_norms', store=True)
    other_norm_reduced = fields.Float(string='Định mức sau giảm HĐ khác (giờ)', compute='_compute_norms', store=True)
    other_actual_total = fields.Float(string='Tổng số giờ thực tế HĐ khác', compute='_compute_criteria_stats', store=False)
    other_balance = fields.Float(string='Thừa / Thiếu HĐ khác', compute='_compute_criteria_stats', store=False)

    # Sổ cái giờ chuẩn chi tiết cho từng ô tiêu chí
    teaching_ledger_ids = fields.One2many('faculty.hour.ledger', 'lecturer_id', domain=[('category', '=', 'teaching')], string='Chi tiết Giờ chuẩn Giảng dạy')
    research_ledger_ids = fields.One2many('faculty.hour.ledger', 'lecturer_id', domain=[('category', '=', 'research')], string='Chi tiết Giờ chuẩn NCKH')
    other_ledger_ids = fields.One2many('faculty.hour.ledger', 'lecturer_id', domain=[('category', '=', 'other')], string='Chi tiết Giờ chuẩn Hoạt động khác')

    # =========================================================================
    # TAB QUY HOẠCH & PHÁT TRIỂN CÁN BỘ
    # =========================================================================
    cadre_planning_title = fields.Char(string='Chức danh quy hoạch bổ nhiệm', placeholder='VD: Quy hoạch Phó Trưởng khoa / Trưởng bộ môn')
    cadre_planning_period = fields.Char(string='Giai đoạn quy hoạch', placeholder='VD: 2026 - 2031')
    training_development_plan = fields.Text(string='Kế hoạch đào tạo & bồi dưỡng năng lực')

    # =========================================================================
    # TAB LÝ LỊCH KHOA HỌC (ĐỦ 15 MỤC CHUẨN)
    # =========================================================================
    # Mục 1: Thông tin cá nhân (Đã có sẵn qua partner_id: name, phone, email, contact_address)
    gender = fields.Selection([('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')], string='Giới tính', default='male')
    birth_date = fields.Date(string='Ngày sinh')
    place_of_birth = fields.Char(string='Nơi sinh (Tỉnh/Thành phố)')
    hometown = fields.Char(string='Quê quán')
    id_card_number = fields.Char(string='Số CCCD / Hộ chiếu')
    id_card_issue_date = fields.Date(string='Ngày cấp CCCD')
    id_card_place = fields.Char(string='Nơi cấp CCCD')
    office_address = fields.Char(string='Địa chỉ cơ quan công tác', default='Khoa Đào tạo Đại học')

    # Mục 3: Trình độ Ngoại ngữ & Tin học
    foreign_languages = fields.Char(string='Ngoại ngữ (Trình độ/Chứng chỉ)', placeholder='VD: Tiếng Anh IELTS 7.0, Tiếng Pháp B1')
    it_skills = fields.Char(string='Tin học (Trình độ/Chứng chỉ)', placeholder='VD: Ứng dụng CNTT cơ bản, Python, SQL')

    # Mục 4, 5, 9, 10, 13: Bảng dòng quá trình (Resume lines)
    resume_line_ids = fields.One2many('faculty.lecturer.resume.line', 'lecturer_id', string='Dòng quá trình LLKH')

    # Mục 6: Kinh nghiệm quản lý & đào tạo
    management_experience = fields.Text(string='Kinh nghiệm quản lý, giảng dạy & đào tạo')

    # Mục 7: Công trình khoa học đã công bố (Có cờ is_top_selected tối đa 5 bài)
    publication_ids = fields.One2many('faculty.lecturer.publication', 'lecturer_id', string='Công trình khoa học đã công bố')

    # Mục 8: Sách, giáo trình đã xuất bản
    published_books = fields.Text(string='Sách, giáo trình, tài liệu học tập đã xuất bản')

    # Mục 11: Công trình/giải pháp áp dụng thực tiễn
    practical_applications = fields.Text(string='Công trình, giải pháp áp dụng vào thực tiễn')

    # Mục 12: Hướng dẫn sau đại học (NCS & Thạc sĩ)
    postgraduate_supervision = fields.Text(string='Hướng dẫn Nghiên cứu sinh & Học viên cao học')

    # Mục 14: Thành tựu hoạt động KH&CN nổi bật khác
    other_achievements = fields.Text(string='Thành tựu hoạt động KH&CN nổi bật khác')

    # Mục 15: Lời cam đoan
    commitment_statement = fields.Text(
        string='Lời cam đoan',
        default='Tôi xin cam đoan những thông tin được kê khai trong Bản lý lịch khoa học này là hoàn toàn chính xác và trung thực. Nếu có điều gì sai sót, tôi xin chịu hoàn toàn trách nhiệm trước Pháp luật và cơ quan quản lý.'
    )

    _sql_constraints = [
        ('lecturer_code_unique', 'unique(lecturer_code)', 'Mã giảng viên đã tồn tại trong hệ thống! Vui lòng kiểm tra lại.'),
    ]

    # =========================================================================
    # COMPUTE METHODS
    # =========================================================================
    @api.depends('rank_id', 'position_title')
    def _compute_rank_position_display(self):
        position_map = dict(self._fields['position_title'].selection)
        for rec in self:
            rank_str = f"Bậc {rec.rank_id.sequence}/16" if rec.rank_id else "Chưa xếp bậc"
            pos_str = position_map.get(rec.position_title, '')
            rec.rank_position_display = f"{rank_str} - {pos_str}" if pos_str else rank_str

    @api.depends('rank_date', 'rank_id.promotion_interval_months')
    def _compute_next_rank_date(self):
        for rec in self:
            if rec.rank_date:
                interval_months = rec.rank_id.promotion_interval_months if rec.rank_id else 36
                rec.next_rank_date = rec.rank_date + relativedelta(months=interval_months)
            else:
                rec.next_rank_date = False

    @api.depends('next_rank_date')
    def _compute_days_to_promotion(self):
        today = fields.Date.today()
        for rec in self:
            if rec.next_rank_date:
                delta = (rec.next_rank_date - today).days
                rec.days_to_promotion = delta
                rec.is_promotion_soon = (0 <= delta <= 60)
            else:
                rec.days_to_promotion = 9999
                rec.is_promotion_soon = False

    def _search_days_to_promotion(self, operator, value):
        today = fields.Date.today()
        if operator in ('>', '>=', '<', '<=', '=', '!='):
            target_date = today + relativedelta(days=int(value))
            return [('next_rank_date', operator, target_date)]
        return []

    def _search_is_promotion_soon(self, operator, value):
        today = fields.Date.today()
        date_60 = today + relativedelta(days=60)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('next_rank_date', '>=', today), ('next_rank_date', '<=', date_60)]
        else:
            return ['|', ('next_rank_date', '<', today), ('next_rank_date', '>', date_60)]

    @api.depends('title_norm_id', 'reduction_ids', 'study_weeks')
    def _compute_norms(self):
        """
        Tính định mức gốc và định mức sau giảm của 3 tiêu chí
        """
        for rec in self:
            t_base = rec.title_norm_id.teaching_norm if rec.title_norm_id else 270.0
            r_base = rec.title_norm_id.research_norm if rec.title_norm_id else 600.0
            o_base = rec.title_norm_id.other_norm if rec.title_norm_id else 100.0

            # Tính tổng phần trăm giảm từ các chế độ kiêm nhiệm
            pct_t = sum(red.percent_teaching for red in rec.reduction_ids)
            pct_r = sum(red.percent_research for red in rec.reduction_ids)
            pct_o = sum(red.percent_other for red in rec.reduction_ids)

            # Quy tắc: Đi học >= 4 tuần giảm theo công thức Số tuần / 44
            if rec.study_weeks >= 4:
                study_pct = min((rec.study_weeks / 44.0) * 100.0, 100.0)
                pct_t += study_pct
                pct_r += study_pct
                pct_o += study_pct

            pct_t = min(pct_t, 100.0)
            pct_r = min(pct_r, 100.0)
            pct_o = min(pct_o, 100.0)

            t_reduced = round(t_base * (1.0 - pct_t / 100.0), 2)
            r_reduced = round(r_base * (1.0 - pct_r / 100.0), 2)
            o_reduced = round(o_base * (1.0 - pct_o / 100.0), 2)

            rec.teaching_norm_base = t_base
            rec.teaching_norm_reduced = t_reduced
            rec.teaching_norm_lecture_50 = round(t_reduced * 0.5, 2)

            rec.research_norm_base = r_base
            rec.research_norm_reduced = r_reduced

            rec.other_norm_base = o_base
            rec.other_norm_reduced = o_reduced

    def _compute_criteria_stats(self):
        """
        Tổng hợp giờ chuẩn thực tế từ Sổ cái Giờ chuẩn trung tâm qua _read_group.
        Tối ưu hóa tuyệt đối, chống N+1 query.
        """
        for rec in self:
            domain = [('lecturer_id', '=', rec.id)]
            if rec.active_academic_year_id:
                domain.append(('academic_year_id', '=', rec.active_academic_year_id.id))

            # Query _read_group gom nhóm theo category và activity_type
            grouped_data = self.env['faculty.hour.ledger']._read_group(
                domain=domain,
                groupby=['category', 'activity_type'],
                aggregates=['standard_hours:sum']
            )

            actual_teaching_total = 0.0
            actual_teaching_lecture = 0.0
            actual_research_total = 0.0
            actual_other_total = 0.0

            for category, activity_type, hours_sum in grouped_data:
                hours = hours_sum or 0.0
                if category == 'teaching':
                    actual_teaching_total += hours
                    if activity_type == 'lecture':
                        actual_teaching_lecture += hours
                elif category == 'research':
                    actual_research_total += hours
                elif category == 'other':
                    actual_other_total += hours

            rec.teaching_actual_lecture = actual_teaching_lecture
            rec.teaching_actual_total = actual_teaching_total
            rec.teaching_balance = actual_teaching_total - rec.teaching_norm_reduced

            rec.research_actual_total = actual_research_total
            rec.research_balance = actual_research_total - rec.research_norm_reduced

            rec.other_actual_total = actual_other_total
            rec.other_balance = actual_other_total - rec.other_norm_reduced

    # =========================================================================
    # ACTIONS & SYNC
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        records = super(FacultyLecturer, self).create(vals_list)
        for rec in records:
            rec._sync_security_groups()
        return records

    def write(self, vals):
        res = super(FacultyLecturer, self).write(vals)
        perm_keys = ['can_edit_subjects', 'can_edit_classes', 'can_edit_exams', 'can_edit_faculty_tasks', 'can_manage_hr', 'user_id']
        if any(k in vals for k in perm_keys):
            for rec in self:
                rec._sync_security_groups()
        return res

    def _sync_security_groups(self):
        """
        Tự động đồng bộ các cờ phân quyền trực quan trên hồ sơ sang res.groups
        """
        self.ensure_one()
        if not self.user_id:
            return

        training_group = self.env.ref('faculty_work_mgmt.group_faculty_training', raise_if_not_found=False)
        exam_group = self.env.ref('faculty_work_mgmt.group_faculty_exam', raise_if_not_found=False)
        dean_group = self.env.ref('faculty_work_mgmt.group_faculty_dean', raise_if_not_found=False)

        user = self.user_id

        # Đồng bộ quyền Đào tạo
        if training_group:
            if self.can_edit_subjects or self.can_edit_classes:
                user.sudo().write({'groups_id': [(4, training_group.id)]})
            else:
                user.sudo().write({'groups_id': [(3, training_group.id)]})

        # Đồng bộ quyền Khảo thí
        if exam_group:
            if self.can_edit_exams:
                user.sudo().write({'groups_id': [(4, exam_group.id)]})
            else:
                user.sudo().write({'groups_id': [(3, exam_group.id)]})

        # Đồng bộ quyền Quản lý/Nhân sự/Nhiệm vụ
        if dean_group:
            if self.can_edit_faculty_tasks or self.can_manage_hr:
                user.sudo().write({'groups_id': [(4, dean_group.id)]})

    def action_check_promotion_reminders(self):
        """
        Hàm định kỳ quét các giảng viên sắp đến hạn nâng bậc (<= 60 ngày)
        để tạo hoạt động nhắc việc (mail.activity) cho cán bộ nhân sự.
        """
        candidates = self.search([('is_promotion_soon', '=', True)])
        activity_type_todo = self.env.ref('mail.mail_activity_data_todo')

        for rec in candidates:
            # Kiểm tra xem đã có activity nhắc chưa
            existing = self.env['mail.activity'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id),
                ('activity_type_id', '=', activity_type_todo.id),
                ('summary', 'like', 'Nhắc nâng bậc lương'),
            ], limit=1)
            if not existing and rec.next_rank_date:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=rec.next_rank_date,
                    summary=f'Nhắc nâng bậc lương cho {rec.name} (còn {rec.days_to_promotion} ngày)',
                    note=f'Giảng viên {rec.name} ({rec.lecturer_code}) sắp đến niên hạn nâng từ {rec.rank_id.name if rec.rank_id else "bậc hiện tại"} vào ngày {rec.next_rank_date.strftime("%d/%m/%Y")}. Vui lòng làm thủ tục đề nghị nâng bậc lương.'
                )
        return True

    def action_print_llkh(self):
        """
        Nút bấm In/Xuất Lý lịch Khoa học 15 mục
        """
        self.ensure_one()
        return self.env.ref('faculty_work_mgmt.action_report_faculty_lecturer_llkh').report_action(self)


class FacultyLecturerResumeLine(models.Model):
    _name = 'faculty.lecturer.resume.line'
    _description = 'Dòng Quá trình Lý lịch Khoa học'
    _order = 'type, period desc, id'

    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên', required=True, ondelete='cascade', index=True)
    type = fields.Selection([
        ('training', '1. Quá trình đào tạo'),
        ('work', '2. Quá trình công tác chuyên môn'),
        ('project', '3. Đề tài / Nhiệm vụ KH&CN'),
        ('ip', '4. Văn bằng SHTT & Ứng dụng thực tiễn'),
        ('award', '5. Giải thưởng & Khen thưởng khoa học'),
    ], string='Phân loại mục', required=True, index=True)

    period = fields.Char(string='Thời gian / Niên khóa', placeholder='VD: 2018 - 2022')
    institution = fields.Char(string='Cơ sở đào tạo / Đơn vị công tác / Cấp quản lý', placeholder='VD: Đại học Quốc gia, Bộ GD&ĐT...')
    name = fields.Char(string='Nội dung / Chuyên ngành / Tên đề tài / Tên giải thưởng', required=True)
    role = fields.Char(string='Vai trò / Chức danh / Cương vị', placeholder='VD: Chủ nhiệm, Thư ký, Học viên...')
    result = fields.Char(string='Kết quả / Xếp loại / Số quyết định', placeholder='VD: Xuất sắc, Đạt loại Giỏi, Bằng số 12345...')


class FacultyLecturerPublication(models.Model):
    _name = 'faculty.lecturer.publication'
    _description = 'Công trình Khoa học Công bố'
    _order = 'year desc, sequence, id'

    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='STT', default=10)
    name = fields.Char(string='Tên công trình / Bài báo khoa học', required=True)
    authors = fields.Char(string='Tác giả / Nhóm tác giả', placeholder='VD: Nguyễn Văn A, Trần Thị B')
    journal = fields.Char(string='Tên tạp chí / Kỷ yếu hội thảo', required=True)
    year = fields.Integer(string='Năm công bố', default=lambda self: date.today().year, required=True)
    pub_type = fields.Selection([
        ('wos_scopus', 'Tạp chí Quốc tế uy tín (WoS / Scopus)'),
        ('national_journal', 'Tạp chí Khoa học trong nước'),
        ('conference', 'Kỷ yếu Hội thảo Khoa học'),
    ], string='Phân loại xuất bản', default='national_journal', required=True)
    impact_factor_rank = fields.Char(string='Chỉ số IF / Điểm HĐGSNN', placeholder='VD: Q1, Q2, 0.75 điểm')

    # Cờ giới hạn tối đa 5 công trình tiêu biểu
    is_top_selected = fields.Boolean(
        string='Chọn in LLKH (Tối đa 5 bài tiêu biểu)',
        default=False,
        help='Tích chọn tối đa 5 công trình khoa học tiêu biểu nhất để xuất in Lý lịch khoa học.'
    )

    @api.constrains('is_top_selected', 'lecturer_id')
    def _check_top_selected_limit(self):
        for rec in self:
            if rec.is_top_selected and rec.lecturer_id:
                count = self.search_count([
                    ('lecturer_id', '=', rec.lecturer_id.id),
                    ('is_top_selected', '=', True),
                ])
                if count > 5:
                    raise ValidationError(_('Mỗi giảng viên chỉ được chọn tối đa 5 công trình tiêu biểu để xuất Lý lịch Khoa học!'))
