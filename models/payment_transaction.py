import logging
from werkzeug import urls
from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'payfast':
            return res

        # 1. Permissions & Setup
        tx_sudo = self.sudo()
        provider_sudo = tx_sudo.provider_id
        base_url = provider_sudo.get_base_url()
        
        # 2. Prepare Data (Per PayFast Docs)
        # Docs: "amount" must be decimal (e.g., 100.00)
        payfast_amount = f"{tx_sudo.amount:.2f}"
        
        # Docs: "item_name" is required
        item_name = (tx_sudo.reference or 'Order')[:100]

        # Docs: Split name into first/last
        partner_name = tx_sudo.partner_name or tx_sudo.partner_id.name or 'Customer'
        name_parts = partner_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # 3. Build Dictionary (Insertion Order matches Docs preference)
        payfast_payload = {
            'merchant_id': provider_sudo.payfast_merchant_id,
            'merchant_key': provider_sudo.payfast_merchant_key,
            'return_url': urls.url_join(base_url, '/payment/payfast/return'),
            'cancel_url': urls.url_join(base_url, '/payment/payfast/cancel'),
            'notify_url': urls.url_join(base_url, '/payment/payfast/ipn'),
            'name_first': first_name[:100],
            'name_last': last_name[:100],
            'email_address': tx_sudo.partner_email or tx_sudo.partner_id.email or '',
            'm_payment_id': tx_sudo.reference,
            'amount': payfast_amount,
            'item_name': item_name,
        }

        # 4. Generate Signature (Per Docs Step 2)
        # Docs: "MD5 the parameter string and pass it as a hidden input named signature"
        payfast_payload['signature'] = provider_sudo._payfast_generate_signature(payfast_payload)

        # 5. Define Target URL (Per Docs)
        if provider_sudo.payfast_sandbox:
            target_url = 'https://sandbox.payfast.co.za/eng/process'
        else:
            target_url = 'https://www.payfast.co.za/eng/process'

        # 6. Return Explicit Keys to fix the "Empty Action" bug
        return {
            'payfast_url': target_url,       # Explicit URL variable
            'payfast_data': payfast_payload  # Explicit Data dictionary
        }
    
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'payfast' or len(tx) == 1:
            return tx

        reference = notification_data.get('m_payment_id')
        if not reference:
            raise ValidationError("PayFast: Received data with missing reference (m_payment_id).")

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'payfast')])
        if not tx:
            raise ValidationError(f"PayFast: No transaction found matching reference {reference}.")
        
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'payfast':
            return

        if not self.provider_id._payfast_verify_signature(notification_data):
            _logger.warning("PayFast: Signature verification failed for ref %s", self.reference)

        if 'pf_payment_id' in notification_data:
            self.provider_reference = notification_data.get('pf_payment_id')

        status = notification_data.get('payment_status')
        _logger.info("PayFast: IPN status %s for ref %s", status, self.reference)

        if status == 'COMPLETE':
            self._set_done()
        elif status == 'CANCELLED':
            self._set_canceled()
        elif status == 'PENDING':
            self._set_pending()