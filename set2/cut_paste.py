#!/usr/bin/python3

import aes_lib
from pkcs7 import Pkcs7
from pkcs7 import StripPkcs7

# Block size used by AES here.
BLOCK_SIZE = 16

def ParseCookie(cookie):
	params = {}
	print(cookie)

	for url_param in cookie.decode().split('&'):
		kv = url_param.split('=')
		params[kv[0]] = kv[1]

	return params

def EncodeProfile(profile):
	# Ensures all profile info are always encoded in the same order.
	return 'email=%s&uid=%s&role=%s' % (
		profile['email'], profile['uid'], profile['role'])

def CreateProfile(email_address):
	# Don't allow encoding special characters in email addresses.
	if '&' in email_address or '=' in email_address:
		raise Exception('Invalid characters in profile.')

	profile = {}
	profile['email'] = email_address
	profile['uid'] = 10
	profile['role'] = 'user'

	return EncodeProfile(profile)

def CreateEncryptedProfile(email_address, encrypter):
	profile = CreateProfile(email_address)
	return encrypter.aes_pad_and_encrypt(bytes(profile, 'ascii'))

def DecryptRole(encrypted_profile, encrypter):
	pt = encrypter.aes_decrypt_and_depad(encrypted_profile)
	profile = ParseCookie(pt)
	return profile

def StartPositionEqualBytes(s1, s2):
	assert len(s1) == len(s2)
	start_pos = -1
	size = 0
	found_equal_byte = False

	for i in range(0, len(s1)):
		if s1[i] == s2[i]:
			if not found_equal_byte:
				start_pos = i
				found_equal_byte = True
			size += 1

		if found_equal_byte and s1[i] != s2[i]:
			break

	return (start_pos, size)

if __name__ == "__main__":
	enc = aes_lib.AESCipher()

	# The length of the email address is such that the encoded
	# profile string will be composed for 36 bytes: the last 4 bytes,
	# containing the word 'user', will lay at the beginning of a new
	# block (with padding).
	p1 = CreateEncryptedProfile('aname@bar.com', enc)

	# The second address is such that the second 16-byte block will
	# start with admin; the remaining bytes are filled with the Pkcs7
	# padding that we know our oracle uses internally. The rest of
	# the address is optional, but we include it in case our oracle
	# performs some basic validation of email addresses.
	address = 'XXXXXXXXXXadmin'
	address += chr(11) * 11
	address += '@bar.it'

	p2 = CreateEncryptedProfile(address, enc)
	# The second block contains the ciphertext we are looking for.
	encrypted_admin_block = p2[16:32]

	# We replace the last block of p1 with the encrypted "admin"
	# block.
	fake_admin = p1[:32]
	fake_admin += encrypted_admin_block

	# TADA! Same profile, but role is now admin.
	print(DecryptRole(fake_admin, enc))