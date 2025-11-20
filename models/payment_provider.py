import logging
import hashlib
import urllib.parse
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('payfast', 'PayFast')],
        ondelete={'payfast': 'set default'}
    )
    
    payfast_merchant_id = fields.Char(
        string="Merchant ID",
        help="The Merchant ID provided by PayFast",
        required_if_provider='payfast'
    )
    payfast_merchant_key = fields.Char(
        string="Merchant Key",
        help="The Merchant Key provided by PayFast",
        required_if_provider='payfast'
    )
    payfast_passphrase = fields.Char(
        string="Passphrase",
        help="The passphrase set in your PayFast account settings.",
        groups="base.group_system"
    )
    
    payfast_sandbox = fields.Boolean(
        string="Test Mode",
        default=True,
        help="Run transactions in the PayFast Sandbox."
    )

    is_published = fields.Boolean(
        string='Published',
        default=True,
        help="Whether the provider is visible on the website."
    )

    def _get_redirect_form_view(self, is_validation=False):
        if self.code == 'payfast':
            return self.env.ref('payment_payfast.payfast_redirect_form')
        return super()._get_redirect_form_view(is_validation)

    def _payfast_generate_signature(self, data, incoming=False):
        data_to_sign = {k: v for k, v in data.items() if v and k != 'signature'}
        sorted_keys = sorted(data_to_sign.keys())
        
        query_parts = []
        for key in sorted_keys:
            val = str(data_to_sign[key]).strip()
            encoded_val = urllib.parse.quote_plus(val)
            query_parts.append(f"{key}={encoded_val}")

        query_string = "&".join(query_parts)

        if self.payfast_passphrase:
            pass_val = urllib.parse.quote_plus(self.payfast_passphrase.strip())
            query_string += f"&passphrase={pass_val}"

        return hashlib.md5(query_string.encode('utf-8')).hexdigest()

    def _payfast_verify_signature(self, data):
        received_signature = data.get('signature')
        if not received_signature:
            return False
        expected_signature = self._payfast_generate_signature(data, incoming=True)
        return received_signature == expected_signature

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'payfast':
            return default_codes
        return ['card', 'eft']