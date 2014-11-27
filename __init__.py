# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .product import *


def register():
    Pool.register(
        ProductSupplierPrice,
        module='purchase_supplier_price_period', type_='model')
    Pool.register(
        CreatePurchase,
        module='purchase_supplier_price_period', type_='wizard')
