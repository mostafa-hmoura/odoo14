from odoo import api, fields, models
from odoo.exceptions import UserError


class PublicMarketAttachementTemplate(models.Model):
    _name = "public.market.attachement.template"
    _desciption = "Public Market Attachement Template"

    code = fields.Many2one("market", u"Code", required=True)
    name = fields.Char(u"Description", required=True)
    line_ids = fields.One2many("public.market.attachement.template.line", "attachement_id")


class PublicMarketAttachemenTemplatetLine(models.Model):
    _name = "public.market.attachement.template.line"

    attachement_id = fields.Many2one("public.market.attachement.template", u"Attachement", ondelete="cascade")
    price_number = fields.Char("N° de prix", required=True)
    price_code = fields.Char(u"Code de prix")
    name = fields.Char(u"Désignation", required=True)
    uom = fields.Char(u"U", required=True)
    quantity = fields.Float(u"CPS", required=True)
    price_unit = fields.Float(u"P.U")

    line_ids = fields.One2many("public.market.attachement.sous.template.line", "attachement_id")


class PublicMarketAttachementSousTemplate(models.Model):
    _name = "public.market.attachement.sous.template"
    _desciption = "Public Market Attachement Sous Template"
    _rec_name = 'code'

    code = fields.Many2one("public.market.attachement.template", u"№ de Prix", ondelete="cascade", required=True)

    line_id = fields.Many2one("public.market.attachement.template.line", u"ligne d'Attachement",
                              domain="[('attachement_id', '=', code)]",
                              ondelete="cascade", required=True)

    line_ids = fields.One2many("public.market.attachement.sous.template.line", "attachement_id")

    @api.model
    def create(self, vals):

        self.check_sous_attachement(vals['line_id'])

        res = super(PublicMarketAttachementSousTemplate, self).create(vals)

        for line in res['line_ids']:
            line.line_id = res['line_id']

        return res


    @api.onchange('line_id')
    def check_sous_attachement_change(self):
        self.check_sous_attachement(self.line_id.id)

    def check_sous_attachement(self,line_id):

        state = self.env['public.market.attachement.sous.template'].search([('line_id','=', line_id)])

        if state:
            raise UserError('des sous lignes déja existe pour la ligne d\'attachement sélectionnée !')
            return False

        else:
            return True

class PublicMarketAttachemenSousTemplatetLine(models.Model):
    _name = "public.market.attachement.sous.template.line"

    attachement_id = fields.Many2one("public.market.attachement.sous.template", u"Attachement", ondelete="cascade")

    line_id = fields.Many2one("public.market.attachement.template.line")

    price_number = fields.Char("N° de prix", required=True)
    price_code = fields.Char(u"Code de prix")
    name = fields.Char(u"Désignation", required=True)
    uom = fields.Char(u"U", required=True)
    quantity = fields.Float(u"CPS", required=True)
    price_unit = fields.Float(u"P.U", required=True)

