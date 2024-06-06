import pickle
import hashlib
import inspect
import copy


class CacheManagerSnapshot:
    def __init__(self, functions):
        self.functions = functions



class CacheManager:

    functions = set()
    cache = {}

    @classmethod
    def register_function(cls, func):
        cls.functions.add(_function_hash(func))
    
    @classmethod
    def snapshot(cls):
        functions_snapshot = copy.deepcopy(cls.functions)
        cls.functions = set()
        return CacheManagerSnapshot(functions_snapshot)

    @classmethod
    def get(cls, func, *args, **kwargs):
        function_cache = cls.cache.get(_function_hash(func))
        if function_cache is not None:
            key = _cache_key(args, kwargs)
            val = function_cache.get(key)
            if val is not None:
                return pickle.loads(val)
        return None

    @classmethod
    def put(cls, func, val, *args, **kwargs):
        hashcode = _function_hash(func)
        function_cache = cls.cache.get(hashcode)
        if function_cache is None:
            cls.cache[hashcode] = function_cache = {}
        
        key = _cache_key(args, kwargs)
        function_cache[key] = pickle.dumps(val)
    

    @classmethod
    def cleanup(cls, snapshot):
        changed = False
        for function_hash in snapshot.functions:
            if function_hash not in cls.functions:
                cls.cache.pop(function_hash, None)
                changed = True
        
        if changed:
            print("Removed obsolete caches")



def _get_hash(data):
    data_bytes = pickle.dumps(data)
    return hashlib.md5(data_bytes).hexdigest()

def _cache_key(args, kwargs):
    return _get_hash((args, kwargs))
    

def _function_hash(func):
    func_code = inspect.getsource(func)
    func_code_hash = hashlib.sha256(func_code.encode('utf-8')).hexdigest()

    func_globals = {k: v for k, v in func.__globals__.items() if k in func.__code__.co_names}
    globals_hash = _get_hash(func_globals)
    
    return hashlib.md5((func_code_hash + globals_hash).encode('UTF-8')).hexdigest()
