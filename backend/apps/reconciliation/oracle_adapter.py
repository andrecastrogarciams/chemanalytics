import json
import os
from datetime import date
from pathlib import Path


class OracleReconciliationError(Exception):
    pass


class OracleReconciliationAdapter:
    LOTS_QUERY = """
    SELECT
      NF1,
      DATA,
      CODPRO,
      CODDER,
      DESDER,
      PESO
    FROM USU_VBI_OPREC_V2
    WHERE DATA BETWEEN :date_start AND :date_end
    """

    USAGES_QUERY_TEMPLATE = """
    SELECT
      NF1,
      CODPRO,
      DESPRO,
      QTDUTI
    FROM USU_VBI_QUIREC_V2
    WHERE NF1 IN ({bind_names})
    """

    def _load_fixture(self):
        fixture = os.getenv("ORACLE_RECONCILIATION_FIXTURE_PATH") or os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            try:
                return json.loads(Path(fixture).read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                raise OracleReconciliationError("Oracle reconciliation fixture or connection not configured.") from exc
        raise OracleReconciliationError("Oracle reconciliation fixture or connection not configured.")

    def fetch_lots(self, filters):
        fixture = os.getenv("ORACLE_RECONCILIATION_FIXTURE_PATH") or os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
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

        query = self.LOTS_QUERY
        params = {
            "date_start": filters["date_start"],
            "date_end": filters["date_end"],
        }
        if filters.get("nf1"):
            query += " AND NF1 = :nf1"
            params["nf1"] = filters["nf1"]
        if filters.get("codpro"):
            query += " AND CODPRO = :codpro"
            params["codpro"] = filters["codpro"]
        if filters.get("codder"):
            query += " AND CODDER = :codder"
            params["codder"] = filters["codder"]

        rows = self._fetch_rows(query, params)
        return [
            {
                "nf1": str(row["NF1"]),
                "data": self._parse_date(row["DATA"]),
                "codpro": str(row["CODPRO"]),
                "codder": str(row["CODDER"]),
                "desder": row.get("DESDER"),
                "peso": row["PESO"],
            }
            for row in rows
        ]

    def fetch_usages(self, nf1_list):
        fixture = os.getenv("ORACLE_RECONCILIATION_FIXTURE_PATH") or os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            payload = self._load_fixture()
            usages = payload.get("usages", [])
            allowed = set(nf1_list)
            return [usage for usage in usages if usage["nf1"] in allowed]

        if not nf1_list:
            return []

        bind_names = []
        params = {}
        for index, nf1 in enumerate(nf1_list):
            key = f"nf1_{index}"
            bind_names.append(f":{key}")
            params[key] = nf1

        query = self.USAGES_QUERY_TEMPLATE.format(bind_names=", ".join(bind_names))
        rows = self._fetch_rows(query, params)
        return [
            {
                "nf1": str(row["NF1"]),
                "codpro": str(row["CODPRO"]),
                "despro": row["DESPRO"],
                "qtduti": row["QTDUTI"],
            }
            for row in rows
        ]

    def _fetch_rows(self, query, params):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            self._apply_query_timeout(cursor)
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            return rows
        except Exception as exc:
            raise OracleReconciliationError("Oracle reconciliation query failed.") from exc
        finally:
            connection.close()

    def _connect(self):
        try:
            import oracledb
        except ImportError as exc:
            raise OracleReconciliationError("Oracle driver not installed.") from exc

        user = os.getenv("ORACLE_USER")
        password = os.getenv("ORACLE_PASSWORD")
        dsn = os.getenv("ORACLE_DSN") or self._build_dsn(oracledb)
        if not user or not password or not dsn:
            raise OracleReconciliationError("Oracle reconciliation fixture or connection not configured.")

        try:
            connection = oracledb.connect(user=user, password=password, dsn=dsn)
            self._apply_connection_timeout(connection)
            return connection
        except Exception as exc:
            raise OracleReconciliationError("Oracle connection failed.") from exc

    @staticmethod
    def _build_dsn(oracledb):
        host = os.getenv("ORACLE_HOST")
        port = os.getenv("ORACLE_PORT", "1521")
        service_name = os.getenv("ORACLE_SERVICE_NAME")
        if not host or not service_name:
            return None
        return oracledb.makedsn(host=host, port=port, service_name=service_name)

    @staticmethod
    def _apply_connection_timeout(connection):
        if hasattr(connection, "call_timeout"):
            connection.call_timeout = 30000

    @staticmethod
    def _apply_query_timeout(cursor):
        if hasattr(cursor, "call_timeout"):
            cursor.call_timeout = 30000

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
