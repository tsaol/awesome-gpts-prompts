import boto3
import time
import requests
from botocore.exceptions import ClientError


aws_access_key_id = 'YOUR_SCCESS_KEY'
aws_secret_access_key = 'YOUR_SECRET_KEY'

# AWS Region
regions = ['us-east-1', 'us-west-2']
ami_ids = {
    'us-east-1': 'ami-053b0d53c279acc90',
    'us-west-2': 'ami-03f65b8614a860c29'
}

#Instance type
instance_type = 'p4de.24xlarge'
ssh_key_ids = {
    'us-east-1': '073392471888-Virginia',
    'us-west-2': '073392471888-oregon'
}
vpc_ids = {
    'us-east-1': 'vpc-0bbe00320e5cd35ac',
    'us-west-2': 'vpc-063df67cd15808e0b'
}
security_group_ids = {
    'us-east-1': 'sg-0df23916dcf6c101e',
    'us-west-2': 'sg-02cfabc447112946c'
}
ebs_volume_size_gb = 16

#Webhook URL
webhook_url = 'FEISHU_URL'


def create_ec2_instance(region, ami_id, instance_type, ssh_key_id, vpc_id, security_group_id, ebs_volume_size_gb):
    try:
        ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key)

        # 创建EC2实例
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=ssh_key_id,
            SecurityGroupIds=[security_group_id],
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': ebs_volume_size_gb,
                        'VolumeType': 'gp2'
                    }
                },
            ],
            MinCount=3,
            MaxCount=3
        )

        instance_id = response['Instances'][0]['InstanceId']
        print(f"launch ec2 instance {instance_id} in region {region} sucessful")

        return instance_id
    except ClientError as e:
        print(f"launch ec2 instance fail: {str(e)}")
        return None


def send_feishu_message(message):
    try:
        data = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(feishu_webhook_url, json=data, headers=headers)
        if response.status_code == 200:
            print("send notification sucessful")
        else:
            print(f"send notification fail，HTTP response code: {response.status_code}")
    except Exception as e:
        print(f"send notification exception : {str(e)}")


def main():
    while True:
        try:
            for region in regions:
                # 在每个区域分别创建EC2实例
                ami_id = ami_ids.get(region)
                ssh_key_id = ssh_key_ids.get(region)
                vpc_id = vpc_ids.get(region)
                security_group_id = security_group_ids.get(region)

                instance_id = create_ec2_instance(region, ami_id, instance_type, ssh_key_id, vpc_id, security_group_id,
                                                  ebs_volume_size_gb)

                if instance_id:
                    send_feishu_message(f"EC2实例 {instance_id} 在 {region} 区域创建成功")
        except Exception as e:
            print(f"发生异常: {str(e)}")

        time.sleep(10)


if __name__ == "__main__":
    main()
