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


class FakeBailException(Exception):
    """
    designated exception for overriding confchecks.bail()
    """


@pytest.fixture
def fake_bail():
    """
    override confchecks.bail() with a function that raises FakeBailException
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    # pylint: disable=redefined-outer-name
    def fake_bail(message):
        raise FakeBailException(message)

    confchecks.bail = fake_bail


@pytest.mark.secrets_data({"foo": 60})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_missing(prepare_secrets, fake_bail):
    """
    Test the case of missing name to check.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    with pytest.raises(FakeBailException):
        confchecks.check_int("nonexistent")


@pytest.mark.secrets_data({"foo": 60})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_missing_optional(prepare_secrets):
    """
    Test the case of missing optional name.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    confchecks.check_int("nonexistent", mandatory=False)


@pytest.mark.secrets_data({"foo": "bar"})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_invalid_value_type(prepare_secrets, fake_bail):
    """
    Test the case of invalid value type.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    with pytest.raises(FakeBailException):
        confchecks.check_int("foo")


@pytest.mark.secrets_data({"foo": 42})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_min_unspecified_positive(prepare_secrets):
    """
    Test the case of unspecified min.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    confchecks.check_int("foo", max_val=60)


@pytest.mark.secrets_data({"foo": 42})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_max_unspecified_positive(prepare_secrets):
    """
    Test the case of unspecified max.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    confchecks.check_int("foo", min_val=60)


@pytest.mark.secrets_data({"foo": 42})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_max_negative(prepare_secrets, fake_bail):
    """
    Test the case of value higher than max.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    with pytest.raises(FakeBailException):
        confchecks.check_int("foo", max_val=10)


@pytest.mark.secrets_data({"foo": 42})
# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_min_negative(prepare_secrets, delete_confcheck, fake_bail):
    """
    Test the case of value lower than min.
    """
    # pylint: disable=import-outside-toplevel
    import confchecks

    with pytest.raises(FakeBailException):
        confchecks.check_int("foo", min_val=50)
