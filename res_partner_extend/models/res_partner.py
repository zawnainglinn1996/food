from odoo import models, fields, api, _

DOCUMENT_CHECKLIST = [
    'Company Register',
    'Tax Registration',
    'Business License',
    'FDA Registration',
    'Halal Certificate'
]

class Partner(models.Model):
    _inherit = "res.partner"

    discount_type = fields.Selection(selection=[('percentage', 'Percentage'), ('fixed', 'Fixed')],
                                     string='Discount Type', default="fixed")
    discount_rate = fields.Float(string="Discount Rate")

    document_checklist = fields.One2many('document.checklist', 'partner_id', string='Document Check list', copy=True)

    #for legal structure
    corporation = fields.Boolean("Corporation")
    joint_venture = fields.Boolean("Joint Venture")
    partnership = fields.Boolean("Partnership")
    franchise = fields.Boolean("Franchise")
    sole_proprietorship = fields.Boolean("Sole Proprietorship")
    non_profit = fields.Boolean("Non Profit")

    #Type of Business/Commodity Service 
    retailer = fields.Boolean("Retailer")
    construction_contractor = fields.Boolean("Construction Contractor")
    dealer = fields.Boolean("Distribution/Dealer")
    broadcaster = fields.Boolean("Publication/Broadcaster")
    professional_services = fields.Boolean("Professional Services")
    service_provider = fields.Boolean("Service Provider")
    manufacturer =  fields.Boolean("Manufacturer")
    consultant = fields.Boolean("Consultant")
    freight = fields.Boolean("Freight/Transporation")
    whole_sealer = fields.Boolean("Whole Sealer")
    other = fields.Boolean("Other")

    tt_payment = fields.Boolean("TT")
    cheque_payment = fields.Boolean("Cheque")
    others_payment = fields.Boolean("Others")

    #Attachment
    bank = fields.Char("Bank Name")
    branch = fields.Char("Branch Name")
    branch_address = fields.Char("Branch Address")
    beneficiary = fields.Char("Beneficiary Name")
    type_of_account = fields.Char("Type of Account")
    account_number = fields.Char("Account No.")
    micr_code = fields.Char("MICR Code No")
    swift_code = fields.Char("Swift/IBN Code")
    ifsc_no = fields.Char("IFSC No.(Branch Code NO)")
    nrc = fields.Char("Name & NRC/Password No")

    @api.model
    def default_get(self,default_fields):
        res = super(Partner, self).default_get(default_fields)

        document_checklist = [
            (0, 0, {'name': record}) for record in DOCUMENT_CHECKLIST
        ]

        res.update({
            'document_checklist': document_checklist
        })
        return res