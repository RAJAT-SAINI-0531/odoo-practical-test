from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    """
    Extend estate.property with invoice generation and smart button.
    All accounting logic lives here, zero changes to the base estate module.
    """
    _inherit = 'estate.property'

    # -------------------------------------------------------------------------
    # Invoice relation
    # -------------------------------------------------------------------------
    invoice_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='estate_property_id',
        string='Invoices',
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count',
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for prop in self:
            prop.invoice_count = len(prop.invoice_ids)

    # -------------------------------------------------------------------------
    # Override action_sold — add buyer check + invoice creation
    # -------------------------------------------------------------------------
    def action_sold(self):
        for prop in self:
            # Guard 1: already sold → raise (idempotency: no silent double invoice)
            if prop.state == 'sold':
                raise UserError(
                    _('Property "%s" is already sold. No new invoice will be created.')
                    % prop.name
                )
            # Guard 2: buyer required before sold
            if not prop.buyer_id:
                raise UserError(
                    _('Please set a buyer on property "%s" before marking it as sold.')
                    % prop.name
                )

        # Let parent handle state transition and cancelled-property guard
        result = super().action_sold()

        # Create invoice for each property (now guaranteed to be in 'sold' state)
        for prop in self:
            prop._create_sale_invoice()

        return result

    # -------------------------------------------------------------------------
    # Invoice creation logic (private helper — single responsibility)
    # -------------------------------------------------------------------------
    def _create_sale_invoice(self):
        self.ensure_one()
        company = self.company_id or self.env.company

        # Find the first sales journal for this company
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', company.id)],
            limit=1,
            order='id asc',
        )
        if not journal:
            raise UserError(
                _('No sales journal found for company "%s". '
                  'Please configure one before selling properties.')
                % company.name
            )

        # Resolve income account from journal default (no hardcoded account code)
        account = journal.default_account_id
        if not account:
            # Fallback: first active income account in the company's chart
            account = self.env['account.account'].search(
                [
                    ('account_type', '=', 'income'),
                    ('company_id', '=', company.id),
                    ('deprecated', '=', False),
                ],
                limit=1,
            )
        if not account:
            raise UserError(
                _('No income account found for company "%s". '
                  'Please check your accounting configuration.')
                % company.name
            )

        commission_amount = self.selling_price * 0.06
        admin_fee_amount = 100.00

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.buyer_id.id,
            'journal_id': journal.id,
            'company_id': company.id,
            'estate_property_id': self.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': _('Real Estate Commission (6%%) — %s') % self.name,
                    'quantity': 1,
                    'price_unit': commission_amount,
                    'account_id': account.id,
                }),
                (0, 0, {
                    'name': _('Administrative Fee — %s') % self.name,
                    'quantity': 1,
                    'price_unit': admin_fee_amount,
                    'account_id': account.id,
                }),
            ],
        })
        return invoice

    # -------------------------------------------------------------------------
    # Smart button action
    # -------------------------------------------------------------------------
    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('estate_property_id', '=', self.id)],
            'context': {
                'default_estate_property_id': self.id,
                'default_move_type': 'out_invoice',
            },
        }