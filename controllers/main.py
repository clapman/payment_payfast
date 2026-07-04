import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PayFastController(http.Controller):
    _return_url = '/payment/payfast/return'
    _cancel_url = '/payment/payfast/cancel'
    _notify_url = '/payment/payfast/ipn'

    @http.route(
        _return_url,
        type='http',
        auth='public',
        methods=['GET', 'POST'],
        csrf=False,
        save_session=False,
    )
    def payfast_return(self, **data):
        _logger.info("PayFast return with data:\n%s", pprint.pformat(data))
        self._process_payment_data(data)
        return request.redirect('/payment/status')

    @http.route(
        _cancel_url,
        type='http',
        auth='public',
        methods=['GET', 'POST'],
        csrf=False,
        save_session=False,
    )
    def payfast_cancel(self, **data):
        _logger.info("PayFast cancel with data:\n%s", pprint.pformat(data))
        self._process_payment_data(data)
        return request.redirect('/payment/status')

    @http.route(
        _notify_url,
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        save_session=False,
    )
    def payfast_ipn(self, **data):
        _logger.info("PayFast IPN received:\n%s", pprint.pformat(data))
        try:
            post_items = self._get_ordered_post_items()
            tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('payfast', data)
            if not tx_sudo:
                _logger.warning("PayFast IPN: no transaction for data")
                return 'FAIL'
            tx_sudo.provider_id._payfast_verify_itn_signature(post_items, data.get('signature'))
            tx_sudo._process('payfast', data)
            return 'OK'
        except Forbidden:
            _logger.warning("PayFast IPN: invalid signature")
            return 'FAIL'
        except Exception:
            _logger.exception("PayFast IPN error")
            return 'FAIL'

    def _process_payment_data(self, data):
        """Process customer redirect callbacks when PayFast includes payment data."""
        if not data.get('m_payment_id'):
            return
        if not data.get('signature'):
            _logger.info(
                "PayFast return/cancel for %s without signature; redirect only",
                data.get('m_payment_id'),
            )
            return
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('payfast', data)
        if not tx_sudo:
            return
        post_items = self._get_ordered_post_items()
        tx_sudo.provider_id._payfast_verify_itn_signature(post_items, data.get('signature'))
        tx_sudo._process('payfast', data)

    @staticmethod
    def _get_ordered_post_items():
        """Return POST/GET items in request order for PayFast signature verification."""
        if request.httprequest.form:
            return list(request.httprequest.form.items())
        return list(request.httprequest.args.items())
