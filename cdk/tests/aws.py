from aws_cdk import Stack, App
from constructs import Construct
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_lambda
from aws_cdk import aws_ec2
from aws_cdk import aws_rds
from aws_cdk import aws_dynamodb
from aws_cdk import aws_s3
from aws_cdk import aws_logs


class AwsResouses:
    @staticmethod
    def create_app() -> App:
        return App()

    @staticmethod
    def create_stack(scope: Construct, id: str, env: any) -> Stack:
        return Stack(scope, id, env=env)

    @staticmethod
    def create_host_zone(
        scope: Construct, id: str, hosted_zone_name: str
    ) -> route53.HostedZone:
        return route53.HostedZone(scope, id, zone_name=hosted_zone_name)

    @staticmethod
    def create_lambda_function(scope: Construct, id: str) -> aws_lambda.Function:
        return aws_lambda.Function(
            scope,
            id,
            code=aws_lambda.Code.from_inline("console.log('hello world')"),
            handler="ingestor.handler",
            runtime=aws_lambda.Runtime.NODEJS_18_X,
        )

    @staticmethod
    def create_vpc(scope: Construct, id: str) -> aws_ec2.Vpc:
        return aws_ec2.Vpc(
            scope, id, ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/16"), vpc_name=id
        )

    @staticmethod
    def create_ec2_instance(
        scope: Construct, id: str, vpc: aws_ec2.Vpc
    ) -> aws_ec2.Instance:
        return aws_ec2.Instance(
            scope,
            id,
            instance_type=aws_ec2.InstanceType.of(
                aws_ec2.InstanceClass.BURSTABLE2, aws_ec2.InstanceSize.MICRO
            ),
            machine_image=aws_ec2.MachineImage.generic_linux(
                ami_map={"us-east-1": "ami-xxxxxxxxxxxxxxxx"}
            ),
            vpc=vpc,
        )

    @staticmethod
    def create_rds_instance(
        scope: Construct, id: str, vpc: aws_ec2.Vpc
    ) -> aws_rds.DatabaseInstance:
        return aws_rds.DatabaseInstance(
            scope,
            id,
            engine=aws_rds.DatabaseInstanceEngine.mysql(
                version=aws_rds.MysqlEngineVersion.VER_8_0_35
            ),
            instance_type=aws_ec2.InstanceType.of(
                aws_ec2.InstanceClass.BURSTABLE2, aws_ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
        )

    @staticmethod
    def create_rds_cluster(
        scope: Construct, id: str, vpc: aws_ec2.Vpc
    ) -> aws_rds.DatabaseCluster:
        return aws_rds.DatabaseCluster(
            scope,
            id,
            engine=aws_rds.DatabaseClusterEngine.aurora_mysql(
                version=aws_rds.AuroraMysqlEngineVersion.VER_3_05_0
            ),
            vpc=vpc,
            writer=aws_rds.ClusterInstance.provisioned(
                f"{id}-Instance",
            ),
        )

    @staticmethod
    def create_dynamodb_table(scope: Construct, id: str) -> aws_dynamodb.Table:
        return aws_dynamodb.Table(
            scope,
            id,
            partition_key=aws_dynamodb.Attribute(
                name="id", type=aws_dynamodb.AttributeType.STRING
            ),
        )

    @staticmethod
    def create_s3_bucket(scope: Construct, id: str) -> aws_s3.Bucket:
        return aws_s3.Bucket(scope, id, bucket_name=id)

    @staticmethod
    def create_log_group(scope: Construct, id: str) -> aws_logs.LogGroup:
        return aws_logs.LogGroup(scope, id, log_group_name=id)
