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

    # 4 Trường độc lập: Chức vụ, Chức danh, Học vị, Học hàm & Giảng viên thỉnh giảng
    admin_position = fields.Selection([
        ('can_bo', 'Cán bộ'),
        ('pho_khoa', 'Phó Trưởng khoa'),
        ('truong_khoa', 'Trưởng khoa'),
    ], string='Chức vụ', tracking=True,
       help='Chức vụ hành chính: Cán bộ, Phó Trưởng khoa, Trưởng khoa hoặc để trống.')

    academic_rank = fields.Selection([
        ('tro_giang', 'Trợ giảng'),
        ('giang_vien', 'Giảng viên'),
        ('giang_vien_chinh', 'Giảng viên chính'),
        ('giang_vien_cao_cap', 'Giảng viên cao cấp'),
    ], string='Chức danh', tracking=True,
       help='Chức danh giảng dạy: Trợ giảng, Giảng viên, Giảng viên chính, Giảng viên cao cấp.')

    degree = fields.Selection([
        ('bachelor', 'Cử nhân'),
        ('master', 'Thạc sĩ'),
        ('doctor', 'Tiến sĩ'),
    ], string='Học vị', default='master', tracking=True)
    academic_degree = fields.Selection(
        related='degree',
        string='Học vị cao nhất',
        store=True,
        readonly=False
    )
    degree_recognition_year = fields.Integer(string='Năm công nhận học vị', placeholder='VD: 2018')

    academic_title = fields.Selection([
        ('none', 'Không'),
        ('assoc_prof', 'Phó Giáo sư'),
        ('prof', 'Giáo sư'),
    ], string='Học hàm', default='none', tracking=True)
    title_appointment_year = fields.Integer(string='Năm bổ nhiệm học hàm', placeholder='VD: 2020')

    is_visiting = fields.Boolean(
        string='Giảng viên thỉnh giảng',
        default=False,
        tracking=True,
        help='Thực hiện chế độ và tính định mức theo chức danh như giảng viên cơ hữu.'
    )

    position_title = fields.Char(string='Chức vụ cũ', compute='_compute_legacy_position_title', store=False)

    title_norm_id = fields.Many2one(
        'faculty.title.norm',
        string='Mức chuẩn chức danh áp dụng',
        compute='_compute_title_norm_id',
        store=True,
        readonly=False,
        tracking=True
    )

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
    reduction_ids = fields.One2many('faculty.norm.reduction', 'lecturer_id', string='Bảng miễn giảm định mức thủ công')
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
    # Tiêu chí 1: Giảng dạy (A: Định mức thực tế phải nộp, B = 0.5 * A)
    teaching_norm_base = fields.Float(string='Định mức gốc Giảng dạy (tiết)', compute='_compute_norms', store=True)
    teaching_reduction_pct = fields.Float(string='Tổng % giảm Giảng dạy', compute='_compute_norms', store=True)
    teaching_hours_reduced = fields.Float(string='Tổng giờ GD được miễn giảm (tiết)', compute='_compute_norms', store=True)
    teaching_norm_reduced = fields.Float(string='Định mức thực tế phải nộp A (tiết)', compute='_compute_norms', store=True,
                                         help='A: Định mức Giảng dạy sau miễn giảm = Định mức gốc - Tổng giờ GD được miễn giảm.')
    teaching_norm_lecture_50 = fields.Float(string='Định mức lên lớp tối thiểu (B = 0.5*A)', compute='_compute_norms', store=True,
                                            help='B = 0.5 * A: Định mức lên lớp tối thiểu theo quy định.')
    net_teaching_quota = fields.Float(string='Định mức GD sau miễn giảm (A)', related='teaching_norm_reduced', store=True)
    min_classroom_quota = fields.Float(string='Định mức lên lớp tối thiểu (B)', related='teaching_norm_lecture_50', store=True)

    teaching_actual_lecture = fields.Float(string='Giờ giảng thực tế (đứng lớp)', compute='_compute_criteria_stats', store=False)
    actual_classroom_hours = fields.Float(string='Giờ lên lớp thực tế (b)', related='teaching_actual_lecture', store=False)
    other_teaching_hours = fields.Float(string='Giờ quy đổi giảng dạy khác', compute='_compute_criteria_stats', store=False)
    teaching_actual_total = fields.Float(string='Tổng số giờ thực tế Giảng dạy', compute='_compute_criteria_stats', store=False,
                                         help='Tổng = Giờ giảng đứng lớp + Coi thi + Chấm thi + Chấm kiểm tra + Ra đề mới + Hướng dẫn...')
    total_teaching_hours = fields.Float(string='Tổng giờ giảng đạt được (a = b + khác)', related='teaching_actual_total', store=False)
    teaching_balance = fields.Float(string='Thừa / Thiếu Giảng dạy', compute='_compute_criteria_stats', store=False)

    # Tiêu chí 2: Nghiên cứu khoa học (C: Định mức thực tế phải nộp)
    research_norm_base = fields.Float(string='Định mức gốc NCKH (giờ)', compute='_compute_norms', store=True)
    research_reduction_pct = fields.Float(string='Tổng % giảm NCKH', compute='_compute_norms', store=True)
    research_hours_reduced = fields.Float(string='Tổng giờ NCKH được miễn giảm (giờ)', compute='_compute_norms', store=True)
    research_norm_reduced = fields.Float(string='Định mức thực tế phải nộp C (giờ)', compute='_compute_norms', store=True,
                                         help='C: Định mức NCKH sau miễn giảm = Định mức gốc - Tổng giờ NCKH được miễn giảm.')
    net_research_quota = fields.Float(string='Định mức NCKH sau miễn giảm (C)', related='research_norm_reduced', store=True)

    research_actual_total = fields.Float(string='Tổng số giờ thực tế NCKH', compute='_compute_criteria_stats', store=False)
    research_balance = fields.Float(string='Thừa / Thiếu NCKH', compute='_compute_criteria_stats', store=False)

    # Tiêu chí 3: Hoạt động khác (Không miễn giảm)
    other_norm_base = fields.Float(string='Định mức gốc HĐ khác (giờ)', compute='_compute_norms', store=True)
    other_norm_reduced = fields.Float(string='Định mức thực tế HĐ khác (giờ)', compute='_compute_norms', store=True,
                                      help='Theo quy chế tại rules.md: Hoạt động khác KHÔNG miễn giảm.')
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
    @api.depends('rank_id', 'admin_position', 'academic_rank')
    def _compute_rank_position_display(self):
        admin_map = dict(self._fields['admin_position'].selection)
        rank_map = dict(self._fields['academic_rank'].selection)
        for rec in self:
            rank_str = f"Bậc {rec.rank_id.sequence}/16" if rec.rank_id else ""
            pos_parts = []
            if rec.admin_position and rec.admin_position in admin_map:
                pos_parts.append(admin_map[rec.admin_position])
            if rec.academic_rank and rec.academic_rank in rank_map:
                pos_parts.append(rank_map[rec.academic_rank])
            pos_str = " - ".join(pos_parts)
            if rank_str and pos_str:
                rec.rank_position_display = f"{rank_str} - {pos_str}"
            elif rank_str:
                rec.rank_position_display = rank_str
            elif pos_str:
                rec.rank_position_display = pos_str
            else:
                rec.rank_position_display = "Chưa xếp bậc"

    def _compute_legacy_position_title(self):
        for rec in self:
            rec.position_title = rec.admin_position or rec.academic_rank or ''

    @api.depends('academic_rank')
    def _compute_title_norm_id(self):
        for rec in self:
            if not rec.academic_rank:
                rec.title_norm_id = False
                continue
            norms = self.env['faculty.title.norm'].search([
                '|', ('academic_rank', '=', rec.academic_rank),
                     ('code', '=', rec.academic_rank)
            ])
            if not norms:
                rank_label = dict(self._fields['academic_rank'].selection).get(rec.academic_rank, '')
                if rank_label:
                    norms = self.env['faculty.title.norm'].search([('name', 'ilike', rank_label)])
            if norms:
                # Nếu có nhiều mức thì lấy mức cao nhất
                rec.title_norm_id = norms.sorted(
                    key=lambda n: (n.teaching_norm, n.research_norm, n.other_norm),
                    reverse=True
                )[0]
            else:
                rec.title_norm_id = False

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

    @api.depends(
        'academic_rank', 'title_norm_id', 'title_norm_id.teaching_norm',
        'title_norm_id.research_norm', 'title_norm_id.other_norm',
        'reduction_ids', 'reduction_ids.percentage', 'reduction_ids.scope',
        'reduction_ids.academic_year_id', 'active_academic_year_id', 'study_weeks'
    )
    def _compute_norms(self):
        """
        Tính định mức gốc và định mức thực tế phải nộp sau miễn giảm:
        - Định mức thực tế phải nộp A (Giảng dạy) = Định mức gốc - Tổng số giờ GD được miễn giảm
        - B = 0.5 * A: Định mức lên lớp tối thiểu
        - Định mức thực tế phải nộp C (NCKH) = Định mức gốc - Tổng số giờ NCKH được miễn giảm
        - Hoạt động khác: Giữ nguyên định mức gốc (KHÔNG miễn giảm theo rules.md)
        """
        for rec in self:
            if rec.title_norm_id:
                t_base = rec.title_norm_id.teaching_norm or 0.0
                r_base = rec.title_norm_id.research_norm or 0.0
                o_base = rec.title_norm_id.other_norm or 0.0
            elif rec.academic_rank:
                norms = self.env['faculty.title.norm'].search([
                    '|', ('academic_rank', '=', rec.academic_rank),
                         ('code', '=', rec.academic_rank)
                ])
                if not norms:
                    rank_label = dict(self._fields['academic_rank'].selection).get(rec.academic_rank, '')
                    if rank_label:
                        norms = self.env['faculty.title.norm'].search([('name', 'ilike', rank_label)])
                if norms:
                    t_base = max(norms.mapped('teaching_norm'))
                    r_base = max(norms.mapped('research_norm'))
                    o_base = max(norms.mapped('other_norm'))
                else:
                    t_base = 0.0
                    r_base = 0.0
                    o_base = 0.0
            else:
                t_base = 0.0
                r_base = 0.0
                o_base = 0.0

            # Lọc danh sách miễn giảm theo năm học đang theo dõi (active_academic_year_id)
            current_year = rec.active_academic_year_id or self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1)
            if current_year:
                valid_reductions = rec.reduction_ids.filtered(lambda r: not r.academic_year_id or r.academic_year_id == current_year)
            else:
                valid_reductions = rec.reduction_ids

            pct_t = sum(r.percentage for r in valid_reductions if r.scope in ('teaching', 'both'))
            pct_r = sum(r.percentage for r in valid_reductions if r.scope in ('research', 'both'))

            # Đi học >= 4 tuần tự động tính giảm theo công thức: Số tuần / 44
            if rec.study_weeks >= 4:
                study_pct = (rec.study_weeks / 44.0) * 100.0
                pct_t += study_pct
                pct_r += study_pct

            # Trần tối đa 100%
            pct_t = min(max(pct_t, 0.0), 100.0)
            pct_r = min(max(pct_r, 0.0), 100.0)

            # Tổng số giờ được miễn giảm
            teaching_hours_reduced = round(t_base * (pct_t / 100.0), 2)
            research_hours_reduced = round(r_base * (pct_r / 100.0), 2)

            # Công thức: Định mức thực tế phải nộp (A và C) = Định mức gốc - Tổng số giờ được miễn giảm
            t_net = max(0.0, round(t_base - teaching_hours_reduced, 2))
            r_net = max(0.0, round(r_base - research_hours_reduced, 2))
            # Hoạt động khác: KHÔNG miễn giảm theo quy chế rules.md
            o_net = o_base

            rec.teaching_norm_base = t_base
            rec.teaching_reduction_pct = pct_t
            rec.teaching_hours_reduced = teaching_hours_reduced
            rec.teaching_norm_reduced = t_net
            rec.teaching_norm_lecture_50 = round(t_net * 0.5, 2)

            rec.research_norm_base = r_base
            rec.research_reduction_pct = pct_r
            rec.research_hours_reduced = research_hours_reduced
            rec.research_norm_reduced = r_net

            rec.other_norm_base = o_base
            rec.other_norm_reduced = o_net

    def _compute_criteria_stats(self):
        """
        Tổng hợp giờ chuẩn thực tế từ Sổ cái Giờ chuẩn trung tâm qua _read_group.
        Một lần truy vấn duy nhất cho toàn bộ recordset, chống N+1 query.
        Chỉ tính các dòng có date <= today và state = 'posted' (buổi/nhiệm vụ đã diễn ra và đã ghi sổ).
        Groupby bao gồm ['lecturer_id', 'academic_year_id', ...] để không bị gộp nhầm số giờ giữa các năm học khác nhau.
        """
        if not self:
            return

        today = fields.Date.today()

        # Xây dựng domain chung cho toàn bộ recordset (1 SQL query duy nhất)
        lecturer_ids = self.ids
        year_ids = list(set(
            rec.active_academic_year_id.id
            for rec in self
            if rec.active_academic_year_id
        ))

        domain = [
            ('lecturer_id', 'in', lecturer_ids),
            ('date', '<=', today),
            ('state', '=', 'posted'),
        ]
        if len(year_ids) == 1:
            domain.append(('academic_year_id', '=', year_ids[0]))
        elif year_ids:
            domain.append(('academic_year_id', 'in', year_ids))

        grouped_data = self.env['faculty.hour.ledger']._read_group(
            domain=domain,
            groupby=['lecturer_id', 'academic_year_id', 'category', 'activity_type', 'is_direct_teaching'],
            aggregates=['standard_hours:sum'],
        )

        # Index kết quả: {(lecturer_id, academic_year_id): {(category, activity_type, is_direct): sum}}
        stats = {}
        for lecturer, academic_year, category, activity_type, is_direct, hours_sum in grouped_data:
            lid = lecturer.id if lecturer else False
            yid = academic_year.id if academic_year else False
            if not lid:
                continue
            stats.setdefault((lid, yid), {})
            stats[(lid, yid)][(category, activity_type, is_direct)] = hours_sum or 0.0

        for rec in self:
            yid = rec.active_academic_year_id.id if rec.active_academic_year_id else False
            rec_stats = stats.get((rec.id, yid), {})
            if not rec_stats and not yid:
                cur_y = self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1)
                if cur_y:
                    rec_stats = stats.get((rec.id, cur_y.id), {})

            actual_teaching_lecture = 0.0
            actual_other_teaching = 0.0
            actual_research_total = 0.0
            actual_other_total = 0.0

            for (cat, atype, is_dir), hours in rec_stats.items():
                if cat == 'teaching':
                    if is_dir or atype == 'lecture':
                        actual_teaching_lecture += hours
                    else:
                        actual_other_teaching += hours
                elif cat == 'research':
                    actual_research_total += hours
                elif cat == 'other':
                    actual_other_total += hours

            actual_teaching_total = round(actual_teaching_lecture + actual_other_teaching, 2)
            rec.teaching_actual_lecture = round(actual_teaching_lecture, 2)
            rec.other_teaching_hours = round(actual_other_teaching, 2)
            rec.teaching_actual_total = actual_teaching_total
            rec.teaching_balance = round(actual_teaching_total - rec.teaching_norm_reduced, 2)

            rec.research_actual_total = round(actual_research_total, 2)
            rec.research_balance = round(actual_research_total - rec.research_norm_reduced, 2)

            rec.other_actual_total = round(actual_other_total, 2)
            rec.other_balance = round(actual_other_total - rec.other_norm_reduced, 2)

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
        norm_keys = ['academic_rank', 'title_norm_id', 'study_weeks', 'active_academic_year_id']
        if any(k in vals for k in norm_keys):
            Balance = self.env['faculty.workload.balance']
            for rec in self:
                Balance.recompute_for_lecturer(rec.id, rec.active_academic_year_id.id if rec.active_academic_year_id else None)
        return res

    def _sync_security_groups(self):
        """
        Tự động đồng bộ các cờ phân quyền trực quan trên hồ sơ sang res.groups.
        Gom thành 1 lần write duy nhất để tránh nhiều SQL UPDATE liên tiếp.
        """
        self.ensure_one()
        if not self.user_id:
            return

        training_group = self.env.ref('faculty_work_mgmt.group_faculty_training', raise_if_not_found=False)
        exam_group = self.env.ref('faculty_work_mgmt.group_faculty_exam', raise_if_not_found=False)
        dean_group = self.env.ref('faculty_work_mgmt.group_faculty_dean', raise_if_not_found=False)

        cmds = []

        # Đồng bộ quyền Đào tạo
        if training_group:
            if self.can_edit_subjects or self.can_edit_classes:
                cmds.append((4, training_group.id))
            else:
                cmds.append((3, training_group.id))

        # Đồng bộ quyền Khảo thí
        if exam_group:
            if self.can_edit_exams:
                cmds.append((4, exam_group.id))
            else:
                cmds.append((3, exam_group.id))

        # Đồng bộ quyền Quản lý/Nhân sự/Nhiệm vụ Khoa
        if dean_group:
            if self.can_edit_faculty_tasks or self.can_manage_hr:
                cmds.append((4, dean_group.id))
            else:
                cmds.append((3, dean_group.id))

        # Luôn đảm bảo tài khoản có nhóm quyền cơ bản của Giảng viên (group_faculty_user)
        user_group = self.env.ref('faculty_work_mgmt.group_faculty_user', raise_if_not_found=False)
        if user_group:
            cmds.append((4, user_group.id))

        if cmds:
            group_field = 'group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'
            self.user_id.sudo().write({group_field: cmds})

    def action_create_user_account(self):
        """
        Tạo nhanh tài khoản người dùng Odoo cho giảng viên kèm mật khẩu mặc định (123456)
        và tự động liên kết, đồng bộ nhóm quyền ngay lập tức mà không cần email xác nhận.
        """
        self.ensure_one()
        if self.user_id:
            raise UserError('Giảng viên này đã có tài khoản người dùng liên kết: %s' % (self.user_id.login or self.user_id.name))

        # Ưu tiên lấy email, nếu không có lấy theo mã giảng viên
        login = self.email or (self.lecturer_code and f"{self.lecturer_code.strip().lower()}@vnua.edu.vn")
        if not login:
            raise UserError('Vui lòng nhập Email hoặc Mã giảng viên trên hồ sơ trước khi tạo tài khoản.')

        login = login.strip()

        # Kiểm tra xem tài khoản này đã tồn tại trong res.users chưa
        User = self.env['res.users'].sudo()
        existing = User.search([('login', '=', login)], limit=1)
        if existing:
            self.write({'user_id': existing.id})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Đã liên kết tài khoản',
                    'message': f'Đã liên kết với tài khoản có sẵn ({existing.login}) thành công!',
                    'sticky': False,
                    'type': 'success',
                }
            }

        group_field = 'group_ids' if 'group_ids' in User._fields else 'groups_id'
        user_group = self.env.ref('faculty_work_mgmt.group_faculty_user', raise_if_not_found=False)
        groups = [(4, user_group.id)] if user_group else []

        new_user = User.create({
            'name': self.name,
            'login': login,
            'password': '123456', # Tạo trực tiếp bỏ qua email xác nhận
            'partner_id': self.partner_id.id,
            group_field: groups,
        })
        new_user.write({'password': '123456'})
        self.write({'user_id': new_user.id})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Tạo tài khoản thành công',
                'message': f'Đã tạo tài khoản cho {self.name}!\nTên đăng nhập: {login}\nMật khẩu khởi tạo: 123456',
                'sticky': True,
                'type': 'success',
            }
        }

    def action_reset_password_default(self):
        """
        Đặt lại mật khẩu cho tài khoản người dùng liên kết về mặc định: 123456
        """
        self.ensure_one()
        if not self.user_id:
            raise UserError('Chưa có tài khoản người dùng nào được liên kết với giảng viên này.')
        self.user_id.sudo().write({'password': '123456'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Đặt lại mật khẩu thành công',
                'message': f'Mật khẩu của tài khoản {self.user_id.login} đã được đặt về: 123456',
                'sticky': False,
                'type': 'success',
            }
        }

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
    source_research_id = fields.Many2one('faculty.research.work', string='Công trình NCKH nguồn', index=True, ondelete='set null',
                                         help='Liên kết ngược về công trình NCKH gốc để chống tạo trùng khi duyệt lại.')


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
    source_research_id = fields.Many2one('faculty.research.work', string='Công trình NCKH nguồn', index=True, ondelete='set null',
                                         help='Liên kết ngược về công trình NCKH gốc để chống tạo trùng khi duyệt lại.')

    # Cờ giới hạn tối đa 5 công trình tiêu biểu
    is_top_selected = fields.Boolean(
        string='Chọn in LLKH (Tối đa 5 bài tiêu biểu)',
        default=False,
        help='Tích chọn tối đa 5 công trình khoa học tiêu biểu nhất để xuất in Lý lịch khoa học.'
    )

    @api.constrains('is_top_selected')
    def _check_top_selected_limit(self):
        for rec in self:
            if rec.is_top_selected and rec.lecturer_id:
                # Đếm trực tiếp trên quan hệ One2many đã loaded (bao gồm cả bản ghi mới chưa flush)
                count = len(rec.lecturer_id.publication_ids.filtered('is_top_selected'))
                if count > 5:
                    raise ValidationError(_(
                        'Giảng viên "%(name)s" đã chọn %(count)d công trình tiêu biểu. '
                        'Tối đa chỉ được 5 công trình!',
                        name=rec.lecturer_id.name,
                        count=count,
                    ))
