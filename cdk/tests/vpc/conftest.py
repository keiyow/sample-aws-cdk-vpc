import pytest
import os
from tests.helper import Helper


@pytest.fixture(scope="session")
def config_dir():
    return os.path.join(os.path.dirname(__file__), "config")


@pytest.fixture(scope="session")
def config_multi_with_nat(config_dir):
    return Helper.load_config(config_dir, "multi_with_nat.yaml")


@pytest.fixture(scope="session")
def config_multi_with_single_nat(config_dir):
    return Helper.load_config(config_dir, "multi_with_single_nat.yaml")


@pytest.fixture(scope="session")
def config_multi_with_no_nat(config_dir):
    return Helper.load_config(config_dir, "multi_with_no_nat.yaml")


@pytest.fixture(scope="session")
def config_single_with_nat(config_dir):
    return Helper.load_config(config_dir, "single_with_nat.yaml")


@pytest.fixture(scope="session")
def config_single_with_no_nat(config_dir):
    return Helper.load_config(config_dir, "single_with_no_nat.yaml")


@pytest.fixture(scope="session")
def config_multi_with_nat_ipv6_dualstack(config_dir):
    return Helper.load_config(config_dir, "multi_with_nat_ipv6_dualstack.yaml")
