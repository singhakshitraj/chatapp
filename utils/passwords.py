from passlib.context import CryptContext

crypt_context = CryptContext(schemes=['bcrypt'])

class PasswordHelpers:
    @staticmethod
    def hash_password(plaintext_password):
        return crypt_context.hash(plaintext_password)
    
    @staticmethod
    def verify_password(incoming_password,hashed_password):
        return crypt_context.verify(secret=incoming_password,hash=hashed_password)