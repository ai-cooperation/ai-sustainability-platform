"""Tests for ClimatiqConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests as requests_lib

from src.connectors.base import ConnectorError
from src.connectors.carbon.climatiq import ClimatiqConnector

SAMPLE_RESPONSE = {
    "co2e": 0.42,
    "co2e_unit": "kg",
    "activity_id": "electricity-supply_grid-source_residual_mix",
    "emission_factor": {
        "id": "ef-123",
        "name": "Grid electricity - residual mix",
    },
    "source": "DEFRA 2023",
}


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings = MagicMock()
        settings.climatiq_api_key = "test-api-key"
        mock_settings.return_value = settings
        return ClimatiqConnector()


@pytest.fixture
def connector_no_key():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings = MagicMock()
        settings.climatiq_api_key = ""
        mock_settings.return_value = settings
        return ClimatiqConnector()


class TestClimatiqConnector:
    def test_name(self, connector: ClimatiqConnector):
        assert connector.name == "climatiq"

    def test_domain(self, connector: ClimatiqConnector):
        assert connector.domain == "carbon"

    def test_fetch_no_api_key(self, connector_no_key: ClimatiqConnector):
        with pytest.raises(ConnectorError, match="API key is not configured"):
            connector_no_key.fetch(
                emission_factor_id="test",
                activity_value=1,
                activity_unit="kWh",
            )

    def test_fetch_missing_params(self, connector: ClimatiqConnector):
        with pytest.raises(ConnectorError, match="requires"):
            connector.fetch()

    @patch("src.connectors.carbon.climatiq.requests.post")
    def test_fetch_success(self, mock_post, connector: ClimatiqConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = connector.fetch(
            emission_factor_id="ef-123",
            activity_value=100,
            activity_unit="kWh",
        )

        assert result["co2e"] == 0.42
        mock_post.assert_called_once()

        # Verify auth header
        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["Authorization"] == "Bearer test-api-key"

        # Verify correct payload structure (energy params for kWh)
        sent_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert sent_json["emission_factor"]["activity_id"] == "ef-123"
        assert sent_json["parameters"]["energy"] == 100
        assert sent_json["parameters"]["energy_unit"] == "kWh"

    @patch("src.connectors.carbon.climatiq.requests.post")
    def test_fetch_weight_unit(self, mock_post, connector: ClimatiqConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        connector.fetch(
            emission_factor_id="ef-456",
            activity_value=50,
            activity_unit="kg",
        )

        call_kwargs = mock_post.call_args
        sent_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert sent_json["parameters"]["weight"] == 50
        assert sent_json["parameters"]["weight_unit"] == "kg"

    @patch("src.connectors.carbon.climatiq.requests.post")
    def test_fetch_money_unit(self, mock_post, connector: ClimatiqConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        connector.fetch(
            emission_factor_id="ef-789",
            activity_value=1000,
            activity_unit="USD",
        )

        call_kwargs = mock_post.call_args
        sent_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert sent_json["parameters"]["money"] == 1000
        assert sent_json["parameters"]["money_unit"] == "USD"

    @patch("src.connectors.carbon.climatiq.requests.post")
    def test_fetch_with_body_override(self, mock_post, connector: ClimatiqConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        custom_body = {"custom_field": "custom_value"}
        connector.fetch(
            emission_factor_id="ef-123",
            activity_value=1,
            activity_unit="kWh",
            body=custom_body,
        )

        call_kwargs = mock_post.call_args
        sent_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert sent_json == custom_body

    @patch("src.connectors.carbon.climatiq.requests.post")
    def test_fetch_http_error(self, mock_post, connector: ClimatiqConnector):
        mock_post.side_effect = requests_lib.RequestException("Forbidden")

        with pytest.raises(ConnectorError, match="request failed"):
            connector.fetch(
                emission_factor_id="ef-123",
                activity_value=1,
                activity_unit="kWh",
            )

    def test_normalize_success(self, connector: ClimatiqConnector):
        df = connector.normalize(SAMPLE_RESPONSE)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "co2e" in df.columns
        assert "co2e_unit" in df.columns
        assert "source" in df.columns
        assert len(df) == 1
        assert df["co2e"].iloc[0] == 0.42
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_invalid_input(self, connector: ClimatiqConnector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2, 3])

    def test_normalize_missing_co2e(self, connector: ClimatiqConnector):
        with pytest.raises(ConnectorError, match="Missing 'co2e'"):
            connector.normalize({"activity_id": "test"})
