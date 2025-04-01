import random
import string

class ShortURL:
    def __init__(self, short_code, url):
        self.short_code = short_code
        self.url = url

def short_code_generator():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))