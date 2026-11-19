# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FacultyHourLedger(models.Model):
    _name = 'faculty.hour.ledger'
    _description = 'Sổ cái Giờ chuẩn Trung tâm'
    _inherit = ['department.back.to.list.mixin']
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

    # Phân loại rõ 2 nhánh trong Giảng dạy
    teaching_branch = fields.Selection([
        ('direct', 'Giờ lên lớp trực tiếp (b)'),
        ('converted', 'Giờ quy đổi giảng dạy khác'),
    ], string='Nhánh giảng dạy', compute='_compute_teaching_branch', store=True, readonly=False, index=True,
       help='Phân loại 2 nhánh: (a) Giờ lên lớp trực tiếp để tính biến b; (b) Giờ quy đổi giảng dạy khác để cộng với b thành tổng a.')

    is_direct_teaching = fields.Boolean(
        string='Lên lớp trực tiếp (b)',
        compute='_compute_teaching_branch',
        store=True,
        readonly=False,
        index=True,
        help='Tích chọn nếu là giờ lên lớp trực tiếp (để tổng hợp biến b).'
    )

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
        ('teaching_plan', 'Lập kế hoạch giảng dạy học phần'),
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

    state = fields.Selection([
        ('staging', 'Dự thảo / Tạm tính'),
        ('posted', 'Đã ghi sổ / Chính thức'),
        ('cancelled', 'Đã hủy / Bút toán đảo'),
    ], string='Trạng thái sổ cái', default='posted', index=True)

    is_reversal = fields.Boolean(string='Bút toán đảo', default=False, index=True)
    reversal_source_id = fields.Many2one('faculty.hour.ledger', string='Bút toán gốc được đảo', ondelete='set null')

    is_locked = fields.Boolean(string='Đã chốt sổ', default=False, index=True,
                               help='Khi đã chốt sổ cuối năm, không được chỉnh sửa hoặc xóa dòng này.')
    notes = fields.Text(string='Ghi chú')

    @api.depends('category', 'activity_type')
    def _compute_teaching_branch(self):
        for rec in self:
            if rec.category == 'teaching':
                if rec.activity_type == 'lecture':
                    rec.teaching_branch = 'direct'
                    rec.is_direct_teaching = True
                else:
                    rec.teaching_branch = 'converted'
                    rec.is_direct_teaching = False
            else:
                rec.teaching_branch = False
                rec.is_direct_teaching = False

    _sql_constraints = [
        ('check_standard_hours', 'CHECK(standard_hours >= 0 OR is_reversal = True)', 'Số giờ chuẩn phải lớn hơn hoặc bằng 0 (trừ bút toán đảo)!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super(FacultyHourLedger, self).create(vals_list)
        # Tự động cập nhật Bảng cân đối giờ chuẩn cho giảng viên liên quan
        lec_year_pairs = set(
            (rec.lecturer_id.id, rec.academic_year_id.id)
            for rec in records
            if rec.lecturer_id and rec.academic_year_id
        )
        Balance = self.env['faculty.workload.balance']
        for lec_id, year_id in lec_year_pairs:
            Balance.recompute_for_lecturer(lec_id, year_id)
        return records

    def unlink(self):
        for rec in self:
            if rec.is_locked:
                raise UserError(_('Không thể xóa dòng sổ cái đã chốt cuối năm: "%s"!') % rec.name)
        lec_year_pairs = set(
            (rec.lecturer_id.id, rec.academic_year_id.id)
            for rec in self
            if rec.lecturer_id and rec.academic_year_id
        )
        res = super(FacultyHourLedger, self).unlink()
        Balance = self.env['faculty.workload.balance']
        for lec_id, year_id in lec_year_pairs:
            Balance.recompute_for_lecturer(lec_id, year_id)
        return res

    def write(self, vals):
        for rec in self:
            if rec.is_locked and not (len(vals) == 1 and 'is_locked' in vals):
                raise UserError(_('Dòng sổ cái này đã chốt cuối năm, không được phép chỉnh sửa: "%s"!') % rec.name)
        lec_year_pairs = set(
            (rec.lecturer_id.id, rec.academic_year_id.id)
            for rec in self
            if rec.lecturer_id and rec.academic_year_id
        )
        res = super(FacultyHourLedger, self).write(vals)
        for rec in self:
            if rec.lecturer_id and rec.academic_year_id:
                lec_year_pairs.add((rec.lecturer_id.id, rec.academic_year_id.id))
        Balance = self.env['faculty.workload.balance']
        for lec_id, year_id in lec_year_pairs:
            Balance.recompute_for_lecturer(lec_id, year_id)
        return res

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
        vals.setdefault('state', 'posted')

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


class FacultyWorkloadLedger(models.Model):
    """
    Alias / Kế thừa kỹ thuật cho faculty.workload.ledger theo chuẩn Ledger Pattern
    """
    _name = 'faculty.workload.ledger'
    _inherit = 'faculty.hour.ledger'
    _description = 'Sổ cái Giờ chuẩn (Workload Ledger)'


class FacultyManualDeclaration(models.Model):
    """
    Tờ khai công việc thủ công (faculty.manual.declaration)
    Áp dụng Ledger Pattern: tách biệt tờ khai và sổ cái.
    Khi Duyệt (approved), gọi _lock_and_post() dùng SELECT ... FOR UPDATE SKIP LOCKED để chuyển sổ.
    Khi Hủy, sinh bút toán đảo (reversal).
    """
    _name = 'faculty.manual.declaration'
    _description = 'Tờ khai Công việc Giảng viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Tên công việc / Tờ khai', required=True, tracking=True,
                       placeholder='VD: Khảo thí học phần X, Hướng dẫn khóa luận tốt nghiệp...')
    code = fields.Char(string='Mã tờ khai', copy=False, default=lambda self: _('Mới'))
    lecturer_id = fields.Many2one(
        'faculty.lecturer',
        string='Giảng viên khai báo',
        required=True,
        default=lambda self: self.env['faculty.lecturer'].search([('user_id', '=', self.env.uid)], limit=1),
        index=True,
        tracking=True
    )
    academic_year_id = fields.Many2one(
        'faculty.academic.year',
        string='Năm học',
        required=True,
        default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False,
        index=True,
        tracking=True
    )
    semester_id = fields.Many2one('faculty.academic.semester', string='Học kỳ')
    date = fields.Date(string='Ngày thực hiện', default=fields.Date.context_today, required=True, tracking=True)

    category = fields.Selection([
        ('teaching', '1. Giảng dạy'),
        ('research', '2. Nghiên cứu khoa học'),
        ('other', '3. Hoạt động khác'),
    ], string='Nhóm công việc', required=True, default='teaching', tracking=True)

    teaching_branch = fields.Selection([
        ('direct', 'Giờ lên lớp trực tiếp (b)'),
        ('converted', 'Giờ quy đổi giảng dạy khác'),
    ], string='Nhánh giảng dạy', default='converted', tracking=True,
       help='Giờ lên lớp trực tiếp để tính biến b; Giờ quy đổi giảng dạy khác để cộng với b thành tổng a.')

    is_direct_teaching = fields.Boolean(
        string='Lên lớp trực tiếp (b)',
        compute='_compute_is_direct_teaching',
        store=True,
        readonly=False
    )

    activity_type = fields.Selection([
        ('lecture', 'Giờ giảng đứng lớp'),
        ('exam_proctoring', 'Coi thi'),
        ('exam_grading', 'Chấm thi'),
        ('exam_audit', 'Chấm kiểm tra'),
        ('exam_creation', 'Ra đề thi mới'),
        ('thesis_guidance', 'Hướng dẫn Khóa luận / Luận văn'),
        ('internship', 'Hướng dẫn Thực hành / Thực tập'),
        ('research_paper', 'Bài báo khoa học'),
        ('research_project', 'Đề tài KH&CN'),
        ('research_book', 'Sách / Giáo trình'),
        ('research_workshop', 'Hội thảo / Tọa đàm'),
        ('curriculum_dev', 'Biên soạn CTĐT / Đề cương'),
        ('initiative', 'Sáng kiến / Giải pháp'),
        ('faculty_meeting', 'Sinh hoạt chuyên môn'),
        ('party_union', 'Công tác Đảng - Đoàn'),
        ('sports_culture', 'Thể dục thể thao'),
        ('admissions', 'Tuyển sinh / Tuyển dụng'),
        ('course_org', 'Tổ chức lớp bồi dưỡng'),
        ('other', 'Hoạt động hành chính khác'),
    ], string='Loại nhiệm vụ', required=True, default='exam_grading', tracking=True)

    raw_hours = fields.Float(string='Số lượng / Số giờ gốc', required=True, default=1.0, tracking=True)
    coefficient = fields.Float(string='Hệ số quy đổi', required=True, default=1.0, tracking=True)
    standard_hours = fields.Float(string='Số giờ chuẩn quy đổi', compute='_compute_standard_hours', store=True, tracking=True)

    proof_file = fields.Binary(string='File minh chứng', attachment=True)
    proof_filename = fields.Char(string='Tên file minh chứng')

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('to_approve', 'Chờ Trưởng khoa duyệt'),
        ('approved', 'Đã duyệt / Đã ghi sổ'),
        ('cancelled', 'Đã hủy / Bút toán đảo'),
    ], string='Trạng thái', default='draft', tracking=True)

    ledger_id = fields.Many2one('faculty.hour.ledger', string='Bút toán Sổ cái chính thức', readonly=True)
    reversal_ledger_id = fields.Many2one('faculty.hour.ledger', string='Bút toán đảo', readonly=True)
    notes = fields.Text(string='Ghi chú giải trình')

    @api.depends('category', 'teaching_branch')
    def _compute_is_direct_teaching(self):
        for rec in self:
            rec.is_direct_teaching = (rec.category == 'teaching' and rec.teaching_branch == 'direct')

    @api.depends('raw_hours', 'coefficient')
    def _compute_standard_hours(self):
        for rec in self:
            rec.standard_hours = round(rec.raw_hours * rec.coefficient, 2)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('Mới')) == _('Mới'):
                vals['code'] = self.env['ir.sequence'].next_by_code('faculty.manual.declaration') or f"DEC-{fields.Date.today().strftime('%Y%m%d%H%M')}"
        return super(FacultyManualDeclaration, self).create(vals_list)

    def action_submit(self):
        for rec in self:
            rec.state = 'to_approve'

    def action_draft(self):
        for rec in self:
            if rec.state == 'approved':
                raise UserError(_('Bản ghi đã duyệt không thể quay về dự thảo. Vui lòng bấm Hủy để sinh bút toán đảo!'))
            rec.state = 'draft'

    def action_approve(self):
        for rec in self:
            rec._lock_and_post()

    def _lock_and_post(self):
        """
        Sử dụng SELECT ... FOR UPDATE SKIP LOCKED để khóa giao dịch chống race-condition
        và chuyển bút toán sang posted trên Sổ cái faculty.hour.ledger.
        """
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM faculty_manual_declaration WHERE id = %s FOR UPDATE SKIP LOCKED",
            (self.id,)
        )
        if not self.env.cr.fetchone():
            raise UserError(_('Bản ghi tờ khai này đang được xử lý bởi một giao dịch khác hoặc đã bị khóa. Vui lòng thử lại sau!'))
        ledger_vals = {
            'lecturer_id': self.lecturer_id.id,
            'academic_year_id': self.academic_year_id.id,
            'semester_id': self.semester_id.id if self.semester_id else False,
            'date': self.date,
            'category': self.category,
            'activity_type': self.activity_type,
            'teaching_branch': self.teaching_branch,
            'is_direct_teaching': self.is_direct_teaching,
            'name': f"[Tờ khai] {self.name}",
            'raw_hours': self.raw_hours,
            'coefficient': self.coefficient,
            'standard_hours': self.standard_hours,
            'res_model': self._name,
            'res_id': self.id,
            'state': 'posted',
        }
        ledger_entry = self.env['faculty.hour.ledger'].post_ledger_entry(ledger_vals)
        self.write({
            'ledger_id': ledger_entry.id,
            'state': 'approved',
        })
        return ledger_entry

    def action_cancel(self):
        for rec in self:
            if rec.state == 'approved' and rec.ledger_id:
                # Sinh bút toán đảo (reversal)
                reversal_vals = {
                    'lecturer_id': rec.lecturer_id.id,
                    'academic_year_id': rec.academic_year_id.id,
                    'semester_id': rec.semester_id.id if rec.semester_id else False,
                    'date': fields.Date.today(),
                    'category': rec.category,
                    'activity_type': rec.activity_type,
                    'teaching_branch': rec.teaching_branch,
                    'is_direct_teaching': rec.is_direct_teaching,
                    'name': f"[Bút toán đảo] Hủy tờ khai: {rec.name}",
                    'raw_hours': -rec.raw_hours,
                    'coefficient': rec.coefficient,
                    'standard_hours': -rec.standard_hours,
                    'res_model': rec._name,
                    'res_id': rec.id,
                    'state': 'cancelled',
                    'is_reversal': True,
                    'reversal_source_id': rec.ledger_id.id,
                }
                reversal_entry = self.env['faculty.hour.ledger'].create(reversal_vals)
                rec.write({
                    'reversal_ledger_id': reversal_entry.id,
                    'state': 'cancelled',
                })
            else:
                rec.write({'state': 'cancelled'})
        return True


