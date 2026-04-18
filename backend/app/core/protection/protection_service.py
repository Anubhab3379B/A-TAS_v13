"""
[Module 4] Self-Protection & Integrity Service.
Dynamic SHA-256 tree-hash of the live source code — NOT a static sentinel.
"""
import hashlib
import os
import psutil
from loguru import logger
from pathlib import Path


class ProtectionService:
    """
    [Module 4] A-TAS Self-Protection & Integrity Guard.
    Computes a live SHA-256 tree-hash of the entire app/ source tree at startup.
    Any modification to source files is detected on the next integrity check.
    """

    def __init__(self):
        self._app_root = Path(__file__).resolve().parent.parent.parent
        self.code_integrity_hash = self._calculate_self_hash()
        logger.info(
            f"A-TAS Self-Protection Layer Online. "
            f"Baseline hash: {self.code_integrity_hash[:16]}..."
        )

    def _calculate_self_hash(self) -> str:
        """
        Walks the app/ directory tree, hashing every .py file's content.
        Returns a combined SHA-256 hex-digest as the integrity baseline.
        Deterministic across runs on unmodified code.
        """
        combined = hashlib.sha256()
        for py_file in sorted(self._app_root.rglob("*.py")):
            try:
                combined.update(py_file.read_bytes())
            except (IOError, PermissionError):
                pass
        return combined.hexdigest()

    def verify_integrity(self) -> bool:
        """Re-computes the live hash and compares to the baseline."""
        current_hash = self._calculate_self_hash()
        if current_hash != self.code_integrity_hash:
            logger.critical(
                "SYSTEM INTEGRITY COMPROMISED — "
                f"Hash mismatch: {current_hash[:16]} ≠ {self.code_integrity_hash[:16]}"
            )
            return False
        return True

    def detect_debuggers(self) -> bool:
        """Detects presence of common reverse-engineering / analysis tools."""
        analysis_procs = {"x64dbg", "ghidra", "wireshark", "fiddler", "ida64", "radare2", "dnspy"}
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if name in analysis_procs:
                    logger.warning(f"Analysis tool detected: {proc.info['name']}.")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def obfuscate_data(self, data: str) -> str:
        """XOR-based obfuscation for tactical data strings."""
        key = 0x41
        return "".join(chr(ord(c) ^ key) for c in data)

    def _lockdown(self):
        logger.error("LOCKDOWN INITIATED — purging volatile memory...")
        os._exit(1)
