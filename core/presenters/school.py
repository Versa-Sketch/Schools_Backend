from rest_framework.response import Response


class SchoolPresenter:
    def success(self, school):
        return Response({
            'id': school.id,
            'name': school.name,
            'subdomain': school.subdomain,
            'address': school.address,
            'contact_email': school.contact_email,
            'contact_phone': school.contact_phone,
            'is_active': school.is_active,
        }, status=200)
