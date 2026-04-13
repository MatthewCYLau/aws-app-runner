resource "aws_key_pair" "ec2_key" {
  key_name   = "aws-app-bastion-public-key"
  public_key = file(var.public_key_path)
}

resource "aws_instance" "compute_instance" {
  ami                    = local.instance_ami
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[0].id
  availability_zone      = data.aws_availability_zones.available_zones.names[0]
  vpc_security_group_ids = ["${aws_security_group.bastion_vm.id}"]
  key_name               = aws_key_pair.ec2_key.key_name
  user_data              = file("./scripts/start_up.sh")
  ebs_block_device {
    device_name           = "/dev/sdh"
    volume_size           = 1
    volume_type           = "standard"
    delete_on_termination = true
    encrypted             = true
  }

  volume_tags = merge(
    local.common_tags,
    { Name = "AWS App Public EC2 instance data volume" }
  )

  tags = merge(
    local.common_tags,
    { Name = "AWS App Public EC2 instance" }
  )
}

/*
resource "aws_ebs_volume" "extra_storage" {
  availability_zone = data.aws_availability_zones.available_zones.names[0]
  size              = 1
  type              = "standard"

  tags = merge(
    local.common_tags,
    { Name = "AWS App Public EC2 instance data volume" }
  )
}

resource "aws_volume_attachment" "ebs_att" {
  device_name = "/dev/sdh"
  volume_id   = aws_ebs_volume.extra_storage.id
  instance_id = aws_instance.compute_instance.id
}
*/

output "ec2_public_ip" {
  value = aws_instance.compute_instance.public_ip
}

