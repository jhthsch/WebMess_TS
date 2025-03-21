from setuptools import setup, find_packages
import os


# Projektname und Version
def read_version():
    return "0.1.0"


# Lies die Inhalte aus requirements.txt
def read_requirements():
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []


# Lies die Inhalte aus README.md
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="WebAppTS",
    version=read_version(),
    author="Thomas Schmidt",
    author_email="jhthsch@gmail.com",
    description="Ein WebApp-Projekt mit Dash und Backend-Prozessen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/dein-repo",  # Falls vorhanden
    packages=find_packages(),
    install_requires=read_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "WebAppTS": [
            "webappts=src.WebAppTS:main",  # Falls eine main() Funktion existiert
        ]
    },
)
