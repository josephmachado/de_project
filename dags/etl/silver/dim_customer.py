def create_dataset(cleaned_customer_df, cleaned_nation_df, cleaned_region_df):
    return cleaned_customer_df\
        .join(cleaned_nation_df, on="nationkey", how="left", suffix="_nation")\
        .join(cleaned_region_df, on="regionkey", how="left", suffix="_region")\
        .rename({
            "name_nation": "nation_name",
            "name_region": "region_name",
            "comment_nation": "nation_comment",
            "comment_region": "region_comment"
        })
