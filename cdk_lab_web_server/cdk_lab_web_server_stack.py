import os.path

from aws_cdk.aws_s3_assets import Asset as S3asset

from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds
    # aws_sqs as sqs,
)

from constructs import Construct

dirname = os.path.dirname(__file__)
        
class CdkLabWebServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cdk_lab_vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Instance Role and SSM Managed Policy
        InstanceRole = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        InstanceRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        
        # Create an EC2 instance
        web1 = ec2.Instance(self, "web1", 
                            vpc=cdk_lab_vpc,
                            instance_type=ec2.InstanceType("t2.micro"),
                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                            role=InstanceRole,
                            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                            )
                                            
        # Create an EC2 instance
        web2 = ec2.Instance(self, "web2", 
                            vpc=cdk_lab_vpc,
                            instance_type=ec2.InstanceType("t2.micro"),
                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                            role=InstanceRole,
                            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                            )
                                            
        # Create an RDS Database
        rdsDB = rds.DatabaseInstance(self, "RDS MySQL",
                            vpc=cdk_lab_vpc,
                            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                            instance_type= ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
                            engine= rds.DatabaseInstanceEngine.MYSQL,
                            credentials= rds.Credentials.from_generated_secret("Admin"),
                            port=3306,
                            )


        # Script in S3 as Asset
        webinitscriptasset = S3asset(self, "Asset", path=os.path.join(dirname, "configure.sh"))
        asset_path = web1.user_data.add_s3_download_command(
            bucket=webinitscriptasset.bucket,
            bucket_key=webinitscriptasset.s3_object_key
        )

        # Userdata executes script from S3 for web1
        web1.user_data.add_execute_file_command(
            file_path=asset_path
            )
        webinitscriptasset.grant_read(web1.role)
        
        # Userdata executes script from S3 for web2
        web2.user_data.add_execute_file_command(
            file_path=asset_path
            )
        webinitscriptasset.grant_read(web2.role)
        
        # Allow inbound HTTP traffic in security groups
        web1.connections.allow_from_any_ipv4(ec2.Port.tcp(80))
        web2.connections.allow_from_any_ipv4(ec2.Port.tcp(80))
        rdsDB.connections.allow_internally(ec2.Port.tcp(3306), description="Open port for connection")