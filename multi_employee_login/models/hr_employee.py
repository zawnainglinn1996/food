from odoo import models


class hr_employee_(models.Model):
    _inherit = 'hr.employee'

    _sql_constraints = [
        ('user_uniq', 'CHECK(1=1)', "A user cannot be linked to multiple employees in the same company.")
    ]

    # def init(self):
    #     print("\n \n \n \n \n \n")
    #     try:
    #         self._cr.execute("""ALTER TABLE hr_employee DROP CONSTRAINT IF EXISTS user_uniq;""")
    #     except:
    #         pass