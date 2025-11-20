{
    'name': 'Payment Provider: PayFast',
    'version': '19.0.1.0.0',
    'author': 'Jacques Joubert - https://github.com/clapman',
    'category': 'Accounting/Payment Providers',
    'summary': 'A South African payment gateway.',
    'depends': ['payment'],
    'data': [
        'views/payment_payfast_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'application': False,
    'license': 'LGPL-3',
}