from app.mcp.github_client import GitHubMCPConfig


def test_default_config_is_read_only() -> None:
    assert GitHubMCPConfig().read_only is True


def test_docker_parameters_use_loopback_callback() -> None:
    config = GitHubMCPConfig(callback_port=8085, read_only=True)
    params = config.docker_parameters()

    assert params.command == "docker"
    assert "127.0.0.1:8085:8085" in params.args
    assert "GITHUB_OAUTH_CALLBACK_PORT" in params.args
    assert params.env["GITHUB_READ_ONLY"] == "1"
