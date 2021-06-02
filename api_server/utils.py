from hashlib import sha1

def data_to_hash(data: dict):
    return sha1(str(data).encode()).hexdigest() 
