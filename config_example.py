AD_SERVER = "ad.example.net"
AD_DOMAIN = "example.net"
AD_CA_CERT_FILE = "rootca.crt" 
AD_BIND_USERNAME = "SA-ADLookup"
AD_BIND_PASSWORD ="12345LuggaggeAmazing"

SECRET_KEY = "change-this-to-something-random"

"""
# To generate a random string for SECRET_KEY 

from __future__ import print_function

from os import urandom
import binascii

print(binascii.hexlify(urandom(32)).decode(encoding="utf-8"))
"""
