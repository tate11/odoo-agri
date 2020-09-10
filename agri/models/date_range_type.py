from odoo import models, fields, api, _, exceptions


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    season = fields.Boolean(string='Is season?', default=False)

    def unlink(self):
        """
        Cannot delete a date_range_type with 'season' flag = True
        """
        for rec in self:
            if rec.season:
                raise exceptions.ValidationError(
                    _('You cannot delete a date range type with '
                      'flag "season"'))
            else:
                super(DateRangeType, rec).unlink()
