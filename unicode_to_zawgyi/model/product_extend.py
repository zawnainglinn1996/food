from odoo import models, fields, api, _
import re


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    zawgyi_product_name = fields.Char(string='Product Name ', compute='get_zawgyi_name', store=True)

    @staticmethod
    def uni2zg(text):
        rules = [
            {"from": u"\u1004\u103a\u1039", "to": u"\u1064"}, {"from": u"\u1039\u1010\u103d", "to": u"\u1096"},
            {"from": u"\u1014(?=[\u1030\u103d\u103e\u102f\u1039])", "to": u"\u108f"},
            {"from": u"\u102b\u103a", "to": u"\u105a"}, {"from": u"\u100b\u1039\u100c", "to": u"\u1092"},
            {"from": u"\u102d\u1036", "to": u"\u108e"}, {"from": u"\u104e\u1004\u103a\u1038", "to": u"\u104e"},
            {"from": u"[\u1025\u1009](?=[\u1039\u102f\u1030])", "to": u"\u106a"},
            {"from": u"[\u1025\u1009](?=[\u103a])", "to": u"\u1025"},
            {"from": u"\u100a(?=[\u1039\u102f\u1030\u103d])", "to": u"\u106b"},
            {"from": u"(\u1039[\u1000-\u1021])\u102f", "to": u"\\1\u1033"},
            {"from": u"(\u1039[\u1000-\u1021])\u1030", "to": u"\\1\u1034"}, {"from": u"\u1039\u1000", "to": u"\u1060"},
            {"from": u"\u1039\u1001", "to": u"\u1061"}, {"from": u"\u1039\u1002", "to": u"\u1062"},
            {"from": u"\u1039\u1003", "to": u"\u1063"}, {"from": u"\u1039\u1005", "to": u"\u1065"},
            {"from": u"\u1039\u1007", "to": u"\u1068"}, {"from": u"\u1039\u1008", "to": u"\u1069"},
            {"from": u"\u100a(?=[\u1039\u102f\u1030])", "to": u"\u106b"}, {"from": u"\u1039\u100b", "to": u"\u106c"},
            {"from": u"\u1039\u100c", "to": u"\u106d"}, {"from": u"\u100d\u1039\u100d", "to": u"\u106e"},
            {"from": u"\u100e\u1039\u100d", "to": u"\u106f"}, {"from": u"\u1039\u100f", "to": u"\u1070"},
            {"from": u"\u1039\u1010", "to": u"\u1071"}, {"from": u"\u1039\u1011", "to": u"\u1073"},
            {"from": u"\u1039\u1012", "to": u"\u1075"}, {"from": u"\u1039\u1013", "to": u"\u1076"},
            {"from": u"\u1039\u1013", "to": u"\u1076"}, {"from": u"\u1039\u1014", "to": u"\u1077"},
            {"from": u"\u1039\u1015", "to": u"\u1078"}, {"from": u"\u1039\u1016", "to": u"\u1079"},
            {"from": u"\u1039\u1017", "to": u"\u107a"}, {"from": u"\u1039\u1018", "to": u"\u107b"},
            {"from": u"\u1039\u1019", "to": u"\u107c"}, {"from": u"\u1039\u101c", "to": u"\u1085"},
            {"from": u"\u103f", "to": u"\u1086"}, {"from": u"(\u103c)\u103e", "to": u"\\1\u1087"},
            {"from": u"\u103d\u103e", "to": u"\u108a"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])\u102d", "to": u"\\2\\3\\4\u108b"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])\u102e", "to": u"\\2\\3\\4\u108c"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])\u1036", "to": u"\\2\\3\\4\u108d"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])", "to": u"\\2\\3\\4\\1"},
            {"from": u"\u101b(?=[\u102f\u1030\u103d\u108a])", "to": u"\u1090"},
            {"from": u"\u100f\u1039\u100d", "to": u"\u1091"}, {"from": u"\u100b\u1039\u100b", "to": u"\u1097"}, {
                "from": u"([\u1000-\u1021\u1029\u1090])([\u1060-\u1069\u106c\u106d\u1070-\u107c\u1085\u108a])?([\u103b-\u103e]*)?\u1031",
                "to": u"\u1031\\1\\2\\3"},
            {"from": u"([\u1000-\u1021\u1029])([\u1060-\u1069\u106c\u106d\u1070-\u107c\u1085])?(\u103c)",
             "to": u"\\3\\1\\2"}, {"from": u"\u103a", "to": u"\u1039"}, {"from": u"\u103b", "to": u"\u103a"},
            {"from": u"\u103c", "to": u"\u103b"}, {"from": u"\u103d", "to": u"\u103c"},
            {"from": u"\u103e", "to": u"\u103d"}, {"from": u"\u103d\u102f", "to": u"\u1088"},
            {"from": u"([\u102f\u1030\u1014\u101b\u103c\u108a\u103d\u1088])([\u1032\u1036]{0,1})\u1037",
             "to": u"\\1\\2\u1095"}, {"from": u"\u102f\u1095", "to": u"\u102f\u1094"},
            {"from": u"([\u1014\u101b])([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])\u1037",
             "to": u"\\1\\2\u1095"}, {"from": u"\u1095\u1039", "to": u"\u1094\u1039"},
            {"from": u"([\u103a\u103b])([\u1000-\u1021])([\u1036\u102d\u102e\u108b\u108c\u108d\u108e]?)\u102f",
             "to": u"\\1\\2\\3\u1033"},
            {"from": u"([\u103a\u103b])([\u1000-\u1021])([\u1036\u102d\u102e\u108b\u108c\u108d\u108e]?)\u1030",
             "to": u"\\1\\2\\3\u1034"}, {"from": u"\u103a\u102f", "to": u"\u103a\u1033"},
            {"from": u"\u103a([\u1036\u102d\u102e\u108b\u108c\u108d\u108e])\u102f", "to": u"\u103a\\1\u1033"},
            {"from": u"([\u103a\u103b])([\u1000-\u1021])\u1030", "to": u"\\1\\2\u1034"},
            {"from": u"\u103a\u1030", "to": u"\u103a\u1034"},
            {"from": u"\u103a([\u1036\u102d\u102e\u108b\u108c\u108d\u108e])\u1030", "to": u"\u103a\\1\u1034"},
            {"from": u"\u103d\u1030", "to": u"\u1089"},
            {"from": u"\u103b([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])",
             "to": u"\u107e\\1"}, {
                "from": u"\u107e([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])([\u103c\u108a])([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
                "to": u"\u1084\\1\\2\\3"}, {
                "from": u"\u107e([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])([\u103c\u108a])",
                "to": u"\u1082\\1\\2"}, {
                "from": u"\u107e([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])([\u1033\u1034]?)([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
                "to": u"\u1080\\1\\2\\3"},
            {"from": u"\u103b([\u1000-\u1021])([\u103c\u108a])([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
             "to": u"\u1083\\1\\2\\3"}, {"from": u"\u103b([\u1000-\u1021])([\u103c\u108a])", "to": u"\u1081\\1\\2"},
            {"from": u"\u103b([\u1000-\u1021])([\u1033\u1034]?)([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
             "to": u"\u107f\\1\\2\\3"}, {"from": u"\u103a\u103d", "to": u"\u103d\u103a"},
            {"from": u"\u103a([\u103c\u108a])", "to": u"\\1\u107d"},
            {"from": u"([\u1033\u1034])\u1094", "to": u"\\1\u1095"}
        ]
        for rule in rules:
            text = re.sub(rule["from"], rule["to"], text)
        return text

    @api.depends('name')
    def get_zawgyi_name(self):
        for rec in self:
            if rec.name:
                rec.zawgyi_product_name = rec.uni2zg(rec.name)
            else:
                rec.zawgyi_product_name = False


