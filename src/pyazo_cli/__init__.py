#!/usr/bin/env python3

import os
import platform
import shutil
import sys
import tempfile
import time
from configparser import ConfigParser
from datetime import datetime
from subprocess import PIPE, Popen, run

import click
import pyclip  # type:ignore
import requests

# Configuration
config_parser = ConfigParser()
config_parser.read_dict(
    {
        "pyazo": {
            "url": "https://pyazo.example.com/api",
            "token": "",
            "util": "",
            "output_dir": "",
        }
    }
)
_ = config_parser.read(os.path.expanduser("~/.config/pyazo/config.ini"))
config = config_parser["pyazo"]
tmp_file = os.path.join(tempfile.gettempdir(), "screenshot.png")

OS_BACKENDS = {
    "Linux": {
        "maim": ["-s", "-n", "0", tmp_file],
        "scrot": ["-s", tmp_file],
        "import": [tmp_file],  # ImageMagick
        "grimshot": ["save", "area", tmp_file],
        "spectacle": ["-b", "-r", "-n", "-o", tmp_file],
        "hyprshot": ["-m", "region", "-s", "-z", "-o", "/", "-f", tmp_file],
    },
    "Darwin": {
        "screencapture": ["-i", tmp_file],
    },
}


def notify(message: str, time: int):
    if platform.system() == "Darwin":
        Popen(
            [
                "osascript",
                "-e",
                f'display notification "{message}" with title "pyazo"',
            ]
        )
    else:
        Popen(["notify-send", "-t", str(time), message])


def make_screenshot():
    util = config.get("util")
    backends = OS_BACKENDS[platform.system()]
    if util is not None:
        args = backends[util]
        ret = run([util] + args)
        if ret.returncode != 0:
            message = "Error: Failed to take screenshot."
            print(message, file=sys.stderr)
            notify(message, 4000)
            exit(-1)
    else:
        for util, args in backends.items():
            if shutil.which(util) is not None and run([util] + args).returncode == 0:
                break

    if not os.path.isfile(tmp_file):
        message = "Error: Failed to take screenshot."
        print(message, file=sys.stderr)
        notify(message, 4000)
        exit(-1)


def upload_file(
    filename: str,
    copy_clipboard: bool,
    output_url: bool,
    private: bool,
    clear_metadata: bool,
):
    with open(filename, "rb") as img:
        request_url = f"{config.get('url')}/images"
        params = {"private": private, "clear_metadata": clear_metadata}

        r = requests.post(
            request_url,
            headers={"Authorization": f"Bearer {config.get('token')}"},
            files={"upload_file": img},
            params=params,
        )

    if r.status_code >= 400:
        message = f"Error: Failed to upload screenshot. [{r.status_code}]"
        print(message, file=sys.stderr)
        notify(message, 4000)
        exit(-2)

    url = f"{config.get('url')}/{r.json()['id']}"

    if copy_clipboard:
        pyclip.copy(url)

    if output_url:
        print(url)

    return url


def save_file():
    output_dir: str | None = config.get("output_dir")
    if output_dir in (None, ""):
        if shutil.which("xdg-user-dir") is not None:
            p = Popen(["xdg-user-dir", "PICTURES"], stdout=PIPE, stderr=PIPE)
            output, _ = p.communicate()
            output_dir = os.path.join(output.decode().strip(), "screenshots")
        else:
            os.remove(tmp_file)
            return

    date = datetime.now().replace(microsecond=0).isoformat()
    image_file = f"pyazo_{date}"
    time.sleep(1 / 100)
    shutil.move(tmp_file, os.path.join(output_dir, f"{image_file}.png"))


def delete_last_image() -> None:
    request_url = f"{config.get('url')}/images"
    r = requests.get(
        request_url,
        headers={"Authorization": f"Bearer {config.get('token')}"},
        params={"per_page": 1},
    )
    image_id: str = r.json()["results"][0]["id"]
    request_url = f"{config.get('url')}/images/{image_id}"
    r = requests.delete(
        request_url,
        headers={"Authorization": f"Bearer {config.get('token')}"},
    )
    if r.status_code >= 400:
        message = f"Error: Failed to delete image. [{r.status_code}]"
        print(message, file=sys.stderr)
        notify(message, 4000)
        exit(-2)


@click.command()
@click.option("-p", "--private", is_flag=True, help="Make the image private")
@click.option("-i", "--image", help="Path to the image to upload")
@click.option(
    "-c",
    "--clear-metadata",
    is_flag=True,
    help="Clear image metadata",
)
@click.option("-d", "--delete", is_flag=True, help="Delete last uploaded image")
@click.option(
    "--no-copy",
    is_flag=True,
    help="Don't copy the url to the clipboard after upload.",
)
@click.option(
    "--no-output",
    is_flag=True,
    help="Don't print the url to stdout after upload.",
)
@click.option(
    "--no-save",
    is_flag=True,
    help="Don't save the file locally after upload.",
)
def main(
    private: bool,
    image: str,
    delete: bool,
    clear_metadata: bool,
    no_copy: bool,
    no_output: bool,
    no_save: bool,
):
    if image:
        url = upload_file(
            image,
            not no_copy,
            not no_output,
            private,
            clear_metadata,
        )
    elif delete:
        delete_last_image()
        return
    else:
        make_screenshot()
        url = upload_file(
            tmp_file,
            not no_copy,
            not no_output,
            private,
            clear_metadata,
        )
        if not no_save:
            save_file()

    notify(f"Screenshot uploaded {url}", 1500)
