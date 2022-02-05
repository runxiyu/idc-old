specs:
	./mmark specs.md > specs.xml
	xml2rfc specs.xml

prepare:
	pip3 install --user xml2rfc
