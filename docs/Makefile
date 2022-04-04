all: whitepaper.txt

whitepaper.txt:
	# https://github.com/mmarkdown/mmark
	mmark whitepaper.md > whitepaper.xml
	# pip3 install xml2rfc
	xml2rfc whitepaper.xml --verbose --text
