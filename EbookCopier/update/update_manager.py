import requests
import subprocess
import sys
import time
from pathlib import Path


class UpdateManger:
    def __init__(self,
                 path="__init__.py",
                 owner="GoobersGaming",
                 name="EbookCopier", branch="main",
                 source_path="EbookCopier/__init__.py",
                 restart_file="EbookCopier.bat"):

        self.path = path
        self.repo_owner = owner
        self.repo_name = name
        self.branch = branch
        self.source_path = source_path
        self.restart_file = restart_file
        self.local_version = []
        self.source_version = []
        self.zip_path = None
        self.git_raw_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{self.source_path}"
        self.zip_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/refs/heads/{self.branch}.zip"

    def check_for_update(self):
        self.source_version = self._check_source_version()
        self.local_version = self._check_local_version()
        print(f"Source version: {self.source_version}")
        print(f"Local version: {self.local_version}")
        if not self.local_version or not self.source_version:
            return False

        if not self._compare_version():
            return False
        return True

    def _check_local_version(self):
        try:
            with open(self.path, "r") as file:
                line = str(file.readline())
                if "__version__" not in line:
                    return None
                return self._parse_version(line)
        except FileNotFoundError as e:
            print("No local file found: ", str(e))
            return None

        return None

    def _check_source_version(self):
        try:
            response = requests.get(self.git_raw_url)
            response.raise_for_status()
            version = str(response.text)
            if version:
                return self._parse_version(version)
        except requests.RequestException as e:
            print("An error reaching the url: ", str(e))

    def _parse_version(self, line):
        version = []
        if "__version__" not in line:
            return None
        line = line.replace("__version__", "")
        line = line.replace('"', "")
        for digit in line:
            if digit.isdigit():
                version.append(digit)
        return version

    def _compare_version(self):
        for local, source in zip(self.local_version, self.source_version):
            if local < source:
                print("New version available")
                return True
        return False

    def download_repo(self):
        # Convert version to string
        version_str = ".".join(map(str, self.source_version))
        # Path for zip to be saved to
        self.zip_path = Path.cwd().parent / f"Ebook-{version_str}.zip"

        # Open site and grab download
        response = requests.get(self.zip_url, stream=True)

        if response.status_code == 200:
            with open(self.zip_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
                print(f"File downloaded successfully to {self.zip_path}")
                return True
        else:
            print(f"Failed to download file. Statue code: {response.status_code}")
            return False

    def start_install(self):
        cwd_dir = Path.cwd().parent
        venv_path = Path(sys.executable)
        install_script = Path.cwd() / "update" / "install_update.py"
        restart_path = cwd_dir / self.restart_file
        subprocess.Popen(
            [
                str(venv_path),
                str(install_script),
                "-p", str(self.zip_path),
                "-r", str(restart_path),
                "--delete"
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=str(cwd_dir)
        )
        time.sleep(1)
        sys.exit(0)
