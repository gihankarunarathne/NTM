rm -R ./locale
mkdir ./locale

echo
echo ==== en - English ====
mkdir ./locale/en
mkdir ./locale/en/LC_MESSAGES
msgfmt -o ./locale/en/LC_MESSAGES/ntm.mo ./locale.src/en/ntm.po
echo OK en

echo 
echo ==== it - Italian ====
mkdir ./locale/it
mkdir ./locale/it/LC_MESSAGES
msgfmt -o ./locale/it/LC_MESSAGES/ntm.mo ./locale.src/it/ntm.po
echo OK it

echo 
echo ==== es - Spanish ====
mkdir ./locale/es
mkdir ./locale/es/LC_MESSAGES
msgfmt -o ./locale/es/LC_MESSAGES/ntm.mo ./locale.src/es/ntm.po
echo OK es

echo 
echo ==== de - German ====
mkdir ./locale/de
mkdir ./locale/de/LC_MESSAGES
msgfmt -o ./locale/de/LC_MESSAGES/ntm.mo ./locale.src/de/ntm.po
echo OK de

echo 
echo ==== pl - Polish ====
mkdir ./locale/pl
mkdir ./locale/pl/LC_MESSAGES
msgfmt -o ./locale/pl/LC_MESSAGES/ntm.mo ./locale.src/pl/ntm.po
echo OK pl

echo 
echo ==== sk - Slovak ====
mkdir ./locale/sk
mkdir ./locale/sk/LC_MESSAGES
msgfmt -o ./locale/sk/LC_MESSAGES/ntm.mo ./locale.src/sk/ntm.po
echo OK sk

echo 
echo ==== pt - Portuguese ====
mkdir ./locale/pt
mkdir ./locale/pt/LC_MESSAGES
msgfmt -o ./locale/pt/LC_MESSAGES/ntm.mo ./locale.src/pt/ntm.po
echo OK pt

echo 
echo ==== el - Greek ====
mkdir ./locale/el
mkdir ./locale/el/LC_MESSAGES
msgfmt -o ./locale/el/LC_MESSAGES/ntm.mo ./locale.src/el/ntm.po
echo OK el

echo 
echo ==== km - Khmer ====
mkdir ./locale/km
mkdir ./locale/km/LC_MESSAGES
msgfmt -o ./locale/km/LC_MESSAGES/ntm.mo ./locale.src/km/ntm.po
echo OK km

