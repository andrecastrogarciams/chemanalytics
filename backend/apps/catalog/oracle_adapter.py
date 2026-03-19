import json
import os
from pathlib import Path


class OracleSyncError(Exception):
    pass


class OracleCatalogAdapter:
    def fetch_articles(self):
        fixture = os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            data = json.loads(Path(fixture).read_text(encoding="utf-8"))
            return data["articles"]
        raise OracleSyncError("Oracle fixture or connection not configured.")

    def fetch_chemicals(self):
        fixture = os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            data = json.loads(Path(fixture).read_text(encoding="utf-8"))
            return data["chemicals"]
        raise OracleSyncError("Oracle fixture or connection not configured.")
