# Whatson
This is the repository for an experimental Question-Answering-System developed in the context of the "Special Topics in Artificial Intelligence" WS14 course at the University of Osnabrück.

## Installation on Ubuntu
```
git clone https://github.com/mome/watson
cd watson
./install_requirements.sh
```


### System Package Requirements :
* python2.7
* python-pip
* java
* graphviz (for parsetree printing)
* mplayer (for speech synthesis)

### Python Requirements :
* nltk
* html2text
* rdflib
* wikipedia

### External Requirements :
* Stanford Parser
* Stanford NER-Tagger
* Stanford POS-Tagger

## ToDo:
* introduce answer choice function
* integrate document_search() into QA
** some function from question to document_search() call (question types)
** answer generation (answer types)
* document_search(): keyword to ner-macht-word distance
* introduce answer confidence
* expand NER to more than 3 or 7 classes (with some ontology: cyc, dbpedia, ...)
* more document sources than wikipedia (schoolarpedia, wikibooks, maybe own corpus storage (netstore??))
