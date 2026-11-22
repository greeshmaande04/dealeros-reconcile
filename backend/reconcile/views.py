
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import UnknownOrg, get_disagreements


class DisagreementsView(APIView):
    """GET /api/disagreements/?org=ORG-A&reason=VALUE_MISMATCH&sort=-value"""

    def get(self, request):
        org = request.query_params.get("org")
        if not org:  # org is REQUIRED: no org, no data
            return Response({"error": "org is required"}, status=400)
        try:
            rows = get_disagreements(
                org,
                reason=request.query_params.get("reason") or None,
                sort=request.query_params.get("sort") or None,
            )
        except UnknownOrg:
            return Response({"error": "unknown org"}, status=404)
        return Response({"count": len(rows), "results": rows})