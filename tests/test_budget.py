import os

from leishgene.budget import check_budget


def _noise(path, size):
    path.write_bytes(os.urandom(size))  # incompressible, so gzip size ~ raw size


def test_no_violation_small(tmp_path):
    (tmp_path / "G1.json").write_text("[]")
    (tmp_path / "names.json").write_text("[]")
    assert check_budget(tmp_path) == []


def test_oversize_shard_reported(tmp_path):
    _noise(tmp_path / "G1.json", 2000)
    (tmp_path / "names.json").write_text("[]")
    messages = check_budget(tmp_path, max_shard_bytes=1000)
    assert len(messages) == 1 and "G1.json" in messages[0]


def test_oversize_names_reported(tmp_path):
    _noise(tmp_path / "names.json", 2000)
    messages = check_budget(tmp_path, max_names_bytes=1000)
    assert len(messages) == 1 and "names.json" in messages[0]


def test_compressible_data_measured_after_gzip(tmp_path):
    (tmp_path / "G1.json").write_text("a" * 100_000)  # 100 kB raw, a few hundred bytes gzipped
    assert check_budget(tmp_path, max_shard_bytes=10_000) == []
