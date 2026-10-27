import subprocess
import os

REPO_NAME = os.environ["repo_name"]
ROOT_PATH = os.environ["dest_path"]
CONFIG_NAME = os.environ.get("RCLONE_CONFIG_NAME", "")

if CONFIG_NAME == "":
    result = subprocess.run(["rclone", "listremotes"], capture_output=True)
    CONFIG_NAME = result.stdout.decode().split("\n")[0]
if not CONFIG_NAME.endswith(":"):
    CONFIG_NAME = CONFIG_NAME + ":"

if ROOT_PATH.startswith("/"):
    ROOT_PATH = ROOT_PATH[1:]

if __name__ == "__main__":
    destination = f"{CONFIG_NAME}/{ROOT_PATH}"
    subprocess.run(
        ["rclone", "sync", "./", destination, "-c", "--copy-links"],
        check=True,
    )
    if os.environ.get("FORCE_REUPLOAD", "false") == "true":
        subprocess.run(
            ["rclone", "copy", "./", destination, "--ignore-times", "--copy-links",
             "--files-from-raw", os.environ["REFRESH_MANIFEST"]],
            check=True,
        )
