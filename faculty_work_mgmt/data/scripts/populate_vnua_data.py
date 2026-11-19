# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import base64
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, r'C:\Program Files\Odoo 20.0.20260927\server')
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

def populate():
    config_file = r'C:\Program Files\Odoo 20.0.20260927\server\odoo.conf'
    odoo.tools.config.parse_config(['-c', config_file, '-d', 'Quantrikhoa'], setup_logging=False)
    
    registry = Registry('Quantrikhoa')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        today = date.today()
        print(f"=== BẮT ĐẦU KHỞI TẠO DỮ LIỆU KHOA KINH TẾ - HỌC VIỆN NÔNG NGHIỆP VIỆT NAM (Ngày: {today.strftime('%d/%m/%Y')}) ===")
        
        # 1. CẤU HÌNH THAM SỐ HỆ THỐNG (Hệ số bù trừ chéo & đơn giá giờ vượt)
        ICP = env['ir.config_parameter'].sudo()
        def _set_param(k, v):
            rec = ICP.search([('key', '=', k)], limit=1)
            if rec:
                rec.value = str(v)
            else:
                ICP.create({'key': k, 'value': str(v)})
        _set_param('faculty_work_mgmt.rate_t_to_r', '1.0')
        _set_param('faculty_work_mgmt.rate_r_to_t', '1.0')
        _set_param('faculty_work_mgmt.overtime_teaching_rate', '150000.0')
        print("[1/15] Đã thiết lập tham số hệ thống: rate_t_to_r=1.0, rate_r_to_t=1.0, overtime_rate=150,000 VNĐ.")

        # 2. BẬC LƯƠNG VIÊN CHỨC GIẢNG DẠY (16 Bậc)
        RankConfig = env['faculty.rank.config']
        rank_data = [
            (1, 2.34, 36), (2, 2.67, 36), (3, 3.00, 36), (4, 3.33, 36),
            (5, 3.66, 36), (6, 3.99, 36), (7, 4.32, 36), (8, 4.65, 36),
            (9, 4.98, 36), (10, 5.31, 36), (11, 5.64, 36), (12, 5.97, 36),
            (13, 6.30, 36), (14, 6.63, 36), (15, 6.96, 36), (16, 7.29, 36)
        ]
        rank_objs = {}
        for seq, coef, interval in rank_data:
            r = RankConfig.search([('sequence', '=', seq)], limit=1)
            if not r:
                r = RankConfig.create({
                    'sequence': seq,
                    'salary_coefficient': coef,
                    'promotion_interval_months': interval,
                })
            else:
                r.write({'salary_coefficient': coef, 'promotion_interval_months': interval})
            rank_objs[seq] = r
        print("[2/15] Đã khởi tạo 16 Bậc lương viên chức giảng dạy (Bậc 1-16).")

        # 3. ĐỊNH MỨC THEO CHỨC DANH (faculty.title.norm)
        TitleNorm = env['faculty.title.norm']
        title_norms_data = [
            ('Giáo sư (GS)', 'GS', 'giang_vien_cao_cap', 'prof', 'doctor', 340.0, 280.0, 100.0),
            ('Phó Giáo sư (PGS)', 'PGS', 'giang_vien_cao_cap', 'assoc_prof', 'doctor', 320.0, 240.0, 100.0),
            ('Giảng viên chính (GVC)', 'GVC', 'giang_vien_chinh', 'none', 'doctor', 300.0, 200.0, 100.0),
            ('Giảng viên (GV)', 'GV', 'giang_vien', 'none', 'master', 280.0, 160.0, 100.0),
            ('Giảng viên tập sự / Trợ giảng', 'GVTS', 'tro_giang', 'none', 'bachelor', 200.0, 100.0, 80.0),
        ]
        title_norm_objs = {}
        for name, code, rank_val, title_val, deg_val, t_norm, r_norm, o_norm in title_norms_data:
            tn = TitleNorm.search([('code', '=', code)], limit=1)
            vals = {
                'name': name,
                'code': code,
                'academic_rank': rank_val,
                'academic_title': title_val,
                'academic_degree': deg_val,
                'teaching_norm': t_norm,
                'research_norm': r_norm,
                'other_norm': o_norm,
            }
            if not tn:
                tn = TitleNorm.create(vals)
            else:
                tn.write(vals)
            title_norm_objs[code] = tn
        print("[3/15] Đã khởi tạo Định mức 3 tiêu chuẩn chức danh: GS, PGS, GVC, GV, GVTS.")

        # 4. NĂM HỌC & HỌC KỲ (faculty.academic.year, faculty.academic.semester)
        Year = env['faculty.academic.year']
        Sem = env['faculty.academic.semester']
        
        y2526 = Year.search([('code', '=', '2025-2026')], limit=1)
        if not y2526:
            y2526 = Year.create({
                'name': '2025 - 2026',
                'code': '2025-2026',
                'date_start': date(2025, 9, 1),
                'date_end': date(2026, 8, 31),
                'is_current': True,
            })
        else:
            y2526.write({'is_current': True, 'date_start': date(2025, 9, 1), 'date_end': date(2026, 8, 31)})

        y2425 = Year.search([('code', '=', '2024-2025')], limit=1)
        if not y2425:
            y2425 = Year.create({
                'name': '2024 - 2025',
                'code': '2024-2025',
                'date_start': date(2024, 9, 1),
                'date_end': date(2025, 8, 31),
                'is_current': False,
            })

        sem1 = Sem.search([('academic_year_id', '=', y2526.id), ('code', '=', 'HK1-2526')], limit=1)
        if not sem1:
            sem1 = Sem.create({
                'name': 'Học kỳ 1 (2025 - 2026)',
                'code': 'HK1-2526',
                'academic_year_id': y2526.id,
                'date_start': date(2025, 9, 1),
                'date_end': date(2026, 1, 15),
                'is_current': False,
            })

        sem2 = Sem.search([('academic_year_id', '=', y2526.id), ('code', '=', 'HK2-2526')], limit=1)
        if not sem2:
            sem2 = Sem.create({
                'name': 'Học kỳ 2 (2025 - 2026)',
                'code': 'HK2-2526',
                'academic_year_id': y2526.id,
                'date_start': date(2026, 1, 16),
                'date_end': date(2026, 6, 15),
                'is_current': True,
            })
        print("[4/15] Đã khởi tạo Năm học 2025-2026 (Hiện hành) và Học kỳ 1, 2.")

        # 5. BẢNG QUY CHUẨN ĐỘNG & QUY TẮC KHẢO THÍ (faculty.norm.config, faculty.exam.grading.rule)
        NormConf = env['faculty.norm.config']
        nc = NormConf.search([('active', '=', True)], limit=1)
        if not nc:
            nc = NormConf.create({
                'name': 'Bảng Quy chuẩn Giờ chuẩn Khoa Kinh tế - HVNN',
                'academic_year_id': y2526.id,
                'active': True,
                'large_class_threshold': 40,
                'large_class_coeff': 1.2,
                'proctoring_rate': 1.5,
                'grading_rate_essay': 0.05,
                'grading_rate_multiple_choice': 0.02,
                'grading_rate_report': 0.08,
                'grading_rate_oral': 0.1,
            })

        Rule = env['faculty.exam.grading.rule']
        rules_data = [
            (1, 1, 39, 'fixed', 5.0, 'Lớp nhỏ dưới 40 bài: Chấm kiểm tra 5 bài'),
            (2, 40, 79, 'percent', 15.0, 'Lớp trung bình 40-79 bài: Chấm kiểm tra 15%'),
            (3, 80, 9999, 'percent', 10.0, 'Lớp đông từ 80 bài trở lên: Chấm kiểm tra 10%'),
        ]
        for seq, mi, ma, a_type, a_val, notes in rules_data:
            r = Rule.search([('min_students', '=', mi), ('max_students', '=', ma)], limit=1)
            vals = {
                'sequence': seq,
                'min_students': mi,
                'max_students': ma,
                'audit_type': a_type,
                'audit_value': a_val,
                'notes': notes,
            }
            if not r:
                Rule.create(vals)
            else:
                r.write(vals)
        print("[5/15] Đã cấu hình Bảng quy chuẩn giờ chuẩn và Quy tắc khảo thí chấm kiểm tra động.")

        # 6. QUY ĐỊNH THANH TOÁN (faculty.payment.regulation)
        PayReg = env['faculty.payment.regulation']
        pr = PayReg.search([('document_number', '=', '125/QĐ-HVNN-KT')], limit=1)
        if not pr:
            pr = PayReg.create({
                'name': 'Quy định thanh toán chế độ Thực tập & Công tác thực tế Khoa Kinh tế',
                'document_number': '125/QĐ-HVNN-KT',
                'document_date': date(2025, 1, 1),
                'payment_category': 'internship',
            })
            PayLine = env['faculty.payment.regulation.line']
            pay_lines = [
                (10, 'Tiền công tác phí cán bộ hướng dẫn thực tế', 'ngày', 250000.0, 'Định mức 250.000đ/ngày/người'),
                (20, 'Thù lao quản lý và tổ chức đoàn thực tập', 'buổi', 300000.0, 'Hỗ trợ công tác tổ chức thực tế'),
                (30, 'Kinh phí hỗ trợ tài liệu học tập & khảo sát thực địa', 'bộ', 150000.0, 'In ấn tài liệu chuyên đề'),
                (40, 'Kinh phí thuê phương tiện đưa đón sinh viên thực tế', 'chuyến', 3500000.0, 'Xe 45 chỗ đưa đón'),
            ]
            for seq, name, unit, rate, f_desc in pay_lines:
                PayLine.create({
                    'regulation_id': pr.id,
                    'sequence': seq,
                    'name': name,
                    'unit': unit,
                    'standard_rate': rate,
                    'formula_desc': f_desc,
                })
        print("[6/15] Đã khởi tạo Quy định thanh toán công tác thực hành, thực tập thực tế.")

        # 7. DANH SÁCH GIẢNG VIÊN TIÊU BIỂU KHOA KINH TẾ (faculty.lecturer)
        Lec = env['faculty.lecturer']
        lecturers_data = [
            {
                'name': 'PGS.TS. Trần Đình Thao',
                'lecturer_code': 'GV_VNUA_01',
                'email': 'tdthao@vnua.edu.vn',
                'phone': '0912345678',
                'gender': 'male',
                'birth_date': today + timedelta(days=3), # Cảnh báo sinh nhật trong 3 ngày tới!
                'admin_position': 'truong_khoa',         # Trưởng khoa
                'academic_rank': 'giang_vien_cao_cap',   # GVCC
                'academic_title': 'assoc_prof',          # PGS
                'degree': 'doctor',                      # TS
                'rank_id': rank_objs[12].id,
                'rank_date': today - relativedelta(months=34, days=15), # 45 ngày nữa nâng bậc lương!
                'title_norm_id': title_norm_objs['PGS'].id,
                'active_academic_year_id': y2526.id,
                'hometown': 'Gia Lâm, Hà Nội',
                'foreign_languages': 'Tiếng Anh C1, Tiếng Pháp B1',
                'it_skills': 'R, Stata, Python, SPSS',
                'management_experience': 'Trưởng khoa Kinh tế (2020 - nay); Trưởng Bộ môn Kinh tế Nông nghiệp & Chính sách (2015 - 2020)',
            },
            {
                'name': 'TS. Nguyễn Thị Minh Hiền',
                'lecturer_code': 'GV_VNUA_02',
                'email': 'ntmhien@vnua.edu.vn',
                'phone': '0987654321',
                'gender': 'female',
                'birth_date': today + timedelta(days=6), # Cảnh báo sinh nhật trong 6 ngày tới!
                'admin_position': 'pho_khoa',            # Phó Trưởng khoa
                'academic_rank': 'giang_vien_chinh',     # GVC
                'academic_title': 'none',
                'degree': 'doctor',                      # TS
                'rank_id': rank_objs[8].id,
                'rank_date': today - relativedelta(months=34, days=20), # 40 ngày nữa nâng bậc lương!
                'title_norm_id': title_norm_objs['GVC'].id,
                'active_academic_year_id': y2526.id,
                'hometown': 'TP. Bắc Ninh, Bắc Ninh',
                'foreign_languages': 'Tiếng Anh IELTS 7.5',
                'it_skills': 'Stata, EViews, SPSS',
                'management_experience': 'Phó Trưởng khoa phụ trách NCKH & Hợp tác Quốc tế (2021 - nay)',
            },
            {
                'name': 'TS. Bùi Thị Nga',
                'lecturer_code': 'GV_VNUA_03',
                'email': 'btnga@vnua.edu.vn',
                'phone': '0903123456',
                'gender': 'female',
                'birth_date': date(1982, 5, 12),
                'admin_position': 'can_bo',
                'academic_rank': 'giang_vien_chinh',     # GVC
                'academic_title': 'none',
                'degree': 'doctor',                      # TS
                'rank_id': rank_objs[6].id,
                'rank_date': today - relativedelta(months=18),
                'title_norm_id': title_norm_objs['GVC'].id,
                'active_academic_year_id': y2526.id,
                'hometown': 'Nam Sách, Hải Dương',
                'foreign_languages': 'Tiếng Anh B2',
                'it_skills': 'R, Python, Stata, SQL',
                'management_experience': 'Trưởng Bộ môn Phân tích Kinh tế & Kinh tế lượng (2022 - nay)',
            },
            {
                'name': 'ThS. Vũ Ngọc Huyên',
                'lecturer_code': 'GV_VNUA_04',
                'email': 'vnhuyen@vnua.edu.vn',
                'phone': '0915998877',
                'gender': 'male',
                'birth_date': date(1989, 11, 20),
                'admin_position': 'can_bo',
                'academic_rank': 'giang_vien',             # GV
                'academic_title': 'none',
                'degree': 'master',
                'rank_id': rank_objs[4].id,
                'rank_date': today - relativedelta(months=24),
                'title_norm_id': title_norm_objs['GV'].id,
                'active_academic_year_id': y2526.id,
                'hometown': 'Hưng Yên',
                'foreign_languages': 'Tiếng Anh B2',
                'it_skills': 'SPSS, MS Office Nâng cao',
                'management_experience': 'Bí thư Đoàn thanh niên Khoa Kinh tế, Trợ lý Quản lý Sinh viên',
            },
            {
                'name': 'ThS. Đỗ Thị Diệp',
                'lecturer_code': 'GV_VNUA_05',
                'email': 'dtdiep@vnua.edu.vn',
                'phone': '0977889900',
                'gender': 'female',
                'birth_date': date(1996, 8, 15),
                'admin_position': 'can_bo',
                'academic_rank': 'tro_giang',            # GV tập sự
                'academic_title': 'none',
                'degree': 'master',
                'rank_id': rank_objs[1].id,
                'rank_date': today - relativedelta(months=6),
                'title_norm_id': title_norm_objs['GVTS'].id,
                'active_academic_year_id': y2526.id,
                'hometown': 'Hà Nam',
                'foreign_languages': 'Tiếng Anh TOEIC 780',
                'it_skills': 'Excel, Power BI, Kế toán MISA',
                'management_experience': 'Giảng viên tập sự Bộ môn Kế toán - Tài chính Nông thôn',
            },
            {
                'name': 'ThS. Lê Hoàng Long',
                'lecturer_code': 'GV_VNUA_06',
                'email': 'lhlong@vnua.edu.vn',
                'phone': '0933445566',
                'gender': 'male',
                'birth_date': date(1990, 3, 25),
                'admin_position': 'can_bo',
                'academic_rank': 'giang_vien',             # GV đang đi học NCS
                'academic_title': 'none',
                'degree': 'master',
                'rank_id': rank_objs[3].id,
                'rank_date': today - relativedelta(months=12),
                'title_norm_id': title_norm_objs['GV'].id,
                'active_academic_year_id': y2526.id,
                'study_weeks': 22,                       # Đi học 22 tuần -> giảm 50%
                'hometown': 'Thái Bình',
                'foreign_languages': 'Tiếng Anh IELTS 6.5',
                'it_skills': 'Stata, R Studio',
                'management_experience': 'Nghiên cứu sinh chuyên ngành Kinh tế Nông nghiệp',
            },
        ]

        lecturer_objs = {}
        for l_data in lecturers_data:
            code = l_data['lecturer_code']
            lec = Lec.search([('lecturer_code', '=', code)], limit=1)
            if not lec:
                lec = Lec.create(l_data)
            else:
                lec.write(l_data)
            lecturer_objs[code] = lec
        print("[7/15] Đã khởi tạo 6 Giảng viên nòng cốt Khoa Kinh tế - HVNN (Kèm ngày sinh & ngày nâng bậc sắp đến).")

        # 8. BẢNG MIỄN GIẢM ĐỊNH MỨC THỦ CÔNG (faculty.norm.reduction)
        Reduction = env['faculty.norm.reduction']
        reductions_data = [
            (lecturer_objs['GV_VNUA_01'], 30.0, 'both', 'Kiêm nhiệm Trưởng khoa Kinh tế'),
            (lecturer_objs['GV_VNUA_02'], 20.0, 'both', 'Kiêm nhiệm Phó Trưởng khoa Kinh tế'),
            (lecturer_objs['GV_VNUA_03'], 30.0, 'both', 'Kiêm nhiệm Trưởng Bộ môn Phân tích KT & Kinh tế lượng'),
            (lecturer_objs['GV_VNUA_05'], 30.0, 'teaching', 'Giảng viên mới / tập sự trong năm đầu công tác'),
            (lecturer_objs['GV_VNUA_06'], 50.0, 'both', 'Cử đi học Nghiên cứu sinh tiến sĩ (22 tuần / 44 tuần)'),
        ]
        for l_rec, pct, sc, reason in reductions_data:
            exist_r = Reduction.search([
                ('lecturer_id', '=', l_rec.id),
                ('academic_year_id', '=', y2526.id),
                ('name', '=', reason),
            ], limit=1)
            if not exist_r:
                Reduction.create({
                    'lecturer_id': l_rec.id,
                    'academic_year_id': y2526.id,
                    'name': reason,
                    'percentage': pct,
                    'scope': sc,
                })
        print("[8/15] Đã cấu hình các dòng Miễn giảm định mức theo chức danh kiêm nhiệm và đi học.")

        # 9. CHƯƠNG TRÌNH ĐÀO TẠO & HỌC PHẦN (faculty.curriculum, faculty.course, faculty.course.syllabus)
        Curr = env['faculty.curriculum']
        Course = env['faculty.course']
        Syllabus = env['faculty.course.syllabus']

        curr_data = [
            ('Cử nhân Kinh tế Nông nghiệp', 'CTDT-KTNN', '7620115', 135.0, 4.0),
            ('Cử nhân Quản trị Kinh doanh Nông nghiệp', 'CTDT-QTKDNA', '7340101', 132.0, 4.0),
            ('Cử nhân Kinh tế Phát triển', 'CTDT-KTPT', '7310105', 130.0, 4.0),
        ]
        curr_objs = {}
        for c_name, c_code, c_moet, cr_cnt, dur in curr_data:
            c = Curr.search([('code', '=', c_code)], limit=1)
            if not c:
                c = Curr.create({
                    'name': c_name,
                    'code': c_code,
                    'total_credits': cr_cnt,
                    'state': 'approved',
                })
            curr_objs[c_code] = c

        courses_data = [
            ('Kinh tế Vi mô Nông nghiệp', 'KTNN101', curr_objs['CTDT-KTNN'].id, 3.0, 30.0, 15.0, lecturer_objs['GV_VNUA_01'].id, [lecturer_objs['GV_VNUA_01'].id, lecturer_objs['GV_VNUA_04'].id]),
            ('Kinh tế Nông nghiệp & Phát triển Nông thôn', 'KTNN201', curr_objs['CTDT-KTNN'].id, 3.0, 30.0, 15.0, lecturer_objs['GV_VNUA_01'].id, [lecturer_objs['GV_VNUA_01'].id]),
            ('Kinh tế lượng Ứng dụng trong Nông nghiệp', 'KTL202', curr_objs['CTDT-KTPT'].id, 3.0, 30.0, 15.0, lecturer_objs['GV_VNUA_03'].id, [lecturer_objs['GV_VNUA_03'].id]),
            ('Quản trị Chuỗi cung ứng Nông sản', 'QTKD301', curr_objs['CTDT-QTKDNA'].id, 3.0, 30.0, 15.0, lecturer_objs['GV_VNUA_02'].id, [lecturer_objs['GV_VNUA_02'].id, lecturer_objs['GV_VNUA_05'].id]),
            ('Marketing Nông sản & Thực phẩm', 'QTKD302', curr_objs['CTDT-QTKDNA'].id, 2.0, 20.0, 10.0, lecturer_objs['GV_VNUA_02'].id, [lecturer_objs['GV_VNUA_02'].id]),
            ('Thẩm định Dự án Đầu tư Nông nghiệp', 'KTNN305', curr_objs['CTDT-KTNN'].id, 3.0, 30.0, 15.0, lecturer_objs['GV_VNUA_01'].id, [lecturer_objs['GV_VNUA_01'].id]),
            ('Kinh tế Tuần hoàn & Nông nghiệp Sinh thái', 'KTNN401', curr_objs['CTDT-KTNN'].id, 2.0, 20.0, 10.0, lecturer_objs['GV_VNUA_03'].id, [lecturer_objs['GV_VNUA_03'].id, lecturer_objs['GV_VNUA_06'].id]),
        ]
        course_objs = {}
        for c_name, c_code, cur_id, cr_cnt, lec_h, prac_h, head_id, lecs in courses_data:
            cs = Course.search([('code', '=', c_code)], limit=1)
            c_vals = {
                'name': c_name,
                'code': c_code,
                'curriculum_id': cur_id,
                'credit_count': cr_cnt,
                'lecture_hours': lec_h,
                'practice_hours': prac_h,
                'head_lecturer_id': head_id,
                'lecturer_ids': [(6, 0, lecs)],
            }
            if not cs:
                cs = Course.create(c_vals)
            else:
                cs.write(c_vals)
            course_objs[c_code] = cs
            course_objs[c_code] = cs

            # Đề cương chi tiết
            syl = Syllabus.search([('course_id', '=', cs.id)], limit=1)
            if not syl:
                Syllabus.create({
                    'course_id': cs.id,
                    'name': f"Đề cương chi tiết: {c_name} (Áp dụng 2025)",
                    'apply_year': 2025,
                    'decision_number': f"25{cs.id}/QĐ-HVNN",
                    'decision_date': date(2025, 8, 15),
                    'state': 'applied',
                })
        print("[9/15] Đã khởi tạo 3 CTĐT, 7 Học phần chuyên ngành và Đề cương chi tiết tương ứng.")

        # 10. LỚP SINH VIÊN (faculty.student.class)
        StudentClass = env['faculty.student.class']
        classes_data = [
            ('Lớp Đại học Kinh tế Nông nghiệp K67A', 'K67KTNNA', curr_objs['CTDT-KTNN'].id, 46, 'Giảng đường A-201'),
            ('Lớp Đại học Kinh tế Nông nghiệp K67B', 'K67KTNNB', curr_objs['CTDT-KTNN'].id, 44, 'Giảng đường A-202'),
            ('Lớp Đại học Quản trị Kinh doanh Nông nghiệp K68', 'K68QTKDA', curr_objs['CTDT-QTKDNA'].id, 38, 'Giảng đường B-305'),
            ('Lớp Đại học Kinh tế Phát triển K68', 'K68KTE', curr_objs['CTDT-KTPT'].id, 52, 'Hội trường B-101'),
            ('Lớp Đại học Kinh tế Nông nghiệp K69', 'K69KTNNA', curr_objs['CTDT-KTNN'].id, 48, 'Giảng đường A-105'),
        ]
        class_objs = {}
        for name, code, cur_id, count, room in classes_data:
            sc = StudentClass.search([('code', '=', code)], limit=1)
            if not sc:
                sc = StudentClass.create({
                    'name': name,
                    'code': code,
                    'curriculum_id': cur_id,
                    'academic_year_id': y2526.id,
                    'student_count': count,
                    'classroom': room,
                })
            class_objs[code] = sc
        print("[10/15] Đã khởi tạo 5 Lớp sinh viên K67, K68, K69 (có sĩ số >= 40 tự nhân hệ số 1.2).")

        # 11. HỌC PHẦN THEO LỚP & CHECKLIST 7 BƯỚC & LỊCH GIẢNG (Trục trung tâm)
        ClassCourse = env['faculty.class.course']
        TeachingSession = env['faculty.teaching.session']

        cc_data = [
            {
                'class_id': class_objs['K67KTNNA'].id,
                'course_id': course_objs['KTNN101'].id,
                'semester_id': sem1.id,
                'head_lecturer_id': lecturer_objs['GV_VNUA_01'].id, # Thầy Thao
                'lecturer_ids': [(6, 0, [lecturer_objs['GV_VNUA_01'].id, lecturer_objs['GV_VNUA_04'].id])],
                'start_date': date(2025, 9, 8),
                'end_date': date(2025, 12, 20),
                'exam_date': date(2025, 12, 28),
                'grading_deadline': date(2026, 1, 10),
                'exam_format': 'essay',
                'question_source': 'new_paper',
            },
            {
                'class_id': class_objs['K67KTNNB'].id,
                'course_id': course_objs['KTNN201'].id,
                'semester_id': sem1.id,
                'head_lecturer_id': lecturer_objs['GV_VNUA_01'].id, # Thầy Thao
                'lecturer_ids': [(6, 0, [lecturer_objs['GV_VNUA_01'].id])],
                'start_date': date(2025, 9, 10),
                'end_date': date(2025, 12, 22),
                'exam_date': date(2025, 12, 30),
                'grading_deadline': date(2026, 1, 12),
                'exam_format': 'multiple_choice',
                'question_source': 'question_bank',
            },
            {
                'class_id': class_objs['K68KTE'].id,
                'course_id': course_objs['KTL202'].id,
                'semester_id': sem1.id,
                'head_lecturer_id': lecturer_objs['GV_VNUA_03'].id, # Cô Nga
                'lecturer_ids': [(6, 0, [lecturer_objs['GV_VNUA_03'].id])],
                'start_date': date(2025, 9, 15),
                'end_date': date(2025, 12, 25),
                'exam_date': date(2026, 1, 5),
                'grading_deadline': date(2026, 1, 18),
                'exam_format': 'essay',
                'question_source': 'new_paper',
            },
            {
                'class_id': class_objs['K68QTKDA'].id,
                'course_id': course_objs['QTKD301'].id,
                'semester_id': sem2.id,
                'head_lecturer_id': lecturer_objs['GV_VNUA_02'].id, # Cô Hiền
                'lecturer_ids': [(6, 0, [lecturer_objs['GV_VNUA_02'].id, lecturer_objs['GV_VNUA_05'].id])],
                'start_date': date(2026, 1, 19),
                'end_date': date(2026, 5, 10),
                'exam_date': date(2026, 5, 20),
                'grading_deadline': date(2026, 5, 30),
                'exam_format': 'essay_paper',
                'question_source': 'new_paper',
            },
        ]

        cc_objs = []
        for ccd in cc_data:
            cc = ClassCourse.search([
                ('class_id', '=', ccd['class_id']),
                ('course_id', '=', ccd['course_id']),
                ('semester_id', '=', ccd['semester_id']),
            ], limit=1)
            if not cc:
                cc = ClassCourse.create(ccd)
            else:
                cc.write(ccd)
            cc_objs.append(cc)

            # Khởi tạo Checklist nếu chưa có
            if not cc.checklist_ids:
                cc._init_checklist_steps()

            # Thiết lập cảnh báo mẫu trên Checklist:
            # - Bước 1 & 2 đã hoàn thành
            for chk in cc.checklist_ids:
                if chk.step_number in (1, 2):
                    chk.is_done = True
                    chk.done_date = cc.start_date
                elif chk.step_number == 5:
                    # Đặt quá hạn (Màu Tím)
                    chk.deadline = today - timedelta(days=2)
                    chk.is_done = False
                elif chk.step_number == 6:
                    # Đặt khẩn cấp (Màu Đỏ <= 3 ngày)
                    chk.deadline = today + timedelta(days=2)
                    chk.is_done = False

            # Tạo các buổi học thực tế (Teaching Sessions)
            # 5 buổi trong quá khứ (date <= today) -> tự động ghi Sổ cái
            sess_dates = [
                (today - timedelta(days=20), 'morning', 4, cc.head_lecturer_id.id, False),
                (today - timedelta(days=15), 'afternoon', 4, cc.head_lecturer_id.id, False),
                (today - timedelta(days=10), 'morning', 4, cc.head_lecturer_id.id, False),
                (today - timedelta(days=5), 'morning', 4, cc.head_lecturer_id.id, False),
                (today - timedelta(days=2), 'afternoon', 4, cc.head_lecturer_id.id, False),
                # 1 buổi có dạy thay
                (today - timedelta(days=1), 'morning', 4, cc.head_lecturer_id.id, True),
                # 2 buổi tương lai
                (today + timedelta(days=3), 'morning', 4, cc.head_lecturer_id.id, False),
                (today + timedelta(days=7), 'afternoon', 4, cc.head_lecturer_id.id, False),
            ]
            for s_date, s_time, p_count, lec_id, is_sub in sess_dates:
                exist_s = TeachingSession.search([
                    ('class_course_id', '=', cc.id),
                    ('date', '=', s_date),
                    ('session_time', '=', s_time),
                ], limit=1)
                if not exist_s:
                    sub_lec_id = lecturer_objs['GV_VNUA_04'].id if is_sub else False
                    TeachingSession.create({
                        'class_course_id': cc.id,
                        'date': s_date,
                        'session_time': s_time,
                        'period_count': p_count,
                        'lecturer_id': lec_id,
                        'is_substituted': is_sub,
                        'substitute_lecturer_id': sub_lec_id,
                    })

        print("[11/15] Đã khởi tạo 4 Lớp học phần, Checklist học vụ 7 bước (kèm cảnh báo Quá hạn Tím & Khẩn cấp Đỏ) và Lịch giảng chi tiết.")

        # 12. HƯỚNG DẪN KHÓA LUẬN, LUẬN VĂN & THỰC TẬP (faculty.thesis.guidance, faculty.internship.project)
        Thesis = env['faculty.thesis.guidance']
        thesis_data = [
            {
                'name': 'Đánh giá hiệu quả kinh tế chuỗi giá trị gạo ST25 tại Đồng bằng sông Cửu Long',
                'code': 'KL-2025-01',
                'academic_year_id': y2526.id,
                'guidance_level': 'bachelor',
                'student_names': 'Nguyễn Hoàng Nam, Lê Thị Mai',
                'student_code': 'SV670123',
                'student_count': 2,
                'lecturer_id': lecturer_objs['GV_VNUA_01'].id, # Thầy Thao
                'standard_hours': 25.0,
                'defense_date': today - timedelta(days=15),
            },
            {
                'name': 'Phân tích các yếu tố ảnh hưởng đến tiếp cận tín dụng xanh của nông hộ tại tỉnh Lâm Đồng',
                'code': 'LV-2025-02',
                'academic_year_id': y2526.id,
                'guidance_level': 'master',
                'student_names': 'Trần Thị Thảo',
                'student_code': 'CH31KT05',
                'student_count': 1,
                'lecturer_id': lecturer_objs['GV_VNUA_02'].id, # Cô Hiền
                'standard_hours': 35.0,
                'defense_date': today - timedelta(days=10),
            },
            {
                'name': 'Ứng dụng kinh tế lượng phân tích biến động giá thịt lợn miền Bắc giai đoạn 2020-2025',
                'code': 'NCKHSV-2025-03',
                'academic_year_id': y2526.id,
                'guidance_level': 'student_research',
                'student_names': 'Nhóm SV K67 Kinh tế Phát triển',
                'student_code': 'SV670889',
                'student_count': 3,
                'lecturer_id': lecturer_objs['GV_VNUA_03'].id, # Cô Nga
                'standard_hours': 15.0,
                'defense_date': today - timedelta(days=5),
            },
        ]
        for td in thesis_data:
            t = Thesis.search([('code', '=', td['code'])], limit=1)
            if not t:
                t = Thesis.create(td)
            else:
                t.write(td)
            t.action_approve()

        # Thực hành & Thực tập (faculty.internship.project)
        Intern = env['faculty.internship.project']
        it = Intern.search([('code', '=', 'TT-BAVI-2025')], limit=1)
        if not it:
            it = Intern.create({
                'name': 'Khảo sát chuỗi giá trị và Thực tập nghề nghiệp tại HTX Nông nghiệp Công nghệ cao Ba Vì - Hà Nội',
                'code': 'TT-BAVI-2025',
                'academic_year_id': y2526.id,
                'course_ids': [(6, 0, [course_objs['KTNN201'].id, course_objs['QTKD301'].id])],
                'host_organization': 'HTX Nông nghiệp Công nghệ cao Ba Vì',
                'area_location': 'Huyện Ba Vì, TP. Hà Nội',
                'start_date': today - timedelta(days=14),
                'end_date': today - timedelta(days=8),
                'payment_regulation_id': pr.id,
            })
            Part = env['faculty.internship.participant']
            Part.create({
                'project_id': it.id,
                'lecturer_id': lecturer_objs['GV_VNUA_04'].id, # Thầy Huyên (Trưởng đoàn)
                'role': 'leader',
                'student_count': 45,
                'days_count': 6,
                'standard_hours': 18.0,
            })
            Part.create({
                'project_id': it.id,
                'lecturer_id': lecturer_objs['GV_VNUA_05'].id, # Cô Diệp (Thành viên)
                'role': 'member',
                'student_count': 45,
                'days_count': 6,
                'standard_hours': 12.0,
            })
            it.action_load_budget_lines()
            it.action_approve()

        print("[12/15] Đã khởi tạo Hướng dẫn Khóa luận, Luận văn, NCKH Sinh viên và Đợt Thực tập Nghề nghiệp HTX Ba Vì.")

        # 13. NGHIÊN CỨU KHOA HỌC & HOẠT ĐỘNG KHÁC (faculty.research.work, faculty.other.work)
        Research = env['faculty.research.work']
        PartResearch = env['faculty.research.participant']
        research_data = [
            {
                'name': 'Impact of climate smart agriculture practices on rice production efficiency in Red River Delta',
                'code': 'NCKH-SCOPUS-2025',
                'academic_year_id': y2526.id,
                'research_type': 'article_wos_scopus',
                'publication_info': 'Agricultural Economics (Wiley), Scopus Q1',
                'total_hours': 120.0,
                'leader_id': lecturer_objs['GV_VNUA_01'].id,
                'acceptance_date': today - timedelta(days=30),
            },
            {
                'name': 'Nghiên cứu chuỗi giá trị và giải pháp nâng cao hiệu quả kinh tế ngành hàng rau an toàn tại Hà Nội',
                'code': 'NCKH-BNN-2025',
                'academic_year_id': y2526.id,
                'research_type': 'project_level',
                'project_scope': 'ministry',
                'publication_info': 'Bộ Nông nghiệp và Phát triển Nông thôn nghiệm thu',
                'total_hours': 150.0,
                'leader_id': lecturer_objs['GV_VNUA_02'].id, # Cô Hiền
                'acceptance_date': today - timedelta(days=25),
            },
            {
                'name': 'Giáo trình Kinh tế Nông nghiệp Nâng cao (Tái bản có sửa chữa)',
                'code': 'SACH-KTNN-2025',
                'academic_year_id': y2526.id,
                'research_type': 'book',
                'book_type': 'handbook',
                'publication_info': 'NXB Nông nghiệp Hà Nội (ISBN: 978-604-60-3120-1)',
                'total_hours': 80.0,
                'leader_id': lecturer_objs['GV_VNUA_01'].id,
                'acceptance_date': today - timedelta(days=40),
            },
            {
                'name': 'Phân tích các yếu tố quyết định chuyển đổi số trong các HTX nông nghiệp vùng Bắc Trung Bộ',
                'code': 'NCKH-VNUA-2025',
                'academic_year_id': y2526.id,
                'research_type': 'article_domestic',
                'publication_info': 'Tạp chí Khoa học Nông nghiệp Việt Nam, Tập 23, Số 4',
                'total_hours': 40.0,
                'leader_id': lecturer_objs['GV_VNUA_03'].id, # Cô Nga
                'acceptance_date': today - timedelta(days=18),
            },
        ]
        for rd in research_data:
            code = rd['code']
            r = Research.search([('code', '=', code)], limit=1)
            lead_lec_id = rd['leader_id']
            hours_val = rd['total_hours']
            vals = dict(rd)
            vals.pop('total_hours', None)
            if not r:
                r = Research.create(vals)
            else:
                r.write(vals)

            part = PartResearch.search([('research_id', '=', r.id), ('lecturer_id', '=', lead_lec_id)], limit=1)
            if not part:
                PartResearch.create({
                    'research_id': r.id,
                    'lecturer_id': lead_lec_id,
                    'role': 'leader',
                    'standard_hours': hours_val,
                    'contribution_ratio': 100.0,
                })
            else:
                part.write({'standard_hours': hours_val})
            r.action_approve()

        # Hoạt động khác của Khoa (faculty.other.work)
        OtherWork = env['faculty.other.work']
        other_data = [
            {
                'name': 'Sinh hoạt chuyên môn Bộ môn Kinh tế Nông nghiệp: Nâng cao năng lực nghiên cứu định lượng',
                'code': 'HDK-SHCM-2025',
                'academic_year_id': y2526.id,
                'activity_type': 'professional_meeting',
                'lead_lecturer_id': lecturer_objs['GV_VNUA_01'].id,
                'standard_hours': 15.0,
                'completion_date': today - timedelta(days=12),
            },
            {
                'name': 'Tổ chức Ngày hội Tư vấn Tuyển sinh Đại học năm 2026 tại các tỉnh Hải Dương, Hưng Yên',
                'code': 'HDK-TS-2025',
                'academic_year_id': y2526.id,
                'activity_type': 'admissions',
                'lead_lecturer_id': lecturer_objs['GV_VNUA_04'].id,
                'standard_hours': 20.0,
                'completion_date': today - timedelta(days=6),
            },
            {
                'name': 'Hội nghị Cán bộ Viên chức & Người lao động Khoa Kinh tế năm học 2025 - 2026',
                'code': 'HDK-HNCB-2025',
                'academic_year_id': y2526.id,
                'activity_type': 'party_union',
                'lead_lecturer_id': lecturer_objs['GV_VNUA_02'].id,
                'standard_hours': 10.0,
                'completion_date': today - timedelta(days=35),
            },
            {
                'name': 'Giải bóng đá Nam - Nữ Công đoàn Khoa Kinh tế chào mừng 20/11',
                'code': 'HDK-TDTT-2025',
                'academic_year_id': y2526.id,
                'activity_type': 'sports_culture',
                'lead_lecturer_id': lecturer_objs['GV_VNUA_04'].id,
                'standard_hours': 12.0,
                'completion_date': today - timedelta(days=45),
            },
        ]
        for od in other_data:
            code = od['code']
            ow = OtherWork.search([('code', '=', code)], limit=1)
            if not ow:
                ow = OtherWork.create(od)
            else:
                ow.write(od)
            ow.action_approve()

        print("[13/15] Đã khởi tạo 4 Công trình NCKH tiêu biểu (Scopus Q1, Đề tài Bộ, Giáo trình, Tạp chí) và 4 Hoạt động Khoa.")

        # 14. PHÂN CÔNG 6 MẢNG CHỨC NĂNG & THƯ VIỆN NHỎ & TỜ KHAI THỦ CÔNG
        Stream = env['faculty.stream.assignment']
        streams = [
            ('training', '1. Mảng Đào tạo & Quản lý Học vụ', lecturer_objs['GV_VNUA_01'].id, lecturer_objs['GV_VNUA_01'].id),
            ('research', '2. Mảng Nghiên cứu Khoa học & Hợp tác Quốc tế', lecturer_objs['GV_VNUA_02'].id, lecturer_objs['GV_VNUA_01'].id),
            ('student_affairs', '3. Mảng Công tác Sinh viên & Khảo thí', lecturer_objs['GV_VNUA_04'].id, lecturer_objs['GV_VNUA_02'].id),
            ('facilities_admin', '4. Mảng Cơ sở vật chất & Hành chính Tổng hợp', lecturer_objs['GV_VNUA_04'].id, lecturer_objs['GV_VNUA_01'].id),
            ('cadre_personnel', '5. Mảng Cán bộ, Nhân sự & Phát triển Đội ngũ', lecturer_objs['GV_VNUA_02'].id, lecturer_objs['GV_VNUA_01'].id),
            ('party_union', '6. Mảng Đảng, Đoàn thể & Văn thể mỹ', lecturer_objs['GV_VNUA_04'].id, lecturer_objs['GV_VNUA_02'].id),
        ]
        for w_stream, name, l_id, s_id in streams:
            sa = Stream.search([('work_stream', '=', w_stream), ('academic_year_id', '=', y2526.id)], limit=1)
            vals = {
                'work_stream': w_stream,
                'name': name,
                'academic_year_id': y2526.id,
                'lecturer_id': l_id,
                'supervisor_id': s_id,
                'task_nature': 'regular',
                'cycle': 'annual',
            }
            if not sa:
                Stream.create(vals)
            else:
                sa.write(vals)

        # Thư viện nhỏ Khoa (faculty.library.category, faculty.library.document)
        LibCat = env['faculty.library.category']
        LibDoc = env['faculty.library.document']
        lib_cats = [
            ('Giáo trình & Bài giảng Nông nghiệp', 'CAT-GIAOTRINH'),
            ('Văn bản & Quy chế Đào tạo Học viện', 'CAT-QUYCHE'),
            ('Tài liệu Hội thảo & Đề tài KHCN', 'CAT-HOITHAO'),
        ]
        cat_objs = {}
        for cname, ccode in lib_cats:
            lc = LibCat.search([('code', '=', ccode)], limit=1)
            if not lc:
                lc = LibCat.create({'name': cname, 'code': ccode})
            cat_objs[ccode] = lc

        sample_pdf_bytes = base64.b64encode(b"%PDF-1.4 Sample VNUA Economics Document Content").decode('utf-8')
        docs_data = [
            ('Giáo trình Kinh tế Vi mô Nông nghiệp (Tập 1)', 'DOC-VIMO-2025', cat_objs['CAT-GIAOTRINH'].id, 'book', lecturer_objs['GV_VNUA_01'].id),
            ('Quy chế Đào tạo Đại học theo hệ thống Tín chỉ Học viện Nông nghiệp', 'DOC-QC-TINCHI', cat_objs['CAT-QUYCHE'].id, 'regulation', lecturer_objs['GV_VNUA_01'].id),
            ('Kỷ yếu Hội thảo Khoa học Quốc gia Nông nghiệp Thông minh 2025', 'DOC-KYEU-2025', cat_objs['CAT-HOITHAO'].id, 'scientific_paper', lecturer_objs['GV_VNUA_02'].id),
        ]
        for dname, dcode, cid, dtype, author_id in docs_data:
            ld = LibDoc.search([('code', '=', dcode)], limit=1)
            vals = {
                'name': dname,
                'code': dcode,
                'category_id': cid,
                'document_type': dtype,
                'author_id': author_id,
                'year': 2025,
                'attachment_file': sample_pdf_bytes,
                'attachment_filename': f"{dcode}.pdf",
                'security_level': 'internal',
                'review_state': 'approved',
            }
            if not ld:
                LibDoc.create(vals)
            else:
                ld.write(vals)

        # Tờ khai thủ công (faculty.manual.declaration)
        ManualDec = env['faculty.manual.declaration']
        # Tờ khai 1: Approved -> ghi Sổ cái
        m1 = ManualDec.search([('name', '=', 'Chấm kiểm tra bổ sung Học phần Kinh tế Nông nghiệp K67')], limit=1)
        if not m1:
            m1 = ManualDec.create({
                'name': 'Chấm kiểm tra bổ sung Học phần Kinh tế Nông nghiệp K67',
                'lecturer_id': lecturer_objs['GV_VNUA_03'].id, # Cô Nga
                'academic_year_id': y2526.id,
                'semester_id': sem1.id,
                'category': 'teaching',
                'teaching_branch': 'converted',
                'activity_type': 'exam_audit',
                'raw_hours': 10.0,
                'coefficient': 1.0,
                'date': today - timedelta(days=8),
            })
            m1.action_approve()

        # Tờ khai 2: Submitted (Chờ duyệt)
        m2 = ManualDec.search([('name', '=', 'Hỗ trợ coi thi đột xuất kỳ thi phụ Đợt 1')], limit=1)
        if not m2:
            m2 = ManualDec.create({
                'name': 'Hỗ trợ coi thi đột xuất kỳ thi phụ Đợt 1',
                'lecturer_id': lecturer_objs['GV_VNUA_04'].id, # Thầy Huyên
                'academic_year_id': y2526.id,
                'semester_id': sem1.id,
                'category': 'teaching',
                'teaching_branch': 'converted',
                'activity_type': 'exam_proctoring',
                'raw_hours': 6.0,
                'coefficient': 1.0,
                'date': today - timedelta(days=3),
            })
            m2.action_submit()

        print("[14/15] Đã thiết lập Biểu phân công 6 mảng chức năng, Thư viện nhỏ Khoa và Tờ khai công việc.")

        # 15. TỔNG KẾT BẢNG CÂN ĐỐI BÙ TRỪ GIỜ CHUẨN & DASHBOARD REAL-TIME
        # Để đảm bảo thể hiện chính xác 4 kịch bản quy chuẩn:
        # Bổ sung các bút toán vào faculty.hour.ledger để đạt đúng các con số toán học
        Ledger = env['faculty.hour.ledger']
        Balance = env['faculty.workload.balance']

        # Giảng viên 1: PGS.TS. Trần Đình Thao (Kịch bản 1: Hoàn thành nhiệm vụ & Tính tiền vượt giờ)
        # Định mức sau giảm: A = 320 * (1 - 0.3) = 224, B = 0.5 * 224 = 112, C = 240 * (1 - 0.3) = 168
        # Thêm giờ lên lớp b = 130 (> 112 -> n > 0), giờ quy đổi khác = 85 -> a = 215 + ...
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_01'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=20),
            'category': 'teaching',
            'activity_type': 'lecture',
            'teaching_branch': 'direct',
            'is_direct_teaching': True,
            'name': 'Giảng dạy lý thuyết trên lớp - HP Kinh tế Nông nghiệp K67A',
            'standard_hours': 130.0,
            'raw_hours': 130.0,
            'state': 'posted',
        })
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_01'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=15),
            'category': 'teaching',
            'activity_type': 'exam_grading',
            'teaching_branch': 'converted',
            'is_direct_teaching': False,
            'name': 'Chấm thi kết thúc học phần Kinh tế Nông nghiệp',
            'standard_hours': 85.0,
            'raw_hours': 85.0,
            'state': 'posted',
        })

        # Giảng viên 3: TS. Bùi Thị Nga (Kịch bản 3: Thừa GD m=20, thiếu NCKH nhưng đạt sàn 25% -> Bù trừ GD sang NCKH)
        # A = 300 * 0.7 = 210, B = 105, C = 200 * 0.7 = 140
        # Tạo b = 155 (n = 50), khác = 75 -> a = 230 (m = 20)
        # NCKH c = 120 (< 140 thiếu 20h, nhưng 120 >= 0.25*140 = 35 -> đạt sàn)
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_03'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=22),
            'category': 'teaching',
            'activity_type': 'lecture',
            'teaching_branch': 'direct',
            'is_direct_teaching': True,
            'name': 'Giảng dạy Kinh tế lượng ứng dụng K68KTE',
            'standard_hours': 155.0,
            'raw_hours': 155.0,
            'state': 'posted',
        })
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_03'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=18),
            'category': 'teaching',
            'activity_type': 'exam_grading',
            'teaching_branch': 'converted',
            'is_direct_teaching': False,
            'name': 'Chấm bài tập lớn và bài kiểm tra Kinh tế lượng',
            'standard_hours': 55.0,
            'raw_hours': 55.0,
            'state': 'posted',
        })
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_03'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=12),
            'category': 'research',
            'activity_type': 'research_project',
            'name': 'Thực hiện đề tài KHCN cấp cơ sở HVNN',
            'standard_hours': 80.0,
            'raw_hours': 80.0,
            'state': 'posted',
        })

        # Giảng viên 2: TS. Nguyễn Thị Minh Hiền (Kịch bản 4: Thiếu giờ GD a < A, nhưng thừa NCKH o > 0 -> Bù trừ NCKH sang GD)
        # A = 300 * 0.8 = 240, B = 120, C = 200 * 0.8 = 160
        # b = 150 (n = 30), khác = 40 -> a = 190 (< 240, thiếu 50h)
        # NCKH c = 220 (> 160, thừa o = 60h)
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_02'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=25),
            'category': 'teaching',
            'activity_type': 'lecture',
            'teaching_branch': 'direct',
            'is_direct_teaching': True,
            'name': 'Giảng dạy Quản trị Chuỗi cung ứng Nông sản K68',
            'standard_hours': 150.0,
            'raw_hours': 150.0,
            'state': 'posted',
        })
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_02'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=20),
            'category': 'research',
            'activity_type': 'research_paper',
            'name': 'Công bố bài báo quốc tế về Chuỗi cung ứng xanh',
            'standard_hours': 70.0,
            'raw_hours': 70.0,
            'state': 'posted',
        })

        # Giảng viên 4: ThS. Vũ Ngọc Huyên (Kịch bản 2: b < B nhưng a >= A, đủ NCKH -> Hoàn thành nhưng tiền = 0)
        # A = 280, B = 140, C = 160
        # b = 100 (< 140 -> n = 0), khác = 185 -> a = 285 (> 280), c = 165 (> 160)
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_04'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=21),
            'category': 'teaching',
            'activity_type': 'lecture',
            'teaching_branch': 'direct',
            'is_direct_teaching': True,
            'name': 'Giảng dạy môn Kinh tế Môi trường Nông nghiệp',
            'standard_hours': 100.0,
            'raw_hours': 100.0,
            'state': 'posted',
        })
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_04'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=16),
            'category': 'teaching',
            'activity_type': 'exam_grading',
            'teaching_branch': 'converted',
            'is_direct_teaching': False,
            'name': 'Chấm bài tập lớn và quản lý hồ sơ thực tế',
            'standard_hours': 167.0,
            'raw_hours': 167.0,
            'state': 'posted',
        })
        Ledger.create({
            'lecturer_id': lecturer_objs['GV_VNUA_04'].id,
            'academic_year_id': y2526.id,
            'semester_id': sem1.id,
            'date': today - timedelta(days=10),
            'category': 'research',
            'activity_type': 'research_workshop',
            'name': 'Báo cáo tham luận tại Hội thảo Khoa học Sinh viên Khoa Kinh tế',
            'standard_hours': 150.0,
            'raw_hours': 150.0,
            'state': 'posted',
        })

        # Tính lại toàn bộ bảng cân đối
        for l_code, l_obj in lecturer_objs.items():
            Balance.recompute_for_lecturer(l_obj.id, y2526.id)

        # Đồng bộ lịch chung (faculty.calendar.event)
        CalendarEvent = env['faculty.calendar.event']
        CalendarEvent.action_sync_all_events()

        # Tạo Dashboard điều hành thông minh Real-time (faculty.dashboard)
        Dashboard = env['faculty.dashboard']
        dash = Dashboard.search([], limit=1)
        if not dash:
            dash = Dashboard.create({'name': f"Bảng Điều hành Khoa Kinh tế - {today.strftime('%d/%m/%Y')}"})
        dash._populate_dashboard_data()

        print("[15/15] Đã tính toán Bảng Cân đối Giờ chuẩn, Đồng bộ Lịch chung và Nạp dữ liệu Dashboard Real-time.")
        
        # COMMIT TO DB
        cr.commit()
        print("=== HOÀN TẤT 100% CƠ SỞ DỮ LIỆU KHOA KINH TẾ - HỌC VIỆN NÔNG NGHIỆP VIỆT NAM ===")

if __name__ == '__main__':
    populate()
