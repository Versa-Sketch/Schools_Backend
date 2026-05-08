import io

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsAdmin, IsPrincipal
from analytics.interactors.upload import UploadExamCSVInteractor
from analytics.presenters.upload import UploadPresenter
from analytics.services.csv_parser import generate_template_csv
from analytics.services.seed import generate_seed_csv
from analytics.storages.analytics_storage import AnalyticsDB


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def template_download_view(request):
    csv_string = generate_template_csv()
    response = HttpResponse(csv_string, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_template.csv"'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def upload_view(request):
    return UploadExamCSVInteractor(
        storage=AnalyticsDB(),
        presenter=UploadPresenter(),
    ).upload(user=request.user, csv_file=request.FILES.get('csv_file'))


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPrincipal | IsAdmin])
def seed_view(request):
    if not settings.DEBUG:
        return Response({'success': False, 'detail': 'Not available in production.'}, status=403)
    csv_file      = io.BytesIO(generate_seed_csv().encode('utf-8'))
    csv_file.name = 'seed_data.csv'
    return UploadExamCSVInteractor(
        storage=AnalyticsDB(),
        presenter=UploadPresenter(),
    ).upload(user=request.user, csv_file=csv_file)
