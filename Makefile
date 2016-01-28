
.PHONY: build
build: epaper/ui/main.py

%.py: %.ui
	pyuic5 -o $@ $<

%.qm: %.ts
	lrelease $<
