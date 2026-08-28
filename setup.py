from pathlib import Path

from setuptools import find_packages, setup

requirements_path = Path(__file__).with_name("requirements.txt")
with requirements_path.open() as f:
    requirements = f.read().splitlines()

setup(
    name="FLIPKART RECOMMENDER",
    version="0.1",
    author="Sudhanshu",
    packages=find_packages(),
    install_requires = requirements,
)