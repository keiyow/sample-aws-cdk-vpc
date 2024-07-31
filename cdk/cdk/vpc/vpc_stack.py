from aws_cdk import Stack, CfnOutput, CfnTag, Fn
from constructs import Construct
from aws_cdk import aws_ec2 as ec2


class VpcStack(Stack):
    def __init__(
        self, scope: Construct, id: str, service_name: str, config, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = {}

        if config:
            # VPC作成
            cfn_vpc = self._create_vpc("{}-VPC".format(service_name), config["vpcCidr"])

            # サブネットを格納
            cfn_subnets = {}
            # Routeを格納
            cfn_route = {}

            # IPv4用のインターネットゲートウェイ作成
            cfn_internet_gateway = self._create_internet_gateway(
                "{}-Gateway".format(service_name)
            )

            cfn_egress_internet_gateway = None
            ipv6_cidr = None

            # VPCにインターネットゲートウェイをアタッチ
            self._create_gateway_attachment(
                "{}-GatewayAttachment".format(service_name),
                cfn_vpc.ref,
                cfn_internet_gateway.ref,
            )

            # 公開ネットワーク側のルートテーブル作成
            cfn_public_route_table = self._create_route_table(
                "{}-Route-Public".format(service_name), cfn_vpc.ref
            )

            # インターネットゲートウェイへのルーティング作成
            cfn_route["public"] = self._create_route(
                "{}-PublicRoute".format(service_name),
                cfn_public_route_table.ref,
                gateway_id=cfn_internet_gateway.ref,
            )

            # IPv6関連の作成
            # https://docs.aws.amazon.com/ja_jp/vpc/latest/userguide/vpc-migrate-ipv6.html
            if "ipv6" in config and config["ipv6"]:
                # IPv6用のEgressインターネットゲートウェイの作成
                cfn_egress_internet_gateway = self._create_egress_internet_gateway(
                    "{}-EgressGateway".format(service_name),
                    vpc_id=cfn_vpc.ref,
                )

                ipv6_cidr = self._create_cidr_block(
                    "{}-IPv6-CidrBlock".format(service_name),
                    cfn_vpc.ref,
                    amazon_provided_ipv6_cidr_block=(
                        config["amazon_provided_ipv6_cidr_block"]
                        if "amazon_provided_ipv6_cidr_block" in config
                        else None
                    ),
                    ipv6_cidr_block=(
                        config["ipv6_cidr"] if "ipv6_cidr" in config else None
                    ),
                )

                cfn_route["public-ipv6"] = self._create_route(
                    "{}-PublicRoute-IPv6".format(service_name),
                    cfn_public_route_table.ref,
                    gateway_id=cfn_internet_gateway.ref,
                    ipv6=config["ipv6"],
                )

            # 公開ネットワーク作成Loop
            for index, subnets in enumerate(config["publicSubnets"]):

                # サブネットの作成
                subnet_name = "{}-Subnet-{}".format(service_name, subnets["name"])
                cfn_subnet = self._create_subnet(
                    subnet_name,
                    cfn_vpc.ref,
                    cidr_block=subnets["cidr"] if "cidr" in subnets else None,
                    availability_zone=subnets["az"],
                    publicflag=True,
                    # ipv6_cidr_block=(
                    #     ipv6_cidr.ref
                    #     if ipv6_cidr and ("ipv6" in subnets and subnets["ipv6"])
                    #     else None
                    # ),
                )
                if ipv6_cidr:
                    cfn_subnet.add_dependency(ipv6_cidr)

                if "ipv6" in subnets and subnets["ipv6"]:
                    cfn_subnet.ipv6_cidr_block = Fn.select(
                        index,
                        Fn.cidr(
                            Fn.select(0, cfn_vpc.attr_ipv6_cidr_blocks),
                            256,
                            "64",
                        ),
                    )
                    cfn_subnet.assign_ipv6_address_on_creation = True

                cfn_subnets[subnets["name"]] = dict(subnet=cfn_subnet)

                # サブネットにルートテーブルを適用
                self._subnet_route_table_association(
                    subnet_name + "-Association",
                    subnet_id=cfn_subnet.ref,
                    route_table_id=cfn_public_route_table.ref,
                )

                # Natが有効の場合
                if "nat" in subnets and subnets["nat"]:
                    # Natgateway用のEIP
                    cfn_nat_ip = self._create_eip(
                        "{}-EIP-{}".format(service_name, subnets["name"])
                    )

                    cfn_subnets[subnets["name"]]["natip"] = cfn_nat_ip

                    # Nat Gatewayの作成
                    CfnNatGateway = self._create_nat_gateway(
                        "{}-NatGateway-{}".format(service_name, subnets["name"]),
                        cfn_subnet.ref,
                        cfn_nat_ip.get_att("AllocationId").to_string(),
                    )

                    cfn_subnets[subnets["name"]]["nat"] = CfnNatGateway

            # 非公開ネットワーク作成Loop
            for index, subnets in enumerate(config["privateSubnets"]):
                # サブネットの作成
                subnet_name = "{}-Subnet-{}".format(service_name, subnets["name"])
                cfn_subnet = self._create_subnet(
                    subnet_name,
                    cfn_vpc.ref,
                    cidr_block=subnets["cidr"],
                    availability_zone=subnets["az"],
                    publicflag=False,
                )
                if ipv6_cidr:
                    cfn_subnet.add_dependency(ipv6_cidr)

                if "ipv6" in subnets and subnets["ipv6"]:
                    cfn_subnet.ipv6_cidr_block = Fn.select(
                        index + len(config["publicSubnets"]),
                        Fn.cidr(
                            Fn.select(0, cfn_vpc.attr_ipv6_cidr_blocks),
                            256,
                            "64",
                        ),
                    )
                    cfn_subnet.assign_ipv6_address_on_creation = True

                cfn_subnets[subnets["name"]] = dict(subnet=cfn_subnet)

                # RouteTableの作成
                route_table_name = "{}-Route-{}".format(service_name, subnets["name"])
                cfn_route_table = self._create_route_table(
                    route_table_name, cfn_vpc.ref
                )

                # サブネットにルートテーブルを適用
                self._subnet_route_table_association(
                    subnet_name + "-Association",
                    subnet_id=cfn_subnet.ref,
                    route_table_id=cfn_route_table.ref,
                )

                # プライベートのIPv6がインターネットに出るためのルーティング
                if "ipv6" in subnets and subnets["ipv6"]:
                    ipv6Route = self._create_route(
                        "{}-{}-IPv6".format(service_name, subnets["name"]),
                        route_table_id=cfn_route_table.ref,
                        egress_only_internet_gateway_id=cfn_egress_internet_gateway.ref,
                    )

                    cfn_route["{}-IPv6".format(subnets["name"])] = ipv6Route

                # Natが有効の場合
                if subnets["nat"]:
                    # 非公開ネットワークが使用する公開ネットワーク側のNatgatewayId
                    nat_gateway_id = cfn_subnets[subnets["natRoute"]]["nat"].ref
                    # NatGateway経由でInternetでるルーティングを追加
                    natRoute = self._create_route(
                        "{}-{}-nat".format(service_name, subnets["name"]),
                        route_table_id=cfn_route_table.ref,
                        natgateway_id=nat_gateway_id,
                    )
                    cfn_route[subnets["name"]] = natRoute

                    if "ipv6" in subnets and subnets["ipv6"]:
                        natIpv6Route = self._create_route(
                            "{}-{}-nat-ipv6".format(service_name, subnets["name"]),
                            route_table_id=cfn_route_table.ref,
                            natgateway_id=nat_gateway_id,
                            ipv6=True,
                        )

                        cfn_route["{}-IPv6".format(subnets["name"])] = natIpv6Route

                        if "dns64" in subnets and subnets["dns64"]:
                            cfn_subnet.enable_dns64 = True

                else:
                    # # 単純なルーティング
                    # route = self._create_route(
                    #     service_name + "-" + subnets["name"],
                    #     route_table_id=cfn_route_table.ref,
                    # )

                    cfn_route[subnets["name"]] = None

            # VPCのexport
            CfnOutput(
                self,
                "VPC",
                value=cfn_vpc.ref,
                export_name="{}-VPC".format(service_name),
            )
            for network in cfn_subnets:
                CfnOutput(
                    self,
                    "Subnet-{}".format(network),
                    value=cfn_subnets[network]["subnet"].ref,
                    export_name="{}-Subnet-{}".format(service_name, network),
                )

            self.vpc = {"vpc": cfn_vpc, "route": cfn_route, "subnets": cfn_subnets}

    def _create_vpc(self: Stack, name: str, cidr: str) -> ec2.CfnVPC:
        """カスタムVPCを作成

        Args:
            self (Stack): Stack
            name (str): VPC Name
            cidr (str): VPC CIDR Block

        Returns:
            ec2.CfnVPC:
        """
        return ec2.CfnVPC(
            self,
            name,
            cidr_block=cidr,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags=[CfnTag(key="Name", value=name)],
        )

    def _create_internet_gateway(self: Stack, name: str) -> ec2.CfnInternetGateway:
        """インターネットゲートウェイを作成

        Args:
            self (Stack): Stack
            name (str): Internetgateway Name

        Returns:
            ec2.CfnInternetGateway:
        """
        return ec2.CfnInternetGateway(self, name, tags=[CfnTag(key="Name", value=name)])

    def _create_gateway_attachment(
        self: Stack, name: str, vpc_id: str, internet_gateway_id: str
    ) -> ec2.CfnVPCGatewayAttachment:
        """インターネットゲートウェイをVPCに繋げる

        Args:
            self (Stack): Stack
            name (str): Gateway Attachment Name
            vpc_id (str): VPC Id

        Returns:
            ec2.CfnVPCGatewayAttachment:
        """
        return ec2.CfnVPCGatewayAttachment(
            self, name, vpc_id=vpc_id, internet_gateway_id=internet_gateway_id
        )

    def _create_egress_internet_gateway(
        self: Stack, name: str, vpc_id: str
    ) -> ec2.CfnEgressOnlyInternetGateway:
        """IPv6専用のEgressインターネットゲートウェイの作成

        Args:
            self (Stack): Stack
            name (str): Egress Internetgateway Name
            vpc_id (str): VPC Id
        """
        return ec2.CfnEgressOnlyInternetGateway(self, name, vpc_id=vpc_id)

    def _create_cidr_block(
        self: Stack,
        name: str,
        vpc_id: str,
        amazon_provided_ipv6_cidr_block: bool = None,
        ipv6_cidr_block: str = None,
        ipv6_ipam_pool_id: str = None,
        ipv6_pool: str = None,
        cidr_block: str = None,
    ) -> ec2.CfnVPCCidrBlock:
        """CIDRブロックの作成

        Args:
            self (Stack): _description_
            name (str): _description_
            vpc_id (str): _description_
            amazon_provided_ipv6_cidr_block (bool, optional): _description_. Defaults to None.
            ipv6_cidr_block (str, optional): _description_. Defaults to None.
            ipv6_ipam_pool_id (str, optional): _description_. Defaults to None.
            ipv6_pool (str, optional): _description_. Defaults to None.
            cidr_block (str, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        return ec2.CfnVPCCidrBlock(
            self,
            name,
            vpc_id=vpc_id,
            cidr_block=cidr_block,
            amazon_provided_ipv6_cidr_block=amazon_provided_ipv6_cidr_block,
            ipv6_cidr_block=ipv6_cidr_block,
            ipv6_ipam_pool_id=ipv6_ipam_pool_id,
            ipv6_pool=ipv6_pool,
        )

    def _create_subnet(
        self,
        name,
        vpc_id,
        cidr_block: str = None,
        availability_zone: str = None,
        publicflag: bool = True,
        ipv6_cidr_block: str = None,
    ) -> ec2.CfnSubnet:
        """VPCサブネットの作成

        Args:
            name (_type_): _description_
            vpc_id (_type_): _description_
            subnets (_type_): _description_
            publicflag (bool): _description_

        Returns:
            ec2.CfnSubnet: _description_
        """
        return ec2.CfnSubnet(
            self,
            name,
            cidr_block=cidr_block,
            availability_zone=availability_zone,
            vpc_id=vpc_id,
            map_public_ip_on_launch=publicflag,
            ipv6_cidr_block=ipv6_cidr_block,
            tags=[CfnTag(key="Name", value=name)],
        )

    def _create_route_table(self: Stack, name: str, vpc_id: str) -> ec2.CfnRouteTable:
        """ルートテーブルの作成

        Args:
            self (Stack): _description_
            name (str): _description_
            vpc_id (str): _description_

        Returns:
            ec2.CfnRouteTable: _description_
        """
        return ec2.CfnRouteTable(
            self, name, vpc_id=vpc_id, tags=[CfnTag(key="Name", value=name)]
        )

    def _subnet_route_table_association(
        self, name, subnet_id, route_table_id
    ) -> ec2.CfnSubnetRouteTableAssociation:
        """ルートテーブルの割り当て

        Args:
            name (_type_): _description_
            subnet_id (_type_): _description_
            route_table_id (_type_): _description_

        Returns:
            ec2.CfnSubnetRouteTableAssociation: _description_
        """
        return ec2.CfnSubnetRouteTableAssociation(
            self, name, subnet_id=subnet_id, route_table_id=route_table_id
        )

    def _create_eip(self: Stack, name: str) -> ec2.CfnEIP:
        """Elastic IPの生成

        Args:
            self (Stack): _description_
            name (str): _description_

        Returns:
            ec2.CfnEIP: _description_
        """
        return ec2.CfnEIP(self, name, domain="vpc")

    def _create_nat_gateway(
        self: Stack, name: str, subnet_id: str, allocation_id: str
    ) -> ec2.CfnNatGateway:
        """NAT Gatewayの作成

        Args:
            self (Stack): _description_
            name (str): _description_
            subnet_id (str): _description_
            allocation_id (str): _description_

        Returns:
            ec2.CfnNatGateway: _description_
        """
        return ec2.CfnNatGateway(
            self, name, subnet_id=subnet_id, allocation_id=allocation_id
        )

    def _create_route(
        self: Stack,
        name: str,
        route_table_id: str,
        gateway_id: str = "",
        natgateway_id: str = "",
        egress_only_internet_gateway_id: str = None,
        ipv6: bool = False,
    ) -> ec2.CfnRoute:
        """ルーティングの作成

        Args:
            self (Stack): _description_
            name (str): _description_
            route_table_id (str): _description_
            gateway_id (str, optional): _description_. Defaults to "".
            natgateway_id (str, optional): _description_. Defaults to "".

        Returns:
            ec2.CfnRoute: _description_
        """
        # ゲートウェイIDがある時
        if gateway_id:
            return ec2.CfnRoute(
                self,
                name,
                gateway_id=gateway_id,
                destination_cidr_block="0.0.0.0/0" if not ipv6 else None,
                destination_ipv6_cidr_block="::/0" if ipv6 else None,
                route_table_id=route_table_id,
            )
        # NAT ゲートウェイがある時
        elif natgateway_id:
            return ec2.CfnRoute(
                self,
                name,
                nat_gateway_id=natgateway_id,
                destination_cidr_block="0.0.0.0/0" if not ipv6 else None,
                # https://docs.aws.amazon.com/ja_jp/vpc/latest/userguide/nat-gateway-nat64-dns64.html#nat-gateway-nat64-what-is
                destination_ipv6_cidr_block="64:ff9b::/96" if ipv6 else None,
                route_table_id=route_table_id,
            )
        elif egress_only_internet_gateway_id:
            return ec2.CfnRoute(
                self,
                name,
                egress_only_internet_gateway_id=egress_only_internet_gateway_id,
                destination_ipv6_cidr_block="::/0",
                route_table_id=route_table_id,
            )
        else:
            return ec2.CfnRoute(
                self,
                name,
                destination_cidr_block="0.0.0.0/0",
                route_table_id=route_table_id,
            )
