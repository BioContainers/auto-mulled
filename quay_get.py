#!/home/wolffj/miniconda2/bin/python2.7

# Copyright 2016 Joachim Wolff
# Mail: wolffj@informatik.uni-freiburg.de
#
# Chair of Bioinformatics
# Department of Computer Science
# Faculty of Engineering
# Albert-Ludwigs-University Freiburg im Breisgau

import argparse
import cPickle as pickle
import hashlib
import json
import os
import shutil

import requests

from whoosh.fields import *
from whoosh.index import create_in
from whoosh.qparser import QueryParser


class QuayDownload():
    def __init__(self):
        self._index = None
    def __del__(self):
        pass

    def build_index(self, p_quey_namespace):
        """This functions creates a index to quickly examine the repositories of a given quay organization."""
        # download all information about the repositories from the
        # given organization in self._quay_namespace
        url = 'https://quay.io/api/v1/repository'
        parameters = {'public':'true','namespace': p_quey_namespace}
        r = requests.get(url, headers={'Accept-encoding': 'gzip'}, params=parameters,
                            timeout=12)

        # delete old index data and create the dir "indexdir" new
        if os.path.exists("indexdir"):
            shutil.rmtree("indexdir")
        os.mkdir("indexdir")
        schema = Schema(title=TEXT(stored=True))
        self._index = create_in("indexdir", schema)

        json_decoder = json.JSONDecoder()
        decoded_request = json_decoder.decode(r.text)
        # print(len(decoded_request))        
        writer = self._index.writer()
        for i in xrange(len(decoded_request['repositories'])):
            writer.add_document(title=decoded_request['repositories'][i]['name'])
       
        writer.commit()

    def search_repository(self, p_search_string):
        with self._index.searcher() as searcher:
            query = QueryParser("title", self._index.schema).parse(p_search_string)
            results = searcher.search(query)
            print "The query \"", p_search_string, "\" resulted in", len(results) ,"result(s)."
            for i in results:
                print i
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Searches in a given quay organization for a repository')
    parser.add_argument('--organization', dest='organization_string', type=str,
                        help='Organization.')
    parser.add_argument('--search', dest='search_string', type=str,
                        help='The name of the tool.')
    parser.add_argument('--update', dest='update_index', action='store_true',
                        help='The index of the given organization should be updated.')                    
    args = parser.parse_args()

    quay = None
    # check if index should be updated or if it needs to be created for the first time
    if args.update_index or not os.path.exists("QuayObj"):
        # update given Index if existing
        if os.path.exists("QuayObj"):
            os.remove("QuayObj")
        quay = QuayDownload()
        quay.build_index(args.organization_string)

    if os.path.exists("QuayObj"):
        fileObject = open("QuayObj",'r')
        quay = pickle.load(fileObject)
        fileObject.close()

    if args.search_string is not None:
        quay.search_repository(args.search_string)
    
    fileObject = open("QuayObj",'wb')
    pickle.dump(quay, fileObject)
    fileObject.close()
