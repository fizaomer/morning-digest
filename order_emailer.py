import os
import csv
import smtplib
import requests
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ENV VARIABLES
SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2023-04")
SHOPIFY_ADMIN_API_TOKEN = os.getenv("SHOPIFY_ADMIN_API_TOKEN")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

CSV_FILENAME = "orders_export.csv"

# Define which fields to extract
COLUMN_MAPPING = {
    "Name": lambda o: o["name"],
    "Email": lambda o: o["email"],
    "Financial Status": lambda o: o["financial_status"],
    "Created at": lambda o: o["created_at"],
    "Lineitem quantity": lambda o: sum(i["quantity"] for i in o["line_items"]),
    "Payment Method": lambda o: o.get("payment_gateway_names", [""])[0],
    "Shipping Name": lambda o: o.get("shipping_address", {}).get("name", ""),
    "Shipping Street": lambda o: o.get("shipping_address", {}).get("address1", ""),
    "Shipping City": lambda o: o.get("shipping_address", {}).get("city", ""),
    "Shipping Province": lambda o: o.get("shipping_address", {}).get("province", ""),
    "Shipping Zip": lambda o: o.get("shipping_address", {}).get("zip", ""),
    "Shipping Country": lambda o: o.get("shipping_address", {}).get("country", ""),
    "Shipping Method": lambda o: o.get("shipping_lines", [{}])[0].get("title", "Not specified"),  # <-- 👈 Added line
    "Lineitem name": lambda o: ", ".join(i["name"] for i in o["line_items"]),
    "Lineitem price": lambda o: ", ".join(str(i["price"]) for i in o["line_items"]),
    "Lineitem sku": lambda o: ", ".join(i.get("sku", "") for i in o["line_items"]),
    "Shipping Phone": lambda o: o.get("shipping_address", {}).get("phone", ""),
    "Notes": lambda o: o.get("note", ""),
    "Note Attributes": lambda o: ", ".join(f"{n['name']}: {n['value']}" for n in o.get("note_attributes", [])),
    "Total Price": lambda o: o["total_price"],
    "Subtotal": lambda o: o["subtotal_price"],
    "Shipping Price": lambda o: o.get("total_shipping_price_set", {}).get("shop_money", {}).get("amount", ""),
    "Discount Amount": lambda o: o["total_discounts"],
    "Tags": lambda o: o.get("tags", "")
}



def fetch_unfulfilled_orders():
    url = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}/orders.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "status": "open",
        "fulfillment_status": "unfulfilled",
        "limit": 250
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("orders", [])


def write_csv(orders):
    with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(COLUMN_MAPPING.keys())
        for order in orders:
            row = []
            for extractor in COLUMN_MAPPING.values():
                try:
                    row.append(extractor(order))
                except Exception:
                    row.append("")
            writer.writerow(row)


def format_order_summary(orders):
    summaries = []
    for o in orders:
        shipping_method = o.get("shipping_lines", [{}])[0].get("title", "Not specified")

        lines = [
            f"Order: {o['name']}",
            f"Customer: {o.get('shipping_address', {}).get('name', '')}",
            f"Email: {o.get('email', '')}",
            f"Shipping Method: {shipping_method}",
            f"Address: {o.get('shipping_address', {}).get('address1', '')}, "
            f"{o.get('shipping_address', {}).get('city', '')}, "
            f"{o.get('shipping_address', {}).get('province', '')} "
            f"{o.get('shipping_address', {}).get('zip', '')}, "
            f"{o.get('shipping_address', {}).get('country', '')}",
            "Items:"
        ]
        for item in o["line_items"]:
            sku = item.get("sku", "")
            lines.append(f"  - {item['quantity']} x {item['name']} (SKU: {sku})")
        lines.append("-" * 40)
        summaries.append("\n".join(lines))
    return "\n\n".join(summaries)


def send_email(subject, body, attach_csv):
    if not RECIPIENT_EMAIL:
        print("❌ RECIPIENT_EMAIL is missing in your .env file.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg.set_content(body)

    if attach_csv and os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="text",
                subtype="csv",
                filename=CSV_FILENAME
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

    if attach_csv and os.path.exists(CSV_FILENAME):
        os.remove(CSV_FILENAME)
        print(f"🗑️ Deleted {CSV_FILENAME} after sending.")


def main():
    orders = fetch_unfulfilled_orders()
    if not orders:
        print("✅ No unfulfilled orders found. No email sent.")
        return

    write_csv(orders)
    summary = format_order_summary(orders)
    send_email("Zabihah Unfulfilled Orders", summary, attach_csv=True)
    print("✅ Email sent with CSV attachment.")


if __name__ == "__main__":
    main()
