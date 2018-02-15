'''
Expand "environment" variables in string.
'''
import re
import os
import string

tmplExpandKeywords = {}

class SafeFormat(object) :
    '''Preserve unmatched format strings.'''
    def __init__(self, **kw) :
        self.__dict = kw

    def __getitem__(self, name) :
        return self.__dict.get(name, '{%s}' % name)


def addTemplateKey(key, value) :
    global tmplExpandKeywords
    tmplExpandKeywords[key] = value


def tmplExpandJson(j) :
    '''
    Expand the string values in a json object.
    '''
    if isinstance(j, list) and not isinstance(j, str) :
        # Expand array contents
        updated = []
        for obj in j :
            if isinstance(obj, dict) :
                # array of dicts
                updated.append(tmplExpandJson(obj))

            elif isinstance(obj, list) and not isinstance(obj, str) :
                # array of arrays
                updated.append(tmplExpandJson(obj))    

            elif  isinstance(obj, str) or isinstance(obj, unicode) :
                # array of strings - expand
                updated.append(tmplExpand(obj))

            else :
                # Other
                updated.append(obj)

        del j[:]
        j.extend(updated)

    elif isinstance(j, dict) : 
        # Expand dictionary
        for key in j :
            j[key] = tmplExpandJson(j[key])

    elif isinstance(j, str) or isinstance(j, unicode) :
        # Expand String
        j = tmplExpand(j)

    return j


def tmplExpand(s) :
    '''
    Replace environment variables of the format {var}.
    '''
    global tmplExpandKeywords
    #expanded = re.sub(r"\${(\w+?)}", r"{\1}", s)
    expanded = string.Formatter().vformat(s, [], SafeFormat(**tmplExpandKeywords))
    expanded = string.Formatter().vformat(expanded, [], SafeFormat(**os.environ.__dict__["data"]))
    return expanded
