# This is a Jenkins server test with terraform deployment and triggers

## Jenkinsfile

A basic declarative Jenkinsfile

- Clones git repo  
- Binds AWS IAM user creds in terraform stages with AWS Creds plugin
- Stages for terraform init and apply  
- Destroy stage incorporatesusing user input  

## Terraform script  

- A basic AWS S3 bucket is deployed
- State file is stored in S3 backend  
- S3 bucket name uniqueness is guranteed  

## User data  

EC2 startup script to bootstrap Jenkins server
