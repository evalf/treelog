'Logging framework that organizes messages in a tree'

__version__ = '1.0'

from importlib import import_module

_sub_mods = {
    'proto',
    'iter'
}
_state_attrs = {
    'set',
    'add',
    'disable',
    'context',
    'withcontext',
}
_state_funcs = {
    level + op
        for level in ['debug', 'info', 'user', 'warning', 'error']
            for op in ['', 'data', 'file']
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
_legacy = {
    'version': __version__,
    'Log': None,
}

def __dir__():
    return (
        '__version__',
        *_sub_mods,
        *_state_attrs,
        *_state_funcs,
        *_log_objs,
        *_legacy,
    )

def __getattr__(attr):
    if attr in _state_attrs:
        _state = import_module(f'._state', 'treelog')
        obj = getattr(_state, attr)
    elif attr in _state_funcs:
        _state = import_module(f'._state', 'treelog')
        obj = _state.partial(attr)
    elif attr in _log_objs:
        m = import_module(f'._{attr[:-3].lower()}', 'treelog')
        obj = getattr(m, attr)
    elif attr in _sub_mods:
        obj = import_module(f'.{attr}', 'treelog')
    elif attr in _legacy:
        obj = _legacy[attr]
    else:
        raise AttributeError(attr)
    globals()[attr] = obj
    return obj
