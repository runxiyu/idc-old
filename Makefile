specs:
	./mmark specs.md > specs.xml
	xml2rfc specs.xml --verbose --text --html

prepare:
	pip3 install --user xml2rfc
