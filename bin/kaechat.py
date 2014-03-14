#! /usr/bin/env python2.7
import sys, os
if __name__ == "__main__":
    sys.path.insert(0,
        os.path.join(os.path.dirname(__file__) or os.getcwd(), "..", "lib"))
    sys.path.insert(0,
        os.path.join(os.path.dirname(__file__) or os.getcwd(), "lib"))
    import kaechatlib
    kaechatlib.main()
