import json
import os
from datetime import date
from pathlib import Path


class OracleReconciliationError(Exception):
    pass


class OracleReconciliationAdapter:
    def _load_fixture(self):
        fixture = os.getenv("ORACLE_RECONCILIATION_FIXTURE_PATH") or os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            try:
                return json.loads(Path(fixture).read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                raise OracleReconciliationError("Oracle reconciliation fixture or connection not configured.") from exc
        raise OracleReconciliationError("Oracle reconciliation fixture or connection not configured.")

    def fetch_lots(self, filters):
        payload = self._load_fixture()
        lots = payload.get("lots", [])
        normalized = []
        for lot in lots:
            normalized.append(
                {
                    **lot,
                    "data": self._parse_date(lot["data"]),
                }
            )
        return self._filter_lots(normalized, filters)

    def fetch_usages(self, nf1_list):
        payload = self._load_fixture()
        usages = payload.get("usages", [])
        allowed = set(nf1_list)
        return [usage for usage in usages if usage["nf1"] in allowed]

    @staticmethod
    def _parse_date(value):
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)

    @staticmethod
    def _filter_lots(lots, filters):
        filtered = []
        for lot in lots:
            if filters.get("nf1") and lot["nf1"] != filters["nf1"]:
                continue
            if filters.get("codpro") and lot["codpro"] != filters["codpro"]:
                continue
            if filters.get("codder") and lot["codder"] != filters["codder"]:
                continue
            filtered.append(lot)
        return filtered
