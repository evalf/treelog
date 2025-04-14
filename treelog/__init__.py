'Logging framework that organizes messages in a tree'

__version__ = '1.0'

from importlib import import_module

_sub_mods = {
    'proto',
    'iter'
}
_state_attrs = {
    'current',
    'set',
    'add',
    'disable',
    'context',
    'withcontext',
}
_log_objs = {
    'DataLog',
    'FilterLog',
    'HtmlLog',
    'LoggingLog',
    'NullLog',
    'RecordLog',
    'RichOutputLog',
    'StderrLog',
    'StdoutLog',
    'TeeLog',
}
_log_funcs = {
    'debug',
    'info',
    'user',
    'warning',
    'error',
}
_log_file_funcs = {
    'debugfile',
    'infofile',
    'userfile',
    'warningfile',
    'errorfile',
}
_legacy = {
    'version': __version__,
    'Log': None,
}

def __dir__():
    return (
        '__version__',
        *_sub_mods,
        *_state_attrs,
        *_log_objs,
        *_log_funcs,
        *_log_file_funcs,
        *_legacy,
    )

def __getattr__(attr):
    if attr in _state_attrs:
        _state = import_module(f'._state', 'treelog')
        obj = getattr(_state, attr)
    elif attr in _log_funcs:
        _state = import_module(f'._state', 'treelog')
        obj = _state.Print(getattr(_state.Level, attr))
    elif attr in _log_file_funcs:
        _state = import_module(f'._state', 'treelog')
        obj = _state.Print(getattr(_state.Level, attr[:-4])).open
    elif attr in _log_objs:
        m = import_module(f'._{attr[:-3].lower()}', 'treelog')
        obj = getattr(m, attr)
    elif attr in _sub_mods:
        obj = import_module(f'.{attr}', 'treelog')
    elif attr in _legacy:
        obj = _legacy[attr]
    else:
        raise AttributeError(attr)
    if attr != 'current':
        globals()[attr] = obj
    return obj
