from odoo import models, fields, api

class Survey(models.Model):
    _inherit = 'survey.survey'

    base_url = fields.Char(string="Database URL")
    db_name = fields.Char(string="Database Name")
    user = fields.Char(string="User")
    password = fields.Char(string="Password")
    param_type_checklist = fields.Html(string="Parameter Type Checklist", compute='_compute_param_type_checklist')

    @api.depends('question_ids')
    def _compute_param_type_checklist(self):
        required_param_types = {
            'base_url': 'Base URL',
            'db_name': 'DB Name',
            'user': 'Email',
            'password': 'Password',
        }

        for survey in self:
            covered_param_types = survey.question_ids.mapped('param_type')
            checklist_html = '<ul style="list-style-type:none;">'

            for param_type, label in required_param_types.items():
                if param_type in covered_param_types:
                    checklist_html += f'<li>✔️ {label}</li>'
                else:
                    checklist_html += f'<li>❌ {label}</li>'

            checklist_html += '</ul>'
            survey.param_type_checklist = checklist_html

    @api.model
    def store_params_from_responses(self, user_input):
        # Iterate through all the user's response lines
        for line in user_input.user_input_line_ids:
            question = line.question_id
            if question.param_type:
                if question.param_type == 'base_url':
                    self.base_url = line.value_text
                elif question.param_type == 'db_name':
                    self.db_name = line.value_text
                elif question.param_type == 'user':
                    self.user = line.value_text
                elif question.param_type == 'password':
                    self.password = line.value_text

    def _check_and_compute_scores(self):
        for user_input in self.user_input_ids:
            for line in user_input.user_input_line_ids:
                if line.question_id.question_type == 'code':
                    if line.answer_score == 100.0:
                        # Mark the answer as correct
                        line.answer_is_correct = True
                    else:
                        # Mark the answer as incorrect
                        line.answer_is_correct = False
                else:
                    # Default behavior for other question types
                    line.is_correct = line._compute_is_correct()