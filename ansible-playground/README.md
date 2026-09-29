Ansible playground

```
ansible-galaxy collection install amazon.aws
ansible ec2_hosts -i inventory.ini -m raw -a "uptime"
ansible ec2_hosts -i inventory.ini -m ping
ansible-playbook -i inventory.ini list-s3.yaml
```
