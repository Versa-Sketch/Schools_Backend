from rest_framework.response import Response


class BulkUploadPresenter:
    def bulk_upload_success(self, batch):
        data = {
            'batch_id': batch.id,
            'status': batch.status,
            'total_rows': batch.total_rows,
            'success_count': batch.success_count,
            'error_count': batch.error_count,
        }
        if batch.error_report:
            data['error_report_url'] = batch.error_report.url
        return Response(data, status=200)
