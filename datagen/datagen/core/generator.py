"""
Core data generator.
Orchestrates generation of all 25 tables in FK-safe order,
yielding batches of dicts to the sink.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator, Any

from mimesis import Person, Address, Internet, Finance, Text
from mimesis.locales import Locale

from datagen.config import (
    ScaleConfig,
    DISTRIBUTIONS,
    CATALOG,
    CAUSAL_DELTAS,
    CUSTOMER_STATUSES,
    ORDER_STATUSES,
    PAYMENT_STATUSES,
    SHIPMENT_STATUSES,
)
from datagen.core.distributions import Distributions
from datagen.core.schema import (
    Warehouse,
    ProductCategory,
    Product,
    ProductVariant,
    ProductAttribute,
    Inventory,
    Advertiser,
    Campaign,
    AdGroup,
    AdCreative,
    Keyword,
    AdGroupKeyword,
    Customer,
    CustomerAddress,
    Device,
    Session,
    Order,
    OrderLine,
    Payment,
    Shipment,
    ShipmentLine,
    Return,
    ReturnLine,
    AdImpression,
    AdClick,
    AdConversion,
    row_to_dict,
)

Batch = list[dict[str, Any]]


class Generator:
    def __init__(self, config: ScaleConfig):
        self.config = config
        self.dist = Distributions(config.seed)

        # Mimesis providers
        self.person = Person(Locale.EN)
        self.address = Address(Locale.EN)
        self.internet = Internet()
        self.finance = Finance()
        self.text = Text(Locale.EN)

        # Time range as UTC-aware datetimes
        self.start_dt = datetime(
            config.start.year, config.start.month, config.start.day, tzinfo=timezone.utc
        )
        self.end_dt = datetime(
            config.end.year,
            config.end.month,
            config.end.day,
            23,
            59,
            59,
            tzinfo=timezone.utc,
        )
        self.range_seconds = int((self.end_dt - self.start_dt).total_seconds())

        # In-memory ID/timestamp stores for FK references and causal ordering
        self._warehouse_ids: list[str] = []
        self._category_ids: list[str] = []
        self._product_ids: list[str] = []
        self._variant_ids: list[str] = []
        self._variant_prices: dict[str, float] = {}  # variant_id → price
        self._advertiser_ids: list[str] = []
        self._campaign_ids: list[str] = []
        self._ad_group_ids: list[str] = []
        self._creative_ids: list[str] = []
        self._keyword_ids: list[str] = []
        self._customer_ids: list[str] = []
        self._customer_created: dict[str, datetime] = {}  # customer_id → created_at dt
        self._customer_addresses: dict[
            str, list[str]
        ] = {}  # customer_id → [address_id]
        self._customer_devices: dict[str, list[str]] = {}  # customer_id → [device_id]
        self._device_created: dict[str, datetime] = {}  # device_id → created_at dt
        self._customer_orders: dict[str, list[dict]] = {}  # customer_id → [order dict]
        self._sessions: list[dict] = []
        self._impressions: list[dict] = []
        self._clicks: list[dict] = []

    # -----------------------------------------------------------------------
    # Timestamp helpers
    # -----------------------------------------------------------------------

    def _uid(self) -> str:
        return str(uuid.uuid4())

    def _random_ts(
        self, after: datetime | None = None, before: datetime | None = None
    ) -> datetime:
        """Return a random UTC datetime within [after, before]."""
        lo = after or self.start_dt
        hi = before or self.end_dt
        if lo >= hi:
            return lo
        delta = int((hi - lo).total_seconds())
        offset = self.dist.randint(0, max(delta - 1, 0))
        return lo + timedelta(seconds=offset)

    def _ts_str(self, dt: datetime) -> str:
        return dt.isoformat()

    def _add_seconds(self, dt: datetime, lo: int, hi: int) -> datetime:
        return dt + timedelta(seconds=self.dist.randint(lo, hi))

    def _add_minutes(self, dt: datetime, lo: int, hi: int) -> datetime:
        return dt + timedelta(minutes=self.dist.randint(lo, hi))

    def _add_hours(self, dt: datetime, lo: int, hi: int) -> datetime:
        return dt + timedelta(hours=self.dist.randint(lo, hi))

    def _add_days(self, dt: datetime, lo: int, hi: int) -> datetime:
        return dt + timedelta(days=self.dist.randint(lo, hi))

    def _clamp(self, dt: datetime) -> datetime:
        """Ensure timestamp never exceeds end_dt."""
        return min(dt, self.end_dt)

    # -----------------------------------------------------------------------
    # Batch yielding helper
    # -----------------------------------------------------------------------

    def _batched(
        self, rows: list[dict], batch_size: int
    ) -> Generator[Batch, None, None]:
        for i in range(0, len(rows), batch_size):
            yield rows[i : i + batch_size]

    # -----------------------------------------------------------------------
    # Fixed catalog generators
    # -----------------------------------------------------------------------

    def generate_warehouses(self) -> Generator[Batch, None, None]:
        rows = []
        for _ in range(CATALOG["num_warehouses"]):
            wid = self._uid()
            ts = self._ts_str(self._random_ts())
            self._warehouse_ids.append(wid)
            rows.append(
                row_to_dict(
                    Warehouse(
                        warehouse_id=wid,
                        name=f"{self.address.city()} Fulfillment Center",
                        country=self.dist.choice(["US", "GB", "DE", "CA", "AU"]),
                        city=self.address.city(),
                        is_active=True,
                        timezone=self.dist.choice(
                            [
                                "America/New_York",
                                "America/Chicago",
                                "America/Los_Angeles",
                                "Europe/London",
                                "Europe/Berlin",
                            ]
                        ),
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_product_categories(self) -> Generator[Batch, None, None]:
        rows = []
        slugs: set[str] = set()

        top_level_count = CATALOG["num_categories"] // 5
        for _ in range(top_level_count):
            cid = self._uid()
            name = self.text.word().capitalize()
            slug = self._unique_slug(name, slugs)
            ts = self._ts_str(self._random_ts())
            self._category_ids.append(cid)
            rows.append(
                row_to_dict(
                    ProductCategory(
                        category_id=cid,
                        parent_id=None,
                        name=name,
                        slug=slug,
                        depth=0,
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )

        remaining = CATALOG["num_categories"] - top_level_count
        for _ in range(remaining):
            cid = self._uid()
            name = self.text.word().capitalize()
            slug = self._unique_slug(name, slugs)
            ts = self._ts_str(self._random_ts())
            parent = self.dist.choice(self._category_ids[:top_level_count])
            self._category_ids.append(cid)
            rows.append(
                row_to_dict(
                    ProductCategory(
                        category_id=cid,
                        parent_id=parent,
                        name=name,
                        slug=slug,
                        depth=1,
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def _unique_slug(self, name: str, seen: set) -> str:
        base = name.lower().replace(" ", "-")
        slug = base
        i = 1
        while slug in seen:
            slug = f"{base}-{i}"
            i += 1
        seen.add(slug)
        return slug

    def generate_products(self) -> Generator[Batch, None, None]:
        rows = []
        for _ in range(CATALOG["num_products"]):
            pid = self._uid()
            ts = self._ts_str(self._random_ts())
            self._product_ids.append(pid)
            rows.append(
                row_to_dict(
                    Product(
                        product_id=pid,
                        category_id=self.dist.choice(self._category_ids),
                        name=" ".join(self.text.words(quantity=3)).title(),
                        description=self.text.sentence(),
                        brand=self.person.last_name(),
                        base_price=self.dist.random_float(5.0, 500.0),
                        status="active",
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_product_variants(self) -> Generator[Batch, None, None]:
        rows = []
        skus: set[str] = set()
        sizes = ["XS", "S", "M", "L", "XL", "XXL", "One Size"]
        colors = [
            "Black",
            "White",
            "Red",
            "Blue",
            "Green",
            "Yellow",
            "Navy",
            "Grey",
            "Pink",
            "Purple",
        ]

        for _ in range(CATALOG["num_variants"]):
            vid = self._uid()
            ts = self._ts_str(self._random_ts())
            pid = self.dist.choice(self._product_ids)
            price = self.dist.random_float(5.0, 500.0)
            sku = self._unique_sku(skus)
            self._variant_ids.append(vid)
            self._variant_prices[vid] = price
            rows.append(
                row_to_dict(
                    ProductVariant(
                        variant_id=vid,
                        product_id=pid,
                        sku=sku,
                        size=self.dist.choice(sizes),
                        color=self.dist.choice(colors),
                        price_override=price if self.dist.bernoulli(0.3) else None,
                        weight_kg=self.dist.random_float(0.1, 10.0, 3),
                        is_active=True,
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def _unique_sku(self, seen: set) -> str:
        while True:
            sku = f"SKU-{self.dist.randint(10000, 99999)}-{self.dist.randint(100, 999)}"
            if sku not in seen:
                seen.add(sku)
                return sku

    def generate_product_attributes(self) -> Generator[Batch, None, None]:
        rows = []
        attr_keys = ["material", "fit", "care", "origin", "certification"]
        for vid in self._variant_ids:
            ts = self._ts_str(self._random_ts())
            num_attrs = self.dist.randint(1, 3)
            for order, key in enumerate(self.dist.choices(attr_keys, num_attrs)):
                rows.append(
                    row_to_dict(
                        ProductAttribute(
                            attribute_id=self._uid(),
                            variant_id=vid,
                            attr_key=key,
                            attr_value=self.text.word(),
                            display_order=order,
                            created_at=ts,
                            updated_at=ts,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    def generate_inventory(self) -> Generator[Batch, None, None]:
        rows = []
        for vid in self._variant_ids:
            for wid in self._warehouse_ids:
                ts = self._ts_str(self._random_ts())
                rows.append(
                    row_to_dict(
                        Inventory(
                            inventory_id=self._uid(),
                            variant_id=vid,
                            warehouse_id=wid,
                            qty_on_hand=self.dist.randint(0, 500),
                            qty_reserved=self.dist.randint(0, 50),
                            created_at=ts,
                            updated_at=ts,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    def generate_advertisers(self) -> Generator[Batch, None, None]:
        rows = []
        for _ in range(CATALOG["num_advertisers"]):
            aid = self._uid()
            ts = self._ts_str(self._random_ts())
            self._advertiser_ids.append(aid)
            rows.append(
                row_to_dict(
                    Advertiser(
                        advertiser_id=aid,
                        name=f"{self.person.last_name()} {self.dist.choice(['Inc', 'LLC', 'Co', 'Corp'])}",
                        billing_email=self.person.email(),
                        status="active",
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_campaigns(self) -> Generator[Batch, None, None]:
        rows = []
        objectives = ["awareness", "consideration", "conversion", "retargeting"]
        for _ in range(CATALOG["num_campaigns"]):
            cid = self._uid()
            ts = self._ts_str(self._random_ts())
            budget = self.dist.random_float(1000.0, 100000.0)
            created_dt = self._random_ts()
            # campaign start_date must be >= created_at date
            start_dt = self._random_ts(after=created_dt)
            # end_date must be >= start_date
            end_dt = (
                self._random_ts(after=start_dt) if start_dt < self.end_dt else start_dt
            )
            self._campaign_ids.append(cid)
            rows.append(
                row_to_dict(
                    Campaign(
                        campaign_id=cid,
                        advertiser_id=self.dist.choice(self._advertiser_ids),
                        name=" ".join(self.text.words(quantity=4)).title(),
                        objective=self.dist.choice(objectives),
                        budget_total=budget,
                        budget_daily=round(budget / 30, 2),
                        start_date=str(start_dt.date()),
                        end_date=str(end_dt.date()),
                        created_at=self._ts_str(created_dt),
                        updated_at=self._ts_str(created_dt),
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_ad_groups(self) -> Generator[Batch, None, None]:
        rows = []
        targeting = ["keyword", "audience", "retargeting", "contextual"]
        strategies = ["manual_cpc", "target_cpa", "maximize_clicks", "target_roas"]
        for _ in range(CATALOG["num_ad_groups"]):
            gid = self._uid()
            ts = self._ts_str(self._random_ts())
            self._ad_group_ids.append(gid)
            rows.append(
                row_to_dict(
                    AdGroup(
                        ad_group_id=gid,
                        campaign_id=self.dist.choice(self._campaign_ids),
                        name=" ".join(self.text.words(quantity=3)).title(),
                        targeting_type=self.dist.choice(targeting),
                        bid_strategy=self.dist.choice(strategies),
                        max_cpc=self.dist.random_float(0.10, 10.0, 4),
                        status="active",
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_ad_creatives(self) -> Generator[Batch, None, None]:
        rows = []
        formats = ["banner", "video", "carousel", "native", "interstitial"]
        for _ in range(CATALOG["num_creatives"]):
            cid = self._uid()
            ts = self._ts_str(self._random_ts())
            self._creative_ids.append(cid)
            rows.append(
                row_to_dict(
                    AdCreative(
                        creative_id=cid,
                        ad_group_id=self.dist.choice(self._ad_group_ids),
                        format=self.dist.choice(formats),
                        headline=self.text.sentence()[:80],
                        image_url=f"https://cdn.example.com/creatives/{self._uid()}.jpg",
                        destination_url=f"https://shop.example.com/p/{self._uid()}",
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_keywords(self) -> Generator[Batch, None, None]:
        rows = []
        match_types = ["exact", "phrase", "broad"]
        for _ in range(CATALOG["num_keywords"]):
            kid = self._uid()
            ts = self._ts_str(self._random_ts())
            self._keyword_ids.append(kid)
            rows.append(
                row_to_dict(
                    Keyword(
                        keyword_id=kid,
                        term=" ".join(
                            self.text.words(quantity=self.dist.randint(1, 3))
                        ),
                        match_type=self.dist.choice(match_types),
                        language="en",
                        created_at=ts,
                        updated_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_ad_group_keywords(self) -> Generator[Batch, None, None]:
        rows = []
        seen: set[tuple] = set()
        for gid in self._ad_group_ids:
            for kid in self.dist.choices(
                self._keyword_ids, CATALOG["keywords_per_group"]
            ):
                pair = (gid, kid)
                if pair in seen:
                    continue
                seen.add(pair)
                ts = self._ts_str(self._random_ts())
                rows.append(
                    row_to_dict(
                        AdGroupKeyword(
                            ad_group_id=gid,
                            keyword_id=kid,
                            bid_override=self.dist.random_float(0.1, 5.0, 4)
                            if self.dist.bernoulli(0.3)
                            else None,
                            is_negative=self.dist.bernoulli(0.1),
                            created_at=ts,
                            updated_at=ts,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    # -----------------------------------------------------------------------
    # Customer-driven generators
    # -----------------------------------------------------------------------

    def generate_customers(self) -> Generator[Batch, None, None]:
        rows = []
        for _ in range(self.config.customers):
            cid = self._uid()
            created_dt = self._random_ts()
            status = self.dist.choice(CUSTOMER_STATUSES)

            # Non-active customers have updated_at > created_at (status changed)
            if status != "active":
                updated_dt = self._clamp(
                    self._add_days(
                        created_dt,
                        CAUSAL_DELTAS["customer_status_change_min_d"],
                        CAUSAL_DELTAS["customer_status_change_max_d"],
                    )
                )
            else:
                updated_dt = created_dt

            self._customer_ids.append(cid)
            self._customer_created[cid] = created_dt
            self._customer_addresses[cid] = []
            self._customer_devices[cid] = []
            self._customer_orders[cid] = []

            rows.append(
                row_to_dict(
                    Customer(
                        customer_id=cid,
                        email=self.person.email(unique=True),
                        full_name=self.person.full_name(),
                        phone=self.person.telephone(),
                        status=status,
                        created_at=self._ts_str(created_dt),
                        updated_at=self._ts_str(updated_dt),
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)

    def generate_customer_addresses(self) -> Generator[Batch, None, None]:
        rows = []
        for cid in self._customer_ids:
            customer_dt = self._customer_created[cid]
            n = self.dist.sample_count(DISTRIBUTIONS["addresses_per_customer"])
            n = max(n, 1)  # always at least one address

            # Generate addresses in chronological order so we can track
            # which was default at each point in time
            addr_created_dts = sorted(
                [self._random_ts(after=customer_dt) for _ in range(n)]
            )

            for i, addr_dt in enumerate(addr_created_dts):
                aid = self._uid()
                is_last = i == n - 1
                # The most recently added address is the current default.
                # All previous addresses had is_default flipped to False
                # when the newer one was added — updated_at reflects that.
                is_default = is_last

                if not is_last:
                    # This address was the default until the next one was added
                    next_addr_dt = addr_created_dts[i + 1]
                    updated_dt = next_addr_dt
                else:
                    updated_dt = addr_dt

                self._customer_addresses[cid].append(aid)
                rows.append(
                    row_to_dict(
                        CustomerAddress(
                            address_id=aid,
                            customer_id=cid,
                            line1=self.address.address(),
                            city=self.address.city(),
                            state=self.address.state(),
                            country="US",
                            is_default=is_default,
                            created_at=self._ts_str(addr_dt),
                            updated_at=self._ts_str(updated_dt),
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    def generate_devices(self) -> Generator[Batch, None, None]:
        rows = []
        types = ["mobile", "desktop", "tablet"]
        oses = ["iOS", "Android", "Windows", "macOS", "Linux"]
        for cid in self._customer_ids:
            customer_dt = self._customer_created[cid]
            n = self.dist.sample_count(DISTRIBUTIONS["devices_per_customer"])
            for _ in range(max(n, 1)):
                did = self._uid()
                created_dt = self._random_ts(after=customer_dt)
                ts = self._ts_str(created_dt)
                self._customer_devices[cid].append(did)
                self._device_created[did] = created_dt
                rows.append(
                    row_to_dict(
                        Device(
                            device_id=did,
                            customer_id=cid,
                            type=self.dist.choice(types),
                            os=self.dist.choice(oses),
                            user_agent=self.internet.user_agent(),
                            created_at=ts,
                            updated_at=ts,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    def generate_sessions(self) -> Generator[Batch, None, None]:
        rows = []
        channels = [
            "organic",
            "paid_search",
            "paid_social",
            "email",
            "direct",
            "referral",
            "affiliate",
        ]
        for cid in self._customer_ids:
            devices = self._customer_devices[cid]
            customer_dt = self._customer_created[cid]
            if not devices:
                continue
            n = self.dist.sample_count(DISTRIBUTIONS["sessions_per_customer"])
            for _ in range(max(n, 1)):
                device_id = self.dist.choice(devices)
                device_dt = self._device_created[device_id]
                # Session must start after both customer and device were created
                earliest = max(customer_dt, device_dt)
                started_dt = self._random_ts(after=earliest)
                duration_m = self.dist.randint(
                    CAUSAL_DELTAS["session_duration_min_m"],
                    CAUSAL_DELTAS["session_duration_max_m"],
                )
                ended_dt = self._clamp(started_dt + timedelta(minutes=duration_m))
                session = row_to_dict(
                    Session(
                        session_id=self._uid(),
                        customer_id=cid,
                        device_id=device_id,
                        channel=self.dist.choice(channels),
                        started_at=self._ts_str(started_dt),
                        ended_at=self._ts_str(ended_dt),
                        created_at=self._ts_str(started_dt),
                        updated_at=self._ts_str(
                            ended_dt
                        ),  # last updated when session closed
                    )
                )
                self._sessions.append(session)
                rows.append(session)
        yield from self._batched(rows, self.config.batch_size)

    # -----------------------------------------------------------------------
    # Orders + order_lines — combined to fix total_amount
    # -----------------------------------------------------------------------

    def generate_orders_and_lines(self) -> tuple:
        """
        Generate orders and order_lines together so total_amount is
        calculated from real line items before the order row is written.
        Returns (order_batch_generator, line_batch_generator).
        """
        order_rows = []
        line_rows = []

        for cid in self._customer_ids:
            addrs = self._customer_addresses[cid]
            customer_dt = self._customer_created[cid]
            if not addrs:
                continue
            n = self.dist.sample_count(DISTRIBUTIONS["orders_per_customer"])
            for _ in range(n):
                oid = self._uid()
                placed_dt = self._random_ts(after=customer_dt)
                ship_addr = self.dist.choice(addrs)
                bill_addr = self.dist.choice(addrs)
                status = self.dist.choice(ORDER_STATUSES)

                # updated_at > created_at for any non-pending order
                if status != "pending":
                    updated_dt = self._clamp(
                        self._add_hours(
                            placed_dt,
                            CAUSAL_DELTAS["order_status_change_min_h"],
                            CAUSAL_DELTAS["order_status_change_max_h"],
                        )
                    )
                else:
                    updated_dt = placed_dt

                # Generate lines first to compute total_amount
                num_lines = self.dist.sample_count(DISTRIBUTIONS["lines_per_order"])
                total = 0.0
                for _ in range(max(num_lines, 1)):
                    vid = self.dist.choice(self._variant_ids)
                    qty = self.dist.randint(1, 5)
                    price = self._variant_prices.get(
                        vid, self.dist.random_float(5.0, 200.0)
                    )
                    discount = (
                        round(price * self.dist.uniform(0, 0.2), 2)
                        if self.dist.bernoulli(0.2)
                        else 0.0
                    )
                    line_tot = round((price - discount) * qty, 2)
                    total += line_tot
                    line_rows.append(
                        row_to_dict(
                            OrderLine(
                                order_line_id=self._uid(),
                                order_id=oid,
                                variant_id=vid,
                                quantity=qty,
                                unit_price=price,
                                discount_amt=discount,
                                line_total=line_tot,
                                created_at=self._ts_str(placed_dt),
                                updated_at=self._ts_str(placed_dt),
                            )
                        )
                    )

                order = row_to_dict(
                    Order(
                        order_id=oid,
                        customer_id=cid,
                        shipping_addr_id=ship_addr,
                        billing_addr_id=bill_addr,
                        status=status,
                        total_amount=round(total, 2),
                        placed_at=self._ts_str(placed_dt),
                        created_at=self._ts_str(placed_dt),
                        updated_at=self._ts_str(updated_dt),
                    )
                )
                order["_placed_dt"] = placed_dt  # internal, stripped before sink
                self._customer_orders[cid].append(order)
                order_rows.append(order)

        def _order_batches():
            yield from self._batched(
                [
                    {k: v for k, v in r.items() if not k.startswith("_")}
                    for r in order_rows
                ],
                self.config.batch_size,
            )

        def _line_batches():
            yield from self._batched(line_rows, self.config.batch_size)

        return _order_batches(), _line_batches()

    # -----------------------------------------------------------------------
    # Fulfillment
    # -----------------------------------------------------------------------

    def generate_shipments(self) -> Generator[Batch, None, None]:
        rows = []
        carriers = ["FedEx", "UPS", "USPS", "DHL", "OnTrac"]
        for orders in self._customer_orders.values():
            for order in orders:
                placed_dt = order.get("_placed_dt") or datetime.fromisoformat(
                    order["placed_at"]
                )
                shipped_dt = self._clamp(
                    self._add_hours(
                        placed_dt,
                        CAUSAL_DELTAS["shipment_delay_min_h"],
                        CAUSAL_DELTAS["shipment_delay_max_h"],
                    )
                )
                status = self.dist.choice(SHIPMENT_STATUSES)

                # updated_at > created_at for any non-processing shipment
                # no clamping — status update can legitimately happen after window end
                if status != "processing":
                    updated_dt = shipped_dt + timedelta(
                        hours=self.dist.randint(
                            CAUSAL_DELTAS["shipment_status_change_min_h"],
                            CAUSAL_DELTAS["shipment_status_change_max_h"],
                        )
                    )
                else:
                    updated_dt = shipped_dt

                rows.append(
                    row_to_dict(
                        Shipment(
                            shipment_id=self._uid(),
                            order_id=order["order_id"],
                            warehouse_id=self.dist.choice(self._warehouse_ids),
                            carrier=self.dist.choice(carriers),
                            tracking_no=f"TRK{self.dist.randint(1000000000, 9999999999)}",
                            status=status,
                            shipped_at=self._ts_str(shipped_dt),
                            created_at=self._ts_str(shipped_dt),
                            updated_at=self._ts_str(updated_dt),
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    def generate_shipment_lines(
        self, shipments: list[dict], order_lines: list[dict]
    ) -> Generator[Batch, None, None]:
        ol_by_order: dict[str, list[dict]] = {}
        for ol in order_lines:
            ol_by_order.setdefault(ol["order_id"], []).append(ol)

        rows = []
        for ship in shipments:
            shipped_dt = datetime.fromisoformat(ship["shipped_at"])
            delivered_dt = self._clamp(
                self._add_days(
                    shipped_dt,
                    CAUSAL_DELTAS["delivery_delay_min_d"],
                    CAUSAL_DELTAS["delivery_delay_max_d"],
                )
            )
            ols = ol_by_order.get(ship["order_id"], [])
            for ol in ols:
                ts = self._ts_str(shipped_dt)
                rows.append(
                    row_to_dict(
                        ShipmentLine(
                            shipment_line_id=self._uid(),
                            shipment_id=ship["shipment_id"],
                            order_line_id=ol["order_line_id"],
                            qty_shipped=ol["quantity"],
                            delivered_at=self._ts_str(delivered_dt),
                            created_at=ts,
                            updated_at=ts,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    # -----------------------------------------------------------------------
    # Returns
    # -----------------------------------------------------------------------

    def generate_returns(self, shipments: list[dict]) -> Generator[Batch, None, None]:
        rows = []
        reasons = [
            "damaged",
            "wrong_item",
            "not_as_described",
            "changed_mind",
            "late_delivery",
        ]
        terminal_statuses = ["refunded", "rejected"]
        open_statuses = ["requested", "approved", "received"]
        ship_by_order = {s["order_id"]: s for s in shipments}

        for orders in self._customer_orders.values():
            for order in orders:
                oid = order["order_id"]
                ship = ship_by_order.get(oid)
                if not ship:
                    continue
                if not self.dist.bernoulli(
                    DISTRIBUTIONS["return_rate"]["a"]
                    / (
                        DISTRIBUTIONS["return_rate"]["a"]
                        + DISTRIBUTIONS["return_rate"]["b"]
                    )
                ):
                    continue
                shipped_dt = datetime.fromisoformat(ship["shipped_at"])
                delivered_dt = shipped_dt + timedelta(days=self.dist.randint(2, 7))
                requested_dt = self._clamp(
                    self._add_days(
                        delivered_dt,
                        CAUSAL_DELTAS["return_delay_min_d"],
                        CAUSAL_DELTAS["return_delay_max_d"],
                    )
                )

                # 60% terminal (refunded/rejected), 40% still in-progress
                if self.dist.bernoulli(0.6):
                    status = self.dist.choice(terminal_statuses)
                    # resolved_at always > requested_at — no clamping
                    resolved_dt = requested_dt + timedelta(
                        days=self.dist.randint(
                            CAUSAL_DELTAS["return_resolution_min_d"],
                            CAUSAL_DELTAS["return_resolution_max_d"],
                        )
                    )
                    resolved_at = self._ts_str(resolved_dt)
                    updated_at = resolved_at  # last updated when resolved
                else:
                    status = self.dist.choice(open_statuses)
                    resolved_at = None
                    updated_at = self._ts_str(requested_dt)

                rows.append(
                    row_to_dict(
                        Return(
                            return_id=self._uid(),
                            order_id=oid,
                            reason=self.dist.choice(reasons),
                            status=status,
                            requested_at=self._ts_str(requested_dt),
                            resolved_at=resolved_at,
                            created_at=self._ts_str(requested_dt),
                            updated_at=updated_at,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    def generate_return_lines(
        self, returns: list[dict], order_lines: list[dict]
    ) -> Generator[Batch, None, None]:
        ol_by_order: dict[str, list[dict]] = {}
        for ol in order_lines:
            ol_by_order.setdefault(ol["order_id"], []).append(ol)

        rows = []
        for ret in returns:
            ts = ret["created_at"]
            ols = ol_by_order.get(ret["order_id"], [])
            if not ols:
                continue
            n = self.dist.sample_count(DISTRIBUTIONS["lines_per_return"])
            for ol in ols[: max(n, 1)]:
                qty = self.dist.randint(1, ol["quantity"])
                refund = round(ol["unit_price"] * qty, 2)
                rows.append(
                    row_to_dict(
                        ReturnLine(
                            return_line_id=self._uid(),
                            return_id=ret["return_id"],
                            order_line_id=ol["order_line_id"],
                            qty_returned=qty,
                            refund_amount=refund,
                            created_at=ts,
                            updated_at=ts,
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    # -----------------------------------------------------------------------
    # Payments — generated after returns so refunded status can be informed
    # -----------------------------------------------------------------------

    def generate_payments(self, returns: list[dict]) -> Generator[Batch, None, None]:
        rows = []
        methods = ["credit_card", "debit_card", "paypal", "apple_pay", "bank_transfer"]

        # Build set of order_ids that have a return, for refunded logic
        returned_order_ids = {r["order_id"] for r in returns}

        for orders in self._customer_orders.values():
            for order in orders:
                placed_dt = order.get("_placed_dt") or datetime.fromisoformat(
                    order["placed_at"]
                )
                created_dt = self._clamp(
                    self._add_seconds(
                        placed_dt,
                        CAUSAL_DELTAS["payment_delay_min_s"],
                        CAUSAL_DELTAS["payment_delay_max_s"],
                    )
                )

                # Determine payment status
                # refunded only if order has a return (90% chance) or randomly (10%)
                oid = order["order_id"]
                if oid in returned_order_ids and self.dist.bernoulli(0.9):
                    status = "refunded"
                else:
                    status = self.dist.choice(
                        ["pending", "captured", "captured", "failed"]
                    )

                # updated_at > created_at for non-pending payments
                if status != "pending":
                    updated_dt = self._clamp(
                        self._add_minutes(
                            created_dt,
                            CAUSAL_DELTAS["payment_status_change_min_m"],
                            CAUSAL_DELTAS["payment_status_change_max_m"],
                        )
                    )
                else:
                    updated_dt = created_dt

                rows.append(
                    row_to_dict(
                        Payment(
                            payment_id=self._uid(),
                            order_id=oid,
                            method=self.dist.choice(methods),
                            amount=order.get("total_amount", 0.0),
                            status=status,
                            provider_ref=f"REF-{self._uid()[:8].upper()}",
                            paid_at=self._ts_str(created_dt),
                            created_at=self._ts_str(created_dt),
                            updated_at=self._ts_str(updated_dt),
                        )
                    )
                )
        yield from self._batched(rows, self.config.batch_size)

    # -----------------------------------------------------------------------
    # Ad event generators
    # -----------------------------------------------------------------------

    def generate_ad_impressions(self) -> Generator[Batch, None, None]:
        rows = []
        placements = [
            "feed",
            "sidebar",
            "search_top",
            "search_bottom",
            "story",
            "banner",
            "interstitial",
        ]
        for session in self._sessions:
            n = self.dist.sample_count(DISTRIBUTIONS["impressions_per_session"])
            if n == 0:
                continue
            session_start = datetime.fromisoformat(session["started_at"])
            session_end = datetime.fromisoformat(session["ended_at"])
            for _ in range(n):
                iid = self._uid()
                impressed = self._random_ts(session_start, session_end)
                ts = self._ts_str(impressed)
                impression = row_to_dict(
                    AdImpression(
                        impression_id=iid,
                        creative_id=self.dist.choice(self._creative_ids),
                        session_id=session["session_id"],
                        customer_id=session["customer_id"],
                        placement=self.dist.choice(placements),
                        cost=self.dist.random_float(0.001, 0.05, 6),
                        impressed_at=ts,
                        created_at=ts,
                    )
                )
                impression["_impressed_dt"] = impressed
                self._impressions.append(impression)
                rows.append(impression)

        yield from self._batched(
            [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
            self.config.batch_size,
        )

    def generate_ad_clicks(self) -> Generator[Batch, None, None]:
        rows = []
        ctr = self.dist.sample(DISTRIBUTIONS["ctr"])
        for impression in self._impressions:
            if not self.dist.bernoulli(ctr):
                continue
            impressed_dt = impression.get("_impressed_dt") or datetime.fromisoformat(
                impression["impressed_at"]
            )
            clicked_dt = self._clamp(
                self._add_seconds(
                    impressed_dt,
                    CAUSAL_DELTAS["click_delay_min_s"],
                    CAUSAL_DELTAS["click_delay_max_s"],
                )
            )
            ts = self._ts_str(clicked_dt)
            clk = row_to_dict(
                AdClick(
                    click_id=self._uid(),
                    impression_id=impression["impression_id"],
                    session_id=impression["session_id"],
                    cost=self.dist.random_float(0.05, 5.0, 6),
                    clicked_at=ts,
                    created_at=ts,
                )
            )
            clk["_clicked_dt"] = clicked_dt
            clk["_customer_id"] = impression["customer_id"]
            self._clicks.append(clk)
            rows.append(clk)

        yield from self._batched(
            [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
            self.config.batch_size,
        )

    def generate_ad_conversions(self) -> Generator[Batch, None, None]:
        rows = []
        cvr = self.dist.sample(DISTRIBUTIONS["cvr"])
        attributions = ["last_click", "first_click", "linear", "time_decay"]

        for click in self._clicks:
            if not self.dist.bernoulli(cvr):
                continue
            cid = click.get("_customer_id")
            orders = self._customer_orders.get(cid, [])
            if not orders:
                continue
            order = self.dist.choice(orders)
            clicked_dt = click.get("_clicked_dt") or datetime.fromisoformat(
                click["clicked_at"]
            )
            conv_dt = self._clamp(
                self._add_seconds(
                    clicked_dt,
                    CAUSAL_DELTAS["conversion_delay_min_m"] * 60,
                    CAUSAL_DELTAS["conversion_delay_max_m"] * 60,
                )
            )
            ts = self._ts_str(conv_dt)
            rows.append(
                row_to_dict(
                    AdConversion(
                        conversion_id=self._uid(),
                        click_id=click["click_id"],
                        order_id=order["order_id"],
                        revenue=order.get("total_amount", 0.0),
                        converted_at=ts,
                        attribution=self.dist.choice(attributions),
                        created_at=ts,
                    )
                )
            )
        yield from self._batched(rows, self.config.batch_size)
