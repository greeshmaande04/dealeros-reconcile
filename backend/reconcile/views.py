from rest_framework.response import Response
from rest_framework.views import APIView

from .services import reconcile_records


class ReconcileView(APIView):
    def get(self, request):
        org_id = request.query_params.get("org_id") or None
        loc_id = request.query_params.get("loc_id") or None
        status_filter = request.query_params.get("status") or None

        data = reconcile_records(
            org_id=org_id,
            loc_id=loc_id,
            status_filter=status_filter,
        )
        return Response(data)
