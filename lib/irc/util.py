
def strlower(x):
    return str(x).lower().replace('{', ']').replace('}', ']')

class casedict(dict):
    """Case-insensitive dictionary. Keys MUST be strings.

    NOTE: Since this class is mainly used by the `irc' module, case
    insensitivity is defined as per the IRC protocol; that is, '[' and ']' are
    the lowercase versions of '{' and '}' respectively.
    """

    def __init__(self, src=None):
        dict.__init__(self)
        if src is not None:
            for k in src:
                self[k] = src[k]

    def __setitem__(self, key, value):
        dict.__setitem__(self, strlower(key), value)

    def __getitem__(self, key):
        return dict.__getitem__(self, strlower(key))

    def __delitem__(self, key):
        return dict.__delitem__(self, strlower(key))

    def __contains__(self, key):
        return dict.__contains__(self, strlower(key))

if __name__ == "__main__":
    d = casedict()
    d["hello"] = "Hi!"
    assert d["hello"] == d["hElLo"]
    print d["HELLO"]
    print d
    del d["HeLLo"]
    print d
