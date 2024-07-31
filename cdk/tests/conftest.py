import pytest
from aws_cdk import Environment
from tests.aws import AwsResouses


@pytest.fixture(scope="session")
def default_conf():
    return {"remote_docker": False}


@pytest.fixture(scope="function")
def app():
    yield AwsResouses.create_app()


@pytest.fixture(scope="session")
def default_cdk_environment():
    return Environment(account="111111111111", region="us-east-1")
