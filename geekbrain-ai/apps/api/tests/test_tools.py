"""Unit tests for database_tool and metrics_tool modules."""

import sqlite3
from unittest.mock import patch, MagicMock

import pytest


class TestDatabaseTool:
    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        """Create a temporary SQLite DB with test data."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """CREATE TABLE monthly_costs (
                service TEXT, month TEXT,
                compute_cost REAL, storage_cost REAL,
                network_cost REAL, third_party_cost REAL, total_cost REAL
            )"""
        )
        conn.execute(
            "INSERT INTO monthly_costs VALUES ('PaymentGW','2026-01',2000,500,300,200,3000)"
        )
        conn.execute(
            "INSERT INTO monthly_costs VALUES ('PaymentGW','2026-02',2500,600,400,500,4000)"
        )
        conn.execute(
            "INSERT INTO monthly_costs VALUES ('AuthSvc','2026-01',1000,200,100,50,1350)"
        )
        conn.execute(
            """CREATE TABLE incidents (
                incident_id TEXT, service TEXT, date TEXT,
                severity TEXT, duration_minutes INTEGER,
                root_cause TEXT, resolution TEXT,
                team_responsible TEXT, reported_by TEXT
            )"""
        )
        conn.execute(
            "INSERT INTO incidents VALUES ('INC-001','PaymentGW','2026-01-15','high',45,'timeout','restart','payments','monitoring')"
        )
        conn.commit()
        conn.close()

        with patch("src.tools.database_tool.DATABASE_PATH", str(db_path)):
            yield db_path

    def test_select_query_returns_results(self):
        from src.tools.database_tool import query_database

        result = query_database("SELECT * FROM monthly_costs WHERE service='PaymentGW'")
        assert "error" not in result
        assert result["row_count"] == 2
        assert "total_cost" in result["columns"]

    def test_rejects_non_select_queries(self):
        from src.tools.database_tool import query_database

        result = query_database("DROP TABLE monthly_costs")
        assert "error" in result
        assert "Only SELECT" in result["error"]

    def test_rejects_dangerous_keywords(self):
        from src.tools.database_tool import query_database

        result = query_database("SELECT * FROM monthly_costs; DELETE FROM monthly_costs")
        assert "error" in result

    def test_sum_aggregation(self):
        from src.tools.database_tool import query_database

        result = query_database(
            "SELECT SUM(total_cost) as total FROM monthly_costs WHERE service='PaymentGW'"
        )
        assert result["rows"][0]["total"] == 7000.0

    def test_invalid_sql_returns_error(self):
        from src.tools.database_tool import query_database

        result = query_database("SELECT * FROM nonexistent_table")
        assert "error" in result


class TestMetricsTool:
    @pytest.fixture(autouse=True)
    def mock_monitoring_api(self):
        """Mock the monitoring API HTTP calls."""
        with patch("src.tools.metrics_tool.MONITORING_API_URL", "http://mock:8000"):
            yield

    def test_get_service_status_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "service": "PaymentGW",
            "status": "healthy",
            "uptime_percent": 99.9,
            "active_alerts": [],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            from src.tools.metrics_tool import get_service_status

            result = get_service_status("PaymentGW")
            assert result["status"] == "healthy"
            assert result["uptime_percent"] == 99.9

    def test_get_service_status_not_found(self):
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch(
            "httpx.get",
            side_effect=httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            ),
        ):
            from src.tools.metrics_tool import get_service_status

            result = get_service_status("NonExistent")
            assert "error" in result

    def test_get_service_metrics_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "service": "PaymentGW",
            "latency_p99_ms": 185.0,
            "error_rate_percent": 0.3,
            "requests_per_minute": 15000,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            from src.tools.metrics_tool import get_service_metrics

            result = get_service_metrics("PaymentGW")
            assert result["latency_p99_ms"] == 185.0
            assert result["requests_per_minute"] == 15000
