from setuptools import find_packages
from setuptools import setup

# reading long description from file
with open("README.md", encoding="utf-8") as file:
    long_description = file.read()


with open("requirements/requirements.txt", encoding="utf-8") as file:
    REQUIREMENTS = file.read()


# calling the setup function
setup(
    name="gmail_attachment_downloader",
    version="0.0.3",
    description="A simple command line application that downloads all the gmail attachments with the specified format and search terms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/douglascdev/gmail_attachment_downloader",
    author="Douglas",
    author_email="douglasc.dev@gmail.com",
    license="MIT License",
    packages=find_packages(include=["gmail_attachment_downloader"]),
    entry_points={
        "console_scripts": [
            "gmail_attachment_dl = gmail_attachment_downloader.__main__:main",
        ],
    },
    install_requires=REQUIREMENTS,
    keywords=("email", "gmail", "attachment", "download"),
)
