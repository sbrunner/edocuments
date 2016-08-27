# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

README = """A sample and productive personal documents library

Scan your documents:
* Auto rotate
* index them on the file name and on the content (OCR)

Mange your pdf:
* index them on the file name and on the content

Search in your library:
* Build the index
* Quick search using the index

`Sources <https://github.com/sbrunner/personal-documents-library/>`_"""

install_requires = [
    'PyYAML',
    'bottle',
    'Mako',
    'Whoosh',
    'metatask'
]

setup_requires = [
]

tests_require = install_requires + [
]

setup(
    name="edocuments",
    version="1.0.0",
    description="eDocuments"
    " - a simple and productive personal documents library",
    long_description=README,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    author="Stéphane Brunner",
    author_email="stephane.brunner@gmail.com",
    url="https://github.com/sbrunner/edocuments/",
    keywords="simple productive personal documents library scan index search",
    packages=find_packages(exclude=["*.tests", "*.tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    test_suite="edocuments",
    entry_points={
        "console_scripts": [
            "edocuments-gui = edocuments:gui_main",
            "edocuments-cmd = edocuments:cmd_main",
        ],
    }
)
