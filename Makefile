VERSION  = 0.1
SHELL	 = bash
TAR_OPTS = --group root --owner root --transform 's|^|rbootstrap-$(VERSION)/|g'

.PHONY: dist

help:
	@echo "dist    - Builds the release archive"
	@echo "clean   - Cleans up the development directory"
	@echo "version - Update the version to be developed"

dist:
	gzip -fk rbootstrap.8
	python setup.py sdist --owner=root --group=root
	@echo "Created dist/rbootstrap-$(VERSION).tar.gz"

version:
	@newversion=$$(dialog --stdout --inputbox "New Version:" 0 0 "$(VERSION)") ; \
        if [ -n "$$newversion" ] ; then \
	    $(MAKE) NEW_VERSION=$$newversion setversion ; \
	fi

setversion:
	sed -ri 's/^(VERSION[[:space:]]*= *).*/\1'"$(NEW_VERSION)/" Makefile
	sed -i "s/^VERSION = .*/VERSION = '$(NEW_VERSION)'/g" scripts/rbootstrap
	sed -i "s/version='.*',/version='$(NEW_VERSION)',/g" setup.py

clean:
	rm -rf *.jail dist MANIFEST rbootstrap.8.gz 2>/dev/null || true
