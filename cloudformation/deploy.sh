#!/bin/bash

# This script deploys the CloudFormation stack.
# It requires the AWS CLI to be configured.

# --- Configuration ---
STACK_NAME="spotify-recommender-stack"
TEMPLATE_FILE="template.yaml"
# Replace with the name of the S3 bucket where your artifacts will be stored
S3_ARTIFACT_BUCKET="spotify-recommender-bucket" # <--- IMPORTANT: CHANGE THIS

# --- Deployment Command ---
echo "Deploying CloudFormation stack: $STACK_NAME..."

aws cloudformation deploy \
  --template-file "$TEMPLATE_FILE" \
  --stack-name "$STACK_NAME" \
  --parameter-overrides S3BucketName="$S3_ARTIFACT_BUCKET" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset

if [ $? -eq 0 ]; then
  echo "Stack deployment initiated successfully."
  echo "You can monitor the progress in the AWS CloudFormation console."
else
  echo "Stack deployment failed. Please check the error messages above."
fi
