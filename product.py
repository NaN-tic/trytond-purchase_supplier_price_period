# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Product', 'ProductSupplierPrice']
__metaclass__ = PoolMeta


class Product:
    __name__ = 'product.product'

    # This method is added in trytond-patches. In trunk 'get_purchase_price'
    # use the new match() method of purchase.product_supplier.price
    def get_supplier_price(self, product_supplier, quantity, to_uom):
        pool = Pool()
        SupplierPrice = pool.get('purchase.product_supplier.price')
        Uom = pool.get('product.uom')

        context = Transaction().context
        with Transaction().set_context(_datetime=context.get('purchase_date')):
            for price in SupplierPrice.search([
                        ('product_supplier', '=', product_supplier.id),
                        ('valid', '=', True),
                        ]):
                if Uom.compute_qty(self.purchase_uom,
                        price.quantity, to_uom) <= quantity:
                    return price.unit_price


class ProductSupplierPrice:
    __name__ = 'purchase.product_supplier.price'

    start_date = fields.Date('Start Date',
        help='Starting date for this price entry to be valid.')
    end_date = fields.Date('End Date',
        help='Ending date for this price entry to be valid.')
    valid = fields.Function(fields.Boolean('Valid'),
        'on_change_with_valid', searcher='search_valid')

    @fields.depends('start_date', 'end_date')
    def on_change_with_valid(self, name=None):
        Date = Pool().get('ir.date')

        context = Transaction().context
        today = (context['_datetime'] if context.get('_datetime')
            else Date.today())
        return ((not self.start_date or self.start_date <= today) and
            (not self.end_date or self.end_date >= today))

    @classmethod
    def search_valid(cls, name, clause):
        Date = Pool().get('ir.date')

        context = Transaction().context
        today = (context['_datetime'] if context.get('_datetime')
            else Date.today())
        return [
            ['OR',
                ('start_date', '=', None),
                ('start_date', '<=', today),
                ],
            ['OR',
                ('end_date', '=', None),
                ('end_date', '>=', today),
                ],
            ]
