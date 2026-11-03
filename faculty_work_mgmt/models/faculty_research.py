# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class FacultyBudgetLine(models.Model):
    """Kế thừa bảng Dự toán dùng chung cho Công trình NCKH"""
    _inherit = 'faculty.budget.line'

    research_id = fields.Many2one('faculty.research.work', string='Công trình NCKH', ondelete='cascade', index=True)


class FacultyCourse(models.Model):
    """Mở rộng Học phần để liên kết với các Học liệu, Ngân hàng đề, Sách từ NCKH"""
    _inherit = 'faculty.course'

    research_material_ids = fields.One2many(
        'faculty.research.work', 'target_course_id',
        string='Học liệu & Ngân hàng đề thi từ NCKH',
        domain=[('research_type', 'in', ['study_material', 'question_bank', 'book'])]
    )


class FacultyResearchWork(models.Model):
    _name = 'faculty.research.work'
    _description = 'Công trình Nghiên cứu Khoa học (Trụ cột 2)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'department.back.to.list.mixin']
    _order = 'academic_year_id desc, start_date desc, id desc'

    name = fields.Char(string='Tên công trình / Đề tài / Hoạt động', required=True, tracking=True,
                       placeholder='VD: Nghiên cứu ứng dụng AI trong quản lý giáo dục đại học')
    code = fields.Char(string='Mã công trình / Đề tài', copy=False, index=True, tracking=True,
                       placeholder='VD: DT-2026-01, BB-WOS-05...')

    # 13 loại hình NCKH chuẩn nghiệp vụ Khoa
    research_type = fields.Selection([
        ('article_wos_scopus', '1. Bài báo quốc tế WoS / Scopus'),
        ('article_domestic', '2. Bài báo khoa học trong nước'),
        ('project_level', '3. Đề tài NCKH các cấp (Trường / Bộ / Nhà nước)'),
        ('project_theory', '4. Đề tài lý luận'),
        ('conference_org', '5. Tổ chức Hội thảo khoa học các cấp'),
        ('seminar_org', '6. Tổ chức Tọa đàm khoa học'),
        ('conference_paper', '7. Bài tham luận khoa học'),
        ('initiative', '8. Sáng kiến kinh nghiệm / Cải tiến'),
        ('study_material', '9. Biên soạn / Chỉnh sửa Học liệu'),
        ('question_bank', '10. Xây dựng Ngân hàng câu hỏi thi'),
        ('book', '11. Sách (Chuyên khảo / Tham khảo / Hướng dẫn)'),
        ('build_curriculum', '12. Xây dựng Chương trình đào tạo mới'),
        ('build_syllabus', '13. Xây dựng Đề cương chi tiết học phần'),
    ], string='Loại hình NCKH', required=True, default='article_domestic', tracking=True)

    # Phân cấp Đề tài NCKH
    project_scope = fields.Selection([
        ('school', 'Cấp Trường / Cơ sở'),
        ('ministry', 'Cấp Bộ / Tỉnh / Ngành'),
        ('state', 'Cấp Quốc gia / Nhà nước'),
    ], string='Phân cấp đề tài', default='school', tracking=True)

    # Phân loại Sách
    book_type = fields.Selection([
        ('monograph', 'Sách chuyên khảo'),
        ('reference', 'Sách tham khảo'),
        ('handbook', 'Sách hướng dẫn / Giáo trình'),
    ], string='Phân loại sách', default='monograph', tracking=True)

    academic_year_id = fields.Many2one('faculty.academic.year', string='Năm học', required=True, tracking=True,
                                       default=lambda self: self.env['faculty.academic.year'].search([('is_current', '=', True)], limit=1).id or False)
    semester_id = fields.Many2one('faculty.academic.semester', string='Học kỳ',
                                  domain="[('academic_year_id', '=', academic_year_id)]")
    norm_config_id = fields.Many2one('faculty.norm.config', string='Định mức quy chuẩn áp dụng',
                                     default=lambda self: self.env['faculty.norm.config'].search([('active', '=', True)], limit=1).id or False)

    leader_id = fields.Many2one('faculty.lecturer', string='Chủ nhiệm / Tác giả chính', required=True, tracking=True,
                                help='Người chủ trì đề tài, tác giả đứng đầu bài báo hoặc chủ biên cuốn sách.')
    participant_ids = fields.One2many('faculty.research.participant', 'research_id', string='Danh sách Thành viên tham gia')

    start_date = fields.Date(string='Ngày bắt đầu / Ký hợp đồng', default=fields.Date.context_today, tracking=True)
    deadline = fields.Date(string='Hạn chót nghiệm thu', tracking=True)
    acceptance_date = fields.Date(string='Ngày nghiệm thu / Xuất bản', tracking=True)

    # Cảnh báo hạn chót: store=False kèm search='_search_alert_level'
    alert_level = fields.Selection([
        ('normal', 'Bình thường'),
        ('urgent', 'Khẩn cấp (<= 3 ngày)'),
        ('overdue', 'Quá hạn'),
    ], string='Cảnh báo tiến độ', compute='_compute_alert_level', search='_search_alert_level', store=False)

    publication_info = fields.Char(string='Tạp chí / Nhà xuất bản / Đơn vị cấp phép', tracking=True,
                                   placeholder='VD: Tạp chí Giáo dục, NXB Đại học Quốc gia, IEEE Access...')
    acceptance_grade = fields.Selection([
        ('excellent', 'Xuất sắc'),
        ('good', 'Tốt / Đạt'),
        ('average', 'Đạt yêu cầu'),
        ('failed', 'Không đạt / Hủy bỏ'),
    ], string='Xếp loại nghiệm thu', default='good', tracking=True)

    # File sản phẩm đính kèm qua Odoo filestore nội bộ
    attachment_file = fields.Binary(string='File sản phẩm / Báo cáo nghiệm thu', attachment=True)
    attachment_filename = fields.Char(string='Tên tệp đính kèm')

    # Cờ trạng thái đưa vào Thư viện Khoa
    library_review_state = fields.Selection([
        ('not_required', 'Không yêu cầu'),
        ('pending', 'Chờ Admin duyệt Thư viện'),
        ('approved', 'Đã lưu vào Thư viện'),
    ], string='Trạng thái Thư viện', default='not_required', tracking=True)

    # Liên kết đích sang Trụ cột 1 (Giảng dạy)
    target_course_id = fields.Many2one('faculty.course', string='Học phần liên quan / Đích',
                                       help='Học phần gắn với đề cương, học liệu, ngân hàng đề thi hoặc tài liệu học tập.')
    target_curriculum_id = fields.Many2one('faculty.curriculum', string='CTĐT liên quan / Đích',
                                           help='Chương trình đào tạo được xây dựng mới hoặc cập nhật.')
    target_syllabus_id = fields.Many2one('faculty.course.syllabus', string='Đề cương chi tiết liên quan / Đích',
                                         help='Đề cương chi tiết được xây dựng mới hoặc cập nhật.')

    # Tổng giờ NCKH quy đổi
    total_hours = fields.Float(string='Tổng giờ NCKH quy chuẩn', compute='_compute_total_hours', store=True)

    # Tab Dự toán kinh phí
    payment_regulation_id = fields.Many2one('faculty.payment.regulation', string='Quy định thanh toán áp dụng',
                                            domain=[('payment_category', 'in', ['research', 'other'])])
    budget_line_ids = fields.One2many('faculty.budget.line', 'research_id', string='Dự toán kinh phí NCKH')
    total_budget = fields.Float(string='Tổng kinh phí dự toán (VNĐ)', compute='_compute_total_budget', store=True)

    # Luồng duyệt chuẩn: draft -> waiting_dean -> approved
    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('waiting_dean', 'Chờ Trưởng khoa duyệt'),
        ('approved', 'Đã duyệt / Đã nghiệm thu'),
    ], string='Trạng thái', default='draft', tracking=True, required=True)

    notes = fields.Text(string='Ghi chú / Tóm tắt nội dung NCKH')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã công trình NCKH đã tồn tại! Vui lòng kiểm tra lại.'),
    ]

    @api.depends('deadline', 'state', 'acceptance_date')
    def _compute_alert_level(self):
        today = fields.Date.today()
        for rec in self:
            if rec.state == 'approved' or rec.acceptance_date:
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
                return [('state', '!=', 'approved'), ('acceptance_date', '=', False), ('deadline', '<', today)]
            elif value == 'urgent':
                return [('state', '!=', 'approved'), ('acceptance_date', '=', False), ('deadline', '>=', today), ('deadline', '<=', three_days)]
            elif value == 'normal':
                return ['|', ('state', '=', 'approved'), ('deadline', '>', three_days)]
        return []

    @api.depends('participant_ids.standard_hours')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = sum(p.standard_hours for p in rec.participant_ids)

    @api.depends('budget_line_ids.subtotal')
    def _compute_total_budget(self):
        for rec in self:
            rec.total_budget = sum(line.subtotal for line in rec.budget_line_ids)

    @api.onchange('leader_id')
    def _onchange_leader_id(self):
        """Tự động thêm Chủ nhiệm/Tác giả chính vào danh sách thành viên với vai trò leader"""
        if self.leader_id and not self.participant_ids:
            self.participant_ids = [(0, 0, {
                'lecturer_id': self.leader_id.id,
                'role': 'leader',
                'contribution_ratio': 100.0,
                'standard_hours': 0.0,
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
        """Nút bấm thủ công nạp lại các mục chi từ Quy định thanh toán"""
        self.ensure_one()
        if not self.payment_regulation_id:
            raise UserError(_('Vui lòng chọn Quy định thanh toán áp dụng trước khi nạp mục chi!'))
        BudgetLine = self.env['faculty.budget.line']
        for line in self.payment_regulation_id.line_ids:
            BudgetLine.create({
                'research_id': self.id,
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
        """Gửi Trưởng khoa phê duyệt"""
        for rec in self:
            if not rec.participant_ids:
                raise ValidationError(_('Vui lòng khai báo danh sách thành viên tham gia trước khi gửi phê duyệt!'))
            rec.state = 'waiting_dean'
            rec.message_post(body=_("Đã gửi hồ sơ công trình NCKH đến Trưởng khoa phê duyệt."))

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
            rec.message_post(body=_("Đã chuyển công trình NCKH về trạng thái Dự thảo."))

    def action_approve(self):
        """
        DUYỆT NGHIỆM THU CÔNG TRÌNH NCKH (state = 'approved'):
        Thực hiện Cơ chế Liên kết chéo tự động (Cross-Pillar Sync):
        1. Ghi giờ chuẩn từng thành viên vào Sổ cái faculty.hour.ledger (category = 'research').
        2. Đẩy sang Trụ cột 1 (Giảng dạy) & Thư viện nhỏ của Khoa:
           - build_curriculum: Tạo/cập nhật faculty.curriculum.
           - build_syllabus: Tạo/cập nhật faculty.course.syllabus gắn với target_course_id.
           - study_material, question_bank, book: Gắn vào target_course_id và đẩy yêu cầu rà soát Thư viện.
        3. Đẩy sang Lý lịch Khoa học 15 mục (faculty.lecturer):
           - Bài báo, Sách, Tham luận: Tạo bản ghi trong faculty.lecturer.publication (Mục 10 LLKH).
           - Đề tài, Sáng kiến: Tạo bản ghi trong faculty.lecturer.resume.line (Mục 11 hoặc 13 LLKH).
        """
        self.ensure_one()
        Ledger = self.env['faculty.hour.ledger']
        ResumeLine = self.env['faculty.lecturer.resume.line']
        Publication = self.env['faculty.lecturer.publication']
        Curriculum = self.env['faculty.curriculum']
        Syllabus = self.env['faculty.course.syllabus']
        LibDoc = self.env['faculty.library.document']

        acc_date = self.acceptance_date or fields.Date.context_today(self)
        acc_year = acc_date.year if acc_date else date.today().year

        # Map activity_type cho Sổ cái
        activity_type_map = {
            'article_wos_scopus': 'research_paper',
            'article_domestic': 'research_paper',
            'conference_paper': 'research_paper',
            'project_level': 'research_project',
            'project_theory': 'research_project',
            'book': 'research_book',
            'conference_org': 'research_workshop',
            'seminar_org': 'research_workshop',
            'initiative': 'initiative',
            'study_material': 'curriculum_dev',
            'question_bank': 'curriculum_dev',
            'build_curriculum': 'curriculum_dev',
            'build_syllabus': 'curriculum_dev',
        }
        ledger_act_type = activity_type_map.get(self.research_type, 'research_project')

        # ---------------------------------------------------------------------
        # 1. GHI SỔ CÁI GIỜ CHUẨN NCKH
        # ---------------------------------------------------------------------
        # Dọn dẹp dòng sổ cái cũ của công trình nếu có giảng viên không còn hợp lệ
        valid_ledger_lecturers = self.participant_ids.filtered(lambda p: p.role != 'attendee' and p.standard_hours > 0).mapped('lecturer_id')
        obsolete_ledgers = Ledger.search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('lecturer_id', 'not in', valid_ledger_lecturers.ids),
            ('is_locked', '=', False),
        ])
        if obsolete_ledgers:
            obsolete_ledgers.unlink()

        for p in self.participant_ids:
            # Quy tắc bắt buộc: Đại biểu tham dự (attendee) luôn standard_hours = 0.0 và không ghi vào sổ cái
            if p.role == 'attendee':
                if p.standard_hours != 0.0:
                    p.standard_hours = 0.0
                continue

            if p.standard_hours > 0:
                role_label = dict(p._fields['role'].selection).get(p.role, '')
                Ledger.post_ledger_entry({
                    'lecturer_id': p.lecturer_id.id,
                    'academic_year_id': self.academic_year_id.id,
                    'semester_id': self.semester_id.id or False,
                    'date': acc_date,
                    'category': 'research',
                    'activity_type': ledger_act_type,
                    'name': f"[{self.code or 'NCKH'}] {self.name} ({role_label})",
                    'raw_hours': p.standard_hours,
                    'coefficient': 1.0,
                    'standard_hours': p.standard_hours,
                    'res_model': self._name,
                    'res_id': self.id,
                    'notes': f"Loại hình NCKH: {dict(self._fields['research_type'].selection).get(self.research_type, '')}",
                })

        # ---------------------------------------------------------------------
        # 2. ĐẨY SANG TRỤ CỘT 1 (GIẢNG DẠY) & THƯ VIỆN KHOA
        # ---------------------------------------------------------------------
        # 2.1. Xây dựng Chương trình đào tạo mới
        if self.research_type == 'build_curriculum':
            curr_code = self.code or f"CTDT-{self.id}"
            curr = self.target_curriculum_id if self.target_curriculum_id.exists() else False
            if not curr:
                curr = Curriculum.search([
                    '|', ('code', 'in', [curr_code, f"CTDT-{self.id}"]),
                         ('name', '=', self.name)
                ], limit=1)
            if curr:
                curr.write({
                    'name': self.name,
                    'decision_date': acc_date,
                    'notes': f"Cập nhật từ nghiệm thu NCKH (duyệt lại): {self.name} ({self.code or ''})",
                })
                self.target_curriculum_id = curr.id
            else:
                new_curr = Curriculum.create({
                    'name': self.name,
                    'code': curr_code,
                    'academic_level': 'bachelor',
                    'decision_date': acc_date,
                    'state': 'draft',
                    'notes': f"Tự động tạo từ nghiệm thu NCKH: {self.name}",
                })
                self.target_curriculum_id = new_curr.id

        # 2.2. Xây dựng Đề cương chi tiết học phần
        elif self.research_type == 'build_syllabus' and self.target_course_id:
            course = self.target_course_id
            syl = self.target_syllabus_id if self.target_syllabus_id.exists() else False
            if not syl:
                syl = Syllabus.search([
                    ('course_id', '=', course.id),
                    '|',
                    ('name', '=', self.name),
                    ('apply_year', '=', acc_year),
                ], limit=1)
            syl_vals = {
                'name': self.name,
                'apply_year': acc_year,
                'attachment_file': self.attachment_file,
                'attachment_filename': self.attachment_filename,
                'decision_date': acc_date,
                'state': 'applied',
            }
            if syl:
                syl.write(syl_vals)
                syl.action_apply()
            else:
                syl_vals.update({
                    'course_id': course.id,
                    'state': 'draft',
                })
                syl = Syllabus.create(syl_vals)
                syl.action_apply()
            self.target_syllabus_id = syl.id

        # 2.3. Biên soạn học liệu, ngân hàng đề thi, sách
        if self.research_type in ('study_material', 'question_bank', 'book'):
            if self.target_course_id:
                # Ghi thông báo chatter vào học phần
                type_label = dict(self._fields['research_type'].selection).get(self.research_type, '')
                self.target_course_id.message_post(body=_(
                    "<b>Đã tiếp nhận sản phẩm NCKH:</b> %s (%s).<br/>Chủ nhiệm/Tác giả: %s."
                ) % (self.name, type_label, self.leader_id.name))

            # Tự động gửi yêu cầu vào Cổng Admin rà soát Thư viện
            self.library_review_state = 'pending'
            # Kiểm tra xem đã tạo tài liệu thư viện tương ứng chưa
            existing_doc = LibDoc.search([
                ('source_model', '=', self._name),
                ('source_id', '=', self.id),
            ], limit=1)
            if existing_doc:
                existing_doc.write({
                    'name': self.name,
                    'attachment_file': self.attachment_file,
                    'attachment_filename': self.attachment_filename or f"{self.name}.pdf",
                })
            elif self.attachment_file:
                # Tìm thư mục thư viện mặc định
                default_cat = self.env['faculty.library.category'].search([
                    ('code', '=', self.research_type)
                ], limit=1) or self.env['faculty.library.category'].search([], limit=1)
                
                doc_type_map = {
                    'study_material': 'study_material',
                    'question_bank': 'question_bank',
                    'book': 'book',
                }
                LibDoc.create({
                    'name': self.name,
                    'code': self.code or f"LIB-RES-{self.id}",
                    'category_id': default_cat.id if default_cat else False,
                    'document_type': doc_type_map.get(self.research_type, 'other'),
                    'attachment_file': self.attachment_file,
                    'attachment_filename': self.attachment_filename or f"{self.name}.pdf",
                    'author_id': self.leader_id.id,
                    'course_id': self.target_course_id.id or False,
                    'curriculum_id': self.target_curriculum_id.id or False,
                    'year': acc_year,
                    'security_level': 'internal',
                    'review_state': 'pending_review',
                    'source_model': self._name,
                    'source_id': self.id,
                })

        # ---------------------------------------------------------------------
        # 3. ĐẨY VÀO LÝ LỊCH KHOA HỌC 15 MỤC (faculty.lecturer)
        # ---------------------------------------------------------------------
        # Thu thập danh sách giảng viên tham gia (Leader + Participants, loại trừ attendee)
        all_lecturers = self.participant_ids.filtered(lambda p: p.role != 'attendee').mapped('lecturer_id')
        if self.leader_id and self.leader_id not in all_lecturers:
            all_lecturers |= self.leader_id

        authors_str = ', '.join(all_lecturers.mapped('name')) or self.leader_id.name

        # 3.1. Bài báo (WoS/Scopus, Trong nước), Sách, Tham luận -> Mục 10 (Công trình đã công bố)
        if self.research_type in ('article_wos_scopus', 'article_domestic', 'conference_paper', 'book'):
            pub_type_val = 'national_journal'
            if self.research_type == 'article_wos_scopus':
                pub_type_val = 'wos_scopus'
            elif self.research_type == 'conference_paper':
                pub_type_val = 'conference'
            elif self.research_type == 'book':
                pub_type_val = 'national_journal'

            # Dọn dẹp publication của giảng viên không còn tham gia
            obsolete_pubs = Publication.search([
                ('source_research_id', '=', self.id),
                ('lecturer_id', 'not in', all_lecturers.ids),
            ])
            if obsolete_pubs:
                obsolete_pubs.unlink()

            for lecturer in all_lecturers:
                # Chống tạo trùng: ưu tiên tìm theo nguồn NCKH gốc trước, sau đó mới tìm theo (lecturer, tên CT, năm)
                dup_pubs = Publication.search([
                    ('source_research_id', '=', self.id),
                    ('lecturer_id', '=', lecturer.id),
                ])
                if not dup_pubs:
                    dup_pubs = Publication.search([
                        ('lecturer_id', '=', lecturer.id),
                        ('name', '=', self.name),
                        ('year', '=', acc_year),
                    ])

                pub_vals = {
                    'lecturer_id': lecturer.id,
                    'name': self.name,
                    'authors': authors_str,
                    'journal': self.publication_info or ('Tạp chí / Hội thảo Khoa học' if self.research_type != 'book' else 'Nhà xuất bản'),
                    'year': acc_year,
                    'pub_type': pub_type_val,
                    'impact_factor_rank': 'WoS/Scopus' if self.research_type == 'article_wos_scopus' else '',
                    'source_research_id': self.id,
                }
                if dup_pubs:
                    dup_pubs[0].write(pub_vals)
                    if len(dup_pubs) > 1:
                        dup_pubs[1:].unlink()
                else:
                    pub_vals['is_top_selected'] = False
                    Publication.create(pub_vals)
        else:
            old_pubs = Publication.search([('source_research_id', '=', self.id)])
            if old_pubs:
                old_pubs.unlink()

        # 3.2. Đề tài NCKH, Sáng kiến -> Mục 11 hoặc 13 (Nhiệm vụ KH&CN hoặc SHTT & Thực tiễn)
        if self.research_type in ('project_level', 'project_theory', 'initiative'):
            resume_type = 'project' if self.research_type in ('project_level', 'project_theory') else 'ip'
            inst_label = dict(self._fields['project_scope'].selection).get(self.project_scope, 'Trường Đại học') if self.research_type == 'project_level' else 'Cơ sở Khoa / Đơn vị'
            grade_label = dict(self._fields['acceptance_grade'].selection).get(self.acceptance_grade, 'Đã nghiệm thu')

            start_yr = self.start_date.strftime('%Y') if self.start_date else str(acc_year)
            period_str = f"{start_yr} - {acc_year}"

            active_participants = self.participant_ids.filtered(lambda p: p.role != 'attendee')
            active_lecturers = active_participants.mapped('lecturer_id')

            # Dọn dẹp resume line của giảng viên không còn tham gia
            obsolete_resumes = ResumeLine.search([
                ('source_research_id', '=', self.id),
                ('lecturer_id', 'not in', active_lecturers.ids),
            ])
            if obsolete_resumes:
                obsolete_resumes.unlink()

            for p in active_participants:
                lecturer = p.lecturer_id
                role_label = dict(p._fields['role'].selection).get(p.role, 'Thành viên')
                dup_resumes = ResumeLine.search([
                    ('source_research_id', '=', self.id),
                    ('lecturer_id', '=', lecturer.id),
                ])
                if not dup_resumes:
                    dup_resumes = ResumeLine.search([
                        ('lecturer_id', '=', lecturer.id),
                        ('name', '=', self.name),
                        ('type', '=', resume_type),
                    ])

                resume_vals = {
                    'lecturer_id': lecturer.id,
                    'type': resume_type,
                    'period': period_str,
                    'institution': inst_label,
                    'name': self.name,
                    'role': role_label,
                    'result': f"{grade_label} (Mã: {self.code or 'Đang cập nhật'})",
                    'source_research_id': self.id,
                }
                if dup_resumes:
                    dup_resumes[0].write(resume_vals)
                    if len(dup_resumes) > 1:
                        dup_resumes[1:].unlink()
                else:
                    ResumeLine.create(resume_vals)
        else:
            old_resumes = ResumeLine.search([('source_research_id', '=', self.id)])
            if old_resumes:
                old_resumes.unlink()

        self.state = 'approved'
        self.message_post(body=_("Đã nghiệm thu và phê duyệt công trình NCKH. Hệ thống đã tự động kết chuyển Sổ cái giờ chuẩn, đồng bộ Trụ cột Giảng dạy và cập nhật Lý lịch Khoa học."))
        return True


class FacultyResearchParticipant(models.Model):
    _name = 'faculty.research.participant'
    _description = 'Thành viên tham gia Công trình NCKH'
    _order = 'research_id, sequence, id'

    research_id = fields.Many2one('faculty.research.work', string='Công trình NCKH', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='STT', default=10)
    lecturer_id = fields.Many2one('faculty.lecturer', string='Giảng viên tham gia', required=True, index=True)

    role = fields.Selection([
        ('leader', 'Chủ nhiệm / Tác giả chính'),
        ('secretary', 'Thư ký khoa học'),
        ('organizer', 'Ban tổ chức hội thảo/tọa đàm'),
        ('chair', 'Chủ tọa / Đồng chủ tọa'),
        ('presenter', 'Báo cáo viên / Viết tham luận'),
        ('member', 'Thành viên thực hiện'),
        ('attendee', 'Đại biểu tham dự (Không tính giờ NCKH)'),
    ], string='Vai trò thực hiện', default='member', required=True)

    contribution_ratio = fields.Float(string='Tỷ lệ đóng góp (%)', default=100.0)
    standard_hours = fields.Float(string='Giờ NCKH quy đổi', default=0.0, required=True,
                                  help='Số giờ chuẩn NCKH được ghi nhận vào Ô Tiêu chí 2.')
    need_revision = fields.Boolean(string='Cần chỉnh sửa', default=False, tracking=True)
    notes = fields.Char(string='Ghi chú nhiệm vụ')

    _sql_constraints = [
        ('check_standard_hours_positive', 'CHECK(standard_hours >= 0)', 'Số giờ NCKH quy đổi phải >= 0!'),
        ('unique_lecturer_research', 'unique(research_id, lecturer_id, role)', 'Giảng viên đã có vai trò này trong công trình NCKH!'),
    ]

    @api.onchange('role')
    def _onchange_role_conference_seminar(self):
        """
        Quy tắc bắt buộc: Vai trò Đại biểu tham dự (role == 'attendee')
        luôn có standard_hours = 0.0 (không tính giờ NCKH), bất kể loại hình.
        """
        if self.role == 'attendee':
            self.standard_hours = 0.0

    @api.constrains('role', 'standard_hours')
    def _check_attendee_hours(self):
        """Ràng buộc cứng: Đại biểu tham dự không được tính giờ NCKH"""
        for rec in self:
            if rec.role == 'attendee' and rec.standard_hours > 0.0:
                raise ValidationError(_('Theo Quy định Khoa: Đại biểu chỉ tham dự KHÔNG được tính giờ NCKH (Giờ NCKH phải = 0)!'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('role') == 'attendee':
                vals['standard_hours'] = 0.0
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('role') == 'attendee':
            vals['standard_hours'] = 0.0
        elif 'standard_hours' in vals:
            for rec in self:
                if rec.role == 'attendee':
                    vals = dict(vals, standard_hours=0.0)
                    break
        return super().write(vals)

