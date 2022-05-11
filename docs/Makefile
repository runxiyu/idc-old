all: update

whitepaper.txt: whitepaper.xml
	xml2rfc whitepaper.xml --verbose --text

whitepaper.xml: whitepaper.md
	mmark whitepaper.md > whitepaper.xml

update: whitepaper.txt
	git add .
	git commit -m "automatic documentation update"
	git push
