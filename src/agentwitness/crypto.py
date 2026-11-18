import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib

KEY_PATH = Path(os.getcwd()) / ".agentwitness" / "keys"

class CryptoSigner:
    def __init__(self, key_dir: Path = KEY_PATH):
        self.key_dir = key_dir
        self.private_key_path = self.key_dir / "private.pem"
        self.public_key_path = self.key_dir / "public.pem"
        self._ensure_keys()

    def _ensure_keys(self):
        # The key directory is private when AgentWitness creates it. Existing
        # user-managed directories are not silently chmodded or recreated.
        if self.key_dir.is_symlink():
            raise ValueError("Signing key directory must not be a symlink")
        self.key_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.key_dir.is_symlink():
            raise ValueError("Signing key directory must not be a symlink")
        if self.private_key_path.is_symlink() or self.public_key_path.is_symlink():
            raise ValueError("Signing key files must not be symlinks")

        # A pre-existing public key with no private counterpart is an
        # incomplete/mismatched keypair, not permission to generate a new one.
        if not self.private_key_path.exists() and self.public_key_path.exists():
            raise RuntimeError("Signing keypair incomplete: public key exists without private key")

        if not self.private_key_path.exists():
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            # open(..., "wb") inherits the process umask, which is commonly
            # 022 and can expose an unencrypted Ed25519 PEM as mode 0644.
            # O_EXCL prevents replacing an existing key or symlink. Mode
            # 0600 is enforced at creation on POSIX, regardless of umask.
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            fd = os.open(
                self.private_key_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            # On write/fsync failure, fail closed but NEVER unlink the path:
            # another process might have replaced its directory entry, and
            # deleting it could destroy unrelated signing material. A partial
            # private file requires explicit, authorised remediation.
            with os.fdopen(fd, "wb") as handle:
                handle.write(pem)
                handle.flush()
                os.fsync(handle.fileno())

            # The public key is safe to publish, but never overwrite an
            # existing file: an unexpected keypair collision must be visible.
            with open(self.public_key_path, "xb") as handle:
                handle.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ))

        # Crash/concurrency and pre-existing-file safety: never sign a receipt
        # if both files exist but belong to different keypairs.
        if not self.private_key_path.is_file() or not self.public_key_path.is_file():
            raise RuntimeError("Signing keypair incomplete; cannot sign or verify")
        private = self._get_private_key()
        public = self._get_public_key()
        expected = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        actual = public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        if expected != actual:
            raise RuntimeError("Signing private/public keypair mismatch")

    def _get_private_key(self):
        with open(self.private_key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None
            )

    def _get_public_key(self):
        with open(self.public_key_path, "rb") as f:
            return serialization.load_pem_public_key(f.read())

    def sign(self, payload: str) -> str:
        private_key = self._get_private_key()
        signature = private_key.sign(payload.encode("utf-8"))
        return signature.hex()

    def verify(self, payload: str, signature_hex: str) -> bool:
        public_key = self._get_public_key()
        try:
            public_key.verify(bytes.fromhex(signature_hex), payload.encode("utf-8"))
            return True
        except Exception:
            return False

def hash_payload(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
