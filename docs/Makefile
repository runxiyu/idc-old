all: whitepaper.txt

whitepaper.txt: whitepaper.xml
	xml2rfc whitepaper.xml --verbose --text

whitepaper.xml: whitepaper.md
	mmark whitepaper.md > whitepaper.xml
