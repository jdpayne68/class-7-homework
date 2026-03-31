terraform {
  backend "S3" {  
    bucket  = "terraform-state-jdpayne"            # Name of the S3 bucket(note: this bucket must already exist)
    key     = "jenkins-test-031726.tfstate"        # The name of the state file in the bucket
    region  = "us-east-1"                          # Use a variable for the region
    encrypt = true                                 # Enable server-side encryption (optional but recommended)
  }
}