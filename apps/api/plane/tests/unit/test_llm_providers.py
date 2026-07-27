import os
from unittest.mock import patch, MagicMock
import pytest

from plane.app.views.external.base import (
    SUPPORTED_PROVIDERS,
    DeepSeekProvider,
    GeminiProvider,
    OpenAIProvider,
    CustomProvider,
    get_llm_config,
    get_llm_response,
)


@pytest.mark.unit
def test_supported_providers_registration():
    assert "deepseek" in SUPPORTED_PROVIDERS
    assert "gemini" in SUPPORTED_PROVIDERS
    assert "openai" in SUPPORTED_PROVIDERS
    assert "custom" in SUPPORTED_PROVIDERS
    assert "ollama" in SUPPORTED_PROVIDERS

    assert DeepSeekProvider.default_model == "deepseek-chat"
    assert "deepseek-reasoner" in DeepSeekProvider.models
    assert DeepSeekProvider.default_base_url == "https://api.deepseek.com/v1"

    assert GeminiProvider.default_model == "gemini-2.0-flash"
    assert "gemini-2.0-flash" in GeminiProvider.models
    assert "gemini-1.5-pro" in GeminiProvider.models


@pytest.mark.unit
@patch("plane.app.views.external.base.get_configuration_value")
def test_get_llm_config_deepseek_defaults(mock_get_config):
    mock_get_config.return_value = ("sk-deepseek-key", "deepseek", "deepseek-chat", None)

    api_key, model, provider, base_url = get_llm_config()

    assert api_key == "sk-deepseek-key"
    assert model == "deepseek-chat"
    assert provider == "deepseek"
    assert base_url == "https://api.deepseek.com/v1"


@pytest.mark.unit
@patch("plane.app.views.external.base.get_configuration_value")
def test_get_llm_config_custom_base_url(mock_get_config):
    custom_url = "http://localhost:11434/v1"
    mock_get_config.return_value = (None, "custom", "llama3", custom_url)

    api_key, model, provider, base_url = get_llm_config()

    assert model == "llama3"
    assert provider == "custom"
    assert base_url == custom_url


@pytest.mark.unit
@patch("plane.app.views.external.base.OpenAI")
def test_get_llm_response_custom_base_url(mock_openai_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Mocked AI Response"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_cls.return_value = mock_client

    text, error = get_llm_response(
        task="Summarize",
        prompt="Hello world",
        api_key="sk-test",
        model="deepseek-chat",
        provider="deepseek",
        base_url="https://api.deepseek.com/v1",
    )

    assert error is None
    assert text == "Mocked AI Response"
    mock_openai_cls.assert_called_once_with(api_key="sk-test", base_url="https://api.deepseek.com/v1")
