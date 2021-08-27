import re
import requests

"""
Object representation of one Gist.

Args:
    Constructor requires json representation as given in Github's API.
"""
class Gist():
    def __init__(self, json_representation: str):
        self.__gist = json_representation
    """
    Returns:
        Gist's URL
    """    
    def url(self):
        return self.__gist['html_url']
    """
    Generator of all files in this Gist
    """ 
    def gist_files_generator(self):
        for file in self.__gist['files']:
            yield file
        # Untested, GET-param per_page=1 could be set, to force multi page to test this
        if self.__gist['truncated'] == "false":
            page = 2
            further_pages = True
            while further_pages == True:
                gist_page_json = requests.get(self.url, params={"page": page}).json()
                for file in gist_page_json:
                    yield file
                if gist_page_json['truncated'] == "false":
                    further_pages = False
                page += 1
    
    """
    Search all files in this Gist for a pattern
    
    Arguments:
        pattern: regular expression of search pattern
        
    Returns:
        List of files matching pattern
    """
    def search_all_gist_files_for_pattern(self, pattern: re) -> bool:
        for file in self.gist_files_generator():
            content = requests.get(self.__gist['files'][file]['raw_url']).text
            if pattern.search(content):
                return True
        return False
            

            


    
    
