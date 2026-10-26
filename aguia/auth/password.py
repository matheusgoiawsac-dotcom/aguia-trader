"""Password hashing utilities."""

import hashlib
import os
from typing import Optional, Tuple


try:
    from argon2 import PasswordHasher as _Argon2PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _ARGON2_AVAILABLE = True
except Exception:
    _ARGON2_AVAILABLE = False
    _Argon2PasswordHasher = None
    VerifyMismatchError = Exception


class PasswordHasher:
    def __init__(self):
        if _ARGON2_AVAILABLE:
            self._hasher = _Argon2PasswordHasher()
            self.algo = "argon2id"
        else:
            # Fallback to scrypt with reasonable params
            self._hasher = None
            self.algo = "scrypt"

    def hash_password(self, password: str) -> Tuple[str, str, Optional[str]]:
        if self.algo == "argon2id" and self._hasher:
            h = self._hasher.hash(password)
            return h, self.algo, None
        else:
            # scrypt fallback
            salt = os.urandom(16)
            key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=64)
            h = "$scrypt$" + salt.hex() + "$" + key.hex()
            params = "n=16384,r=8,p=1,dklen=64"
            return h, "scrypt", params

    def verify_password(self, password: str, stored_hash: str, algo: str = "argon2id") -> bool:
        try:
            if algo == "argon2id" and _ARGON2_AVAILABLE and self._hasher:
                self._hasher.verify(stored_hash, password)
                return True
            elif algo == "scrypt":
                try:
                    parts = stored_hash.split("$")
                    # format $scrypt$salt$key
                    if len(parts) >= 4:
                        salt_hex = parts[2]
                        key_hex = parts[3]
                        salt = bytes.fromhex(salt_hex)
                        expected = bytes.fromhex(key_hex)
                        got = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=len(expected))
                        # constant time compare
                        if len(got) != len(expected):
                            return False
                        result = 0
                        for a, b in zip(got, expected):
                            result |= a ^ b
                        return result == 0
                except Exception:
                    return False
                return False
            else:
                # try argon2 if available
                if _ARGON2_AVAILABLE and self._hasher:
                    try:
                        self._hasher.verify(stored_hash, password)
                        return True
                    except Exception:
                        return False
            return False
        except VerifyMismatchError:
            return False
        except Exception:
            return False
