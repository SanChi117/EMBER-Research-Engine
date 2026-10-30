#!/usr/bin/env python3
"""Reboot baseline contract for 4-repository Git SHA inventory, stdlib only.

These tests verify the frozen source-index's internal consistency only.
They do NOT imply CI for all 2,189 files, no economic PASS, no runtime access.
"""
from __future__ import annotations
from collections import Counter
import copy
import json
from pathlib import Path
import re
import unittest

FILE=Path(__file__).resolve().parents[1]/"docs/PROJECT_RESET_20261030/00_MACHINE_INVENTORY_GIT_TREES.json"
EXPECT={
    "EMBER":(1455,458,163,201,430),
    "SMOKE_STRATEGY":(160,106,16,16,10),
    "SMOKE_TERMINAL_MAIN":(326,236,45,38,8),
    "TELEGRAM_BOT":(248,48,188,2,29),
}
SHA40=re.compile(r"^[0-9a-f]{40}$")

def validate(document:dict):
    entries=document["all_code_and_file_paths"]
    summary=document["sources"]
    if document.get("schema")!="EMBER_REBOOT_FULL_GIT_BLOB_INVENTORY_V1":
        raise AssertionError("WRONG_CATALOG_SCHEMA")
    if len(entries)!=2189 or len(summary)!=4:
        raise AssertionError("MISSING_OR_ADDED_REPOSITORY_FILES")
    counts=Counter(e["repo"] for e in entries)
    for name,expected in EXPECT.items():
        n=expected[0]
        if counts[name]!=n: raise AssertionError(f"BAD_{name}_COUNT")
    for e in entries:
        if not isinstance(e["path"],str) or (
            not e["path"] or e["path"].startswith("/") or
            ".." in e["path"].split("/") or "\n" in e["path"]):
            raise AssertionError("UNSAFE_OR_EMPTY_GIT_PATH")
        if not SHA40.fullmatch(e["git_blob_sha"]):
            raise AssertionError("UNVERIFIED_GIT_BLOB_SHA")
        if not isinstance(e["bytes"],int) or e["bytes"]<0:
            raise AssertionError("INVALID_GIT_BLOB_LENGTH")
    keys={(e["repo"],e["ref"],e["path"]) for e in entries}
    if len(keys)!=len(entries):raise AssertionError("DUPLICATE_GIT_FILE_RECORD")
    for s in summary:
        if s.get("tree_truncated") is not False:
            raise AssertionError("GITHUB_TREE_WAS_TRUNCATED")
        if s["files"] not in counts.values():
            raise AssertionError("SOURCE_FILE_COUNT_NOT_IN_MANIFEST")
        if not isinstance(s["bytes"],int) or s["bytes"]<=0:
            raise AssertionError("MISSING_SOURCE_BYTES")
    a={x["path"]:x for x in entries if x["repo"]=="SMOKE_STRATEGY"}
    b={x["path"]:x for x in entries if x["repo"]=="SMOKE_TERMINAL_MAIN"}
    overlapping=[k for k in a if k in b]
    identical=[k for k in overlapping if a[k]["git_blob_sha"]==b[k]["git_blob_sha"]]
    ov=document["source_overlap"]
    if (len(overlapping),len(identical),len(overlapping)-len(identical))!=(
        ov["shared_paths"],ov["identical_sha"],ov["different_shared_paths"]):
        raise AssertionError("DUPLICATION_SHA_CENSUS_MISMATCH")
    if len(overlapping)!=126 or len(identical)!=121:
        raise AssertionError("UNEXPECTED_SOURCE_OVERLAP")
    versions={s["repo"]:s["ref"] for s in summary}
    if versions["SanChi117/EMBER-Research-Engine"]!="041eaf9fe8275c8c66047efc489b6b72b818a04d":
        raise AssertionError("C117_A181_SOURCE_REF_CHANGED")
    return True

class FrozenInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory=json.loads(FILE.read_text(encoding="utf-8"))
    def test_exact_manifest_with_original_git_blobs(self):
        self.assertTrue(validate(self.inventory))
    def test_does_not_confuse_testing_with_profit(self):
        self.assertEqual(self.inventory["notes"][0].startswith(
            "Inventory is Git trees only"),True)
    def test_missing_file_rejected(self):
        q=copy.deepcopy(self.inventory);q["all_code_and_file_paths"].pop()
        with self.assertRaisesRegex(AssertionError,"MISSING_OR_ADDED"):
            validate(q)
    def test_duplicate_original_repo_path_rejected(self):
        q=copy.deepcopy(self.inventory)
        q["all_code_and_file_paths"][1]["path"]=q["all_code_and_file_paths"][0]["path"]
        q["all_code_and_file_paths"][1]["ref"]=q["all_code_and_file_paths"][0]["ref"]
        q["all_code_and_file_paths"][1]["repo"]=q["all_code_and_file_paths"][0]["repo"]
        with self.assertRaisesRegex(AssertionError,"DUPLICATE_GIT_FILE"):
            validate(q)
    def test_fake_blob_sha_rejected(self):
        q=copy.deepcopy(self.inventory);q["all_code_and_file_paths"][0]["git_blob_sha"]="not-a-real-git-hash"
        with self.assertRaisesRegex(AssertionError,"UNVERIFIED_GIT_BLOB"):
            validate(q)
    def test_changed_overlap_rejected(self):
        q=copy.deepcopy(self.inventory);q["source_overlap"]["identical_sha"]+=1
        with self.assertRaisesRegex(AssertionError,"DUPLICATION_SHA"):
            validate(q)
    def test_truncated_tree_must_abort(self):
        q=copy.deepcopy(self.inventory);q["sources"][0]["tree_truncated"]=True
        with self.assertRaisesRegex(AssertionError,"GITHUB_TREE_WAS_TRUNCATED"):
            validate(q)
    def test_cannot_silently_change_frozen_c117_source(self):
        q=copy.deepcopy(self.inventory);q["sources"][0]["ref"]="main"
        with self.assertRaisesRegex(AssertionError,"C117_A181_SOURCE_REF_CHANGED"):
            validate(q)

if __name__=="__main__":unittest.main(verbosity=2)
