# 🕊️ morning-digest

**Automated daily email report of unfulfilled Shopify orders**

This project fetches all unfulfilled Shopify orders and emails a formatted CSV report every morning at **9 AM EST**, using **GitHub Actions**.

### Features
- Pulls open + unfulfilled orders from the Shopify Admin API  
- Extracts key order details like:
  - Customer name and email
  - Shipping address and phone
  - Line items, quantity, SKUs, and prices
  - Shipping method
  - Notes and tags
- Sends a formatted CSV file to the specified recipient via email
- Cleans up after sending

---

### Setup

1. Clone this repo or fork it.
2. Go to your GitHub repository settings → **Secrets and variables → Actions → New repository secret**, and add:

| Name                  | Value                                  |
|-----------------------|----------------------------------------|
| `SHOPIFY_STORE_NAME`  | Your store name (e.g., `yourstore`)    |
| `SHOPIFY_API_VERSION` | API version (default: `2023-04`)       |
| `SHOPIFY_ADMIN_API_TOKEN` | Private Admin API token            |
| `SENDER_EMAIL`        | Gmail address you're sending from      |
| `SENDER_PASSWORD`     | Gmail app password                     |
| `RECIPIENT_EMAIL`     | Recipient email for the report         |

---
### Schedule

This GitHub Action is scheduled to run daily at: 9:00 AM EST / 13:00 UTC

This is controlled by the cron expression in `.github/workflows/daily-email.yml`.  
If you want to change the time, update this line in that file:
```yaml
schedule:
  - cron: '0 13 * * *'
```

---

### Dependencies
GitHub Actions will automatically install the required Python packages from requirements.txt:
requests
python-dotenv

---

### Project Structure
morning-digest/
├── .github/workflows/daily-email.yml   # GitHub Actions automation
├── order_emailer.py                    # Main script
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
