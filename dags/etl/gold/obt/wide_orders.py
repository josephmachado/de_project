def create_dataset(fct_orders, dim_customer):
    return fct_orders.join(dim_customer, on="customer_key", how="left")

