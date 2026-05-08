from collections import defaultdict

from rest_framework.response import Response

_RISK_PRIORITY = {'ALERT': 3, 'WATCH': 2, 'SAFE': 1}


class SectionPresenter:

    # ------------------------------------------------------------ Screen 3

    def section_students_success(self, section, exam, exam_results, risk_map):
        max_marks = {es.subject_name: es.max_marks for es in exam.subjects.all()}

        by_student  = defaultdict(dict)
        student_obj = {}
        for er in exam_results:
            sid = str(er.student_id)
            by_student[sid][er.subject.subject_name] = er
            student_obj[sid] = er.student

        students = []
        for sid, subj_map in by_student.items():
            total_marks = sum(er.total_marks for er in subj_map.values())
            total_max   = sum(max_marks.get(s, 1) for s in subj_map)
            total_pct   = round((total_marks / total_max) * 100, 1) if total_max else 0

            # Per-subject percentage
            def pct(subject, _subj_map=subj_map):
                er = _subj_map.get(subject)
                if er is None:
                    return None
                mm = max_marks.get(subject, 1)
                return round((er.total_marks / mm) * 100, 1)

            # Subject-wise risk labels
            subject_risk = {
                subj: (risk_map[(sid, subj)].risk_label if (sid, subj) in risk_map else 'SAFE')
                for subj in subj_map
            }

            # Overall risk = worst across subjects
            overall_risk = max(
                subject_risk.values(),
                key=lambda lbl: _RISK_PRIORITY.get(lbl, 0),
                default='SAFE',
            )

            students.append({
                'student_id':     sid,
                'student_ref_id': student_obj[sid].student_ref_id,
                'name':           student_obj[sid].name,
                'maths_pct':      pct('MATHS'),
                'physics_pct':    pct('PHYSICS'),
                'chem_pct':       pct('CHEMISTRY'),
                'total_pct':      total_pct,
                'subject_risk':   subject_risk,
                'overall_risk':   overall_risk,
            })

        students.sort(key=lambda s: s['total_pct'] or 0, reverse=True)

        return Response({
            'success':      True,
            'class_name':   section.academic_class.name,
            'section_name': section.name,
            'section_id':   str(section.id),
            'exam': self._fmt_exam(exam),
            'students':     students,
        }, status=200)

    # ------------------------------------------------------------ Screen 4

    def heatmap_success(self, section, subject_name, exam, questions):
        return Response({
            'success':         True,
            'class_name':      section.academic_class.name,
            'section_name':    section.name,
            'section_id':      str(section.id),
            'subject_name':    subject_name,
            'total_questions': len(questions),
            'exam':            self._fmt_exam(exam),
            'questions': [
                {
                    'q_no':             qa.q_no,
                    'correct_count':    qa.correct_count,
                    'wrong_count':      qa.wrong_count,
                    'skip_count':       qa.skip_count,
                    'difficulty_index': qa.difficulty_index,
                    'difficulty_tag':   qa.difficulty_tag,
                    'has_key_error':    qa.has_key_error,
                }
                for qa in questions
            ],
        }, status=200)

    # ------------------------------------------------------------ Screen 5

    def question_detail_success(self, section, subject_name, q_no, exam, qa):
        return Response({
            'success':      True,
            'class_name':   section.academic_class.name,
            'section_name': section.name,
            'section_id':   str(section.id),
            'subject_name': subject_name,
            'q_no':         q_no,
            'exam':         self._fmt_exam(exam),
            'question': {
                'q_no':                 qa.q_no,
                'correct_count':        qa.correct_count,
                'wrong_count':          qa.wrong_count,
                'skip_count':           qa.skip_count,
                'difficulty_index':     qa.difficulty_index,
                'difficulty_tag':       qa.difficulty_tag,
                'discrimination_index': qa.discrimination_index,
                'has_key_error':        qa.has_key_error,
            },
        }, status=200)

    # ------------------------------------------------------------ shared

    def _fmt_exam(self, exam):
        return {
            'id':        str(exam.id),
            'exam_name': exam.exam_name,
            'exam_date': str(exam.exam_date),
        }
