from jalada.adapters.security.argon2_hasher import Argon2PasswordHasher


def test_a_hash_verifies_only_its_own_password() -> None:
    hasher = Argon2PasswordHasher()

    password_hash = hasher.hash("correct horse battery")

    assert password_hash.startswith("$argon2id$")
    assert hasher.verify(password_hash, "correct horse battery")
    assert not hasher.verify(password_hash, "wrong password")


def test_a_malformed_hash_fails_instead_of_raising() -> None:
    assert not Argon2PasswordHasher().verify("not-a-hash", "anything")
