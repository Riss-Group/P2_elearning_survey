from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero

class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    def _check_answer_type_skipped(self):
        for line in self:
            # Standard validation to check if a question is either skipped or answered
            if (line.skipped == bool(line.answer_type)):
                raise ValidationError(_('A question can either be skipped or answered, not both.'))

            # Allow 0 for numerical type
            if line.answer_type == 'numerical_box' and float_is_zero(line['value_numerical_box'], precision_digits=6):
                continue

            # Check for 'suggestion' type answers
            if line.answer_type == 'suggestion':
                field_name = 'suggested_answer_id'

            # Adaptation for 'code' type questions treated as 'numerical_box'
            elif line.answer_type == 'numerical_box' and line.question_id.question_type == 'code':
                field_name = 'value_numerical_box'

            # Other answer types
            elif line.answer_type:
                field_name = 'value_%s' % line.answer_type
            else:  # Skipped
                field_name = False

            # Check for the presence of the answer based on the field type
            if field_name and not line[field_name]:
                raise ValidationError(_('The answer must be in the right type'))
