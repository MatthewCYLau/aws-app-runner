resource "aws_key_pair" "ec2_key" {
  key_name   = "aws-app-bastion-public-key"
  public_key = file(var.public_key_path)
}

resource "aws_instance" "compute_instance" {
  ami                    = local.instance_ami
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = ["${aws_security_group.ssh.id}"]
  key_name               = aws_key_pair.ec2_key.key_name
  user_data              = file("./scripts/install_postgresql.sh")
  tags = {
    Name = "AWS App Public EC2 instance"
  }
}

output "ec2_public_ip" {
  value = aws_instance.compute_instance.public_ip
}

