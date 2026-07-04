import hashlib
import hmac
import logging
import urllib.parse

from werkzeug.exceptions import Forbidden

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# Order documented for outbound checkout signatures (Step 2: Create security signature).
PAYFAST_CHECKOUT_FIELD_ORDER = (
    'merchant_id',
    'merchant_key',
    'return_url',
    'cancel_url',
    'notify_url',
    'name_first',
    'name_last',
    'email_address',
    'cell_number',
    'm_payment_id',
    'amount',
    'item_name',
    'item_description',
    'custom_int1',
    'custom_int2',
    'custom_int3',
    'custom_int4',
    'custom_int5',
    'custom_str1',
    'custom_str2',
    'custom_str3',
    'custom_str4',
    'custom_str5',
    'email_confirmation',
    'confirmation_address',
    'payment_method',
    'subscription_type',
    'billing_date',
    'recurring_amount',
    'frequency',
    'cycles',
)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('payfast', 'PayFast')],
        ondelete={'payfast': 'set default'},
    )

    payfast_merchant_id = fields.Char(
        string="Merchant ID",
        required_if_provider='payfast',
    )
    payfast_merchant_key = fields.Char(
        string="Merchant Key",
        required_if_provider='payfast',
    )
    payfast_passphrase = fields.Char(
        string="Passphrase",
        help="The passphrase set in your PayFast account settings (Salt Passphrase).",
        groups="base.group_system",
    )

    def _get_redirect_form_view(self, is_validation=False):
        if self.code == 'payfast':
            return self.env.ref('payment_payfast.payfast_redirect_form')
        return super()._get_redirect_form_view(is_validation)

    def _payfast_generate_signature(self, data):
        """Generate the MD5 signature for outbound checkout forms.

        Docs: https://developers.payfast.co.za/docs#step_2_create_security_signature
        """
        self.ensure_one()
        payload_parts = []
        known_keys = set(PAYFAST_CHECKOUT_FIELD_ORDER)
        keys = [key for key in PAYFAST_CHECKOUT_FIELD_ORDER if key in data]
        keys += [key for key in data if key not in known_keys and key != 'signature']

        for key in keys:
            value = data.get(key)
            if value in (None, ''):
                continue
            val_str = str(value).strip().replace('+', ' ')
            encoded_val = urllib.parse.quote_plus(val_str)
            payload_parts.append(f'{key}={encoded_val}')

        payload = '&'.join(payload_parts)
        if self.payfast_passphrase:
            pass_val = urllib.parse.quote_plus(self.payfast_passphrase.strip().replace('+', ' '))
            payload = f'{payload}&passphrase={pass_val}'

        return hashlib.md5(payload.encode('utf-8')).hexdigest()

    def _payfast_verify_itn_signature(self, post_items, received_signature):
        """Validate a PayFast ITN/return signature.

        ITN verification uses POST field order up to (but excluding) the signature field.
        Docs: https://developers.payfast.co.za/docs#step_4_confirm_payment
        """
        self.ensure_one()
        received_signature = (received_signature or '').strip()
        if not received_signature:
            _logger.warning("PayFast: received data with missing signature")
            raise Forbidden()

        payload_parts = []
        for key, value in post_items:
            if key == 'signature':
                break
            encoded_val = urllib.parse.quote_plus(str(value))
            payload_parts.append(f'{key}={encoded_val}')

        payload = '&'.join(payload_parts)
        if self.payfast_passphrase:
            pass_val = urllib.parse.quote_plus(self.payfast_passphrase)
            payload = f'{payload}&passphrase={pass_val}'

        expected_signature = hashlib.md5(payload.encode('utf-8')).hexdigest()
        if not hmac.compare_digest(received_signature, expected_signature):
            _logger.warning("PayFast: invalid signature for provider %s", self.id)
            raise Forbidden()

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'payfast':
            return default_codes
        return ['card', 'eft']
