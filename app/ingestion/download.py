from sec_edgar_downloader import Downloader
from app.config import SEC_EDGAR_EMAIL, RAW_DATA_DIR, TICKERS, N_10K, N_10Q


def download_filings(tickers=TICKERS, n_10k=N_10K, n_10q=N_10Q):
    dl = Downloader("IITMadras-Student-Project", SEC_EDGAR_EMAIL, str(RAW_DATA_DIR))
    for ticker in tickers:
        dl.get("10-K", ticker, limit=n_10k, download_details=True)
        dl.get("10-Q", ticker, limit=n_10q, download_details=True)
        print(f"Downloaded filings for {ticker}")


def verify_downloads():
    base = RAW_DATA_DIR / "sec-edgar-filings"
    if not base.exists():
        print("No filings found — did download_filings() run?")
        return
    for ticker_dir in sorted(base.iterdir()):
        for filing_type_dir in sorted(ticker_dir.iterdir()):
            count = len(list(filing_type_dir.iterdir()))
            print(f"{ticker_dir.name} / {filing_type_dir.name}: {count} filings")


if __name__ == "__main__":
    download_filings()
    verify_downloads()