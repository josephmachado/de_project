import polars as pl

def create_dataset(wide_lineitem, wide_orders):
    order_lineitem_metrics = wide_lineitem.group_by(pl.col("order_key")).agg(pl.col("linenumber").count().alias("num_lineitems"))
    return wide_orders\
        .join(order_lineitem_metrics, on="order_key", how="left")\
        .group_by(
            pl.col("customer_key"), 
            pl.col("name").alias("customer_name"))\
        .agg(
            pl.min("totalprice").alias("min_order_value"),
            pl.max("totalprice").alias("max_order_value"),
            pl.mean("totalprice").alias("avg_order_value"),
            pl.mean("num_lineitems").alias("avg_num_items_per_order"),
        )

