from django.dispatch import Signal

announcement_published   = Signal()  # kwargs: announcement
homework_assigned        = Signal()  # kwargs: homework
study_material_uploaded  = Signal()  # kwargs: material
attendance_confirmed     = Signal()  # kwargs: session
parent_query_created     = Signal()  # kwargs: query
query_reply_added        = Signal()  # kwargs: reply
calendar_event_created   = Signal()  # kwargs: event
bulk_upload_completed    = Signal()  # kwargs: batch, principal_user
