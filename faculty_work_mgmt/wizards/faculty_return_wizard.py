# -*- coding: utf-8 -*-
"""Wizard for requesting revision / return of a research or other work.
Used by Trưởng khoa / Lãnh đạo khi nhấn "Yêu cầu Chỉnh sửa / Trả lại".
"""

from odoo import models, fields, api, _


class FacultyReturnWizard(models.TransientModel):
    _name = 'faculty.return.wizard'
    _description = 'Yêu cầu chỉnh sửa / trả lại sản phẩm'

    reason = fields.Text(string='Lý do trả lại', required=True)
    # Participants for research work
    participant_ids = fields.Many2many(
        comodel_name='faculty.research.participant',
        string='Thành viên cần chỉnh sửa (NCKH)'
    )
    # Participants for other work (different model)
    other_participant_ids = fields.Many2many(
        comodel_name='faculty.other.participant',
        string='Thành viên cần chỉnh sửa (Hoạt động khác)'
    )

    def action_return(self):
        """Set need_revision flag, revert state to draft and notify participants."""
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if not active_ids or not active_model:
            return {'type': 'ir.actions.act_window_close'}
        records = self.env[active_model].browse(active_ids)
        # Determine which participant set to use based on model
        participants = self.participant_ids if active_model == 'faculty.research.work' else self.other_participant_ids
        for rec in records:
            # Mark selected participants as needing revision
            for p in participants:
                if hasattr(p, 'need_revision'):
                    p.need_revision = True
            # Revert record to draft
            rec.state = 'draft'
            # Post message to chatter
            rec.message_post(body=_('Yêu cầu chỉnh sửa lại. Lý do: %s') % self.reason)
            # Schedule activity for each selected participant
            for p in participants:
                partner = getattr(p, 'lecturer_id', None)
                if partner:
                    partner = partner.partner_id if hasattr(partner, 'partner_id') else partner
                    if partner:
                        rec.activity_schedule(
                            'mail.activity_data_warning',
                            summary=_('Cần chỉnh sửa sản phẩm'),
                            note=self.reason,
                            user_id=partner.id,
                        )
        return {'type': 'ir.actions.act_window_close'}

