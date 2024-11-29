import os
import pathlib
import shutil
import zipfile
from uuid import uuid4

from undetected_chromedriver.patcher import Patcher

_BASE_DRIVER_PATH = os.path.join(str(pathlib.Path(__name__).parent.resolve()), ".ucdriver")
DRIVER_PATH = os.path.join(_BASE_DRIVER_PATH, "base_driver")
INSTANCE_DRIVERS = os.path.join(_BASE_DRIVER_PATH, "instances")
os.makedirs(_BASE_DRIVER_PATH, exist_ok=True)
os.makedirs(INSTANCE_DRIVERS, exist_ok=True, mode=0o755)


def cached_package(self):
    if not os.path.exists(DRIVER_PATH):
        path = self._fetch_package()
        shutil.copy2(path, DRIVER_PATH + ".zip")
        os.remove(path)
        unzip_package_main()
    instance_id = uuid4().hex
    self.executable_path = os.path.join(INSTANCE_DRIVERS, instance_id)
    shutil.copyfile(DRIVER_PATH, os.path.join(INSTANCE_DRIVERS, self.executable_path))
    os.chmod(self.executable_path, 0o755)
    return DRIVER_PATH


def unzip_package_main():
    with zipfile.ZipFile(DRIVER_PATH + ".zip", mode="r") as zf:
        for f in zf.namelist():
            if f.split("/")[1] == "chromedriver":
                with zf.open(f) as fs, open(DRIVER_PATH, "wb") as ft:
                    shutil.copyfileobj(fs, ft)
                break
    os.unlink(DRIVER_PATH + ".zip")


def monkey_patch():
    Patcher._fetch_package = Patcher.fetch_package
    Patcher.fetch_package = cached_package
    Patcher.cleanup_unused_files = lambda *args: None
    Patcher.unzip_package = lambda *args: None
