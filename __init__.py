# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import product


def register():
    Pool.register(
        product.ProductSupplierPrice,
        module='purchase_supplier_price_period', type_='model')
    Pool.register(
        product.CreatePurchase,
        depends=['stock_supply'],
        module='purchase_supplier_price_period', type_='wizard')
