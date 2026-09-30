## Ansible playground

- Connect to EC2 instance via SSH

```
chmod 600 ~/.ssh/aws_app
ssh -i ~/.ssh/aws_app ec2-user@54.172.113.129
```

- Ansible playbooks

```
ansible-galaxy collection install amazon.aws
ansible ec2_hosts -i inventory.ini -m raw -a "uptime"
ansible ec2_hosts -i inventory.ini -m ping
ansible-playbook -i inventory.ini list-s3.yaml
```
