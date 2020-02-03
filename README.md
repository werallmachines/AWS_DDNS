# AWS_DDNS

Run as Lambda function within environment. Queries a load balancer's private IPs and updates a public hosted zone's A record with these IPs. Useful if resolving website over public Internet, but sending traffic through VPN tunnel into the VPC.
