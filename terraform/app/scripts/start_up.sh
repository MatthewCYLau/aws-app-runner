 #!/bin/bash
sudo amazon-linux-extras install postgresql10 -y

while [ ! -b /dev/sdh ]; do sleep 5; done
              
# Format the volume if it doesn't have a filesystem
sudo mkfs -t xfs /dev/sdh

# Mount it
sudo mkdir -p /mnt/data
sudo mount /dev/sdh /mnt/data
sudo chown ec2-user:ec2-user /mnt/data