from rest_framework.response import Response


class AnnouncementPresenter:
    def announcement_success(self, announcement, section_id):
        return Response({
            'id': announcement.id,
            'title': announcement.title,
            'audience': announcement.audience,
            'section_id': section_id,
            'published_at': announcement.published_at.isoformat() if announcement.published_at else None,
            'attachments': [
                {
                    'id': a.id,
                    'filename': a.filename,
                    'content_type': a.content_type,
                    'file_url': a.file or None,
                }
                for a in announcement.announcementattachment_set.all()
            ],
        }, status=201)
