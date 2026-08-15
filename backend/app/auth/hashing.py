import bcrypt

# Previously used passlib's CryptContext, but passlib is unmaintained and
# has a well-known compatibility break with bcrypt >= 4.1 (it probes
# `bcrypt.__about__.__version__`, which newer bcrypt releases removed -
# this made every single register/login call crash with a 500). Using
# the `bcrypt` library directly avoids that fragile version-detection
# entirely.
#
# bcrypt has a hard 72-byte input limit; passwords are truncated to that
# (a standard, well-known bcrypt constraint - not a security weakening
# for realistic password lengths) rather than raising an opaque error.


def _prepare(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_prepare(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            _prepare(password), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed/legacy hash in the DB - treat as "doesn't match"
        # rather than crashing the login route.
        return False
