# sample-aws-cdk-vpc

aws-cdk v2を使用してVPCを作成するサンプルです。

## 準備

### cdkインストールと、venv仮想環境

```bash
npm i -g aws-cdk
python3 -m venv .venv
source .venv/bin/activate
```

## 構築

[config](./cdk/config/) にある設定を例として環境を作成します。  
`stage` を指定することで違う環境を作ることができます。  
`service_name` は スタック名の冠名として指定することができます。(test-multi-with-nat-VpcStack がスタック名になります)

 |stage|構成|
 | --- | --- |
 | multi_with_nat | パブリックネットワーク x 2、プライベートネットワーク x 2、NAT Gateway x 2|
 | multi_with_no_nat | パブリックネットワーク x 2、Isolatedネットワーク x 2 |
 | multi_with_nat_ipv6_dualstack|パブリックネットワーク x 2、プライベートネットワーク x 2、NAT Gateway x 2、Egress Only Internet Gateway|
 | multi_with_single_nat |パブリックネットワーク x 2、プライベートネットワーク x 2、NAT Gateway|
 | single_with_nat |パブリックネットワーク、プライベートネットワーク、NAT Gateway|

### DIFFのコマンド例

```bash
cd cdk
cdk diff --context stage=multi_with_nat --context service_name=test-multi-with-nat
```

#### DEPLOYのコマンド例

```bash
cd cdk
cdk deploy --context stage=multi_with_nat --context service_name=test-multi-with-nat
```

#### DESTROYのコマンド例

```bash
cd cdk
cdk destroy --context stage=multi_with_nat --context service_name=test-multi-with-nat
```
