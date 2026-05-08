 #!/bin/bash
sudo amazon-linux-extras install postgresql10 -y

while [ ! -b /dev/sdh ]; do sleep 5; done
              
# Format the volume if it doesn't have a filesystem
sudo mkfs -t xfs /dev/sdh

# Mount it
sudo mkdir -p /mnt/data
sudo mount /dev/sdh /mnt/data
sudo chown ec2-user:ec2-user /mnt/data

# Check if the instance sees an attached role
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
aws s3 ls s3://aws-app-runner-assets