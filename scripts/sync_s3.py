import boto3
import os
import argparse
from datetime import datetime
from botocore.exceptions import ClientError

def create_bucket_if_not_exists(s3_client, bucket_name):
    """Checks if an S3 bucket exists and creates it if it does not."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        # If a client error is thrown, check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print(f"Bucket '{bucket_name}' does not exist. Creating it now...")
            try:
                # S3 buckets must be globally unique.
                # The location constraint needs to be set to the region of the client,
                # unless the region is us-east-1, in which case it should be omitted.
                region = s3_client.meta.region_name
                if region == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                s3_client.get_waiter('bucket_exists').wait(Bucket=bucket_name)
                print(f"Successfully created bucket '{bucket_name}'.")
            except ClientError as create_error:
                print(f"Error creating bucket: {create_error}")
                # Exit if bucket creation fails (e.g., name is taken, permissions issue)
                exit(1)
        else:
            print(f"An unexpected error occurred when checking for the bucket: {e}")
            exit(1)

def sync_s3(bucket_name, direction, local_data_dir='data', local_artifacts_dir='artifacts'):
    """
    Uploads or downloads data and artifacts to/from an S3 bucket with versioning.
    """
    s3_client = boto3.client('s3')

    if direction == 'upload':
        # --- THIS IS THE NEW LOGIC ---
        # Ensure the bucket exists before we try to upload to it.
        create_bucket_if_not_exists(s3_client, bucket_name)
        
        version = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        print(f"Creating new version: {version}")

        # --- Upload Data ---
        s3_data_prefix = f'data/{version}/'
        print(f"\nUploading raw data to s3://{bucket_name}/{s3_data_prefix}...")
        for root, _, files in os.walk(local_data_dir):
            for file in files:
                if not file.startswith('.'): # Ignore hidden files like .DS_Store
                    local_path = os.path.join(root, file)
                    s3_key = os.path.join(s3_data_prefix, file)
                    try:
                        s3_client.upload_file(local_path, bucket_name, s3_key)
                        print(f"  - Uploaded {local_path} to {s3_key}")
                    except Exception as e:
                        print(f"  - Failed to upload {local_path}: {e}")

        # --- Upload Artifacts ---
        s3_artifacts_prefix = f'artifacts/{version}/'
        print(f"\nUploading artifacts to s3://{bucket_name}/{s3_artifacts_prefix}...")
        for root, _, files in os.walk(local_artifacts_dir):
            for file in files:
                 if not file.startswith('.'):
                    local_path = os.path.join(root, file)
                    s3_key = os.path.join(s3_artifacts_prefix, file)
                    try:
                        s3_client.upload_file(local_path, bucket_name, s3_key)
                        print(f"  - Uploaded {local_path} to {s3_key}")
                    except Exception as e:
                        print(f"  - Failed to upload {local_path}: {e}")
        
        print(f"\nUpload complete. Latest version is: {version}")

    elif direction == 'download':
        # To download, we first need to find the latest version
        print("Finding the latest version in S3...")
        
        # We look for the latest timestamped folder in both data and artifacts
        def get_latest_s3_version(prefix):
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
            latest_version = None
            for page in pages:
                if 'CommonPrefixes' in page:
                    versions = [p['Prefix'] for p in page['CommonPrefixes']]
                    if versions:
                        latest_version = max(versions)
            return latest_version

        latest_data_version_prefix = get_latest_s3_version('data/')
        latest_artifacts_version_prefix = get_latest_s3_version('artifacts/')

        if not latest_data_version_prefix or not latest_artifacts_version_prefix:
            print("Could not find any versions in the S3 bucket. Please upload first.")
            return

        print(f"Latest data version found: {latest_data_version_prefix}")
        print(f"Latest artifacts version found: {latest_artifacts_version_prefix}")

        # --- Download Data ---
        print(f"\nDownloading raw data from {latest_data_version_prefix}...")
        os.makedirs(local_data_dir, exist_ok=True)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=latest_data_version_prefix)
        for obj in response.get('Contents', []):
            s3_key = obj['Key']
            local_path = os.path.join(local_data_dir, os.path.basename(s3_key))
            try:
                s3_client.download_file(bucket_name, s3_key, local_path)
                print(f"  - Downloaded {s3_key} to {local_path}")
            except Exception as e:
                print(f"  - Failed to download {s3_key}: {e}")

        # --- Download Artifacts ---
        print(f"\nDownloading artifacts from {latest_artifacts_version_prefix}...")
        os.makedirs(local_artifacts_dir, exist_ok=True)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=latest_artifacts_version_prefix)
        for obj in response.get('Contents', []):
            s3_key = obj['Key']
            local_path = os.path.join(local_artifacts_dir, os.path.basename(s3_key))
            try:
                s3_client.download_file(bucket_name, s3_key, local_path)
                print(f"  - Downloaded {s3_key} to {local_path}")
            except Exception as e:
                print(f"  - Failed to download {s3_key}: {e}")

        print("\nDownload complete.")
    else:
        print(f"Invalid direction '{direction}'. Please choose 'upload' or 'download'.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sync data and artifacts with S3.")
    parser.add_argument('--bucket', type=str, required=True, help="The name of your S3 bucket (must be globally unique).")
    parser.add_argument('--direction', type=str, required=True, choices=['upload', 'download'],
                        help="Direction of synchronization.")
    args = parser.parse_args()

    sync_s3(args.bucket, args.direction)