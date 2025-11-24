from . import controllers
from . import models
from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(env):
    """
    On module installation, set the PayFast icon automatically.
    """
    setup_provider(env, 'payfast')

def uninstall_hook(env):
    reset_payment_provider(env, 'payfast')