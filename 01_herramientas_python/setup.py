from setuptools import setup, find_packages

setup(
    name="nttdata-ibm-twx-tools",
    version="1.0.0",
    description="NTTDATA IBM Integration Designer TWX Reverse Engineering Suite",
    author="NTTDATA",
    packages=find_packages(include=["ibm_twx_tools*"]),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "nttdata-ibm-twx=ibm_twx_tools.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Reverse Engineering",
        "Programming Language :: Python :: 3.10",
    ],
)
