# Forward-AWS-logs-to-PAS

To help organizations address the challenge of monitoring privileged users in the Cloud environment, and detecting, alerting, and responding to high-risk privileged access,

Privileged Threat Analytics capabilities can be used to improve the efficiency of Cloud security teams and to secure threats within the Amazon Web Services (AWS) environment.

This solution provides the following functionality: 

Detect unmanaged Access Keys and Passwords for IAM accounts
- Detect the most privileged accounts in AWS
- Take Shadow Admins into consideration
- Add the IAM privileged user to pending accounts as part of automatic remediation


Detect compromised privileged IAM accounts
- Detect privileged cloud activities that bypassed the Vault, and alert on suspected credentials theft attempts
- Alert and take control over the managed accounts by initiating password rotation or Access key re-creation


## Requirements 
-------------------------------
- PAS version version 10.8 and up (Vault + PVWA + CPM + PTA required)
- Network environment must contain NAT Gateway for the Lambda deployment to succeed. We advise using the CyberArk network template with NAT Gateway
- Network access from the VPC where the Lambda is deployed to PTA 
- For the solution deployment, you need the following permissions:
  - Deploy cloud formation 
  - S3 full permissions 
  - SNS full permissions 
  - Deploy Lambda
  - Create IAM role 
- Before running the solution, create a dedicated bucket in the region where you will perform the deployment with the following files :
  - MySnsToPta.zip
  - PtaCloudTrailToSns.zip 


## Deployment Parameters 

| Parameter                            | Description                                                  | 
|--------------------------------------|--------------------------------------------------------------|
| Bucket Name                          | Enter the name of the bucket of the solution Lambda          | 
| Solution Subnet                      | Enter the subnet in which the solution will be deployed      | 
| Solution VPC                         | Enter the VPC in which the solution will be deployed         | 
| PTA IP                               | Enter the IP of the PTA                                      | 
| PTA Port                             | Enter the PTA Port for delivering logs                       | 




## Manual procedure to change the PTA IP after the solution is deployed 

In AWS console → open EC2 dashboard  in left pane, go to Parameter Store →  look for ‘PTAIP’ parameter →  edit parameter as you wish



## Troubleshooting 

- Logs : In AWS  console → go to Lambda service → Choose your lambda’s name from the list → Press on monitoring → press on “view logs in cloudwatch”


## Deleting the Solution 

- Delete the cloud formation stack

- Delete the Solution trigger that is located under : Cloud Watch→ Rules 


## Licensing 

Copyright 1999-2019 CyberArk Software Ltd.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this software except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

