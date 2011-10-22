#rm -R locale.old
#rm -R locale.src.old
#mv locale locale.old
#mv locale.src locale.src.old
rm -R tmp
rm -R locale
rm -R locale.src
mkdir tmp
mkdir locale.src

for i in $( ls ../src/*.gui ); do
    intltool-extract --local --type=gettext/glade $i
done

cp ../src/*.py ./tmp/
cd tmp
xgettext --language=Python --keyword=_ --keyword=N_ --output=../locale.src/ntm.pot *.py *.h

rm -R tmp

sed \
-e 's/# SOME DESCRIPTIVE TITLE./# Pot file for NTM./' \
-e 's/# Copyright (C) YEAR ORGANIZATION/# Copyright (C) Luigi Tullio/' \
-e 's/# FIRST AUTHOR/# Luigi Tullio/' \
-e 's/Project-Id-Version: PACKAGE VERSION/Project-Id-Version: NTM 1.2/' \
-e 's/# FULL NAME/# Luigi Tullio/' \
-e 's/<EMAIL@ADDRESS>/<tluigi@gmail.com>/' \
-e 's/, YEAR./, 2010./' \
-e 's/PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE/PO-Revision-Date: -/' \
-e 's/Language-Team: LANGUAGE/Language-Team: it/' \
-e 's/plain; charset=CHARSET/plain; charset=utf-8/' \
-e 's/Content-Transfer-Encoding: ENCODING/Content-Transfer-Encoding: utf-8/' \
../locale.src/ntm.pot > ../locale.src/ntm.mod.pot

echo 
echo ==== en - English ====
mkdir ../locale.src/en
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/en/ntm.po -l en

echo 
echo ==== it - Italian ====
mkdir ../locale.src/it
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/it/ntm.po -l it

echo 
echo ==== es - Spanish ====
mkdir ../locale.src/es
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/es/ntm.po -l es

echo 
echo ==== de - German ====
mkdir ../locale.src/de
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/de/ntm.po -l de

echo 
echo ==== pl - Polish ====
mkdir ../locale.src/pl
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/pl/ntm.po -l pl

echo 
echo ==== sk - Slovak ====
mkdir ../locale.src/sk
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/sk/ntm.po -l sk

echo 
echo ==== pt - Portuguese ====
mkdir ../locale.src/pt
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/pt/ntm.po -l pt

echo 
echo ==== el - Greek ====
mkdir ../locale.src/el
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/el/ntm.po -l el

echo 
echo ==== km - Khmer ====
mkdir ../locale.src/km
msginit --no-translator -i ../locale.src/ntm.mod.pot -o ../locale.src/km/ntm.po -l km

cd ..

