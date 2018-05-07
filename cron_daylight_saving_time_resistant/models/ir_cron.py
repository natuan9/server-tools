# -*- coding: utf-8 -*-
# © 2018 Akretion - Raphaël Reverdy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pytz
from datetime import datetime

from openerp import api, fields, models
from openerp.osv import fields as osv_fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.base.ir.ir_cron import _intervalTypes
_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    daylight_saving_time_resistant = fields.Boolean(
        help="Adjust interval to run at the same hour after and before"
        "daylight saving time change. It's used twice a year")

    def _process_job(cls, job_cr, job, cron_cr):
        """Add or remove the Daylight saving offset when needed."""
        with api.Environment.manage():
            now = osv_fields.datetime.context_timestamp(
                job_cr, job['user_id'], datetime.now())
            nextcall = osv_fields.datetime.context_timestamp(
                job_cr, job['user_id'],
                datetime.strptime(
                    job['nextcall'],
                    DEFAULT_SERVER_DATETIME_FORMAT)
            )
            delta = _intervalTypes[job['interval_type']](
                job['interval_number'])

            numbercall = job['numbercall']
            future_call = nextcall
            while future_call < now and numbercall:
                if numbercall > 0:
                    numbercall -= 1
                if numbercall:
                    future_call += delta

            after_offset = future_call.utcoffset()
            before_offset = nextcall.utcoffset()

            diff_offset = after_offset - before_offset

            if diff_offset and job['daylight_saving_time_resistant']:
                if nextcall < now and numbercall:
                    nextcall -= diff_offset
                    modified_next_call = fields.Datetime.to_string(
                        nextcall.astimezone(pytz.UTC))
                    job['nextcall'] = modified_next_call
        super(IrCron, cls)._process_job(job_cr, job, cron_cr)
