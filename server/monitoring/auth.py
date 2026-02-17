from django.http import JsonResponse
from .models import AgentToken


def require_agent_token(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"error": "Missing token"}, status=401)

        try:
            token_value = auth_header.replace("Bearer ", "")
            AgentToken.objects.get(token=token_value)
        except AgentToken.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper
