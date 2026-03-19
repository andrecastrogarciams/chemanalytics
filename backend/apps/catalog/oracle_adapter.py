import json
import os
from pathlib import Path
from django.utils.timezone import now


class OracleSyncError(Exception):
    pass


class OracleCatalogAdapter:
    ARTICLES_QUERY = """
    SELECT
      COD_ARTIGO,
      COD_DERIVACAO,
      ARTIGO,
      DERIVACAO
    FROM USU_VBI_ARTIGOS_SEMI_NOA
    """

    CHEMICALS_QUERY = """
    SELECT
      CODIGO_PRODUTO,
      DESCRICAO,
      COMPLEMENTO,
      CODIGO_FAMILIA,
      UNIDADE_MEDIDA,
      TIPO_PRODUTO,
      DESCRICAO_TIPO,
      STATUS,
      DATA_CONSULTA
    FROM USU_VBI_EQ_PRODUTOS
    """

    def fetch_articles(self):
        fixture = os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            data = json.loads(Path(fixture).read_text(encoding="utf-8"))
            return data["articles"]
        rows = self._fetch_rows(self.ARTICLES_QUERY)
        seen_at = now()
        return [
            {
                "codpro": row["COD_ARTIGO"],
                "codder": row["COD_DERIVACAO"],
                "article_description": row["ARTIGO"],
                "derivation_description": row["DERIVACAO"],
                "source_last_seen_at": seen_at,
            }
            for row in rows
        ]

    def fetch_chemicals(self):
        fixture = os.getenv("ORACLE_FIXTURE_PATH")
        if fixture:
            data = json.loads(Path(fixture).read_text(encoding="utf-8"))
            return data["chemicals"]
        rows = self._fetch_rows(self.CHEMICALS_QUERY)
        return [
            {
                "chemical_code": row["CODIGO_PRODUTO"],
                "description": row["DESCRICAO"],
                "complement": row["COMPLEMENTO"],
                "family_code": row["CODIGO_FAMILIA"],
                "unit_of_measure": row["UNIDADE_MEDIDA"],
                "product_type": row["TIPO_PRODUTO"],
                "product_type_description": row["DESCRICAO_TIPO"],
                "source_status": row["STATUS"],
                "active": self._infer_active(row["STATUS"]),
                "source_last_seen_at": row["DATA_CONSULTA"] or now(),
            }
            for row in rows
        ]

    def _fetch_rows(self, query):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            self._apply_query_timeout(cursor)
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            return rows
        except Exception as exc:
            raise OracleSyncError("Oracle query failed.") from exc
        finally:
            connection.close()

    def _connect(self):
        try:
            import oracledb
        except ImportError as exc:
            raise OracleSyncError("Oracle driver not installed.") from exc

        user = os.getenv("ORACLE_USER")
        password = os.getenv("ORACLE_PASSWORD")
        dsn = os.getenv("ORACLE_DSN") or self._build_dsn(oracledb)
        if not user or not password or not dsn:
            raise OracleSyncError("Oracle fixture or connection not configured.")

        try:
            connection = oracledb.connect(user=user, password=password, dsn=dsn)
            self._apply_connection_timeout(connection)
            return connection
        except Exception as exc:
            raise OracleSyncError("Oracle connection failed.") from exc

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
    def _infer_active(status):
        normalized = str(status or "").strip().upper()
        return normalized not in {"I", "INAT", "INATIVO", "N"}
