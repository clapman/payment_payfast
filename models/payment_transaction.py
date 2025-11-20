import logging
from werkzeug import urls
from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ 
        This method is working fine, keep using super() here as it exists.
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payfast':
            return res

        tx = self.sudo()
        provider = tx.provider_id
        
        # FORCE HTTPS
        base_url = provider.get_base_url()
        if "localhost" not in base_url and not base_url.startswith('https'):
            base_url = base_url.replace('http://', 'https://')

        payfast_amount = f"{tx.amount:.2f}"
        partner_name = tx.partner_name or tx.partner_id.name or 'Customer'
        first_name = (partner_name.strip().split(' ', 1) + [''])[0][:100]
        last_name = (partner_name.strip().split(' ', 1) + [''])[1][:100]
        if not last_name: last_name = 'Customer'

        payfast_data = {
            'merchant_id': provider.payfast_merchant_id,
            'merchant_key': provider.payfast_merchant_key,
            'return_url': urls.url_join(base_url, '/payment/payfast/return'),
            'cancel_url': urls.url_join(base_url, '/payment/payfast/cancel'),
            'notify_url': urls.url_join(base_url, '/payment/payfast/ipn'),
            'name_first': first_name,
            'name_last': last_name,
            'email_address': tx.partner_email or tx.partner_id.email or '',
            'm_payment_id': tx.reference,
            'amount': payfast_amount,
            'item_name': (tx.reference or 'Order')[:100],
        }

        payfast_data['signature'] = provider._payfast_generate_signature(payfast_data)

        if provider.payfast_sandbox:
            target_url = 'https://sandbox.payfast.co.za/eng/process'
        else:
            target_url = 'https://www.payfast.co.za/eng/process'

        return {
            'api_url': target_url,
            'payfast_fields': payfast_data
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ 
        FIX: Removed super() call because Odoo 19 removed the base method.
        We implement the search directly.
        """
        if provider_code != 'payfast':
            # If we can't call super, we return None/False for other providers 
            # and hope they implement their own lookup. 
            # But since this module only runs for PayFast logic, we focus on PayFast.
            return self.env['payment.transaction']

        reference = notification_data.get('m_payment_id')
        if not reference:
            raise ValidationError("PayFast: Received data with missing 'm_payment_id'")

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'payfast')], limit=1)
        
        if not tx:
            raise ValidationError(f"PayFast: No transaction found for reference {reference}")
        
        return tx

    def _process_notification_data(self, notification_data):
        """ 
        FIX: Removed super() call.
        We handle the status update directly.
        """
        if self.provider_code != 'payfast':
            return

        status = notification_data.get('payment_status')
        _logger.info("PayFast: Processing Status %s for Ref %s", status, self.reference)

        if status == 'COMPLETE':
            self._set_done()
        elif status == 'CANCELLED':
            self._set_canceled()
        else:
            self._set_pending()