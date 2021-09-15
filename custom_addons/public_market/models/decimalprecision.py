
from datetime import date, timedelta
from decimal import *

from odoo import api

def tronquer(decimale):
    return float(Decimal(decimale).quantize(Decimal('.01'), rounding=ROUND_DOWN))

def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))

def get_supplier_code(self,product):
    supplierinfo_obj = self.env['product.supplierinfo']
    code_supplier = supplierinfo_obj.search([('product_tmpl_id','=',product.product_tmpl_id.id)],limit=1,order='sequence')
    code_supplier = code_supplier and code_supplier[0].product_code or product.default_code
    return code_supplier

def count_all(self,vehicle_id):
    """ cette fonctionnalité n'est pas encore utilisée"""
    service_type_id = self.env['fleet.service.type'].search([('code','=','maintenance')])
    if service_type_id:
        service_count = self.env['fleet.vehicle.log.services'].search_count([('vehicle_id','=',vehicle_id),('cost_subtype_id','=',service_type_id[0])])
        count_repair = self.env['fleet.vehicle.log.services'].search_count([('vehicle_id','=',vehicle_id),('cost_subtype_id','!=',service_type_id[0])])
        self.env['fleet.vehicle'].write(vehicle_id,{'service_count':service_count,'count_repair':count_repair})
    return True

def get_alert_parameter_for_log(self,log,log_date):
    NOW = date.today()
    param_ids = self.env['fleet.configurator'].search([(1,'=',1)])
    jour_avant_alert = 0
    for param in param_ids:
        jour_avant_alert = param.jour_alert
    msg = log.state
    if msg not in ('done','cancel1','cancel2'):
        if log_date == NOW:
            msg = "today"
        elif log_date > NOW:
            val_before =  timedelta(days=jour_avant_alert)
            if log_date - NOW <= val_before:
                msg = "warning"
            else:
                msg = "alert"
        else:
            msg = "error"


    if msg != "":
        try :
            log.env.invalidate_all()
            log.status = msg
        except:
            log.env.invalidate_all()
    return msg