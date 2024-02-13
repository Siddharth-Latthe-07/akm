import os
import argparse
import boto3

class SecretsUploader:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def upload_to_secrets_manager(self, region, secret_name, file_path):
        client = boto3.client('secretsmanager', region_name=region)
        
        with open(file_path, 'r') as file:
            secret_value = file.read()

        try:
            response = client.describe_secret(SecretId=secret_name)
            secret_exists = True
        except client.exceptions.ResourceNotFoundException:
            secret_exists = False

        if secret_exists:
            response = client.put_secret_value(
                SecretId=secret_name,
                SecretString=secret_value
            )
            print(f"Updated secret '{secret_name}' in {region}.")
        else:
            response = client.create_secret(
                Name=secret_name,
                SecretString=secret_value
            )
            print(f"Created new secret '{secret_name}' in {region}.")

    def sync_folder_to_secrets_manager(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                folder_parts = root.split('/')
                region = folder_parts[-1]  # Last part is the region
                application_name = os.path.basename(root)
                secret_name = f"{application_name}/{file}"
                self.upload_to_secrets_manager(region, secret_name, file_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder_path", help="Path to the folder to sync with AWS Secrets Manager")
    args = parser.parse_args()

    uploader = SecretsUploader(args.folder_path)
    uploader.sync_folder_to_secrets_manager()

if __name__ == "__main__":
    main()

