echo "Install python requirements ..."
pip install -r /path/to/requirements.txt 

echo "Download stanford-parser ..."
wget http://nlp.stanford.edu/software/stanford-parser-full-2014-08-27.zip
echo "Download stanford-tagger ..."
wget http://nlp.stanford.edu/software/stanford-postagger-2014-08-27.zip
echo "Download stanford-ner-tagger ..."
http://nlp.stanford.edu/software/stanford-ner-2014-08-27.zip

unzip stanford-parser-full-2014-08-27.zip -d stanford-parser-full
unzip stanford-postagger-2014-08-27.zip -d stanford-postagger
unzip stanford-ner-2014-08-27.zip -d stanford-ner