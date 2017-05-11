
from . import run
from . import scan
from . import resetdb
from . import user
#from . import group
from . import resetindex
#from . import build_cache
#from . import verify_integrity

commands = ['run', 'resetdb', 'scan', 'user', 'resetindex', ]
try:
    from . import debug
    commands.append('debug')
except ImportError:
    pass

__all__ = commands
