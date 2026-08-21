"""Minimal, typed client for the WooCommerce orders REST API."""

import base64
import json
from collections.abc import Iterator, Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class WooCommerceError(RuntimeError):
    """Raised when WooCommerce cannot return a valid response."""


class WooAddress(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    address_1: str = ""
    address_2: str = ""
    city: str = ""
    postcode: str = ""
    country: str = ""
    email: str = ""
    phone: str = ""
    model_config = ConfigDict(extra="ignore")


class WooMetaData(BaseModel):
    key: str
    value: Any = None
    model_config = ConfigDict(extra="ignore")


class WooLineItem(BaseModel):
    id: int
    name: str
    product_id: int = 0
    variation_id: int = 0
    quantity: int = Field(default=1, ge=0)
    sku: str = ""
    meta_data: list[WooMetaData] = Field(default_factory=list)
    model_config = ConfigDict(extra="ignore")


class WooOrder(BaseModel):
    id: int
    number: str
    status: str
    currency: str = "SEK"
    total: Decimal | None = None
    date_created_gmt: datetime | None = None
    date_created: datetime | None = None
    date_modified_gmt: datetime | None = None
    date_paid_gmt: datetime | None = None
    payment_method: str = ""
    payment_method_title: str = ""
    customer_note: str = ""
    billing: WooAddress = Field(default_factory=WooAddress)
    shipping: WooAddress = Field(default_factory=WooAddress)
    line_items: list[WooLineItem] = Field(default_factory=list)
    meta_data: list[WooMetaData] = Field(default_factory=list)
    model_config = ConfigDict(extra="ignore")


class WooCommerceClient:
    """Read orders from WooCommerce's ``wc/v3`` API over HTTPS."""

    def __init__(
        self,
        base_url: str,
        consumer_key: str,
        consumer_secret: str,
        *,
        timeout: float = 30,
    ) -> None:
        normalized_url = base_url.rstrip("/")
        parsed = urlparse(normalized_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("WooCommerce base URL must be an absolute HTTPS URL")
        if not consumer_key or not consumer_secret:
            raise ValueError("WooCommerce consumer key and secret are required")
        self.base_url = normalized_url
        self.timeout = timeout
        credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode("ascii")
        self._authorization = f"Basic {credentials}"

    def get_orders(
        self,
        *,
        page: int = 1,
        per_page: int = 100,
        status: str | None = None,
        after: datetime | None = None,
        modified_after: datetime | None = None,
    ) -> tuple[list[WooOrder], int]:
        """Return one page of orders and the total number of available pages."""
        if page < 1:
            raise ValueError("page must be at least 1")
        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")
        params: dict[str, str | int] = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        if after:
            params["after"] = after.isoformat()
        if modified_after:
            params.update(
                {
                    "modified_after": modified_after.isoformat(),
                    "dates_are_gmt": "true",
                    "orderby": "modified",
                    "order": "asc",
                }
            )
        payload, headers = self._get("orders", params)
        if not isinstance(payload, list):
            raise WooCommerceError("WooCommerce orders response was not a list")
        try:
            orders = [WooOrder.model_validate(item) for item in payload]
        except ValidationError as error:
            raise WooCommerceError("WooCommerce returned an invalid order") from error
        try:
            total_pages = int(headers.get("X-WP-TotalPages", "1"))
        except ValueError as error:
            raise WooCommerceError("WooCommerce returned invalid pagination headers") from error
        return orders, max(total_pages, 1)

    def iter_orders(
        self,
        *,
        status: str | None = None,
        after: datetime | None = None,
        modified_after: datetime | None = None,
    ) -> Iterator[WooOrder]:
        """Yield all orders, following WooCommerce pagination."""
        page = 1
        while True:
            orders, total_pages = self.get_orders(
                page=page,
                status=status,
                after=after,
                modified_after=modified_after,
            )
            yield from orders
            if page >= total_pages:
                return
            page += 1

    def _get(self, endpoint: str, params: Mapping[str, str | int]) -> tuple[Any, Mapping[str, str]]:
        url = f"{self.base_url}/wp-json/wc/v3/{endpoint}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": self._authorization,
                "User-Agent": "bilen-backend/1.0",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                body = response.read()
                headers = dict(response.headers.items())
        except HTTPError as error:
            raise WooCommerceError(f"WooCommerce request failed with HTTP {error.code}") from error
        except URLError as error:
            raise WooCommerceError("Could not connect to WooCommerce") from error
        try:
            return json.loads(body), headers
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WooCommerceError("WooCommerce returned invalid JSON") from error
