#!/usr/bin/env python3

import os
import platform
import pyperclip
import requests
import shutil
import sys
import tempfile
import time
import click
from configparser import ConfigParser
from datetime import datetime
from subprocess import run, Popen, PIPE

# Configuration
config = ConfigParser()
config.read_dict({
    'pyazo': {
        'url': 'https://pyazo.example.com/api',
        'token': '',
        'util': '',
        'output_dir': '',
    }
})
config.read(os.path.expanduser('~/.config/pyazo/config.ini'))
config = config['pyazo']

tmp_file = os.path.join(tempfile.gettempdir(), 'screenshot.png')

backends = {
    'Linux': {
        'maim': ['-s', '-n', '0', tmp_file],
        'scrot': ['-s', tmp_file],
        'import': [tmp_file]  # ImageMagick
    },
    'Darwin': {
        'screencapture': ['-i', tmp_file]
    },
    'Windows': {
        'snippingtool': ['/clip']  # '/clip' requires at least Win10 1703
    }
}

util = config.get('util')
backend = backends[platform.system()]
if util is not None:
    args = backend[util]
else:
    for util, args in backends[platform.system()].items():
        if shutil.which(util) is not None and run([util] + args).returncode == 0:
            break

def notify(message, time):
    if util == 'screencapture':
        Popen(['osascript', '-e', f'display notification "{message}" with title "pyazo"'])
    else:
        Popen(['notify-send', '-t', str(time), message])


def make_screenshot():
    if run([util] + args).returncode != 0:
        message = 'Error: Failed to take screenshot.'
        print(message, file=sys.stderr)
        notify(message, 4000)
        exit(-1)

    # If the used util stored the screenshot in the clipboard, output it to the tmp file
    if util == 'snippingtool':
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img is not None:
            img.save(tmp_file, optimize=True)

    if not os.path.isfile(tmp_file):
        message = 'Error: Failed to take screenshot.'
        print(message, file=sys.stderr)
        notify(message, 4000)
        exit(-1)


def upload_file(filename, copy_clipboard, output_url, private, clear_metadata):
    with open(filename, 'rb') as img:
        request_url = f'{config.get("url")}/images'
        params = {'private': private, 'clear_metadata': clear_metadata}

        r = requests.post(
            request_url,
            headers={'Authorization': f'Bearer {config.get("token")}'},
            files={'upload_file': img},
            params=params,
        )

        if r.status_code != 200:
            message = f'Error: Failed to upload screenshot. [{r.status_code}]'
            print(message, file=sys.stderr)
            notify(message, 4000)
            exit(-2)

        url = f'{config.get("url")}/{r.json()["id"]}'

        if copy_clipboard:
            pyperclip.copy(url)

        if output_url:
            print(url)

        return url


def save_file():
    output_dir = config.get('output_dir')
    if output_dir == '':
        if shutil.which('xdg-user-dir') is not None:
            p = Popen(['xdg-user-dir', 'PICTURES'], stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()
            output_dir = os.path.join(output.decode().strip(), 'screenshots')
        else:
            os.remove(tmp_file)
            return

    date = datetime.now().replace(microsecond=0).isoformat()
    image_file = f'pyazo_{date}'
    time.sleep(1 / 100)
    shutil.move(tmp_file, os.path.join(output_dir, f'{image_file}.png'))


@click.command()
@click.option('-p', '--private', is_flag=True, help='Make the image private')
@click.option('-i', '--image', help='Path to the image to upload')
@click.option('-c', '--clear-metadata', is_flag=True, help='Clear image metadata')
@click.option('--no-copy', is_flag=True, help='Don\'t copy the url to the clipboard after upload.')
@click.option('--no-output', is_flag=True, help='Don\'t print the url to stdout after upload.')
def upload_image(private, image, clear_metadata, no_copy, no_output):
    if image:
        url = upload_file(image, not no_copy, not no_output, private, clear_metadata)
    else:
        make_screenshot()
        url = upload_file(tmp_file, not no_copy, not no_output, private, clear_metadata)
        save_file()

    notify(f'Screenshot uploaded {url}', 1500)


if __name__ == '__main__':
    upload_image()
