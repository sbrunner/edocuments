
.PHONY: build
build: ui/main.py

%.py: %.ui
	pyuic5 -o $@ $<

%.qm: %.ts
	lrelease $<
