#/usr/bin/env python

# Copyright 2016 Joachim Wolff
# Mail: wolffj@informatik.uni-freiburg.de
# License: MIT
#
# Chair of Bioinformatics
# Department of Computer Science
# Faculty of Engineering
# Albert-Ludwigs-University Freiburg im Breisgau

import argparse
import json
import os
import shutil

import requests

from whoosh.fields import Schema
from whoosh.fields import TEXT
from whoosh.fields import STORED
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.spelling import Corrector
from whoosh import qparser

class QuaySearch():
    """Tool to search within a quay organization for listed software. Prints out search results with docker download command."""
    def __init__(self, p_organization):
        self._index = None
        self._organization = p_organization
    def __del__(self):
        pass

    def build_index(self):
        """This functions creates a index to quickly examine the repositories of a given quay organization."""
        # download all information about the repositories from the
        # given organization in self._organization
        url = 'https://quay.io/api/v1/repository'
        parameters = {'public':'true','namespace': self._organization}
        r = requests.get(url, headers={'Accept-encoding': 'gzip'}, params=parameters,
                            timeout=12)

        # delete old index data and create the dir "indexdir" new
        if os.path.exists("indexdir"):
            shutil.rmtree("indexdir")
        os.mkdir("indexdir")
        schema = Schema(title=TEXT(stored=True), content=STORED)
        self._index = create_in("indexdir", schema)

        json_decoder = json.JSONDecoder()
        decoded_request = json_decoder.decode(r.text)
        writer = self._index.writer()
        for repository in decoded_request['repositories']:
            writer.add_document(title=repository['name'], content=repository['description'])
        writer.commit()

    def search_repository(self, p_search_string, p_non_strict):
        """This function searches matching repositories of an organization.
         Results are displayed with all available versions. Docker download command is given too."""
        # with statement closes searcher after usage.
        with self._index.searcher() as searcher:
            search_string = u"*%s*" % p_search_string
            query = QueryParser("title", self._index.schema).parse(search_string)

            results = searcher.search(query)
            
            if p_non_strict:
                # look for spelling errors and use suggestions as a search term too
                corrector = searcher.corrector("title")
                alternative_strings =  corrector.suggest(p_search_string, limit=2)

                # get all repositories with suggested keywords
                for i in alternative_strings:
                    # search_string = u"*" + u"%s" % i + u"*"
                    search_string = u"*%s*" % i
                    query = QueryParser("title", self._index.schema).parse(search_string)
                    results_tmp = searcher.search(query)
                    results.extend(results_tmp)
           
            # get all versions for the found tools
            dict_results = {}
            for i in results:
                additional_info = self.get_additional_repository_information(i['title'])
                print additional_info
                dict_results[i['title']] = additional_info.keys()
            
            print "The query ", '\033[1m' + p_search_string + '\033[0m', " resulted in", len(results) ,"result(s).",
            
            if p_non_strict:
                print "The search lists the results for ",
                for result in alternative_strings:
                    print '\033[1m' + result + '\033[0m', ", ",
                print "too."
            for i in dict_results:
                print i, "\n\t\t\t", 
                for j in dict_results[i]:
                    print j, "\t\t", "docker pull quay.io/"+self._organization+"/"+i+":"+j+"\n\t\t\t",
                print "\n"
   
    def get_additional_repository_information(self, p_repository_string):
        """Function downloads additional information from quay.io to get the tag-field which includes the version number."""
        url = 'https://quay.io/api/v1/repository/' + u"%s" % self._organization + "/" + u"%s" % p_repository_string
        r = requests.get(url, headers={'Accept-encoding': 'gzip'}, timeout=12)

        json_decoder = json.JSONDecoder()
        decoded_request = json_decoder.decode(r.text)
        return decoded_request['tags']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Searches in a given quay organization for a repository')
    parser.add_argument('--organization', dest='organization_string', type=str,
                        help='Change organization. Default is mulled.')
    parser.add_argument('--non-strict', dest='non_strict_bool', action="store_true",
                        help='Autocorrection of typos activated. Lists more results but can be confusing.\
                        For too many queries quay.io blocks the request and the results can be incomplete.')
    parser.add_argument('search', type=str,
                        help='The name of the tool you want to search for.')        
    args = parser.parse_args()
    
    if args.organization_string is None:
        args.organization_string = 'mulled'
    quay = QuaySearch(args.organization_string)
    quay.build_index()

    if args.search is not None:
        quay.search_repository(args.search, args.non_strict_bool)
    if os.path.exists("indexdir"):
        shutil.rmtree("indexdir")