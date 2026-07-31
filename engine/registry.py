"""
Asset Registry — Manages all supported assets and their metadata.

New asset classes can be registered without modifying the scoring engine.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scoring import AssetClass


class AssetRegistry:
    """
    Registry of all assets tracked by the NOW Index.

    Supports adding new asset classes dynamically without changing
    the scoring engine.
    """

    def __init__(self, data_path: str | Path | None = None) -> None:
        self._assets: dict[str, dict[str, Any]] = {}
        self._data_path = Path(data_path) if data_path else None

    def register(self, ticker: str, name: str, asset_class: AssetClass | str,
                 **metadata) -> str:
        """Register a new asset in the registry. Returns asset_id."""
        if isinstance(asset_class, str):
            try:
                asset_class = AssetClass(asset_class)
            except ValueError:
                asset_class = asset_class

        asset_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"now.{ticker}"))
        self._assets[asset_id] = {
            "asset_id": asset_id,
            "ticker": ticker.upper(),
            "name": name,
            "asset_class": asset_class.value if isinstance(asset_class, AssetClass) else asset_class,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
            **metadata,
        }
        return asset_id

    def unregister(self, asset_id: str) -> bool:
        """Mark an asset as inactive."""
        if asset_id in self._assets:
            self._assets[asset_id]["active"] = False
            return True
        return False

    def get(self, asset_id: str) -> dict[str, Any] | None:
        return self._assets.get(asset_id)

    def get_by_ticker(self, ticker: str) -> dict[str, Any] | None:
        for asset in self._assets.values():
            if asset["ticker"] == ticker.upper():
                return asset
        return None

    def list(self, asset_class: AssetClass | str | None = None,
             active_only: bool = True) -> list[dict[str, Any]]:
        result = []
        for asset in self._assets.values():
            if active_only and not asset.get("active", True):
                continue
            if asset_class is not None:
                ac = asset_class.value if isinstance(asset_class, AssetClass) else asset_class
                if asset["asset_class"] != ac:
                    continue
            result.append(asset)
        return result

    def count(self, asset_class: AssetClass | str | None = None) -> int:
        return len(self.list(asset_class))

    def asset_classes(self) -> list[str]:
        return list({a["asset_class"] for a in self._assets.values()})

    def save(self, path: str | Path | None = None) -> None:
        """Persist registry to JSON file."""
        save_path = Path(path) if path else self._data_path
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(list(self._assets.values()), f, indent=2, ensure_ascii=False)

    def load(self, path: str | Path | None = None) -> int:
        """Load registry from JSON file. Returns number of assets loaded."""
        load_path = Path(path) if path else self._data_path
        if load_path and load_path.exists():
            with open(load_path) as f:
                assets = json.load(f)
            for asset in assets:
                self._assets[asset["asset_id"]] = asset
            return len(assets)
        return 0

    def seed_default_assets(self) -> int:
        """Seed the registry with representative assets across all supported classes."""
        count = 0

        # US Stocks
        for t, n, s, ind, mc in [
            ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", 3.2e12),
            ("MSFT", "Microsoft Corporation", "Technology", "Software", 3.1e12),
            ("GOOGL", "Alphabet Inc.", "Technology", "Internet Services", 2.1e12),
            ("AMZN", "Amazon.com Inc.", "Consumer Cyclical", "Internet Retail", 2.0e12),
            ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors", 2.8e12),
            ("META", "Meta Platforms Inc.", "Technology", "Social Media", 1.3e12),
            ("TSLA", "Tesla Inc.", "Consumer Cyclical", "Auto Manufacturers", 0.7e12),
            ("JPM", "JPMorgan Chase & Co.", "Financial", "Banks", 0.55e12),
            ("V", "Visa Inc.", "Financial", "Credit Services", 0.56e12),
            ("JNJ", "Johnson & Johnson", "Healthcare", "Drug Manufacturers", 0.4e12),
            ("WMT", "Walmart Inc.", "Consumer Defensive", "Discount Stores", 0.5e12),
            ("PG", "Procter & Gamble Co.", "Consumer Defensive", "Household Products", 0.38e12),
            ("MA", "Mastercard Inc.", "Financial", "Credit Services", 0.42e12),
            ("UNH", "UnitedHealth Group Inc.", "Healthcare", "Healthcare Plans", 0.45e12),
            ("HD", "The Home Depot Inc.", "Consumer Cyclical", "Home Improvement", 0.36e12),
            ("BAC", "Bank of America Corp.", "Financial", "Banks", 0.28e12),
            ("DIS", "The Walt Disney Company", "Communication", "Entertainment", 0.2e12),
            ("NFLX", "Netflix Inc.", "Communication", "Entertainment", 0.25e12),
            ("ADBE", "Adobe Inc.", "Technology", "Software", 0.22e12),
            ("CRM", "Salesforce Inc.", "Technology", "Software", 0.24e12),
        ]:
            self.register(t, n, AssetClass.US_STOCK, sector=s, industry=ind,
                          country="US", exchange="NASDAQ", market_cap=mc, currency="USD")
            count += 1

        # ETFs
        for t, n, s in [
            ("SPY", "SPDR S&P 500 ETF Trust", "Large Cap"),
            ("QQQ", "Invesco QQQ Trust", "Technology"),
            ("IVV", "iShares Core S&P 500 ETF", "Large Cap"),
            ("VOO", "Vanguard S&P 500 ETF", "Large Cap"),
            ("VTI", "Vanguard Total Stock Market ETF", "Total Market"),
            ("BND", "Vanguard Total Bond Market ETF", "Bond"),
            ("EEM", "iShares MSCI Emerging Markets ETF", "Emerging Markets"),
            ("ARKK", "ARK Innovation ETF", "Innovation"),
            ("XLF", "Financial Select Sector SPDR Fund", "Financial"),
            ("XLK", "Technology Select Sector SPDR Fund", "Technology"),
        ]:
            self.register(t, n, AssetClass.ETF, sector=s, country="US", exchange="NYSE")
            count += 1

        # Cryptocurrencies
        for t, n, mc in [
            ("BTC-USD", "Bitcoin", 1.2e12),
            ("ETH-USD", "Ethereum", 0.4e12),
            ("SOL-USD", "Solana", 0.07e12),
            ("XRP-USD", "XRP", 0.03e12),
        ]:
            self.register(t, n, AssetClass.CRYPTOCURRENCY, sector="Digital Assets",
                          country="Global", market_cap=mc)
            count += 1

        # REITs
        for t, n, s in [
            ("PLD", "Prologis Inc.", "Industrial REIT"),
            ("AMT", "American Tower Corp.", "Infrastructure REIT"),
            ("EQIX", "Equinix Inc.", "Data Center REIT"),
        ]:
            self.register(t, n, AssetClass.REIT, sector=s, country="US", exchange="NYSE")
            count += 1

        # International Stocks
        for t, n, ac, c, mc in [
            ("TSM", "Taiwan Semiconductor Manufacturing", AssetClass.CHINESE_STOCK, "Taiwan", 0.7e12),
            ("SAP", "SAP SE", AssetClass.EUROPEAN_STOCK, "Germany", 0.25e12),
            ("NVS", "Novartis AG", AssetClass.EUROPEAN_STOCK, "Switzerland", 0.22e12),
            ("ASML", "ASML Holding N.V.", AssetClass.EUROPEAN_STOCK, "Netherlands", 0.35e12),
            ("SONY", "Sony Group Corporation", AssetClass.JAPANESE_STOCK, "Japan", 0.12e12),
            ("TM", "Toyota Motor Corporation", AssetClass.JAPANESE_STOCK, "Japan", 0.3e12),
            ("HSBC", "HSBC Holdings plc", AssetClass.UK_STOCK, "UK", 0.15e12),
            ("BHP", "BHP Group Ltd", AssetClass.AUSTRALIAN_STOCK, "Australia", 0.22e12),
            ("SHOP", "Shopify Inc.", AssetClass.CANADIAN_STOCK, "Canada", 0.1e12),
            ("0700.HK", "Tencent Holdings Ltd", AssetClass.HONG_KONG_STOCK, "Hong Kong", 0.45e12),
            ("005930.KS", "Samsung Electronics Co Ltd", AssetClass.KOREAN_STOCK, "South Korea", 0.4e12),
            ("000660.KS", "SK Hynix Inc", AssetClass.KOREAN_STOCK, "South Korea", 0.1e12),
        ]:
            self.register(t, n, ac, sector="Technology", country=c, market_cap=mc)
            count += 1

        return count
