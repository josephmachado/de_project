from etl.bronze import customer, lineitem, nation, orders, region
from etl.silver import dim_customer, fct_lineitem, fct_orders
from etl.gold.obt import wide_lineitem, wide_orders
from etl.gold.pre_aggregated import customer_outreach_metrics


def create_customer_outreach_metrics():
    # create necessary bronze table
    customer_df = customer.create_dataset()
    lineitem_df = lineitem.create_dataset()
    nation_df = nation.create_dataset()
    orders_df = orders.create_dataset()
    region_df = region.create_dataset()

    # Create silver tables
    dim_customer_df = dim_customer.create_dataset(customer_df, nation_df, region_df)
    fct_lineitem_df = fct_lineitem.create_dataset(lineitem_df)
    fct_orders_df = fct_orders.create_dataset(orders_df)

    # Create gold obt tables
    wide_lineitem_df = wide_lineitem.create_dataset(fct_lineitem_df)
    wide_orders_df = wide_orders.create_dataset(fct_orders_df, dim_customer_df)

    # create gold pre-aggregated tables
    customer_outreach_metrics_df = customer_outreach_metrics.create_dataset(
        wide_lineitem_df, wide_orders_df
    )

    # validate data quality
    customer_outreach_metrics.validate_dataset(customer_outreach_metrics_df)
    return customer_outreach_metrics_df


if __name__ == "__main__":
    print(create_customer_outreach_metrics().limit(10))
