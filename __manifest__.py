{
    'name': 'Payment Provider: PayFast',
    'version': '19.0.1.0.0',
    'author': 'Jacques Joubert',
    'website': 'https://github.com/clapman/payment_payfast',
    'category': 'Accounting/Payment Providers',
    'summary': 'Accept payments via PayFast (South Africa).',
    'description': """
PayFast payment gateway integration for Odoo 19.

Supports redirect checkout, Instant Payment Notifications (IPN), and accounting
payment method mapping for South African merchants.
    """,
    'depends': ['payment', 'account'],
    'data': [
        'views/payment_payfast_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
        'data/account_payment_method.xml',
    ],
    'images': ['static/description/icon.png'],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'application': False,
    'license': 'LGPL-3',
}
