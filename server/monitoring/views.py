import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import AgentSession, ScreenshotLog

@csrf_exempt
def create_session(request):
    """
    Creates a new AgentSession.
    Expected JSON payload:
    {
        "agent_name": "...",
        "agent_version": "...",
        "hostname": "...",
        "username": "...",
        "ip_address": "..."
    }
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST method allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)

        session = AgentSession.objects.create(
            agent_name=data["agent_name"],
            agent_version=data["agent_version"],
            hostname=data["hostname"],
            username=data["username"],
            ip_address=data["ip_address"],
        )

        return JsonResponse(
            {"session_id": session.id},
            status=201
        )

    except KeyError as e:
        return JsonResponse(
            {"error": f"Missing field: {str(e)}"},
            status=400
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON payload"},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )

@csrf_exempt
def log_screenshot(request):
    """
    Logs a screenshot metadata entry.
    Expected JSON payload:
    {
        "session_id": 1,
        "image_path": "...",
        "captured_at": "2026-02-11T05:45:32Z"
    }
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST method allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)

        ScreenshotLog.objects.create(
            session_id=data["session_id"],
            image_path=data["image_path"],
            captured_at=datetime.fromisoformat(
                data["captured_at"].replace("Z", "")
            ),
        )

        return JsonResponse(
            {"status": "ok"},
            status=201
        )

    except KeyError as e:
        return JsonResponse(
            {"error": f"Missing field: {str(e)}"},
            status=400
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON payload"},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
