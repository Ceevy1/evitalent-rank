import pytest

from evitalent.extraction.mock_extractor import MockExtractor


@pytest.fixture()
def candidates():
    return MockExtractor().load_all()

