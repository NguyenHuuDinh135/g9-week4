import httpx

from src.config import MONITORING_API_URL


def get_service_list() -> dict:
    """Get list of all services from monitoring API."""
    try:
        resp = httpx.get(f"{MONITORING_API_URL}/services", timeout=10)
        resp.raise_for_status()
        return {"services": resp.json()}
    except httpx.HTTPError as e:
        return {"error": f"API error: {e}"}


def get_service_status(service_name: str) -> dict:
    """Get current status of a service (uptime, alerts, health)."""
    try:
        resp = httpx.get(f"{MONITORING_API_URL}/status/{service_name}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Service '{service_name}' not found"}
        return {"error": f"API error: {e}"}
    except httpx.HTTPError as e:
        return {"error": f"API error: {e}"}


def get_service_metrics(service_name: str) -> dict:
    """Get current live metrics for a service (latency, error_rate, rpm, cpu, memory)."""
    try:
        resp = httpx.get(f"{MONITORING_API_URL}/metrics/{service_name}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Service '{service_name}' not found"}
        return {"error": f"API error: {e}"}
    except httpx.HTTPError as e:
        return {"error": f"API error: {e}"}


def get_incidents(service_name: str | None = None) -> dict:
    """Get incident records from monitoring API."""
    try:
        url = f"{MONITORING_API_URL}/incidents"
        if service_name:
            url = f"{url}/{service_name}"
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        return {"incidents": resp.json()}
    except httpx.HTTPError as e:
        return {"error": f"API error: {e}"}
