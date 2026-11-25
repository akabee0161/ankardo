import pytest


def test_real_modal_is_refused():
    from artgen import modal_app

    with pytest.raises(AssertionError, match="本物の Modal"):
        modal_app.run([], "c", {})
    with pytest.raises(AssertionError, match="本物の Modal"):
        modal_app.run_matte({})
