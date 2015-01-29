#!/bin/sh

echo "Install system requirements ..."
sudo apt-get install $(grep -vE "^\s*#" requirements.system  | tr "\n" " ")

echo "Install python requirements ..."
sudo pip install -r requirements.txt

echo "Downloading stanford-parser ..."
wget http://nlp.stanford.edu/software/stanford-parser-full-2014-08-27.zip
echo "Downloading stanford-tagger ..."
wget http://nlp.stanford.edu/software/stanford-postagger-2014-08-27.zip
echo "Downloading stanford-ner-tagger ..."
wget http://nlp.stanford.edu/software/stanford-ner-2014-08-27.zip

echo "Unzip folders ..."
unzip stanford-parser-full-2014-08-27.zip  
unzip stanford-postagger-2014-08-27.zip
unzip stanford-ner-2014-08-27.zip

echo "Rename folders ..."
mv stanford-parser-full-2014-08-27 stanford-parser-full
mv stanford-postagger-2014-08-27 stanford-postagger
mv stanford-ner-2014-08-27 stanford-ner

echo "Removing zip files ..."
rm stanford-parser-full-2014-08-27.zip
rm stanford-postagger-2014-08-27.zip
rm stanford-ner-2014-08-27.zip
