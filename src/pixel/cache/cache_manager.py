import cachier

class CacheManager:

    @classmethod
    def get(cls, func, *args, **kwargs):
        cache = cachier.cachier(cache_dir='.cachier_cache', backend='pickle', pickle_reload=)
        cached_func = cache(func) 
        return cached_func(*args, **kwargs)

    @classmethod
    def put(cls, function_name, val, *args, **kwargs):
        pass