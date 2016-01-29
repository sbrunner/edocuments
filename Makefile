
.PHONY: build
build: edocuments/ui/main.py

%.py: %.ui
	pyuic5 -o $@ $<

%.qm: %.ts
	lrelease $<
