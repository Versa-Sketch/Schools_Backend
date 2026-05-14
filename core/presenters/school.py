from rest_framework.response import Response


class SchoolPresenter:
    def success(self, school, config=None):
        data = {
            'id': school.id,
            'name': school.name,
            'subdomain': school.subdomain,
            'address': school.address,
            'contact_email': school.contact_email,
            'contact_phone': school.contact_phone,
            'is_active': school.is_active,
            'logo': school.logo,
        }
        
        if config:
            data['configuration'] = {
                'attendance_frequency': config.attendance_frequency,
                'whatsapp_absent_automation_enabled': config.whatsapp_absent_automation_enabled,
                'parent_query_enabled': config.parent_query_enabled,
            }
        else:
            data['configuration'] = None

        return Response(data, status=200)
