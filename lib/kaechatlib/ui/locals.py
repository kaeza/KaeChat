
import re

HTTPS_RE = re.compile(r'https?://[^ \t]+')
SFTP_RE = re.compile(r's?ftp://[^ \t]+')

TEXT_TAG = None
WEB_LINK_TAG = "web-link"
CHANNEL_LINK_TAG = "channel-link"
