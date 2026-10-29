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
        self.key_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

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
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(pem)
                    handle.flush()
                    os.fsync(handle.fileno())
            except BaseException:
                # Best effort clean-up of a partially created private file.
                try:
                    self.private_key_path.unlink()
                except OSError:
                    pass
                raise

            # The public key is safe to publish, but never overwrite an
            # existing file: an unexpected keypair collision must be visible.
            with open(self.public_key_path, "xb") as handle:
                handle.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ))

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
