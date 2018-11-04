import re
import os
import stat

# PLEASE DO NOT CHANGE THIS FILE
# TO CUSTOMIZE SETTINGS, OVERWRITE VARIABLES IN pm/devconfig.py *OR* SPECIFY CONFIG
# FILE THROUGH THE ENVIRONMENT VARIABLE $PM_CONFIG (ONE OF THESE MUST BE PRESENT)

# Flask DEBUG mode
DEBUG = False

# Secret key used for various hashing operation, please overwrite.
SECRET_KEY = 'secret'

# Whether to send X_ACCEL_ headers, allowing reverse proxies (such as nginx) to handle delivery of files.
# False - Python/Flask reads and sends files.
# True - Python/Flask sends X_ACCEL headers indicating what file to send, see nginx sample config for more info.
# None - Auto-detect, checks for presence of X-FORWARDED-FOR header to determine if we sit behind a proxy 
USE_X_ACCEL = None

# Elasticsearch url and index name
ELASTICSEARCH_HOSTS = ['127.0.0.1:9200', ]
ELASTICSEARCH_INDEX = "photos"

# PostgreSQL connection string
SQLALCHEMY_DATABASE_URI = 'postgresql://user@localhost/dbname'

# Redis connection string (see https://redis-py.readthedocs.io/en/latest/)
#REDIS_URI = "redis://[:password]@localhost:6379/0"
REDIS_URI = "redis://localhost:6379/0"


# TEMP_DIR is where thumbnails (small and large) are stored.
# This can grow to a decent size and probably should be preserved on reboot.
# /var/tmp is chosen here, but this should probably be overwritten
TEMP_DIR = '/var/tmp'
# SAVE_MASK denotes the write mask of thumbnails, this corresponds to 0644
SAVE_MASK = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
# SAVE_GROUP allows specifying another gid under which we save thumbnails 
# Note: This must be the numerical gid, or None (for current user)
SAVE_GROUP = None

### Photo scanning options
# SEARCH_ROOTS are the root folders under which we search for photos
# this should be a list of two-tuples, where the first entry is a directory, and the 
# second entry is a user or list of users which are considered "owners" of these files
# users can be specified by username (string) or database id (integers)
SEARCH_ROOTS = [
    (os.environ['HOME'], 1)
]
# SEARCH_EXCLUDE_DIRS is a list of regular expression patterns, which if matched 
# using re.fullmatch() will not traverse into matched directory
SEARCH_EXCLUDE_DIRS = [
    r'.*?\/\..+', # skip hidden directories (starting with a dot)
    r'.*?\/[Tt][Ee]?[Mm][Pp]', # skip directories named 'tmp' and 'temp'
    r'.*?\/[Cc]ache', # skip directories named 'cache'
    r'.*?\/[Dd]ownloads', # skip directories named 'Downloads'
    r'.*?\/__MACOSX', # skip directories named '__MACOSX'
    r'.*?\/[Rr]ecycled', # skip directories named 'Recycled'
    r'.*?\/[Mm]y [Mm]usic', # skip directories named 'My Music'
    #re.escape(r'/some/absolute/path/we/avoid'), 
] 
# SEARCH_EXCLUDE_FILES is a list of regular expression patterns, which if
# matched using re.fullmatch() (with entire path) will skip that file
SEARCH_EXCLUDE_FILES = [
    r'.*?\/\..+', # skip hidden files
    r'.*?\/[Aa]lbum[Aa]rt[^\/]*'
]

# Cookie things
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_SECURE = False

# Photo sizes - here we reuse flickr sizes
# - https://www.flickr.com/services/api/misc.urls.html
# tuple is (widthx, widthy, cut to size, jpg compression)
# by default, all sizes are considered for computer/web use and are exported in the sRGB color space
# only original photos may be in other color spaces
SIZES = {
    's' : (75,   75,   True , 0.95), 
    'q' : (150,  150,  True , 0.95),
    't' : (100,  100,  False, 0.95), 
    'm' : (240,  240,  False, 0.95), 
    'n' : (320,  320,  False, 0.95), 
    'l' : (500,  500,  False, 0.95),
    'z' : (800,  800,  False, 0.95),
    'c' : (1024, 1024, False, 0.95),
    'h' : (1600, 1600, False, 0.95),
    'k' : (2048, 2048, False, 0.95),
    'o' : (None, None, False, 0.95) # original
}

THUMB_SIZE = 256, 256
LARGE_SIZE = 800, 800
