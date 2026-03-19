import importlib.util
import os

from django.db import connection
from django.utils.timezone import now

from apps.catalog.models import SyncJobRun


def check_database():
    engine = connection.settings_dict.get("ENGINE", "")
    if "sqlite3" in engine:
        return {
            "status": "ok",
            "engine": "sqlite",
            "details": "Bootstrap local com SQLite",
        }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"status": "ok", "engine": engine}
    except Exception as exc:
        return {"status": "error", "engine": engine, "details": str(exc)}


def check_mysql_dependency():
    configured = bool(os.getenv("MYSQL_HOST"))
    if not configured:
        return {"status": "not_configured", "details": "MYSQL_HOST ausente"}
    return {"status": "configured", "details": "Dependencia configurada para story futura"}


def check_oracle_dependency():
    configured = bool(os.getenv("ORACLE_DSN"))
    package_available = importlib.util.find_spec("oracledb") is not None

    if not configured:
        return {"status": "not_configured", "details": "ORACLE_DSN ausente"}
    if not package_available:
        return {"status": "unavailable", "details": "Pacote oracledb nao instalado neste bootstrap"}
    return {"status": "configured", "details": "Driver Oracle disponivel para integracao futura"}


def build_live_payload():
    return {
        "status": "ok",
        "service": "backend",
        "timestamp": now().isoformat(),
    }


def build_dependencies_payload():
    database = check_database()
    mysql = check_mysql_dependency()
    oracle = check_oracle_dependency()
    last_sync = check_last_sync()

    statuses = [database["status"], mysql["status"], oracle["status"], last_sync["status"]]
    overall = "ok" if all(status in {"ok", "configured", "not_configured"} for status in statuses) else "degraded"

    return {
        "status": overall,
        "timestamp": now().isoformat(),
        "dependencies": {
            "app": {"status": "ok"},
            "database": database,
            "mysql": mysql,
            "oracle": oracle,
            "last_sync": last_sync,
        },
    }


def check_last_sync():
    sync_run = SyncJobRun.objects.first()
    if not sync_run:
        return {"status": "not_available", "details": "Nenhuma sincronizacao registrada"}

    details = {
        "job_type": sync_run.job_type,
        "started_at": sync_run.started_at.isoformat(),
        "finished_at": sync_run.finished_at.isoformat() if sync_run.finished_at else None,
    }

    if sync_run.status == SyncJobRun.STATUS_SUCCESS:
        details["records_articles_upserted"] = sync_run.records_articles_upserted
        details["records_products_upserted"] = sync_run.records_products_upserted
        return {"status": "ok", "details": details}

    if sync_run.status == SyncJobRun.STATUS_ERROR:
        details["error_message"] = sync_run.error_message
        return {"status": "error", "details": details}

    return {"status": "running", "details": details}
