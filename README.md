# eDocuments
##### a simple and productive personal documents library

* Scan your documents
  * Highly configurable throw a yaml config file, default configuration do:
    * Auto crop
    * Auto rotate
    * Cleanup your scan
  * Index them on the file name and on the content (OCR)

* Mange your pdf
  * Index them on the file name and on the content

* Search in your library

## Requirement

On Debian you should install the following packages:

* `python3-pyqt5` Library
* `sane-utils` To scan the documents
* `graphicsmagick-imagemagick-compat` Image manipulation
* `tesseract-ocr` The OCR used by default
* `tesseract-ocr-fra` The OCR French language pack
* `optipng` To optimise the generated image size
* `pyqt5-dev-tools` To build the package

Install all needed:
```bash
apt-get install python3-pyqt5 sane-utils graphicsmagick-imagemagick-compat tesseract-ocr tesseract-ocr-fra optipng
```

To build the package:

```bash
apt-get install pyqt5-dev-tools
```

## Install in your home directory

```bash
virtualenv --system-site-packages --python=python3 $HOME/.py
$HOME/.py/bin/pip install edocuments
$HOME/.py/bin/edocument-cmd --install
```
