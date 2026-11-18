"""S02: protect newly generated signing material from default-umask exposure.

POSIX mode tests; Windows ACLs require a separate approved on-machine audit.
Tests never print or upload a PEM.
"""
import os
import stat
import sys
from pathlib import Path

import pytest

from agentwitness.crypto import CryptoSigner


@pytest.mark.skipif(os.name != "posix", reason="POSIX file modes only")
@pytest.mark.parametrize("mask", [0o000, 0o022, 0o077])
def test_new_private_key_is_0600_under_multiple_umasks(tmp_path, mask):
    key_dir = tmp_path / "fresh-keys"
    previous = os.umask(mask)
    try:
        signer = CryptoSigner(key_dir)
    finally:
        os.umask(previous)
    assert stat.S_IMODE(key_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(signer.private_key_path.stat().st_mode) == 0o600
    signature = signer.sign("S02 canary")
    assert signer.verify("S02 canary", signature)
    assert not signer.verify("modified", signature)


def test_public_key_only_collision_fails_before_private_creation(tmp_path):
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    (key_dir / "public.pem").write_bytes(b"preexisting unrelated public data")
    with pytest.raises(RuntimeError, match="public key exists without private"):
        CryptoSigner(key_dir)
    assert not (key_dir / "private.pem").exists()


def test_mismatched_existing_private_and_public_are_rejected(tmp_path):
    a = CryptoSigner(tmp_path / "a")
    b = CryptoSigner(tmp_path / "b")
    (a.public_key_path).write_bytes(b.public_key_path.read_bytes())
    with pytest.raises(RuntimeError, match="keypair mismatch"):
        CryptoSigner(a.key_dir)


def test_write_failure_cannot_unlink_replaced_key(tmp_path, monkeypatch):
    key_dir = tmp_path / "keys"
    key_path = key_dir / "private.pem"
    replacement = b"another independently created key"
    def replace_and_fail(_fd):
        key_path.unlink()
        key_path.write_bytes(replacement)
        raise OSError("simulated fsync error")
    monkeypatch.setattr(os, "fsync", replace_and_fail)
    with pytest.raises(OSError, match="simulated fsync"):
        CryptoSigner(key_dir)
    assert key_path.read_bytes() == replacement


def test_reinitialization_never_overwrites_existing_key(tmp_path):
    signer = CryptoSigner(tmp_path / "keys")
    signature = signer.sign("original")
    same = CryptoSigner(tmp_path / "keys")
    assert same.verify("original", signature)
    assert same.sign("original") == signature


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlink fixtures only")
def test_private_key_symlink_rejected(tmp_path):
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("never modify me", encoding="utf-8")
    (key_dir / "private.pem").symlink_to(outside)
    with pytest.raises(ValueError, match="must not be symlinks"):
        CryptoSigner(key_dir)
    assert outside.read_text(encoding="utf-8") == "never modify me"


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlink fixtures only")
def test_public_key_symlink_rejected(tmp_path):
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("never modify me", encoding="utf-8")
    (key_dir / "public.pem").symlink_to(outside)
    with pytest.raises(ValueError, match="must not be symlinks"):
        CryptoSigner(key_dir)
    assert outside.read_text(encoding="utf-8") == "never modify me"


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlink fixtures only")
def test_directory_symlink_rejected(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="directory must not be a symlink"):
        CryptoSigner(linked)
