#!/usr/bin/env python3
"""Patch data Kleaf 6.6 agar bisa dibaca Kleaf 6.12.

Kleaf 6.12 membuat satu filegroup untuk setiap output yang dideklarasikan
kernel_build(). Daftar module_outs dari device modules 6.6 masih memuat
fs/pstore/pstore_{blk,zone}.ko dua kali, karena modul tersebut sudah pindah
ke daftar GKI arm64 di kernel 6.12. Output ganda membuat Bazel gagal dengan
"filegroup rule ... conflicts with existing filegroup rule".

Skrip ini membungkus empat daftar gabungan di mgk_64.bzl dengan dedupe yang
menjaga urutan. Aman dijalankan berulang (idempotent).
"""

from pathlib import Path
import sys

BZL = Path("kernel_device_modules-6.6/kernel/kleaf/mgk_64.bzl")

HELPER = '''def klee_dedupe(seq):
    """Hapus output ganda tanpa mengubah urutan."""
    seen = {}
    result = []
    for item in seq:
        if item not in seen:
            seen[item] = True
            result.append(item)
    return result

'''

LISTS = [
    ("mgk_64_common_modules", "mgk_module_outs + mgk_64_module_outs"),
    (
        "mgk_64_common_eng_modules",
        "mgk_module_outs + mgk_module_eng_outs + mgk_64_module_outs",
    ),
    (
        "mgk_64_common_userdebug_modules",
        "mgk_module_outs + mgk_module_userdebug_outs + mgk_64_module_outs",
    ),
    (
        "mgk_64_common_user_modules",
        "mgk_module_outs + mgk_module_user_outs + mgk_64_module_outs",
    ),
]


def main() -> int:
    if not BZL.is_file():
        print(f"ERROR: {BZL} tidak ditemukan", file=sys.stderr)
        return 1

    text = BZL.read_text()
    marker = 'mgk_64_defconfig = "mgk_64_k66_defconfig"'
    if "def klee_dedupe(seq):" not in text:
        if marker not in text:
            print(f"ERROR: marker tidak ditemukan di {BZL}", file=sys.stderr)
            return 1
        text = text.replace(marker, HELPER + marker, 1)

    for name, expr in LISTS:
        old = f"{name} = {expr}"
        new = f"{name} = klee_dedupe({expr})"
        if new in text:
            continue
        if old not in text:
            print(f"ERROR: baris tidak ditemukan: {old}", file=sys.stderr)
            return 1
        text = text.replace(old, new, 1)

    BZL.write_text(text)
    print(f"OK: {BZL} module_outs didedupe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
