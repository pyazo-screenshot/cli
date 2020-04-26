# Pyazo

Pyazo is a self-hosted screenshot and image upload utility. It allows you to take a screenshot of a part of your screen and automatically upload it to your own server. You can also directly upload an image from your computer.

It is comprised of a cross-platform client written in Python which defers the actual taking of the screenshot to the built-in OS tools (macOS and Windows) or common utilities (Linux distributions). The server is written as a RESTful FastAPI app with support for basic user accounts and image sharing options.

## Compatibility

* Python >= 3.6 (check with `python --version`)

The following OSes have off-the-shelf compatibility. You can add more back ends for missing systems or configurations.

* Linux (`scrot`, `maim`, or `import` (ImageMagick))
* macOS
* Windows 10

## Installation

* Install [Python] 3
* Install client requirements:

- [requests](https://pypi.org/project/requests/)
- [pyperclip](https://pypi.org/project/pyperclip/)
- [click](https://pypi.org/project/click/)
- [pillow](https://pypi.org/project/pillow/) (Windows only)

## Configuration

Create an external config file. Pyazo extends the default config with the provided values. The following table contain all options and the location of the user config file.

### Client

* Example Config: `config.ini.sample`
* Placement Path: `~/.config/pyazo/config.ini` (`~` refers to the user home directory)

| Key                | Default                                   | Description                                                              |
|--------------------|-------------------------------------------|--------------------------------------------------------------------------|
| url                | https://example.com                       | API endpoint to send the image file in a POST request                    |
| token              | ' '                                       | JWT token (https://github.com/pyazo-screenshot/api/blob/master/README.md)|
| util               | maim                                      | Built-in tool or common utility for taking a screenshot                  |
| output_dir         | `$(xdg-user-dir PICTURES)`/screenshots    | Place to store the image after taking a screenshot                       |

## License

BSD 3-Clause

[Python]: <https://www.python.org/downloads/>
