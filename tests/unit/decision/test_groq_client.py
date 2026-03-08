"""Tests for GroqClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.decision.groq_client import GROQ_API_URL, GroqClient


@pytest.fixture
def mock_settings():
    with patch("src.decision.groq_client.get_settings") as mock_s:
        settings = MagicMock()
        settings.groq_api_key = "test-api-key"
        mock_s.return_value = settings
        yield settings


@pytest.fixture
def client(mock_settings):
    return GroqClient(model="test-model")


class TestGroqClientInit:
    def test_default_model(self, mock_settings):
        c = GroqClient()
        assert c._model == "llama-3.3-70b-versatile"

    def test_custom_model(self, mock_settings):
        c = GroqClient(model="custom-model")
        assert c._model == "custom-model"

    def test_stores_api_key(self, client):
        assert client._api_key == "test-api-key"


class TestGroqClientChat:
    def test_successful_chat(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello world"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            result = client.chat(
                [{"role": "user", "content": "Hi"}],
                temperature=0.5,
                max_tokens=100,
            )

        assert result == "Hello world"
        mock_post.assert_called_once_with(
            GROQ_API_URL,
            headers={
                "Authorization": "Bearer test-api-key",
                "Content-Type": "application/json",
            },
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hi"}],
                "temperature": 0.5,
                "max_tokens": 100,
            },
        )

    def test_missing_api_key_raises(self, mock_settings):
        mock_settings.groq_api_key = ""
        with patch("src.decision.groq_client.get_settings", return_value=mock_settings):
            c = GroqClient()
        with pytest.raises(ValueError, match="GROQ_API_KEY not configured"):
            c.chat([{"role": "user", "content": "Hi"}])

    def test_http_error_propagates(self, client):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=MagicMock(),
        )

        with patch.object(client._client, "post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                client.chat([{"role": "user", "content": "Hi"}])

    def test_default_params(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", return_value=mock_response) as mock_post:
            client.chat([{"role": "user", "content": "Hi"}])

        call_json = mock_post.call_args[1]["json"]
        assert call_json["temperature"] == 0.7
        assert call_json["max_tokens"] == 2048


class TestGroqClientClose:
    def test_close(self, client):
        with patch.object(client._client, "close") as mock_close:
            client.close()
        mock_close.assert_called_once()
