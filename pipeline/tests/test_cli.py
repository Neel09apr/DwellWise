from dwellwise_pipeline.__main__ import parse_args


def test_run_with_no_sources_means_all_of_them_in_order():
    assert parse_args(["run", "--dry-run"]).sources == ["counties", "settlements"]


def test_run_keeps_the_sources_it_is_given():
    assert parse_args(["run", "settlements"]).sources == ["settlements"]
