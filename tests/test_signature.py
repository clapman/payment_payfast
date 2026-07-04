#!/usr/bin/env python3
"""PayFast signature unit checks for audit verification."""
import hashlib
import urllib.parse


def checkout_signature(data, passphrase=None):
    order = (
        'merchant_id', 'merchant_key', 'return_url', 'cancel_url', 'notify_url',
        'name_first', 'name_last', 'email_address', 'm_payment_id', 'amount', 'item_name',
    )
    parts = []
    for key in order:
        val = data.get(key)
        if val in (None, ''):
            continue
        encoded = urllib.parse.quote_plus(str(val).strip().replace('+', ' '))
        parts.append(f'{key}={encoded}')
    payload = '&'.join(parts)
    if passphrase:
        payload += f"&passphrase={urllib.parse.quote_plus(passphrase.strip().replace('+', ' '))}"
    return hashlib.md5(payload.encode()).hexdigest()


def itn_signature(post_items, passphrase=None):
    parts = []
    for key, value in post_items:
        if key == 'signature':
            break
        parts.append(f'{key}={urllib.parse.quote_plus(str(value))}')
    payload = '&'.join(parts)
    if passphrase:
        payload += f'&passphrase={urllib.parse.quote_plus(passphrase)}'
    return hashlib.md5(payload.encode()).hexdigest()


def main():
    checkout_data = {
        'merchant_id': '10000100',
        'merchant_key': '46f0cd694581a',
        'return_url': 'https://example.com/payment/payfast/return',
        'cancel_url': 'https://example.com/payment/payfast/cancel',
        'notify_url': 'https://example.com/payment/payfast/ipn',
        'name_first': 'John',
        'name_last': 'Doe',
        'email_address': 'john@example.com',
        'm_payment_id': 'SO001',
        'amount': '100.00',
        'item_name': 'SO001',
    }
    sig = checkout_signature(checkout_data, passphrase='salt')
    assert len(sig) == 32
    print('checkout signature:', sig)

    post_items = [
        ('m_payment_id', 'SO001'),
        ('pf_payment_id', '12345'),
        ('payment_status', 'COMPLETE'),
        ('amount_gross', '100.00'),
        ('signature', 'ignored'),
    ]
    itn_sig = itn_signature(post_items, passphrase='salt')
    assert len(itn_sig) == 32
    print('itn signature:', itn_sig)
    print('signature tests OK')


if __name__ == '__main__':
    main()
