# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from datetime import date


@tagged('post_install', '-at_install', 'workload_ledger')
class TestWorkloadLedger(TransactionCase):
    """
    Kiểm tra tự động 4 kịch bản toán học (A, B, a, b, C, c, m, n, o)
    theo quy chuẩn Mục 3 trong .agent/rules.md và mô hình Sổ cái & Cân đối giờ:
      A: Định mức giờ giảng dạy sau miễn giảm (net_teaching_quota)
      B = 0.5 * A: Định mức lên lớp tối thiểu (min_classroom_quota)
      b: Giờ lên lớp thực tế (actual_classroom_hours, teaching_branch='direct')
      a = b + giờ quy đổi GD khác: Tổng số giờ giảng đạt được trong năm (total_teaching_hours)
      C: Định mức NCKH sau miễn giảm (net_research_quota)
      c: Giờ NCKH quy đổi thực tế (actual_research_hours)
      m = max(0, a - A): Giờ giảng vượt định mức ban đầu
      n = max(0, b - B): Giờ lên lớp thừa so với mốc 50% định mức
      o = max(0, c - C): Giờ NCKH vượt định mức ban đầu
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Thiết lập cấu hình hệ số bù trừ và đơn giá giờ vượt trong ir.config_parameter
        ICP = cls.env['ir.config_parameter'].sudo()
        def _set_val(key, val):
            if hasattr(ICP, 'set_float'):
                ICP.set_float(key, float(val))
            elif hasattr(ICP, 'set_str'):
                ICP.set_str(key, str(val))
            elif hasattr(ICP, 'set_param'):
                ICP.set_param(key, str(val))
            else:
                record = ICP.search([('key', '=', key)], limit=1)
                if record:
                    record.value = str(val)
                else:
                    ICP.create({'key': key, 'value': str(val)})

        _set_val('faculty_work_mgmt.rate_t_to_r', 1.0)
        _set_val('faculty_work_mgmt.rate_r_to_t', 1.0)
        _set_val('faculty_work_mgmt.overtime_teaching_rate', 150000.0)

        # 1. Tạo Năm học kiểm thử (2025 - 2026)
        cls.academic_year = cls.env['faculty.academic.year'].create({
            'name': '2025 - 2026',
            'code': '2025-2026',
            'date_start': date(2025, 9, 1),
            'date_end': date(2026, 8, 31),
            'is_current': True,
        })

        # 2. Tạo Bảng cấu hình định mức chức danh chuẩn: A=300 (Giảng dạy), C=200 (NCKH)
        cls.title_norm = cls.env['faculty.title.norm'].create({
            'name': 'Giảng viên Chuẩn Kiểm thử',
            'code': 'GV_TEST_NORM',
            'academic_rank': 'giang_vien',
            'teaching_norm': 300.0,
            'research_norm': 200.0,
            'other_norm': 100.0,
        })

    def _create_lecturer(self, code, name):
        """Hàm hỗ trợ tạo hồ sơ Giảng viên gắn với Năm học và Định mức chuẩn"""
        return self.env['faculty.lecturer'].create({
            'name': name,
            'lecturer_code': code,
            'academic_rank': 'giang_vien',
            'title_norm_id': self.title_norm.id,
            'active_academic_year_id': self.academic_year.id,
        })

    def _add_ledger_hour(self, lecturer, category, hours, teaching_branch='direct', activity_type=None):
        """Hàm hỗ trợ tạo bút toán Sổ cái giờ chuẩn đã ghi sổ (posted)"""
        if not activity_type:
            if category == 'teaching':
                activity_type = 'lecture' if teaching_branch == 'direct' else 'exam_grading'
            elif category == 'research':
                activity_type = 'research_paper'
            else:
                activity_type = 'faculty_meeting'

        return self.env['faculty.hour.ledger'].create({
            'lecturer_id': lecturer.id,
            'academic_year_id': self.academic_year.id,
            'category': category,
            'activity_type': activity_type,
            'teaching_branch': teaching_branch if category == 'teaching' else False,
            'standard_hours': hours,
            'state': 'posted',
            'name': f'Ghi sổ {category} - {hours} giờ',
        })

    def test_scenario_1_overtime_paid(self):
        """
        KỊCH BẢN 1:
        A = 300, B = 150, b = 200, a = 375 -> m = 75, n = 50.
        Đủ NCKH (c = 200 >= C = 200) -> Hoàn thành nhiệm vụ và Tính tiền vượt giờ cho n = 50.
        Thành tiền = 50 * 150.000 = 7.500.000 VNĐ.
        """
        lec = self._create_lecturer('GV_KB1', 'Giảng viên KB 1')

        # Giờ lên lớp trực tiếp b = 200
        self._add_ledger_hour(lec, 'teaching', 200.0, teaching_branch='direct', activity_type='lecture')
        # Giờ quy đổi GD khác = 175 -> Tổng giờ giảng a = 200 + 175 = 375
        self._add_ledger_hour(lec, 'teaching', 175.0, teaching_branch='converted', activity_type='exam_grading')
        # Đủ giờ NCKH: c = 200 >= C = 200
        self._add_ledger_hour(lec, 'research', 200.0, activity_type='research_paper')

        balance = self.env['faculty.workload.balance'].create({
            'lecturer_id': lec.id,
            'academic_year_id': self.academic_year.id,
        })

        # Kiểm tra các biến đầu vào và định mức
        self.assertEqual(balance.net_teaching_quota, 300.0, "Định mức giảng dạy A phải là 300")
        self.assertEqual(balance.min_classroom_quota, 150.0, "Định mức lên lớp tối thiểu B phải là 150")
        self.assertEqual(balance.actual_classroom_hours, 200.0, "Giờ lên lớp thực tế b phải là 200")
        self.assertEqual(balance.other_teaching_hours, 175.0, "Giờ quy đổi GD khác phải là 175")
        self.assertEqual(balance.total_teaching_hours, 375.0, "Tổng giờ giảng a = b + khác phải là 375")
        self.assertEqual(balance.net_research_quota, 200.0, "Định mức NCKH C phải là 200")
        self.assertEqual(balance.actual_research_hours, 200.0, "Giờ NCKH thực tế c phải là 200")

        # Kiểm tra biến chênh lệch
        self.assertEqual(balance.m_excess_teaching, 75.0, "m = max(0, a - A) = 375 - 300 = 75")
        self.assertEqual(balance.n_overtime_classroom, 50.0, "n = max(0, b - B) = 200 - 150 = 50")
        self.assertEqual(balance.o_excess_research, 0.0, "o = max(0, c - C) = 0")

        # Không cần bù trừ
        self.assertEqual(balance.teaching_offset, 0.0, "Không trích m vì c >= C")
        self.assertEqual(balance.final_teaching_hours, 375.0, "a_sau phải giữ nguyên 375")
        self.assertEqual(balance.final_research_hours, 200.0, "c_sau phải giữ nguyên 200")

        # Kết luận hoàn thành & tính tiền
        self.assertTrue(balance.is_teaching_passed, "Đạt giờ giảng dạy")
        self.assertTrue(balance.is_research_passed, "Đạt giờ NCKH")
        self.assertTrue(balance.is_completed, "Hoàn thành nhiệm vụ")
        self.assertEqual(balance.result_status, 'completed')
        self.assertEqual(balance.overtime_payment_amount, 50.0 * 150000.0, "Thành tiền = n * đơn giá = 50 * 150.000 = 7.500.000")

    def test_scenario_2_completed_zero_payment(self):
        """
        KỊCH BẢN 2:
        A = 300, B = 150, b = 100, a = 301 -> m = 1, n = 0.
        Đủ NCKH (c = 200 >= C = 200) -> Hoàn thành định mức nhưng Thành tiền = 0đ (do b < B nên n = 0).
        """
        lec = self._create_lecturer('GV_KB2', 'Giảng viên KB 2')

        # Giờ lên lớp trực tiếp b = 100 (< B = 150)
        self._add_ledger_hour(lec, 'teaching', 100.0, teaching_branch='direct', activity_type='lecture')
        # Giờ quy đổi GD khác = 201 -> Tổng giờ giảng a = 100 + 201 = 301 (> A = 300)
        self._add_ledger_hour(lec, 'teaching', 201.0, teaching_branch='converted', activity_type='exam_grading')
        # Đủ giờ NCKH: c = 200 >= C = 200
        self._add_ledger_hour(lec, 'research', 200.0, activity_type='research_paper')

        balance = self.env['faculty.workload.balance'].create({
            'lecturer_id': lec.id,
            'academic_year_id': self.academic_year.id,
        })

        self.assertEqual(balance.actual_classroom_hours, 100.0)
        self.assertEqual(balance.total_teaching_hours, 301.0)
        self.assertEqual(balance.m_excess_teaching, 1.0, "m = max(0, 301 - 300) = 1")
        self.assertEqual(balance.n_overtime_classroom, 0.0, "n = max(0, 100 - 150) = 0")
        self.assertTrue(balance.is_completed, "Hoàn thành nhiệm vụ vì a >= A và c >= C")
        self.assertEqual(balance.result_status, 'completed')
        self.assertEqual(balance.overtime_payment_amount, 0.0, "Thành tiền phải bằng 0 do n = 0")

    def test_scenario_3_teaching_compensate_research(self):
        """
        KỊCH BẢN 3:
        A = 300, B = 150, b = 220, a = 320 -> m = 20, n = 70.
        - Khi c < C (nhưng c >= 0.25*C), đem m = 20 bù đủ c_sau = C và a_sau = 300 >= A -> Nhận đủ tiền 70 giờ (10.500.000 VNĐ).
        - Khi đem hết m = 20 bù nhưng vẫn không đủ C (c_sau < C) -> Ghi nhận n = 70 nhưng Thành tiền = 0đ.
        """
        # --- Trường hợp 3a: Bù ĐỦ C ---
        lec_3a = self._create_lecturer('GV_KB3A', 'Giảng viên KB 3A (Bù đủ)')
        self._add_ledger_hour(lec_3a, 'teaching', 220.0, teaching_branch='direct', activity_type='lecture')
        self._add_ledger_hour(lec_3a, 'teaching', 100.0, teaching_branch='converted', activity_type='exam_grading')
        # C = 200, c = 180 (thiếu 20 giờ). Sàn 25% * 200 = 50 -> 180 >= 50 (Thỏa mãn sàn)
        self._add_ledger_hour(lec_3a, 'research', 180.0, activity_type='research_paper')

        balance_3a = self.env['faculty.workload.balance'].create({
            'lecturer_id': lec_3a.id,
            'academic_year_id': self.academic_year.id,
        })

        self.assertEqual(balance_3a.m_excess_teaching, 20.0, "m = 320 - 300 = 20")
        self.assertEqual(balance_3a.n_overtime_classroom, 70.0, "n = 220 - 150 = 70")
        self.assertTrue(balance_3a.teaching_to_research_floor_met, "Đạt sàn c >= 0.25*C")
        self.assertEqual(balance_3a.teaching_offset, 20.0, "Trích đủ m = 20 để bù thiếu hụt 20 giờ NCKH")
        self.assertEqual(balance_3a.final_research_hours, 200.0, "c_sau = 180 + 20 = 200 = C")
        self.assertEqual(balance_3a.final_teaching_hours, 300.0, "a_sau = 320 - 20 = 300 = A")
        self.assertTrue(balance_3a.is_completed, "Hoàn thành cả 2 nhiệm vụ sau khi bù trừ")
        self.assertEqual(balance_3a.result_status, 'completed')
        self.assertEqual(balance_3a.overtime_payment_amount, 70.0 * 150000.0, "Được nhận đủ tiền 70 giờ = 10.500.000 VNĐ")

        # --- Trường hợp 3b: Bù KHÔNG ĐỦ C ---
        lec_3b = self._create_lecturer('GV_KB3B', 'Giảng viên KB 3B (Bù không đủ)')
        self._add_ledger_hour(lec_3b, 'teaching', 220.0, teaching_branch='direct', activity_type='lecture')
        self._add_ledger_hour(lec_3b, 'teaching', 100.0, teaching_branch='converted', activity_type='exam_grading')
        # C = 200, c = 170 (thiếu 30 giờ). Sàn 50h thỏa mãn (170 >= 50), nhưng m chỉ có 20 không đủ bù 30.
        self._add_ledger_hour(lec_3b, 'research', 170.0, activity_type='research_paper')

        balance_3b = self.env['faculty.workload.balance'].create({
            'lecturer_id': lec_3b.id,
            'academic_year_id': self.academic_year.id,
        })

        self.assertEqual(balance_3b.m_excess_teaching, 20.0)
        self.assertEqual(balance_3b.n_overtime_classroom, 70.0, "n = 70 vẫn được ghi nhận nguyên vẹn")
        self.assertEqual(balance_3b.teaching_offset, 20.0, "Dùng hết 20 giờ m")
        self.assertEqual(balance_3b.final_research_hours, 190.0, "c_sau = 170 + 20 = 190 < C (200)")
        self.assertEqual(balance_3b.final_teaching_hours, 300.0, "a_sau = 320 - 20 = 300 >= A")
        self.assertFalse(balance_3b.is_research_passed, "Không đạt tiêu chuẩn NCKH")
        self.assertFalse(balance_3b.is_completed, "Không hoàn thành nhiệm vụ do thiếu NCKH")
        self.assertEqual(balance_3b.result_status, 'fail_research')
        self.assertEqual(balance_3b.overtime_payment_amount, 0.0, "Bù không đủ C thì Thành tiền = 0đ")

    def test_scenario_4_research_compensate_teaching(self):
        """
        KỊCH BẢN 4:
        A = 300, B = 150, b = 200, a = 200 < A (n = 50).
        Thiếu giờ GD (300 - 200 = 100), nhưng NCKH dư o lớn (C = 200, c = 350 -> o = 150).
        Trích o = 100 bù sang giúp a_sau = 300 = A, c_sau = 250 >= C.
        -> Hoàn thành nhiệm vụ và được tính tiền vượt giờ cho n = 50 (7.500.000 VNĐ).
        """
        lec = self._create_lecturer('GV_KB4', 'Giảng viên KB 4 (NCKH bù GD)')

        # Giờ lên lớp b = 200, không có giờ GD khác -> a = 200 (< A = 300), n = 200 - 150 = 50
        self._add_ledger_hour(lec, 'teaching', 200.0, teaching_branch='direct', activity_type='lecture')
        # NCKH: C = 200, c = 350 -> o = 350 - 200 = 150
        self._add_ledger_hour(lec, 'research', 350.0, activity_type='research_paper')

        balance = self.env['faculty.workload.balance'].create({
            'lecturer_id': lec.id,
            'academic_year_id': self.academic_year.id,
        })

        self.assertEqual(balance.actual_classroom_hours, 200.0)
        self.assertEqual(balance.total_teaching_hours, 200.0, "a = 200 < A = 300")
        self.assertEqual(balance.n_overtime_classroom, 50.0, "n = max(0, 200 - 150) = 50")
        self.assertEqual(balance.o_excess_research, 150.0, "o = max(0, 350 - 200) = 150")

        # Chiều NCKH -> GD: Cần bù deficit_a = 300 - 200 = 100
        self.assertEqual(balance.research_offset, 100.0, "Trích đúng 100 giờ từ o bù sang giảng dạy")
        self.assertEqual(balance.final_teaching_hours, 300.0, "a_sau = 200 + 100 = 300 = A")
        self.assertEqual(balance.final_research_hours, 250.0, "c_sau = 350 - 100 = 250 >= C")

        # Kết luận hoàn thành & tính tiền
        self.assertTrue(balance.is_teaching_passed, "Đạt giờ giảng sau bù trừ")
        self.assertTrue(balance.is_research_passed, "Đạt giờ NCKH sau bù trừ")
        self.assertTrue(balance.is_completed, "Hoàn thành nhiệm vụ")
        self.assertEqual(balance.result_status, 'completed')
        self.assertEqual(balance.overtime_payment_amount, 50.0 * 150000.0, "Được tính tiền cho n = 50: 50 * 150.000 = 7.500.000 VNĐ")

