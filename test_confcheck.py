"""
conftest tests
"""

import json
import os

import pytest


@pytest.fixture
def prepare_secrets(request):
    """
    create secrets.py according to the marker and register cleanup function
    """
    marker = request.node.get_closest_marker("secrets_data")
    secrets_dict = marker.args[0]
    assert isinstance(secrets_dict, dict)
    with open("secrets.py", "w", encoding="utf-8") as fp:
        fp.write("secrets = ")
        fp.write(json.dumps(secrets_dict))

    def remove_secrets():
        os.remove("secrets.py")

    request.addfinalizer(remove_secrets)


@pytest.mark.secrets_data({"foo": 60})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_missing(prepare_secrets):
    """
    Test the case of missing name to check.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    class FakeBailException(Exception):
        """
        designated exception for overriding confchecks.bail()
        """

    def fake_bail(message):
        raise FakeBailException(message)

    confchecks.bail = fake_bail
    with pytest.raises(FakeBailException):
        confchecks.check_int("nonexistent")
