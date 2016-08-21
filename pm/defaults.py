import stat

USE_X_ACCEL = None
TRUST_PROXY = False
SAVE_MASK = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH # save thumbnails with 0644
SAVE_GROUP = None # save thumbnails with another gid, must be numerical

