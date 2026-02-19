from django.http import JsonResponse
from .models import AgentToken


def require_agent_token(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"error": "Missing token"}, status=401)

        try:
            token_value = auth_header.replace("Bearer ", "")
            token = AgentToken.objects.select_related("session").get(token=token_value)
        except AgentToken.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=403)

        session_id = kwargs.get("session_id")
        if session_id is not None and token.session_id != session_id:
            return JsonResponse({"error": "Token does not match session"}, status=403)

        body_session_id = request.POST.get("session_id") if hasattr(request, "POST") else None
        if body_session_id:
            try:
                if token.session_id != int(body_session_id):
                    return JsonResponse({"error": "Token does not match body session_id"}, status=403)
            except ValueError:
                return JsonResponse({"error": "Invalid body session_id"}, status=400)

        request.agent_session = token.session

        return view_func(request, *args, **kwargs)

    return wrapper
