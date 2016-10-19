
from . import run
from . import scan
from . import resetdb
from . import group
from . import reindex
from . import build_cache
from . import verify_integrity

commands = ['run', 'resetdb', 'scan', 'group', 'reindex', 'build_cache', 'verify_integrity']
try:
    from . import debug
    commands.append('debug')
except ImportError:
    pass

__all__ = commands
