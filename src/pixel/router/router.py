import pixel.web.web as web

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Router(metaclass=Singleton):
    def __init__(self):
        self.data = {}

    def add_img(self, id, img_path):
        self.data[id] = img_path
    
    @classmethod
    def create(cls):
        Router()