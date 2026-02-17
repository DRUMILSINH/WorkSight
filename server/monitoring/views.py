import json
import secrets
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import now

from .models import (
    AgentSession,
    ScreenshotLog,
    AgentHeartbeat,
    Recording,
    AgentToken,
)
from .auth import require_agent_token


# ==============================
# SESSION CREATION
# ==============================

@csrf_exempt
def create_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        session = AgentSession.objects.create(
            agent_name=data["agent_name"],
            agent_version=data["agent_version"],
            hostname=data["hostname"],
            username=data["username"],
            ip_address=data["ip_address"],
        )

        # 🔐 Generate secure token
        token_value = secrets.token_hex(32)

        AgentToken.objects.create(
            session=session,
            token=token_value
        )

        return JsonResponse({
            "session_id": session.id,
            "token": token_value
        }, status=201)

    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ==============================
# SCREENSHOT LOGGING
# ==============================

@csrf_exempt
def log_screenshot(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        ScreenshotLog.objects.create(
            session_id=data["session_id"],
            image_path=data["image_path"],
        )

        return JsonResponse({"status": "ok"}, status=201)

    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ==============================
# HEARTBEAT
# ==============================

@csrf_exempt
@require_agent_token
def heartbeat(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        session = AgentSession.objects.get(id=session_id)
        AgentHeartbeat.objects.update_or_create(session=session)
        return JsonResponse({"status": "alive"})

    except AgentSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session"}, status=404)


# ==============================
# RECORDING UPLOAD
# ==============================

@csrf_exempt
@require_agent_token
def upload_recording(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        session = AgentSession.objects.get(id=session_id)
        data = json.loads(request.body)

        recording = Recording.objects.create(
            session=session,
            video_path=data["video_path"],
            drive_file_id=data.get("drive_file_id"),
            started_at=datetime.fromisoformat(data["started_at"]),
            ended_at=datetime.fromisoformat(data["ended_at"]),
            status=data.get("status", "UPLOADED"),
            file_size_bytes=data.get("file_size_bytes"),
        )

        return JsonResponse({"recording_id": recording.id}, status=201)

    except AgentSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ==============================
# DASHBOARD
# ==============================

def dashboard_home(request):
    logs_list = ScreenshotLog.objects.select_related('session').all().order_by('-captured_at')

    search_query = request.GET.get('q', '')
    if search_query:
        logs_list = logs_list.filter(
            Q(session__username__icontains=search_query) |
            Q(session__ip_address__icontains=search_query)
        )

    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'logs': page_obj,
        'search_query': search_query,
        'total_agents': AgentSession.objects.count(),
        'active_sessions': AgentSession.objects.count(),
    }

    return render(request, 'monitoring/dashboard.html', context)


def health_view(request):
    total = Recording.objects.count()
    failed = Recording.objects.filter(status='FAILED').count()

    return JsonResponse({
        "timestamp": now(),
        "total_recordings": total,
        "total_failures": failed,
    })
