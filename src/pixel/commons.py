class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def resetId():
    generator = get_id()

def nextId():
    return next(generator)

def get_id():
    id = 0
    while True:
        id = id + 1
        yield id


generator = get_id()
