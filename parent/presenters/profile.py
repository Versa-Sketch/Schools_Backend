from rest_framework.response import Response


class ParentProfilePresenter:
    def profile_success(self, profile, students, school_config=None):
        school_queries_enabled = school_config.parent_query_enabled if school_config else True
        return Response({
            'id': profile.id,
            'name': profile.name,
            'mobile_number': profile.mobile_number,
            'school': {'id': profile.school_id, 'name': profile.school.name},
            'students': [
                {
                    'id': s.id,
                    'name': s.name,
                    'roll_number': s.roll_number,
                    'academic_class': {'id': s.academic_class_id, 'name': s.academic_class.name},
                    'section': {'id': s.section_id, 'name': s.section.name},
                    'is_parent_query_disabled': not (school_queries_enabled and s.section.parent_query_enabled),
                }
                for s in students
            ],
        }, status=200)

    def student_list_success(self, students):
        results = [
            {
                'id': s.id,
                'name': s.name,
                'roll_number': s.roll_number,
                'admission_number': s.admission_number,
                'academic_class': {'id': s.academic_class_id, 'name': s.academic_class.name},
                'section': {'id': s.section_id, 'name': s.section.name},
            }
            for s in students
        ]
        return Response({'count': len(results), 'results': results}, status=200)
