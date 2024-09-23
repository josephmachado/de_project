import pytest
import polars as pl
from polars.testing import assert_frame_equal
from de_project.etl.silver import dim_customer


# Sample data for testing
@pytest.fixture
def cleaned_customer_df():
    return pl.DataFrame(
        {
            "custkey": [1, 2],
            "name": ["Customer1", "Customer2"],
            "nationkey": [101, 102],
            "regionkey": [201, 202],
        }
    )


@pytest.fixture
def cleaned_nation_df():
    return pl.DataFrame(
        {
            "nationkey": [101, 102],
            "name_nation": ["Nation1", "Nation2"],
            "comment_nation": ["Comment1", "Comment2"],
        }
    )


@pytest.fixture
def cleaned_region_df():
    return pl.DataFrame(
        {
            "regionkey": [201, 202],
            "name_region": ["Region1", "Region2"],
            "comment_region": ["Comment3", "Comment4"],
        }
    )


# The function to test
def test_dim_customer_create_dataset(
    cleaned_customer_df, cleaned_nation_df, cleaned_region_df
):
    result_df = dim_customer.create_dataset(
        cleaned_customer_df, cleaned_nation_df, cleaned_region_df
    )

    expected_df = pl.DataFrame(
        {
            "custkey": [1, 2],
            "name": ["Customer1", "Customer2"],
            "nationkey": [101, 102],
            "regionkey": [201, 202],
            "nation_name": ["Nation1", "Nation2"],
            "nation_comment": ["Comment1", "Comment2"],
            "region_name": ["Region1", "Region2"],
            "region_comment": ["Comment3", "Comment4"],
        }
    )

    assert_frame_equal(result_df, expected_df)
