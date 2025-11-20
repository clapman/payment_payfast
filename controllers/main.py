import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class PayFastController(http.Controller):
    _return_url = '/payment/payfast/return'
    _cancel_url = '/payment/payfast/cancel'
    _notify_url = '/payment/payfast/ipn'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def payfast_return(self, **data):
        return request.redirect('/payment/status')

    @http.route(_cancel_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def payfast_cancel(self, **data):
        return request.redirect('/payment/status')

    @http.route(_notify_url, type='http', auth='public', methods=['POST'], csrf=False)
    def payfast_ipn(self, **data):
        _logger.info("PayFast IPN received data:\n%s", pprint.pformat(data))
        try:
            # 1. Find Transaction
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('payfast', data)
            
            # 2. Process Transaction
            tx_sudo._process_notification_data(data)
            
            return 'OK'
        except Exception as e:
            _logger.exception("PayFast IPN Error")
            return 'FAIL'