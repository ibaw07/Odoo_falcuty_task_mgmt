# -*- coding: utf-8 -*-
"""Wizard definitions for Faculty Schedule Suggestion and Exam Semester Report.
"""

from odoo import api, fields, models
from datetime import datetime, timedelta


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
        Kết quả được lưu vào `suggestion_line_ids` và trả về view dạng list.
        """
        self.suggestion_line_ids.unlink()
        teachers = self.course_id.lecturer_ids
        if not teachers and self.course_id.head_lecturer_id:
            teachers = self.course_id.head_lecturer_id
        Session = self.env["faculty.teaching.session"]
        Exam = self.env["faculty.exam.assignment"]
        sessions = Session.search([("date", ">=", self.date_from), ("date", "<=", self.date_to)])
        exams = Exam.search([
            ("class_course_id.exam_date", "!=", False),
            ("class_course_id.exam_date", ">=", self.date_from),
            ("class_course_id.exam_date", "<=", self.date_to),
        ])
        occupied = {t.id: set() for t in teachers}
        for rec in sessions:
            lec = rec.actual_lecturer_id or rec.lecturer_id
            if lec and lec.id in occupied and rec.date:
                period_str = 'Sáng' if rec.session_time == 'morning' else 'Chiều'
                occupied[lec.id].add((rec.date, period_str))
        for rec in exams:
            lec = rec.lecturer_id
            if lec and lec.id in occupied and rec.class_course_id.exam_date:
                period_str = 'Sáng' if rec.class_course_id.exam_session == 'morning' else 'Chiều'
                occupied[lec.id].add((rec.class_course_id.exam_date, period_str))
        free_lines = []
        cur_date = self.date_from
        while cur_date <= self.date_to:
            for period in ("Sáng", "Chiều"):
                for teacher in teachers:
                    if (cur_date, period) not in occupied.get(teacher.id, set()):
                        free_lines.append((0, 0, {
                            "teacher_id": teacher.id,
                            "date": cur_date,
                            "period": period,
                        }))
            cur_date += timedelta(days=1)
        self.suggestion_line_ids = free_lines
        return {
            "type": "ir.actions.act_window",
            "name": "Kết quả gợi ý lịch trống",
            "res_model": "faculty.schedule.suggestion.line",
            "view_mode": "list,form",
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
    teacher_id = fields.Many2one("faculty.lecturer", string="Giảng viên")
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
        "faculty.academic.semester",
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

