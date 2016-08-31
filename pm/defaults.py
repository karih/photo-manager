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
# SEARCH_ROOT is the root folder under which we search for photos
SEARCH_ROOT = os.environ['HOME']
# SEARCH_EXCLUDE_DIRS is a list of common dir names that should be bypassed
SEARCH_EXCLUDE_DIRS = ['tmp', 'temp', 'backup'] # directory names that are omitted from search
# SEARCH_EXCLUDE_ABSOLUTE_PATHS is a list of absolute paths under SEARCH_ROOT that should be omitted
SEARCH_EXCLUDE_ABSOLUTE_PATHS = ['/do/not/look/in/here', ] 
# Note: In addition to these, all (hidden) folders starting with . are omitted from search.