class ProductProduct(models.Model):
    _inherit = "product.product"

    zawgyi_product_name = fields.Char(string='Product Name ', compute='get_zawgyi_name', store=True)

    @staticmethod
    def uni2zg(text):
        rules = [
            {"from": u"\u1004\u103a\u1039", "to": u"\u1064"}, {"from": u"\u1039\u1010\u103d", "to": u"\u1096"},
            {"from": u"\u1014(?=[\u1030\u103d\u103e\u102f\u1039])", "to": u"\u108f"},
            {"from": u"\u102b\u103a", "to": u"\u105a"}, {"from": u"\u100b\u1039\u100c", "to": u"\u1092"},
            {"from": u"\u102d\u1036", "to": u"\u108e"}, {"from": u"\u104e\u1004\u103a\u1038", "to": u"\u104e"},
            {"from": u"[\u1025\u1009](?=[\u1039\u102f\u1030])", "to": u"\u106a"},
            {"from": u"[\u1025\u1009](?=[\u103a])", "to": u"\u1025"},
            {"from": u"\u100a(?=[\u1039\u102f\u1030\u103d])", "to": u"\u106b"},
            {"from": u"(\u1039[\u1000-\u1021])\u102f", "to": u"\\1\u1033"},
            {"from": u"(\u1039[\u1000-\u1021])\u1030", "to": u"\\1\u1034"}, {"from": u"\u1039\u1000", "to": u"\u1060"},
            {"from": u"\u1039\u1001", "to": u"\u1061"}, {"from": u"\u1039\u1002", "to": u"\u1062"},
            {"from": u"\u1039\u1003", "to": u"\u1063"}, {"from": u"\u1039\u1005", "to": u"\u1065"},
            {"from": u"\u1039\u1007", "to": u"\u1068"}, {"from": u"\u1039\u1008", "to": u"\u1069"},
            {"from": u"\u100a(?=[\u1039\u102f\u1030])", "to": u"\u106b"}, {"from": u"\u1039\u100b", "to": u"\u106c"},
            {"from": u"\u1039\u100c", "to": u"\u106d"}, {"from": u"\u100d\u1039\u100d", "to": u"\u106e"},
            {"from": u"\u100e\u1039\u100d", "to": u"\u106f"}, {"from": u"\u1039\u100f", "to": u"\u1070"},
            {"from": u"\u1039\u1010", "to": u"\u1071"}, {"from": u"\u1039\u1011", "to": u"\u1073"},
            {"from": u"\u1039\u1012", "to": u"\u1075"}, {"from": u"\u1039\u1013", "to": u"\u1076"},
            {"from": u"\u1039\u1013", "to": u"\u1076"}, {"from": u"\u1039\u1014", "to": u"\u1077"},
            {"from": u"\u1039\u1015", "to": u"\u1078"}, {"from": u"\u1039\u1016", "to": u"\u1079"},
            {"from": u"\u1039\u1017", "to": u"\u107a"}, {"from": u"\u1039\u1018", "to": u"\u107b"},
            {"from": u"\u1039\u1019", "to": u"\u107c"}, {"from": u"\u1039\u101c", "to": u"\u1085"},
            {"from": u"\u103f", "to": u"\u1086"}, {"from": u"(\u103c)\u103e", "to": u"\\1\u1087"},
            {"from": u"\u103d\u103e", "to": u"\u108a"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])\u102d", "to": u"\\2\\3\\4\u108b"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])\u102e", "to": u"\\2\\3\\4\u108c"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])\u1036", "to": u"\\2\\3\\4\u108d"},
            {"from": u"(\u1064)([\u1031]?)([\u103c]?)([\u1000-\u1021])", "to": u"\\2\\3\\4\\1"},
            {"from": u"\u101b(?=[\u102f\u1030\u103d\u108a])", "to": u"\u1090"},
            {"from": u"\u100f\u1039\u100d", "to": u"\u1091"}, {"from": u"\u100b\u1039\u100b", "to": u"\u1097"}, {
                "from": u"([\u1000-\u1021\u1029\u1090])([\u1060-\u1069\u106c\u106d\u1070-\u107c\u1085\u108a])?([\u103b-\u103e]*)?\u1031",
                "to": u"\u1031\\1\\2\\3"},
            {"from": u"([\u1000-\u1021\u1029])([\u1060-\u1069\u106c\u106d\u1070-\u107c\u1085])?(\u103c)",
             "to": u"\\3\\1\\2"}, {"from": u"\u103a", "to": u"\u1039"}, {"from": u"\u103b", "to": u"\u103a"},
            {"from": u"\u103c", "to": u"\u103b"}, {"from": u"\u103d", "to": u"\u103c"},
            {"from": u"\u103e", "to": u"\u103d"}, {"from": u"\u103d\u102f", "to": u"\u1088"},
            {"from": u"([\u102f\u1030\u1014\u101b\u103c\u108a\u103d\u1088])([\u1032\u1036]{0,1})\u1037",
             "to": u"\\1\\2\u1095"}, {"from": u"\u102f\u1095", "to": u"\u102f\u1094"},
            {"from": u"([\u1014\u101b])([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])\u1037",
             "to": u"\\1\\2\u1095"}, {"from": u"\u1095\u1039", "to": u"\u1094\u1039"},
            {"from": u"([\u103a\u103b])([\u1000-\u1021])([\u1036\u102d\u102e\u108b\u108c\u108d\u108e]?)\u102f",
             "to": u"\\1\\2\\3\u1033"},
            {"from": u"([\u103a\u103b])([\u1000-\u1021])([\u1036\u102d\u102e\u108b\u108c\u108d\u108e]?)\u1030",
             "to": u"\\1\\2\\3\u1034"}, {"from": u"\u103a\u102f", "to": u"\u103a\u1033"},
            {"from": u"\u103a([\u1036\u102d\u102e\u108b\u108c\u108d\u108e])\u102f", "to": u"\u103a\\1\u1033"},
            {"from": u"([\u103a\u103b])([\u1000-\u1021])\u1030", "to": u"\\1\\2\u1034"},
            {"from": u"\u103a\u1030", "to": u"\u103a\u1034"},
            {"from": u"\u103a([\u1036\u102d\u102e\u108b\u108c\u108d\u108e])\u1030", "to": u"\u103a\\1\u1034"},
            {"from": u"\u103d\u1030", "to": u"\u1089"},
            {"from": u"\u103b([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])",
             "to": u"\u107e\\1"}, {
                "from": u"\u107e([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])([\u103c\u108a])([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
                "to": u"\u1084\\1\\2\\3"}, {
                "from": u"\u107e([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])([\u103c\u108a])",
                "to": u"\u1082\\1\\2"}, {
                "from": u"\u107e([\u1000\u1003\u1006\u100f\u1010\u1011\u1018\u101a\u101c\u101a\u101e\u101f])([\u1033\u1034]?)([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
                "to": u"\u1080\\1\\2\\3"},
            {"from": u"\u103b([\u1000-\u1021])([\u103c\u108a])([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
             "to": u"\u1083\\1\\2\\3"}, {"from": u"\u103b([\u1000-\u1021])([\u103c\u108a])", "to": u"\u1081\\1\\2"},
            {"from": u"\u103b([\u1000-\u1021])([\u1033\u1034]?)([\u1032\u1036\u102d\u102e\u108b\u108c\u108d\u108e])",
             "to": u"\u107f\\1\\2\\3"}, {"from": u"\u103a\u103d", "to": u"\u103d\u103a"},
            {"from": u"\u103a([\u103c\u108a])", "to": u"\\1\u107d"},
            {"from": u"([\u1033\u1034])\u1094", "to": u"\\1\u1095"}
        ]
        for rule in rules:
            text = re.sub(rule["from"], rule["to"], text)
        return text

    @api.depends('name')
    def get_zawgyi_name(self):
        for rec in self:
            if rec.name:
                rec.zawgyi_product_name = rec.uni2zg(rec.name)
            else:
                rec.zawgyi_product_name = False
