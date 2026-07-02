from eventforge.core.config import Settings


def test_api_keys_strip_trailing_newlines_and_spaces() -> None:
    settings = Settings(
        openai_api_key="sk-test\n",
        anthropic_api_key=" sk-ant-test \n",
        tavily_api_key="tvly-test\r\n",
    )
    assert settings.openai_api_key == "sk-test"
    assert settings.anthropic_api_key == "sk-ant-test"
    assert settings.tavily_api_key == "tvly-test"


def test_postgres_password_strips_whitespace() -> None:
    settings = Settings(postgres_password=" changeme\n")
    assert settings.postgres_password == "changeme"


def test_mock_external_apis_auto_enabled_for_local_environment() -> None:
    settings = Settings(environment="local")
    assert settings.use_mock_external_apis is True
