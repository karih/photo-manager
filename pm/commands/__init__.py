
from . import run
from . import scan
from . import resetdb
from . import group
from . import reindex
from . import build_cache

commands = ['run', 'resetdb', 'scan', 'group', 'reindex', 'build_cache']
try:
    from . import debug
    commands.append('debug')
except ImportError:
    pass

__all__ = commands
