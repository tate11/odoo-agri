from odoo import fields, models


class Document(models.Model):
    """ Extension of ir.attachment only used in Agri to handle archiving
    and basic versioning.
    """
    _name = 'agri.document'
    _description = "Agri Document"
    _inherits = {
        'ir.attachment': 'ir_attachment_id',
    }
    _order = "priority desc, id desc"

    ir_attachment_id = fields.Many2one('ir.attachment', string='Related attachment', required=True, ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority",
        help='Gives the sequence order when displaying a list of Agri documents.')
