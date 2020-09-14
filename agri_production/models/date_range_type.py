from odoo import models, fields, api, _, exceptions


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    is_season = fields.Boolean(string='Is Season', default=False)

    def unlink(self):
        """
        Cannot delete a date_range_type with 'is_season' flag = True
        """
        for rec in self:
            if rec.is_season:
                raise exceptions.ValidationError(
                    _('You cannot delete a date range type with '
                      'flag "is_season"'))
            else:
                super(DateRangeType, rec).unlink()
