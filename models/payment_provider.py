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
        required_if_provider='payfast'
    )
    payfast_merchant_key = fields.Char(
        string="Merchant Key",
        required_if_provider='payfast'
    )
    payfast_passphrase = fields.Char(
        string="Passphrase",
        help="The passphrase set in your PayFast account settings.",
        groups="base.group_system"
    )
    payfast_sandbox = fields.Boolean(
        string="Sandbox Test Mode",
        default=True
    )
    
    # Helper to force visibility if the website_payment module isn't fully loaded
    is_published = fields.Boolean(string='Published', default=True)

    def _get_redirect_form_view(self, is_validation=False):
        if self.code == 'payfast':
            return self.env.ref('payment_payfast.payfast_redirect_form')
        return super()._get_redirect_form_view(is_validation)

    def _payfast_generate_signature(self, data):
        """ 
        Generate the MD5 signature per PayFast Python Docs. 
        Docs: https://developers.payfast.co.za/docs#step_2_create_security_signature
        """
        payload = ""
        # PayFast docs say: "Concatenation of name value pairs... listed in the order in which they appear"
        # But their Python example simply iterates the dictionary. 
        # We will iterate the dictionary (Insertion Order) which we control in payment_transaction.py
        for key, value in data.items():
            if key == 'signature' or not value:
                continue
            
            # Logic from PayFast Docs: 
            # payload += key + "=" + urllib.parse.quote_plus(dataArray[key].replace("+", " ")) + "&"
            val_str = str(value)
            encoded_val = urllib.parse.quote_plus(val_str.replace("+", " "))
            payload += f"{key}={encoded_val}&"

        # Remove last '&'
        payload = payload[:-1]

        if self.payfast_passphrase:
            # Docs: "&passphrase=..." (passphrase must be URL encoded too)
            pass_val = urllib.parse.quote_plus(self.payfast_passphrase.strip().replace("+", " "))
            payload += f"&passphrase={pass_val}"

        return hashlib.md5(payload.encode('utf-8')).hexdigest()

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'payfast':
            return default_codes
        return ['card', 'eft']