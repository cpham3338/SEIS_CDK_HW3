#!/bin/sh
# Use this to install software packages
# This script is for EC2 userdata. All commands are executed as administrators. 
yum update -y
amazon-linux-extras install mariadb10.5
amazon-linux-extras install php8.2
yum install -y httpd
systemctl start httpd
systemctl enable httpd