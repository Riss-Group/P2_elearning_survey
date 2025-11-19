from odoo import models, fields, api, _
import logging
_logger = logging.getLogger('')

class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    question_type = fields.Selection(
        selection_add=[('code', 'Code Question')],
        ondelete={'code': 'cascade'}  # Change ondelete policy to 'cascade' or another valid option
    )
    search_model = fields.Char(string="Search Model",
                               help="Technical name of the Odoo model to perform the search on, for example 'res.partner'")
    search_domain = fields.Char(string="Search Domain",
                                help="Search domain to apply, for example [('name', '=', 'Test Contact')]")
    param_type = fields.Selection([
        ('base_url', "Database URL"),
        ('db_name', "Database Name"),
        ('user', "User"),
        ('password', "Password"),
    ], string="Parameter Type")

    param_type_checklist = fields.Html(string="Parameter Type Checklist", compute='_compute_param_type_checklist')
    all_params_covered = fields.Boolean(string="All Parameters Covered", compute='_compute_all_params_covered')

    @api.model
    def create(self, vals):
        if vals.get('question_type') == 'code':
            vals['answer_numerical_box'] = 1
            vals['is_scored_question'] = True
            vals['answer_score'] = 100
        return super(SurveyQuestion, self).create(vals)

    def write(self, vals):
        if 'question_type' in vals and vals['question_type'] == 'code':
            vals['answer_numerical_box'] = 1
            vals['is_scored_question'] = True
            vals['answer_score'] = 100
        return super(SurveyQuestion, self).write(vals)

    @api.depends('survey_id.question_ids')
    def _compute_param_type_checklist(self):
        required_param_types = {
            'base_url': 'Base URL',
            'db_name': 'Base name',
            'user': 'Email',
            'password': 'Password',
        }

        for question in self:
            covered_param_types = question.survey_id.question_ids.mapped('param_type')
            checklist_html = '<ul style="list-style-type:none;">'
            all_checked = True

            for param_type, label in required_param_types.items():
                if param_type in covered_param_types:
                    checklist_html += f'<li>✔️ {label}</li>'
                else:
                    checklist_html += f'<li>❌ {label}</li>'
                    all_checked = False

            checklist_html += '</ul>'
            question.param_type_checklist = checklist_html
            question.all_params_covered = all_checked

    @api.depends('param_type_checklist')
    def _compute_all_params_covered(self):
        for question in self:
            question.all_params_covered = '❌' not in question.param_type_checklist


    @api.onchange('model_id')
    def _onchange_model_id(self):
        for record in self:
            if record.model_id:
                record.search_model = self.model_id.model

    @api.onchange('param_type')
    def _onchange_param_type(self):
        """Automatically set the description based on the param_type."""
        if self.param_type == 'base_url':
            self.description = "You have to copy/paste the URL without the '/' at the end."
        elif self.param_type == 'db_name':
            self.description = "Please enter the exact database name as configured on the server. <br/> To do so, right-click on your odoo main menu, select Inspect, select the cursor on the top-left of the window.<br/> Target the yellow highlighted text on the top-right corner, right under your username. <br/> Double click on the 'mark' line, then on the 'i' line and finally copy the displayed text"

        elif self.param_type == 'user':
            self.description = "Enter your Odoo email address."
        elif self.param_type == 'password':
            self.description = "Enter your Odoo password."