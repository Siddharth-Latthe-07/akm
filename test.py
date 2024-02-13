import os
import argparse
import boto3

class SecretsUploader:
    def __init__(self, region):
        self.region = region
        self.client = boto3.client('secretsmanager', region_name=region)

    def upload_secret(self, secret_name, secret_value):
        try:
            response = self.client.describe_secret(SecretId=secret_name)
            secret_exists = True
        except self.client.exceptions.ResourceNotFoundException:
            secret_exists = False

        if secret_exists:
            response = self.client.put_secret_value(
                SecretId=secret_name,
                SecretString=secret_value
            )
            print(f"Updated secret '{secret_name}' in {self.region}.")
        else:
            response = self.client.create_secret(
                Name=secret_name,
                SecretString=secret_value
            )
            print(f"Created new secret '{secret_name}' in {self.region}.")

class FolderSyncer:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def sync_folder_to_secrets_manager(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Extract the region from the folder path
                folder_parts = root.split('/')
                if len(folder_parts) >= 2:
                    folder_region = folder_parts[-2]  # Second to last part is the region
                else:
                    folder_region = ''
                application_name = os.path.basename(root)
                secret_name = f"{application_name}/{file}"

                # If the file path contains a region name, use it, otherwise upload to all specified regions
                if folder_region:
                    uploader = SecretsUploader(folder_region)
                    uploader.upload_secret(secret_name, self.read_file(file_path))
                else:
                    regions = [d for d in os.listdir(self.folder_path) if os.path.isdir(os.path.join(self.folder_path, d))]
                    for region in regions:
                        uploader = SecretsUploader(region)
                        uploader.upload_secret(secret_name, self.read_file(file_path))

    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.read()

def main():
    parser = argparse.ArgumentParser(description='Upload files as secrets to AWS Secrets Manager.')
    parser.add_argument('folder_path', metavar='folder_path', type=str, help='Path to the folder containing files to upload as secrets')
    args = parser.parse_args()

    folder_syncer = FolderSyncer(args.folder_path)
    folder_syncer.sync_folder_to_secrets_manager()

if __name__ == "__main__":
    main()
