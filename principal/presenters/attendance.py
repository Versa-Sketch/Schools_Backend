from rest_framework.response import Response


def _attendance_percentage(present, total):
    if not total:
        return 0.0
    return round(present / total * 100, 2)


class AttendanceSummaryPresenter:
    def summary_success(self, date, rows):
        classes = []
        for row in rows:
            total = row['total_students']
            present = row['present_count']
            classes.append({
                'class_id': row['class_id'],
                'class_name': row['class_name'],
                'total_students': total,
                'present_count': present,
                'absent_count': total - present,
                'attendance_percentage': _attendance_percentage(present, total),
            })
        return Response({'date': str(date), 'classes': classes}, status=200)

    def detail_success(self, date, academic_class, sections):
        class_total = 0
        class_present = 0
        class_present_names = []
        class_absent_names = []
        formatted_sections = []

        for sec in sections:
            total = sec['total_students']
            present_students = sec['present_students']
            absent_students = sec['absent_students']
            present = len(present_students)
            class_total += total
            class_present += present

            for s in present_students:
                class_present_names.append({'id': s.id, 'name': s.name, 'section': sec['section_name']})
            for s in absent_students:
                class_absent_names.append({'id': s.id, 'name': s.name, 'section': sec['section_name']})

            formatted_sections.append({
                'section_id': sec['section_id'],
                'section_name': sec['section_name'],
                'total_students': total,
                'present_count': present,
                'absent_count': len(absent_students),
                'attendance_percentage': _attendance_percentage(present, total),
                'present_students': [{'id': s.id, 'name': s.name} for s in present_students],
                'absent_students': [{'id': s.id, 'name': s.name} for s in absent_students],
            })

        return Response({
            'date': str(date),
            'class_id': academic_class.id,
            'class_name': academic_class.name,
            'total_students': class_total,
            'present_count': class_present,
            'absent_count': len(class_absent_names),
            'attendance_percentage': _attendance_percentage(class_present, class_total),
            'present_students': class_present_names,
            'absent_students': class_absent_names,
            'sections': formatted_sections,
        }, status=200)
