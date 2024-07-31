from tests.aws import AwsResouses
from aws_cdk.assertions import Capture, Match, Template

from vpc.vpc_stack import VpcStack


def test_vpc_properly(snapshot, app, config_multi_with_nat):
    stack = VpcStack(app, "VpcStack", service_name="Test", config=config_multi_with_nat)

    template = Template.from_stack(stack)

    # Snapshotの差分チェック
    # pytest test/vpc/test_vpc_stack_snapshot.py --snapshot-update
    assert template.to_json() == snapshot
