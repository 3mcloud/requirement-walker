# setup.py
'''
Setup tools
'''
import re
import subprocess
from setuptools import setup, find_packages

NAME = 'requirement-walker'
VERSION = '0.0.4'
AUTHOR = 'Alex Guckenberger'
AUTHOR_EMAIL = 'aguckenberger@mmm.com'
DESCRIPTION = 'Walk through requirements and comments in requirements.txt files.'
URL = 'https://github.com/3mcloud/requirement-walker'
REQUIRES = []
REQUIRES_TEST = [
    'pylint>=2.5.0',
    'pytest>=5.4.1',
    'pytest-cov>=2.8.1',
]

with open('README.md') as readme_file:
    LONG_DESCRIPTION = readme_file.read()


setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=URL,
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=REQUIRES,
    extras_require={
        'dev': REQUIRES_TEST,
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)