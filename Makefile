F=./junqer.py

all: run

run:
	$(F)

check:
	pychecker $(F)

.PHONY: all run check


