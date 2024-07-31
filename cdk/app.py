#!/usr/bin/env python3
import os
import yaml
import aws_cdk as cdk
from vpc.vpc_stack import VpcStack

app = cdk.App()

stage = app.node.try_get_context("stage")
service_name = app.node.try_get_context("service_name")

if os.path.exists("config/{}.yaml".format(stage)):
    # 環境ごとのコンフィグを読み込む
    config_file = open("config/{}.yaml".format(stage), "r")
    config_obj = yaml.safe_load(config_file)
    config_file.close()
else:
    raise Exception("config file not found")

VpcStack(
    app,
    "{}-VpcStack".format(service_name),
    service_name=service_name,
    env=cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
    config=config_obj,
)

app.synth()
