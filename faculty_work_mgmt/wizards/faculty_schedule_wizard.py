# -*- coding: utf-8 -*-
"""Wizard definitions for Faculty Schedule Suggestion and Exam Semester Report.
"""

from odoo import api, fields, models
from datetime import datetime


class FacultyScheduleSuggestionWizard(models.TransientModel):
    _name = "faculty.schedule.suggestion.wizard"
    _description = "Wizard Gợi ý lịch trống giảng viên"

    date_from = fields.Date(string="Từ ngày", required=True)
    date_to = fields.Date(string="Đến ngày", required=True)
    course_id = fields.Many2one(
        "faculty.course",
        string="Môn học",
        required=True,
    )
    suggestion_line_ids = fields.One2many(
        "faculty.schedule.suggestion.line",
        "wizard_id",
        string="Kết quả gợi ý",
        readonly=True,
    )

    def action_find_free_slots(self):
        """Tìm các buổi sáng/chiều mà giảng viên của môn học hoàn toàn trống trong khoảng ngày.
        Kết quả được lưu vào `suggestion_line_ids` và trả về view dạng tree.
        """
        self.suggestion_line_ids.unlink()
        # Lấy danh sách giảng viên thuộc môn học (giả sử có trường many2many `teacher_ids` trên faculty.course)
        teachers = self.course_id.teacher_ids
        # Tìm các buổi học và thi trong khoảng thời gian
        Session = self.env["faculty.teaching.session"]
        Exam = self.env["faculty.exam.assignment"]
        sessions = Session.search(["&", ("date", ">=", self.date_from), ("date", "<=", self.date_to)])
        exams = Exam.search(["&", ("date", ">=", self.date_from), ("date", "<=", self.date_to)])
        # Tạo dictionary {teacher_id: set of occupied datetime (date + period)}
        occupied = {t.id: set() for t in teachers}
        for rec in sessions:
            for t in rec.teacher_ids:
                occupied[t.id].add((rec.date, rec.period))  # period expected field 'period' (Sáng/Chiều)
        for rec in exams:
            for t in rec.teacher_ids:
                occupied[t.id].add((rec.date, rec.period))
        # Xác định các slot trống (giả sử ngày có 2 period: 'Sáng', 'Chiều')
        free_lines = []
        for single_date in fields.Date.range(self.date_from, self.date_to):
            for period in ("Sáng", "Chiều"):
                for teacher in teachers:
                    if (single_date, period) not in occupied.get(teacher.id, set()):
                        free_lines.append((0, 0, {
                            "teacher_id": teacher.id,
                            "date": single_date,
                            "period": period,
                        }))
        self.suggestion_line_ids = free_lines
        # Trả về action hiển thị tree view
        return {
            "type": "ir.actions.act_window",
            "name": "Kết quả gợi ý lịch trống",
            "res_model": "faculty.schedule.suggestion.line",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("wizard_id", "=", self.id)],
        }


class FacultyScheduleSuggestionLine(models.TransientModel):
    _name = "faculty.schedule.suggestion.line"
    _description = "Dòng gợi ý lịch trống"

    wizard_id = fields.Many2one(
        "faculty.schedule.suggestion.wizard",
        string="Wizard",
        ondelete="cascade",
    )
    teacher_id = fields.Many2one("res.users", string="Giảng viên")
    date = fields.Date(string="Ngày")
    period = fields.Selection([
        ("Sáng", "Sáng"),
        ("Chiều", "Chiều"),
    ], string="Buổi")


class FacultyExamReportWizard(models.TransientModel):
    _name = "faculty.exam.report.wizard"
    _description = "Wizard xuất danh sách coi thi, chấm thi theo lớp và học phần trong học kỳ"

    academic_year_id = fields.Many2one(
        "faculty.academic.year",
        string="Năm học",
        required=True,
    )
    semester_id = fields.Many2one(
        "faculty.semester",
        string="Học kỳ",
        required=True,
    )
    student_class_id = fields.Many2one(
        "faculty.student.class",
        string="Lớp",
        required=True,
    )

    def action_generate_report(self):
        """Tạo báo cáo QWeb PDF.
        Các tham số lọc được truyền vào context để template truy vấn.
        """
        report_action = self.env.ref("faculty_work_mgmt.action_faculty_exam_semester_report")
        return report_action.report_action(self, data={
            "academic_year_id": self.academic_year_id.id,
            "semester_id": self.semester_id.id,
            "student_class_id": self.student_class_id.id,
        })

