import logging

from odoo import _, api, models
from odoo.tools import urls

from odoo.addons.payment_payfast.controllers.main import PayFastController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payfast':
            return res

        self.ensure_one()
        provider = self.provider_id

        base_url = provider.get_base_url()
        if 'localhost' not in base_url and not base_url.startswith('https'):
            base_url = base_url.replace('http://', 'https://')

        partner_name = self.partner_name or self.partner_id.name or 'Customer'
        name_parts = partner_name.strip().split(' ', 1)
        first_name = (name_parts[0] if name_parts else 'Customer')[:100]
        last_name = (name_parts[1] if len(name_parts) > 1 else 'Customer')[:100]

        payfast_data = {
            'merchant_id': provider.payfast_merchant_id,
            'merchant_key': provider.payfast_merchant_key,
            'return_url': urls.urljoin(base_url, PayFastController._return_url),
            'cancel_url': urls.urljoin(base_url, PayFastController._cancel_url),
            'notify_url': urls.urljoin(base_url, PayFastController._notify_url),
            'name_first': first_name,
            'name_last': last_name,
            'email_address': self.partner_email or self.partner_id.email or '',
            'm_payment_id': self.reference,
            'amount': f"{self.amount:.2f}",
            'item_name': (self.reference or 'Order')[:100],
        }
        payfast_data['signature'] = provider._payfast_generate_signature(payfast_data)

        api_url = (
            'https://sandbox.payfast.co.za/eng/process'
            if provider.state == 'test'
            else 'https://www.payfast.co.za/eng/process'
        )
        return {
            'api_url': api_url,
            'payfast_fields': payfast_data,
        }

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        if provider_code != 'payfast':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('m_payment_id')

    def _extract_amount_data(self, payment_data):
        if self.provider_code != 'payfast':
            return super()._extract_amount_data(payment_data)

        amount = payment_data.get('amount_gross') or payment_data.get('amount')
        if amount is None:
            return None
        return {
            'amount': float(amount),
            'currency_code': payment_data.get('currency') or self.currency_id.name,
        }

    def _apply_updates(self, payment_data):
        if self.provider_code != 'payfast':
            return super()._apply_updates(payment_data)

        provider_reference = payment_data.get('pf_payment_id')
        if provider_reference:
            self.provider_reference = provider_reference

        status = (payment_data.get('payment_status') or '').upper()
        _logger.info("PayFast: status %s for %s", status, self.reference)

        if status == 'COMPLETE':
            self._set_done()
        elif status in ('CANCELLED', 'CANCELED'):
            self._set_canceled()
        elif status == 'FAILED':
            self._set_error(_("PayFast reported that the payment failed."))
        else:
            self._set_pending()

    def _create_payment(self, **extra_create_values):
        if self.provider_code != 'payfast':
            return super()._create_payment(**extra_create_values)

        journal = self.provider_id.journal_id
        if not journal:
            return super()._create_payment(**extra_create_values)

        payfast_method = journal.inbound_payment_method_line_ids.filtered(
            lambda line: line.payment_method_id.code == 'payfast'
        )
        if payfast_method:
            extra_create_values['payment_method_line_id'] = payfast_method[0].id

        return super()._create_payment(**extra_create_values)
