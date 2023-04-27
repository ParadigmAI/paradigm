from setuptools import setup, find_packages

setup(
    name="paradigm",
    version="0.1",
    packages=find_packages(),
    install_requires=["PyYAML", "docker"],
    entry_points={
        "console_scripts": [
            "paradigm-aws = paradigm-aws:main",
        ],
    },
)
