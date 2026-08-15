import structextract


def test_version_exists():
    assert hasattr(structextract, "__version__")
    assert isinstance(structextract.__version__, str)
