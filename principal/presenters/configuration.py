from rest_framework.response import Response


class ConfigurationPresenter:
    def configuration_success(self, config):
        return Response({
            'school_id': config.school_id,
            'attendance_frequency': config.attendance_frequency,
            'whatsapp_absent_automation_enabled': config.whatsapp_absent_automation_enabled,
            'parent_query_enabled': config.parent_query_enabled,
            'subdomain': config.school.subdomain,
        }, status=200)
