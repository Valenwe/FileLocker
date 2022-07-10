from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
import base64
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad


def base_to_str(byte):
    byte = base64.b64encode(byte)
    return byte.decode('utf-8')


def str_to_base(str):
    str = str.encode("utf-8")
    return base64.b64decode(str)


def encrypt_RSA(pub_key, data):
    encryptor = PKCS1_OAEP.new(RSA.import_key(pub_key).public_key())
    ciphered_text = encryptor.encrypt(data.encode('utf-8'))
    return base_to_str(ciphered_text)


def decrypt_RSA(priv_key, data):
    data = str_to_base(data)
    decryptor = PKCS1_OAEP.new(RSA.import_key(priv_key))
    deciphered_text = decryptor.decrypt(data)

    return deciphered_text.decode("utf8")


def generate_and_encrypt_AES(data):
    try:
        data = data.encode("utf-8")
    except:
        pass

    key = get_random_bytes(16)

    cipher = AES.new(key, AES.MODE_CTR)
    cipher_txt = cipher.encrypt(data)

    return base_to_str(key), base_to_str(cipher.nonce), base_to_str(cipher_txt)


def decrypt_AES(key, nonce, data):
    key = str_to_base(key)
    nonce = str_to_base(nonce)
    data = str_to_base(data)

    decipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    decipher_txt = decipher.decrypt(data)
    # print(decipher_txt)
    # decipher_txt = decipher_txt.decode("utf-8")
    return decipher_txt


def decrypt_AES_ECB(key, data):
    key = key.encode("utf8")
    data = str_to_base(data)

    decipher = AES.new(key, AES.MODE_ECB)
    decipher_txt = decipher.decrypt(data)

    # removes weird ending characters
    decipher_txt = unpad(decipher_txt, 16)

    return decipher_txt.decode("utf-8")


# check if a private key is ciphered or not

def key_is_ciphered(filename, file=True):
    if file:
        with open(filename, "r") as f:
            content = f.read()
    else:
        content = filename

    return "BEGIN" in content


"""
key, nonce, txt = generate_and_encrypt_AES("test")
new_txt = decrypt_AES(key, nonce, txt)
print(new_txt)
"""


"""
with open("keys/test2.pem", "r") as f:
    content = f.read()
# print(content)
test = decrypt_AES_ECB("28f9d1096757d0a6", content)
print(test)
"""
"""
key = "KtOkX4NJIehBhIh4RExhCBdqirjKYv7EA2njhtydpSHrX8M8OhVl8/Tyir1TYZz2rGUoZJg/9YYFzyTigw9nW16P6HoFAG/BxiEoT0Tr8O9DRMPiWEla9kpzPWtJc8RJfQMR4XMq7NQNy8OLH09Nf2QvaY/ifh6VJR/CqNF1Sv5ox0d3XN5dYBl6AYb5zWQEUUnoeDgFgQvkg8NUPREPHsW4bte889yCnCsh0YZOkIy3wzsNLQ7G9aM3wpMabohVgrF9kRWv6uoIfwwiRbtJVzc4XhAf+kUSYJ1ChpqMKmJ49iYbGTDD4jcmY604zEJWLiAf0oiVwqJyc3xGnE1wjg=="
nonce = "hCuSlFLXRjqhqsB6Oa0S/Ed6kPpXZOajDI7+bnxteJppey9YA0CyOoak2Qt9ldTUww0KlwOh6wxkJ6g8U8aTAF3bHje/I3JVZe6AoBsidJUMuddMsi+wgZCM83d+CZ5zMAFeGSUw0JLiSR1fQASknE1KWGDFQUsPAvibD5+/lceLLIRUgnAl2vaz22cV2r/PY3gcvBQSN8ABFkcNG6PKt14hg57pPmq9SMIygydyxvnBoEduVe/CaVQPrs0nEGzolAN83zMj9yIVzQDxkZ3kaHzEENSDPps0C7VvjKkBIpicEsOvn/ecmqISXj+8pUe9PE6wOOc0xHSTW8p54ZJtSw=="
text = "9lktcU/q9ZQq8zF5"

with open("keys/test2.pem", "r") as f:
    priv_key = f.read()

real_key = decrypt_RSA(priv_key, key)
real_nonce = decrypt_RSA(priv_key, nonce)
print(real_key, real_nonce)

real_text = decrypt_AES(real_key, real_nonce, text)
print(real_text)
"""
