import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .simulation_core import NETWORK_SCENARIOS, SimulationEngine


_ENGINE = SimulationEngine("community_network")


def network_simulator(request):
    return render(request, "network_simulator/index.html")


def simulation_state(request):
    return JsonResponse(_ENGINE.snapshot(), json_dumps_params={"ensure_ascii": False})


@csrf_exempt
def reset_simulation(request):
    global _ENGINE
    payload = _json_payload(request)
    network_type = payload.get("network_type", "community_network")
    seed = payload.get("seed")
    if network_type not in NETWORK_SCENARIOS:
        return JsonResponse({"error": "不支持的网络结构"}, status=400, json_dumps_params={"ensure_ascii": False})
    _ENGINE = SimulationEngine(network_type, seed=seed)
    return JsonResponse(_ENGINE.snapshot(), json_dumps_params={"ensure_ascii": False})


@csrf_exempt
def step_simulation(request):
    payload = _json_payload(request)
    intervention = payload.get("intervention")
    try:
        return JsonResponse(_ENGINE.step(intervention=intervention), json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        import traceback
        return JsonResponse(
            {"error": str(e), "traceback": traceback.format_exc()},
            status=500,
            json_dumps_params={"ensure_ascii": False},
        )


@csrf_exempt
def apply_intervention(request):
    payload = _json_payload(request)
    intervention = {
        "intervention_type": payload.get("intervention_type", "targeted_clarification"),
        "target_nodes": payload.get("target_nodes"),
        "content": payload.get("content", "官方发布了完整时间线和现场证据说明。"),
        "credibility": payload.get("credibility", 0.85),
        "emotion_tone": payload.get("emotion_tone", "calm"),
    }
    return JsonResponse(_ENGINE.step(intervention=intervention), json_dumps_params={"ensure_ascii": False})


def _json_payload(request):
    if request.method != "POST" or not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}