class FacultyWorkloadBalance(models.Model):
    """
    Bảng Tổng kết Giờ chuẩn & Thuật toán Bù trừ Chéo (faculty.workload.balance)
    Theo chuẩn quy định tại .agent/rules.md Mục 3.

    Công thức:
      A = net_teaching_quota (định mức giảng sau giảm)
      B = 0.5 * A            (định mức lên lớp tối thiểu)
      b = actual_classroom_hours (giờ lên lớp thực tế, teaching_branch='direct')
      a = b + giờ quy đổi GD khác (tổng giờ giảng, total_teaching_hours)
      C = net_research_quota (định mức NCKH sau giảm)
      c = actual_research_hours (giờ NCKH thực tế)
      m = max(0, a - A), n = max(0, b - B), o = max(0, c - C)

    Bù trừ chéo:
      GD→NCKH: nếu m>0 và c<C và c>=0.25*C: dùng m*rate_t_to_r bù c đến C
      NCKH→GD: nếu a<A và o>0: dùng o*rate_r_to_t bù a đến A

    Chốt tiền: n luôn = max(0, b-B). Tiền vượt giờ = n*đơn_giá CHỈ KHI a_sau>=A VÀ c_sau>=C.
    Giờ NCKH vượt (o) không tính tiền.
    """
    _name = 'faculty.workload.balance'
    _description = 'Bảng Tổng kết Giờ chuẩn & Bù trừ Chéo'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'academic_year_id desc, lecturer_id asc, id desc'

    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên', required=True, index=True)
    academic_year_id = fields.Many2one(
        'faculty.academic.year',
        string='Năm học',
        required=True,
        default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False,
        index=True
    )

    # 1. Nhóm Giảng dạy
    net_teaching_quota = fields.Float(string='ĐM Giảng dạy sau giảm (A)', compute='_compute_balance', store=True)
    min_classroom_quota = fields.Float(string='ĐM Lên lớp tối thiểu (B = 0.5*A)', compute='_compute_balance', store=True)
    actual_classroom_hours = fields.Float(string='Giờ lên lớp thực tế (b)', compute='_compute_balance', store=True)
    other_teaching_hours = fields.Float(string='Giờ quy đổi GD khác', compute='_compute_balance', store=True)
    total_teaching_hours = fields.Float(string='Tổng giờ giảng đạt được (a = b + khác)', compute='_compute_balance', store=True)

    # 2. Nhóm NCKH
    net_research_quota = fields.Float(string='ĐM NCKH sau giảm (C)', compute='_compute_balance', store=True)
    actual_research_hours = fields.Float(string='Số giờ NCKH thực tế (c)', compute='_compute_balance', store=True)

    # Các biến chênh lệch ban đầu
    m_excess_teaching = fields.Float(string='Giờ giảng vượt m = max(0, a - A)', compute='_compute_balance', store=True)
    n_overtime_classroom = fields.Float(string='Giờ lên lớp thừa n = max(0, b - B)', compute='_compute_balance', store=True)
    o_excess_research = fields.Float(string='Giờ NCKH vượt o = max(0, c - C)', compute='_compute_balance', store=True)

    # Bù trừ chéo
    # teaching_offset: giờ GD (m) đã trích để bù sang NCKH (chiều GD→NCKH)
    # research_offset: giờ NCKH (o) đã trích để bù sang GD (chiều NCKH→GD)
    teaching_offset = fields.Float(string='Giờ GD trích bù NCKH (phần m đã dùng)', compute='_compute_balance', store=True)
    research_offset = fields.Float(string='Giờ NCKH trích bù GD (phần o đã dùng)', compute='_compute_balance', store=True)
    final_teaching_hours = fields.Float(string='Giờ GD sau bù trừ (a_sau)', compute='_compute_balance', store=True)
    final_research_hours = fields.Float(string='Giờ NCKH sau bù trừ (c_sau)', compute='_compute_balance', store=True)

    # Điều kiện sàn NCKH cho phép bù trừ chiều GD→NCKH
    teaching_to_research_floor_met = fields.Boolean(
        string='Đạt sàn NCKH để bù trừ GD→NCKH (c >= 0.25*C)',
        compute='_compute_balance', store=True
    )

    # Kết luận hoàn thành
    is_teaching_passed = fields.Boolean(string='Đạt giờ Giảng dạy (a_sau >= A)', compute='_compute_balance', store=True)
    is_research_passed = fields.Boolean(string='Đạt giờ NCKH (c_sau >= C)', compute='_compute_balance', store=True)
    is_completed = fields.Boolean(string='Hoàn thành nhiệm vụ', compute='_compute_balance', store=True)
    result_status = fields.Selection([
        ('completed', 'Hoàn thành nhiệm vụ'),
        ('fail_teaching', 'Không hoàn thành nhiệm vụ giảng dạy'),
        ('fail_research', 'Không đạt giờ NCKH'),
        ('fail_both', 'Không đạt cả 2 nhiệm vụ'),
    ], string='Kết luận hoàn thành', compute='_compute_balance', store=True)

    overtime_teaching_rate = fields.Float(string='Đơn giá 1 giờ giảng vượt (VNĐ)', compute='_compute_balance', store=True)
    overtime_payment_amount = fields.Float(string='Thành tiền vượt giờ (VNĐ)', compute='_compute_balance', store=True)

    # 3. Nhóm Hoạt động khác (Mục riêng độc lập, KHÔNG miễn giảm, KHÔNG bù trừ chéo)
    other_norm = fields.Float(string='ĐM Hoạt động khác chuẩn', compute='_compute_balance', store=True)
    other_actual = fields.Float(string='Thực tế Hoạt động khác', compute='_compute_balance', store=True)
    other_balance = fields.Float(string='Thừa/Thiếu HĐ khác (Độc lập)', compute='_compute_balance', store=True)
    other_status = fields.Selection([
        ('pass', 'Đạt yêu cầu'),
        ('fail', 'Chưa đạt yêu cầu'),
    ], string='Kết quả HĐ khác', compute='_compute_balance', store=True)

    @api.depends('lecturer_id', 'academic_year_id')
    def _compute_balance(self):
        ICP = self.env['ir.config_parameter'].sudo()
        def _get_val(key, default_val):
            if hasattr(ICP, 'get_float'):
                return float(ICP.get_float(key, default_val))
            elif hasattr(ICP, 'get_param'):
                return float(ICP.get_param(key, default_val))
            elif hasattr(ICP, 'get_str'):
                return float(ICP.get_str(key, str(default_val)))
            record = ICP.search([('key', '=', key)], limit=1)
            return float(record.value) if record and record.value else float(default_val)

        rate_t_to_r = _get_val('faculty_work_mgmt.rate_t_to_r', 1.0)
        rate_r_to_t = _get_val('faculty_work_mgmt.rate_r_to_t', 1.0)
        overtime_rate = _get_val('faculty_work_mgmt.overtime_teaching_rate', 150000.0)

        for rec in self:
            if not rec.lecturer_id or not rec.academic_year_id:
                rec.net_teaching_quota = 0.0
                rec.min_classroom_quota = 0.0
                rec.actual_classroom_hours = 0.0
                rec.other_teaching_hours = 0.0
                rec.total_teaching_hours = 0.0
                rec.net_research_quota = 0.0
                rec.actual_research_hours = 0.0
                rec.m_excess_teaching = 0.0
                rec.n_overtime_classroom = 0.0
                rec.o_excess_research = 0.0
                rec.teaching_offset = 0.0
                rec.research_offset = 0.0
                rec.final_teaching_hours = 0.0
                rec.final_research_hours = 0.0
                rec.teaching_to_research_floor_met = False
                rec.is_teaching_passed = False
                rec.is_research_passed = False
                rec.is_completed = False
                rec.result_status = 'fail_both'
                rec.overtime_teaching_rate = overtime_rate
                rec.overtime_payment_amount = 0.0
                rec.other_norm = 0.0
                rec.other_actual = 0.0
                rec.other_balance = 0.0
                rec.other_status = 'fail'
                continue

            lec = rec.lecturer_id
            year = rec.academic_year_id

            # --- Định mức sau giảm ---
            A = lec.teaching_norm_reduced or 0.0   # Định mức giảng dạy sau giảm
            B = round(A * 0.5, 2)                  # Định mức lên lớp tối thiểu
            C = lec.research_norm_reduced or 0.0   # Định mức NCKH sau giảm
            O_norm = lec.other_norm_reduced or 0.0 # Định mức HĐ khác (không giảm)

            # --- Tổng hợp giờ từ sổ cái posted bằng _read_group ---
            # Nhóm theo (lecturer_id, academic_year_id, category, teaching_branch)
            # để tách b (direct) khỏi giờ quy đổi GD khác
            groups = self.env['faculty.hour.ledger']._read_group(
                domain=[
                    ('lecturer_id', '=', lec.id),
                    ('academic_year_id', '=', year.id),
                    ('state', '=', 'posted'),
                ],
                groupby=['category', 'teaching_branch'],
                aggregates=['standard_hours:sum'],
            )

            b = 0.0        # giờ lên lớp trực tiếp
            other_t = 0.0  # giờ quy đổi GD khác
            c = 0.0        # giờ NCKH
            o_act = 0.0    # giờ HĐ khác

            for category, teaching_branch, hours_sum in groups:
                hours_sum = hours_sum or 0.0
                if category == 'teaching':
                    if teaching_branch == 'direct':
                        b += hours_sum
                    else:
                        other_t += hours_sum
                elif category == 'research':
                    c += hours_sum
                elif category == 'other':
                    o_act += hours_sum

            b = round(b, 2)
            other_t = round(other_t, 2)
            a = round(b + other_t, 2)  # Tổng giờ giảng = b + giờ quy đổi GD khác
            c = round(c, 2)
            o_act = round(o_act, 2)

            # --- Tính m, n, o ---
            m = max(0.0, round(a - A, 2))   # Giờ giảng vượt định mức (a > A)
            n = max(0.0, round(b - B, 2))   # Giờ lên lớp thừa (b > B) — LUÔN GIỮ NGUYÊN
            o = max(0.0, round(c - C, 2))   # Giờ NCKH vượt định mức (c > C)

            # --- Thuật toán bù trừ chéo ---
            a_sau = a
            c_sau = c
            # teaching_offset: số giờ m đã trích (chiều GD→NCKH)
            # research_offset: số giờ o đã trích (chiều NCKH→GD)
            teaching_offset = 0.0
            research_offset = 0.0
            floor_met = False

            # Chiều 1: Giảng dạy → NCKH (khi a > A tức m > 0, và c < C)
            if m > 0.0 and c < C:
                # Điều kiện sàn: c phải đạt tối thiểu 25% định mức C
                floor_met = (C > 0.0 and c >= 0.25 * C)
                if floor_met:
                    deficit_c = round(C - c, 2)            # Lượng NCKH còn thiếu
                    # Cần dùng bao nhiêu m để tạo ra đủ deficit_c
                    needed_m = round(deficit_c / rate_t_to_r, 2) if rate_t_to_r > 0.0 else 0.0
                    used_m = min(m, needed_m)              # Không dùng quá m hiện có
                    c_bu = round(used_m * rate_t_to_r, 2)  # Lượng NCKH được bù thêm
                    # Chốt kết quả sau bù trừ
                    c_sau = round(c + c_bu, 2)             # c_sau tối đa = C
                    a_sau = round(a - used_m, 2)           # a_sau luôn >= A
                    teaching_offset = used_m               # Phần m đã trích
                    research_offset = 0.0                  # Chiều này không dùng o

            # Chiều 2: NCKH → Giảng dạy (khi a < A và c > C tức o > 0)
            elif a < A and o > 0.0:
                deficit_a = round(A - a, 2)                # Lượng GD còn thiếu
                # Cần dùng bao nhiêu o để tạo ra đủ deficit_a
                needed_o = round(deficit_a / rate_r_to_t, 2) if rate_r_to_t > 0.0 else 0.0
                used_o = min(o, needed_o)                  # Không dùng quá o hiện có
                a_bu = round(used_o * rate_r_to_t, 2)      # Lượng GD được bù thêm
                # Chốt kết quả sau bù trừ
                a_sau = round(a + a_bu, 2)                 # a_sau tối đa = A
                c_sau = round(c - used_o, 2)               # c_sau luôn >= C
                research_offset = used_o                   # Phần o đã trích
                teaching_offset = 0.0                      # Chiều này không dùng m

            # --- Chốt trạng thái hoàn thành & Tính tiền ---
            is_t_pass = (a_sau >= A)
            is_r_pass = (c_sau >= C)
            is_done = is_t_pass and is_r_pass

            # Số giờ thừa luôn là n = max(0, b - B) — không thay đổi sau bù trừ
            # Tiền vượt giờ CHỈ tính khi HOÀN THÀNH CẢ 2 (a_sau >= A VÀ c_sau >= C)
            # Giờ NCKH vượt (o) KHÔNG tính tiền
            if not is_t_pass and not is_r_pass:
                res_stat = 'fail_both'
                money = 0.0
            elif not is_t_pass:
                res_stat = 'fail_teaching'
                money = 0.0
            elif not is_r_pass:
                res_stat = 'fail_research'
                money = 0.0
            else:
                res_stat = 'completed'
                money = round(n * overtime_rate, 2) if n > 0.0 else 0.0

            # --- Hoạt động khác: Độc lập, không bù trừ, không miễn giảm ---
            o_bal = round(o_act - O_norm, 2)
            o_stat = 'pass' if o_act >= O_norm else 'fail'

            rec.net_teaching_quota = A
            rec.min_classroom_quota = B
            rec.actual_classroom_hours = b
            rec.other_teaching_hours = other_t
            rec.total_teaching_hours = a
            rec.net_research_quota = C
            rec.actual_research_hours = c
            rec.m_excess_teaching = m
            rec.n_overtime_classroom = n
            rec.o_excess_research = o
            rec.teaching_offset = teaching_offset
            rec.research_offset = research_offset
            rec.final_teaching_hours = a_sau
            rec.final_research_hours = c_sau
            rec.teaching_to_research_floor_met = floor_met
            rec.is_teaching_passed = is_t_pass
            rec.is_research_passed = is_r_pass
            rec.is_completed = is_done
            rec.result_status = res_stat
            rec.overtime_teaching_rate = overtime_rate
            rec.overtime_payment_amount = money
            rec.other_norm = O_norm
            rec.other_actual = o_act
            rec.other_balance = o_bal
            rec.other_status = o_stat

    def action_recompute_balance(self):
        """
        Nút bấm tính lại bảng cân đối trên giao diện (xóa bỏ stale cache)
        """
        self._compute_balance()
        return True

    @api.model
    def recompute_for_lecturer(self, lecturer_id, year_id=None):
        """
        Tìm hoặc tạo bản ghi faculty.workload.balance cho giảng viên và năm học,
        sau đó gọi _compute_balance() để cập nhật lại dữ liệu mới nhất.
        """
        if not lecturer_id:
            return False

        domain = [('lecturer_id', '=', lecturer_id)]
        if year_id:
            domain.append(('academic_year_id', '=', year_id))

        balances = self.search(domain)
        if not balances and year_id:
            balances = self.create({
                'lecturer_id': lecturer_id,
                'academic_year_id': year_id,
            })
        elif not balances and not year_id:
            cur_year = self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1)
            if cur_year:
                balances = self.create({
                    'lecturer_id': lecturer_id,
                    'academic_year_id': cur_year.id,
                })

        if balances:
            balances._compute_balance()
        return balances
