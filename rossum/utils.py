from typing import TextIO
import hashlib

BUFFER_SIZE = 65536

def hash_file(file: TextIO) -> str:
    '''
    Hash a file object
    '''
    md5 = hashlib.md5()
    while True:
        data = file.read(BUFFER_SIZE)
        if not data:
            break
        md5.update(data)
    file.seek(0)
    return md5.hexdigest()

