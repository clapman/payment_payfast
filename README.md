# PayFast Payment Provider for Odoo 19

This module integrates the **PayFast** payment gateway (South Africa) with **Odoo 19**, allowing customers to pay for E-commerce orders and Invoices using Credit Cards, Instant EFT, and other PayFast supported methods.

It is designed to handle **Instant Payment Notifications (IPN)** for automatic status updates and includes support for development environments using reverse proxies (e.g., Ngrok).

## Features

*   **Standard Redirect Flow:** Users are redirected to the secure PayFast payment page.
*   **IPN Support:** Automatically updates Odoo transactions (Draft -> Pending -> Paid) via server-to-server communication.
*   **Accounting Integration:** Properly maps payments to the "PayFast" payment method in Bank Journals.
*   **Proxy/Ngrok Support:** Forces HTTPS for callback URLs to prevent connection errors behind reverse proxies or tunnels.
*   **Odoo 19 Native:** Updated for the Odoo 19 Payment API (No `super()` calls in notification handlers).

## Prerequisites

*   Odoo 19.0+
*   A PayFast Merchant Account (or Sandbox Account).

## Installation

1.  Clone this repository into your Odoo `addons` directory:
    ```bash
    git clone https://github.com/clapman/payment_payfast.git
    ```
2.  Restart your Odoo server.
3.  Log in to Odoo as an Administrator.
4.  Activate **Developer Mode**.
5.  Go to **Apps**, click **Update App List**, search for **PayFast**, and click **Activate**.

## Configuration

### 1. Payment Provider Setup
1.  Go to **Accounting** (or Website) > **Configuration** > **Payment Providers**.
2.  Select **PayFast**.
3.  Set the **State** to **Test Mode** (for Sandbox) or **Enabled** (for Production).
4.  Enter your credentials:
    *   **Merchant ID**
    *   **Merchant Key**
    *   **Passphrase** (Ensure this matches your PayFast dashboard settings).
5.  **Publish** the provider.

### 2. Accounting Journal (Critical)
To prevent *"Please define a payment method line"* errors during invoice generation:

1.  Go to **Accounting** > **Configuration** > **Journals**.
2.  Open your **Bank** journal (or the journal used for PayFast).
3.  Go to the **Incoming Payments** tab.
4.  Click **Add a line**.
5.  In the **Payment Method** column, select **PayFast**.
    *   *Note: If PayFast is not visible, ensure you have upgraded the module so the XML data is loaded.*
6.  **Save**.

### 3. System Parameters (For IPN)
For the PayFast server to reach your Odoo instance (especially when using Ngrok):

1.  Go to **Settings** > **Technical** > **System Parameters**.
2.  Ensure `web.base.url` is set to your public HTTPS address (e.g., `https://your-site.ngrok-free.app`).
3.  (Optional) Create a parameter `web.base.url.freeze` with value `True` to prevent Odoo from changing it automatically.

## Workflow

1.  **Checkout:** Customer selects PayFast at checkout and clicks "Pay Now".
2.  **Redirect:** Customer is redirected to the PayFast secure page.
3.  **Payment:** Customer completes payment.
4.  **Return:** Customer is redirected back to `/payment/status` on your Odoo site.
5.  **IPN (Background):** PayFast sends a `POST` request to `/payment/payfast/ipn`.
6.  **Confirmation:** Odoo validates the signature and amount. The Order is confirmed, and the Invoice is marked as **In Payment**.

## Technical Notes for Developers

### HTTP vs HTTPS
The module explicitly forces `https://` in `_get_specific_rendering_values` to ensure compatibility with PayFast's security requirements, even if Odoo detects it is running on `localhost` behind a proxy.

## Troubleshooting

*   **Error:** *Invalid Header* or *404* on IPN.
    *   **Fix:** Check `web.base.url` in System Parameters. Ensure the controller route `/payment/payfast/ipn` is accessible publicly.
*   **Error:** *Please define a payment method line on your payment.*
    *   **Fix:** See Configuration Step 2. You must add "PayFast" to the Incoming Payments tab of your Bank Journal.

## License

LGPL-3