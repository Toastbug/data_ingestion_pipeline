# setup.py
from setuptools import setup, find_packages

setup(
    name             = "aice-reco-tracker",
    version          = "1.0.0",
    description      = "Python SDK for the Aice Reco data ingestion pipeline",
    author           = "Your Name",
    author_email     = "your@email.com",
    packages         = find_packages(),
    python_requires  = ">=3.8",
    install_requires = [
        "requests>=2.28.0"
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)