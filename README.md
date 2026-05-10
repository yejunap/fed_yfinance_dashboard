# FED YFinance Dashboard

A comprehensive financial dashboard built with Streamlit that tracks:

- **Sector Performance**: Technology, Energy, Financials, Industrials, Healthcare, Consumer, Utilities, Materials
- **Global Indices**: S&P 500, NASDAQ, Dow Jones, Russell 2000
- **Commodities**: Crude Oil, Natural Gas, Gold, Silver, Copper
- **Volatility & Interest Rates**: VIX, 10Y Yield, Treasuries, High Yield Bonds
- **International Markets**: China, India, Japan, Korea, Taiwan

## Features

- Real-time data from Yahoo Finance
- Interactive visualizations with Matplotlib
- Date range selector for historical analysis
- Sector and commodity comparisons
- Mobile-responsive layout

## Project Structure

```
agent_projects/
├── fed_dashboard_yfinance_v3.py   # Main dashboard (latest)
├── fed_dashboard_yfinance_v2.py   # Previous version
├── fed_dashboard_yfinance.py      # Original version
├── fed_dashboard.py               # Base dashboard
├── fed_data_raw/                  # Data directory
│   ├── fed_yfinance_latest.json   # Latest data
│   ├── fed_yfinance_historical.json # Historical data
│   └── logs/                      # Cron job logs
└── style_guide/                   # Design system
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fed_dashboard.git
cd agent_projects

# Install dependencies
pip install streamlit pandas matplotlib seaborn numpy yfinance
```

### Running the Dashboard

```bash
streamlit run fed_dashboard_yfinance_v3.py
```

## Data Collection

Data is collected via Yahoo Finance API using the following scripts:

- `fed_data_raw/fed_monitor_yfinance.py` - YFinance data collection
- `fed_data_raw/fed_monitor_stocks.py` - Stock monitoring
- `fed_data_raw/fed_monitor_sox.py` - SOX index monitoring

## Deployment

### Local Development

```bash
streamlit run fed_dashboard_yfinance_v3.py --server.port 8501
```

### GitHub Pages (Public)

The dashboard can be deployed to GitHub Pages for public access.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is for educational and personal use.

## Acknowledgments

- Data provided by [Yahoo Finance](https://finance.yahoo.com/)
- Built with [Streamlit](https://streamlit.io/)
- Visualizations using [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/)

---

**Note**: This dashboard is for informational purposes only and should not be used for financial advice.
