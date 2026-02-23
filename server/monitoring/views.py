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
    AIMetric,
)
from .auth import require_agent_token
from .services.analytics import get_session_analytics


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
@require_agent_token
def log_screenshot(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        session_id = request.POST.get("session_id")
        captured_at_str = request.POST.get("captured_at")

        if not session_id or not captured_at_str or "image" not in request.FILES:
            return JsonResponse({"error": "Missing data"}, status=400)

        try:
            captured_at = datetime.fromisoformat(captured_at_str.replace("Z", "+00:00"))
        except ValueError:
            return JsonResponse({"error": "Invalid captured_at format"}, status=400)

        ScreenshotLog.objects.create(
            session_id=session_id,
            image=request.FILES["image"],
            captured_at=captured_at,
        )

        return JsonResponse({"status": "ok"}, status=201)

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


@csrf_exempt
@require_agent_token
def create_ai_metric(request, session_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    idempotency_key = request.headers.get("X-Idempotency-Key")
    if not idempotency_key:
        return JsonResponse({"error": "Missing X-Idempotency-Key"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required_fields = [
        "agent_timestamp",
        "source_type",
        "source_ref",
        "feature_version",
        "features",
        "productivity_score",
        "anomaly_score",
        "anomaly_label",
        "model_info",
        "pipeline_status",
    ]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return JsonResponse({"error": f"Missing fields: {', '.join(missing)}"}, status=400)

    if data["source_type"] not in {"screenshot", "recording_window"}:
        return JsonResponse({"error": "Invalid source_type"}, status=400)
    if data["anomaly_label"] not in {"normal", "suspicious", "critical"}:
        return JsonResponse({"error": "Invalid anomaly_label"}, status=400)
    if data["pipeline_status"] not in {"ok", "partial", "failed"}:
        return JsonResponse({"error": "Invalid pipeline_status"}, status=400)
    if not isinstance(data.get("features"), dict):
        return JsonResponse({"error": "features must be an object"}, status=400)
    if not isinstance(data.get("model_info"), dict):
        return JsonResponse({"error": "model_info must be an object"}, status=400)

    productivity_score = float(data["productivity_score"])
    anomaly_score = float(data["anomaly_score"])
    if productivity_score < 0 or productivity_score > 100:
        return JsonResponse({"error": "productivity_score must be between 0 and 100"}, status=400)
    if anomaly_score < 0 or anomaly_score > 1:
        return JsonResponse({"error": "anomaly_score must be between 0 and 1"}, status=400)

    existing = AIMetric.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return JsonResponse({"ai_metric_id": existing.id, "status": "duplicate"}, status=200)

    agent_timestamp_raw = data["agent_timestamp"].replace("Z", "+00:00")

    metric = AIMetric.objects.create(
        session_id=session_id,
        agent_timestamp=datetime.fromisoformat(agent_timestamp_raw),
        source_type=data["source_type"],
        source_ref=data["source_ref"],
        ocr_text_hash=data.get("ocr_text_hash"),
        feature_version=data["feature_version"],
        features=data["features"],
        productivity_score=productivity_score,
        anomaly_score=anomaly_score,
        anomaly_label=data["anomaly_label"],
        model_info=data["model_info"],
        pipeline_status=data["pipeline_status"],
        error_code=data.get("error_code"),
        error_message=data.get("error_message"),
        idempotency_key=idempotency_key,
    )

    return JsonResponse({"ai_metric_id": metric.id, "status": "ok"}, status=201)


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

    latest_metrics = AIMetric.objects.select_related('session').order_by('-agent_timestamp')[:10]

    session_analytics_rows = []
    sessions_for_summary = (
        AgentSession.objects.order_by('-started_at')
        .values("id", "username", "hostname")[:8]
    )
    for session in sessions_for_summary:
        analytics = get_session_analytics(session["id"])
        session_analytics_rows.append({
            "session_id": session["id"],
            "username": session["username"],
            "hostname": session["hostname"],
            "baseline_mature_percent": analytics["baseline_mature_ratio"] * 100,
            **analytics,
        })

    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for row in session_analytics_rows:
        risk_counts[row["risk_level"]] += 1

    top_risky_session = None
    for row in session_analytics_rows:
        if row["risk_level"] == "HIGH":
            top_risky_session = row
            break
    if not top_risky_session:
        for row in session_analytics_rows:
            if row["risk_level"] == "MEDIUM":
                top_risky_session = row
                break

    ai_total = AIMetric.objects.count()
    ai_critical = AIMetric.objects.filter(anomaly_label='critical').count()
    ai_suspicious = AIMetric.objects.filter(anomaly_label='suspicious').count()
    ai_failed = AIMetric.objects.filter(pipeline_status='failed').count()
    active_sessions = AgentSession.objects.count()
    total_agents = AgentSession.objects.count()

    if risk_counts["HIGH"] > 0 or ai_failed > 0:
        system_status = "ATTENTION REQUIRED"
        system_status_class = "danger"
    elif risk_counts["MEDIUM"] > 0:
        system_status = "MONITOR CLOSELY"
        system_status_class = "warning"
    else:
        system_status = "STABLE"
        system_status_class = "success"

    context = {
        'logs': page_obj,
        'search_query': search_query,
        'total_agents': total_agents,
        'active_sessions': active_sessions,
        'ai_total': ai_total,
        'ai_critical': ai_critical,
        'latest_ai_metrics': latest_metrics,
        'ai_suspicious': ai_suspicious,
        'ai_failed': ai_failed,
        'session_analytics_rows': session_analytics_rows,
        'risk_high_count': risk_counts["HIGH"],
        'risk_medium_count': risk_counts["MEDIUM"],
        'risk_low_count': risk_counts["LOW"],
        'system_status': system_status,
        'system_status_class': system_status_class,
        'top_risky_session': top_risky_session,
    }

    return render(request, 'monitoring/dashboard.html', context)


def health_view(request):
    total = Recording.objects.count()
    failed = Recording.objects.filter(status='FAILED').count()
    ai_total = AIMetric.objects.count()
    ai_failed = AIMetric.objects.filter(pipeline_status='failed').count()

    return JsonResponse({
        "timestamp": now(),
        "total_recordings": total,
        "total_failures": failed,
        "total_ai_metrics": ai_total,
        "total_ai_failed": ai_failed,
    })
