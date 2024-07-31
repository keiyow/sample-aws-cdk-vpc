from tests.aws import AwsResouses
from aws_cdk.assertions import Capture, Match, Template

from vpc.vpc_stack import VpcStack


def test_vpc_properly_with_nat(app, config_multi_with_nat):
    vpc_stack = VpcStack(
        app, "VpcStack", service_name="Test", config=config_multi_with_nat
    )

    template = Template.from_stack(vpc_stack)

    # サブネット数
    template.resource_count_is("AWS::EC2::Subnet", 4)
    # Nat Gateway数
    template.resource_count_is("AWS::EC2::NatGateway", 2)

    # private1のGatewayネットワーク
    template.has_resource_properties(
        "AWS::EC2::Route",
        Match.object_equals(
            {
                "DestinationCidrBlock": "0.0.0.0/0",
                "NatGatewayId": {"Ref": "TestNatGatewaypublic1"},
                "RouteTableId": {"Ref": "TestRouteprivate1"},
            }
        ),
    )

    # private2のGatewayネットワーク
    template.has_resource_properties(
        "AWS::EC2::Route",
        Match.object_equals(
            {
                "DestinationCidrBlock": "0.0.0.0/0",
                "NatGatewayId": {"Ref": "TestNatGatewaypublic2"},
                "RouteTableId": {"Ref": "TestRouteprivate2"},
            }
        ),
    )


def test_vpc_properly_with_no_nat(app, config_multi_with_no_nat):
    vpc_stack = VpcStack(
        app, "VpcStack", service_name="Test", config=config_multi_with_no_nat
    )

    template = Template.from_stack(vpc_stack)

    # サブネット数
    template.resource_count_is("AWS::EC2::Subnet", 4)
    # Nat Gateway数
    template.resource_count_is("AWS::EC2::NatGateway", 0)

    # private1のGatewayネットワーク(使えない)
    template.has_resource_properties(
        "AWS::EC2::Route",
        Match.object_equals(
            {
                "DestinationCidrBlock": "0.0.0.0/0",
                "GatewayId": {"Ref": "TestGateway"},
                "RouteTableId": {"Ref": "TestRoutePublic"},
            }
        ),
    )

    # private2のGatewayネットワーク(使えない)
    template.has_resource_properties(
        "AWS::EC2::Route",
        Match.object_equals(
            {
                "DestinationCidrBlock": "0.0.0.0/0",
                "GatewayId": {"Ref": "TestGateway"},
                "RouteTableId": {"Ref": "TestRoutePublic"},
            }
        ),
    )
