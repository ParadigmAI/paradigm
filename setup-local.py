from setuptools import setup, find_packages

setup(
    name="paradigm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["PyYAML", "docker"],
    entry_points={
        "console_scripts": [
            "paradigm = paradigm:main",
        ],
    },
)
