import glob
import boto3
import os

class Application:
    def __init__(self, app_name, root_folder):
        self.name = app_name
        self.regions = []
        self.regional_files = {}
        self.default_files = []

        for folder_name in glob.glob(f"{root_folder}/*/"):  # Find directories inside root_folder
            folder_name = folder_name.rstrip('/').split('/')[-1]  # Extract folder name
            self.regions.append(folder_name)  
            self.regional_files[folder_name] = []
            for file_path in glob.glob(f"{root_folder}/{folder_name}/*"):  # Find files inside region folders
                if os.path.isfile(file_path):
                    file_name = os.path.basename(file_path)
                    self.regional_files[folder_name].append({
                        'path': file_path,
                        'secret_id': f"{self.name}/{file_name}"  # Modify secret_id construction
                    })

        # Collect default files from the root folder
        for file_path in glob.glob(f"{root_folder}/*"):
            if os.path.isfile(file_path):
                file_name = os.path.basename(file_path)
                self.default_files.append({
                    'path': file_path,
                    'secret_id': f"{self.name}/{file_name}"  # Modify secret_id construction
                })

    def upload(self, boto_session_by_region):
        for region, files in self.regional_files.items():
            for file_info in files:
                self.upload_single_file(file_info['path'], file_info['secret_id'], boto_session_by_region[region])

        for file_info in self.default_files:
            for region, boto_session in boto_session_by_region.items():
                self.upload_single_file(file_info['path'], file_info['secret_id'], boto_session)

    def upload_single_file(self, file_path, secret_id, boto_session):
        try:
            client = boto_session.client('secretsmanager')
            with open(file_path, 'r') as file:
                secret_value = file.read()
                client.create_secret(
                    Name=secret_id,
                    SecretString=secret_value
                )
                print(f"Created new secret '{secret_id}' in {boto_session.region_name}.")
        except Exception as e:
            print(f"Error uploading secret '{secret_id}' in {boto_session.region_name}: {str(e)}")

def main():
    root_folder = "my-apps"
    apps = []

    for app_folder in glob.glob(f"{root_folder}/*/"):  # Find directories inside root_folder
        app_name = os.path.basename(app_folder.rstrip('/'))  # Extract app name from directory path
        app = Application(app_name, app_folder)
        apps.append(app)

    all_regions = set()
    for app in apps:
        all_regions.update(app.regions)

    boto_session_by_region = {}
    for region in all_regions:
        boto_session_by_region[region] = boto3.Session(region_name=region)

    for app in apps:
        app.upload(boto_session_by_region)

if __name__ == "__main__":
    main()
