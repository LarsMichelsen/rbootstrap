VERSION  = 0.1
SHELL	 = bash
TAR_OPTS = --group root --owner root --transform 's|^|rbootstrap-$(VERSION)/|g'

.PHONY: dist

help:
	@echo "dist    - Builds the release archive"
	@echo "clean   - Cleans up the development directory"
	@echo "version - Update the version to be developed"
	@echo "install - Install to local system"

dist:
	gzip -f -c rbootstrap.8 > rbootstrap.8.gz
	python setup.py sdist --owner=root --group=root
	@echo "Created dist/rbootstrap-$(VERSION).tar.gz"

install:
	gzip -f -c rbootstrap.8 > rbootstrap.8.gz
	python setup.py install

version:
	@newversion=$$(dialog --stdout --inputbox "New Version:" 0 0 "$(VERSION)") ; \
        if [ -n "$$newversion" ] ; then \
	    $(MAKE) NEW_VERSION=$$newversion setversion ; \
	fi

setversion:
	sed -ri 's/^(VERSION[[:space:]]*= *).*/\1'"$(NEW_VERSION)/" Makefile
	sed -i "s/^VERSION = .*/VERSION = '$(NEW_VERSION)'/g" scripts/rbootstrap scripts/rbchroot
	sed -i "s/version='.*',/version='$(NEW_VERSION)',/g" setup.py

clean:
	rm -rf *.jail dist MANIFEST rbchroot.8.gz rbootstrap.8.gz 2>/dev/null || true
