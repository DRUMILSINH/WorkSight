import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

# Ensure these models exist in your monitoring/models.py
from .models import AgentSession, ScreenshotLog, AgentHeartbeat, Recording, AgentToken

@csrf_exempt
def create_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
        session = AgentSession.objects.create(
            agent_name=data["agent_name"],
            agent_version=data["agent_version"],
            hostname=data["hostname"],
            username=data["username"],
            ip_address=data["ip_address"],
        )
        return JsonResponse({"session_id": session.id}, status=201)

    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def log_screenshot(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

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

@csrf_exempt
def heartbeat(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        session = AgentSession.objects.get(id=session_id)
        AgentHeartbeat.objects.update_or_create(session=session)
        return JsonResponse({"status": "alive"})
    except AgentSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session"}, status=404)

@csrf_exempt
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
        )
        return JsonResponse({"recording_id": recording.id}, status=201)
    except AgentSession.DoesNotExist:
        return JsonResponse({"error": "Invalid session"}, status=404)

def dashboard_home(request):
    """
    Renders the main dashboard with search, filtering, and pagination.
    """
    # 1. Base Query: Get all logs, newest first
    # We use 'captured_at' because your previous error confirmed this field exists
    logs_list = ScreenshotLog.objects.select_related('session').all().order_by('-captured_at')

    # 2. Search Logic
    search_query = request.GET.get('q', '')
    if search_query:
        # We removed 'window_title' because your previous error confirmed it was missing
        logs_list = logs_list.filter(
            Q(session__username__icontains=search_query) |
            Q(session__ip_address__icontains=search_query)
        )

    # 3. Pagination
    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4. Context Data
    context = {
        'logs': page_obj,
        'search_query': search_query,
        'total_agents': AgentSession.objects.count(),
        # FIX: Removed '.filter(is_active=True)' because the field does not exist.
        # We just count all agents for now to prevent the crash.
        'active_sessions': AgentSession.objects.count() 
    }

    return render(request, 'monitoring/dashboard.html', context)
