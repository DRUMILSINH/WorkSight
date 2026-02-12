import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.db.models import Prefetch

from .models import AgentSession, ScreenshotLog, AgentHeartbeat, Recording, AgentToken

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

@csrf_exempt
def heartbeat(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        session = AgentSession.objects.get(id=session_id)
    except AgentSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session"}, status=404)

    AgentHeartbeat.objects.update_or_create(session=session)

    return JsonResponse({"status": "alive"})

def dashboard(request):
    sessions = AgentSession.objects.prefetch_related(
        Prefetch(
            "screenshots",
            queryset=ScreenshotLog.objects.order_by("-captured_at")
        )
    ).order_by("-started_at")

    return render(
        request,
        "monitoring/dashboard.html",
        {"sessions": sessions},
    )

@csrf_exempt
def upload_recording(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        session = AgentSession.objects.get(id=session_id)
    except AgentSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session"}, status=404)

    data = json.loads(request.body)

    recording = Recording.objects.create(
        session=session,
        video_path=data["video_path"],
        drive_file_id=data.get("drive_file_id"),
        started_at=datetime.fromisoformat(data["started_at"]),
        ended_at=datetime.fromisoformat(data["ended_at"]),
    )

    return JsonResponse({"recording_id": recording.id}, status=201)

def _authorize(request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None

    token_value = auth.split(" ", 1)[1]

    try:
        return AgentToken.objects.get(token=token_value)
    except AgentToken.DoesNotExist:
        return None
