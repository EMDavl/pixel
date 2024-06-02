import bcrypt

class AuthorizationManager():
    credentials = {}

    @classmethod
    def parse_file(cls, path):
        with open(path) as file:
            lines = file.read().splitlines()
        salt = bcrypt.gensalt()

        for line in lines:
            credentials = line.split(",")
            assert len(credentials) == 2
            login, password = credentials
            assert len(login) > 3
            assert len(password) >= 8
            cls.credentials[login] = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    @classmethod
    def valid_credentials(cls, login, password):
        hashed_pswd = cls.credentials.get(login)
        if hashed_pswd is None:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), hashed_pswd)
        
        