import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class PayFastController(http.Controller):

    @http.route('/payment/payfast/ipn', type='http', auth='public', methods=['POST'], csrf=False)
    def payfast_ipn(self, **data):
        """ 
        PayFast ITN (Instant Transaction Notification).
        PayFast sends a POST request here to update the transaction status.
        """
        _logger.info("PayFast IPN Received data:\n%s", pprint.pformat(data))
        
        try:
            # Odoo standard flow: Find tx -> Verify -> Update
            request.env['payment.transaction'].sudo()._handle_notification_data('payfast', data)
        except Exception as e:
            _logger.exception("PayFast IPN Error")
            # PayFast expects a 200 OK even if we failed internally, 
            # otherwise it keeps retrying. 
            return 'OK' 

        return 'OK'

    @http.route('/payment/payfast/return', type='http', auth='public', csrf=False)
    def payfast_return(self, **data):
        """ User returns to website after payment. """
        _logger.info("PayFast: User returned to site.")
        return request.redirect('/payment/status')

    @http.route('/payment/payfast/cancel', type='http', auth='public', csrf=False)
    def payfast_cancel(self, **data):
        """ User cancelled payment on PayFast. """
        _logger.info("PayFast: User cancelled.")
        return request.redirect('/payment/status')