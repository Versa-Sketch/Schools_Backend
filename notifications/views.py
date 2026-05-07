from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser

from .storages.notification_storage import NotificationDB
from .interactors import ListNotificationsInteractor, MarkReadInteractor, UnreadCountInteractor
from .presenters.notifications import NotificationPresenter


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list_view(request):
    unread_only = request.query_params.get('unread') == 'true'
    return ListNotificationsInteractor(
        storage=NotificationDB(), presenter=NotificationPresenter(),
    ).list_notifications(user=request.user, unread_only=unread_only)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def mark_read_view(request):
    return MarkReadInteractor(
        storage=NotificationDB(), presenter=NotificationPresenter(),
    ).mark_read(user=request.user, notification_ids=request.data.get('ids'))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count_view(request):
    return UnreadCountInteractor(
        storage=NotificationDB(), presenter=NotificationPresenter(),
    ).get_count(user=request.user)
