# EDocuments
##### a simple and productive personal documents library

* Scan your documents
  * Auto rotate
  * index them on the file name and on the content (OCR)

* Mange your pdf
  * index them on the file name and on the content

* Search in your library

## Requirement

On Debian you should install the following packages:

```bash
apt-get install tesseract-ocr python3-pyqt5
```

for specific language (in this case French):

```bash
apt-get install tesseract-ocr
```

to build the package:

```bash
apt-get install pyqt5-dev-tools
```

## Install in your home directory

```bash
virtualenv --system-site-packages --python=python3 $HOME/.py3
$HOME/.py3/bin/pip install edocuments
$HOME/.py3/bin/edocument-cmd --install
```
