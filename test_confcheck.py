import json
import os

import pytest


@pytest.fixture
def prepare_secrets(request):
    marker = request.node.get_closest_marker("secrets_data")
    secrets_dict = marker.args[0]
    assert type(secrets_dict) == dict
    with open("secrets.py", "w") as fp:
        fp.write("secrets = ")
        fp.write(json.dumps(secrets_dict))

    def remove_secrets():
        os.remove("secrets.py")

    request.addfinalizer(remove_secrets)


@pytest.mark.secrets_data({"foo": 60})
def test_check_int_missing(prepare_secrets):
    """
    Test the case of missing name to check.
    """
    import confchecks

    class FakeBailException(Exception):
        pass

    def fake_bail(message):
        raise FakeBailException(message)

    confchecks.bail = fake_bail
    with pytest.raises(FakeBailException):
        confchecks.check_int("nonexistent")
