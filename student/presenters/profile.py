from rest_framework.response import Response


class StudentProfilePresenter:
    def profile_success(self, profile):
        return Response({
            'id': profile.id,
            'name': profile.name,
            'roll_number': profile.roll_number,
            'admission_number': profile.admission_number,
            'is_active': profile.is_active,
            'academic_class': {'id': profile.academic_class_id, 'name': profile.academic_class.name},
            'section': {'id': profile.section_id, 'name': profile.section.name},
            'school': {'id': profile.school_id, 'name': profile.school.name},
        }, status=200)
