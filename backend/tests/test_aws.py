from unittest.mock import patch

from eventforge.core.aws import boto_client
from eventforge.core.config import Settings


def test_boto_client_uses_static_credentials_for_localstack() -> None:
    settings = Settings(
        aws_endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    with patch("eventforge.core.aws.boto3.client") as mock_client:
        boto_client("events", settings)

    kwargs = mock_client.call_args.kwargs
    assert kwargs["endpoint_url"] == "http://localhost:4566"
    assert kwargs["aws_access_key_id"] == "test"
    assert kwargs["aws_secret_access_key"] == "test"


def test_boto_client_uses_default_chain_on_real_aws() -> None:
    settings = Settings(
        aws_endpoint_url="",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    with patch("eventforge.core.aws.boto3.client") as mock_client:
        boto_client("events", settings)

    kwargs = mock_client.call_args.kwargs
    assert "endpoint_url" not in kwargs
    assert "aws_access_key_id" not in kwargs
    assert "aws_secret_access_key" not in kwargs
