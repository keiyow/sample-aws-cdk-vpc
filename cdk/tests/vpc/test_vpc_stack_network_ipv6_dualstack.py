from tests.aws import AwsResouses
from aws_cdk.assertions import Capture, Match, Template

from vpc.vpc_stack import VpcStack


def test_vpc_properly_with_nat_ipv6_dualstack(
    app, config_multi_with_nat_ipv6_dualstack
):
    vpc_stack = VpcStack(
        app,
        "VpcStack",
        service_name="Test",
        config=config_multi_with_nat_ipv6_dualstack,
    )

    template = Template.from_stack(vpc_stack)

    # サブネット数
    template.resource_count_is("AWS::EC2::Subnet", 4)
    # Nat Gateway数
    template.resource_count_is("AWS::EC2::NatGateway", 2)

    # private1のGatewayネットワーク(IPv4)
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

    # private2のGatewayネットワーク(IPv4)
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

    # Egress Only Gateway数
    template.resource_count_is("AWS::EC2::EgressOnlyInternetGateway", 1)

    # private1のGatewayネットワーク(IPv6)
    template.has_resource_properties(
        "AWS::EC2::Route",
        Match.object_equals(
            {
                "DestinationIpv6CidrBlock": "::/0",
                "EgressOnlyInternetGatewayId": {"Ref": "TestEgressGateway"},
                "RouteTableId": {"Ref": "TestRouteprivate1"},
            }
        ),
    )

    # private2のGatewayネットワーク(IPv6)
    template.has_resource_properties(
        "AWS::EC2::Route",
        Match.object_equals(
            {
                "DestinationIpv6CidrBlock": "::/0",
                "EgressOnlyInternetGatewayId": {"Ref": "TestEgressGateway"},
                "RouteTableId": {"Ref": "TestRouteprivate2"},
            }
        ),
    )

    # サブネットのプロパティチェック
    template.has_resource_properties(
        "AWS::EC2::Subnet",
        Match.object_equals(
            {
                "AssignIpv6AddressOnCreation": True,
                "AvailabilityZone": Match.any_value(),
                "CidrBlock": Match.any_value(),
                "Ipv6CidrBlock": Match.any_value(),
                "MapPublicIpOnLaunch": Match.any_value(),
                "Tags": Match.any_value(),
                "VpcId": {"Ref": "TestVPC"},
            }
        ),
    )
