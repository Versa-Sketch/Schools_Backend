from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from analytics.services.csv_parser import generate_template_csv


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def template_download_view(request):
    csv_string = generate_template_csv()
    response = HttpResponse(csv_string, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_template.csv"'
    return response
