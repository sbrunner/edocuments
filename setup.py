# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = """A sample and productive personal documents library

* Scan your documents
  * Auto rotate
  * index them on the file name and on the content (OCR)

* Mange your pdf
  * index them on the file name and on the content

* Search in your library

`Sources <https://github.com/sbrunner/personal-documents-library/>`_"""

install_requires = [
    'PyYAML',
    'autoupgrade',
]

setup_requires = [
]

tests_require = install_requires + [
]

setup(
    name="edocuments",
    version="0.1.1",
    description="eDocuments - a simple and productive personal documents library",
    long_description=README,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    author="Stéphane Brunner",
    author_email="stephane.brunner@gmail.com",
    url="https://github.com/sbrunner/epaper/",
    keywords="simple productive personal documents library scan index search",
    packages=find_packages(exclude=["*.tests", "*.tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    test_suite="epaper",
    entry_points={
        "console_scripts": [
            "edocuments-gui = edocuments:gui_main"
        ],
    }
)
