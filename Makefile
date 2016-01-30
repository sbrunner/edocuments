
.PHONY: build
build: edocuments/ui/main.py edocuments/ui/label_dialog.py

%.py: %.ui
	pyuic5 -o $@ $<

%.qm: %.ts
	lrelease $<
