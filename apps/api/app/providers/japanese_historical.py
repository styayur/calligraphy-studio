"""Japanese historical provider boundary; no benchmark images or network startup."""
from app.providers.base import DatasetProvider


class JapaneseHistoricalProvider(DatasetProvider):
    name = "japanese-historical"
