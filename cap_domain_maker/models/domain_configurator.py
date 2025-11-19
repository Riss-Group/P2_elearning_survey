# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger('')

class DomainConfigurator(models.Model):
    _name = 'domain.configurator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Domain Configurator"

    model_id = fields.Many2one('ir.model', 'Model')
    target_field_id = fields.Many2one('ir.model.fields', 'Target (field)')
    search_domain = fields.Text('Code', help='Python code corresponding')
    search_model = fields.Char('Model to apply', help='To locate the model', related='model_id.model')
    include_archived = fields.Boolean('Include Archived')
    question_title = fields.Char('Question Title')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            self.search_model = self.model_id.model

    @api.onchange('search_model', 'search_domain')
    def _onchange_search_fields(self):
        """ Automatically updates the title of the question based on search_model and search_domain. """
        if self.search_model and self.search_domain:
            # Get the model display name
            model_name = self.env['ir.model'].search([('model', '=', self.search_model)], limit=1).display_name
            # Evaluate the domain to a string for better readability
            domain_description = self._format_search_domain(self.search_model, self.search_domain)
            # Set the title using the model display name and domain description
            self.question_title = f"{model_name} with the following criteria: {domain_description}"
            _logger.info("Question Title updated to: %s", self.question_title)

    def _format_search_domain(self, search_model, search_domain):
        """ Helper method to format the search domain to a readable string using display names of fields. """
        try:
            domain = eval(search_domain)
            if isinstance(domain, list):
                formatted_domain_parts = []
                model = self.env['ir.model'].sudo().search([('model', '=', search_model)], limit=1)
                if not model:
                    return search_domain  # Return as is if the model is not found
                fields = self.env['ir.model.fields'].sudo().search([('model_id', '=', model.id)])
                field_dict = {f.name: f.field_description for f in fields}  # Dictionary of field names and descriptions

                operator_next = False
                for d in domain:
                    if isinstance(d, str) and d in ['|', '&', '!']:
                        if d == '|':
                            logical_operator = "or"
                        elif d == '&':
                            logical_operator = "and"
                        elif d == '!':
                            logical_operator = "not"
                        operator_next = True
                    elif isinstance(d, (list, tuple)) and len(d) == 3:
                        field_name = d[0]
                        operator = d[1]
                        value = d[2]
                        display_name = field_dict.get(field_name, field_name)
                        operator_desc = self._get_operator_description(operator)
                        formatted_part = f"{display_name} {operator_desc} '{value}'"

                        if operator_next and formatted_domain_parts:
                            formatted_domain_parts.append(f"{logical_operator} {formatted_part}")
                            operator_next = False
                        else:
                            formatted_domain_parts.append(formatted_part)

                formatted_string = " ".join(formatted_domain_parts).strip()
                return formatted_string

            return search_domain  # Return as is if not a list
        except Exception as e:
            _logger.error("Error while formatting search domain: %s", e)
            return search_domain  # Return as is if there's an evaluation error

    def _get_operator_description(self, operator):
        """ Helper method to convert an operator into a more human-readable format. """
        descriptions = {
            '=': 'is',
            '!=': 'is not',
            '>': 'is greater than',
            '>=': 'is greater than or equal to',
            '<': 'is less than',
            '<=': 'is less than or equal to',
            'in': 'is in',
            'not in': 'is not in',
            'ilike': 'contains',
            'not ilike': 'does not contain'
        }
        return descriptions.get(operator, operator)

    @api.model
    def create(self, vals):
        # Ensure the title is updated on creation if search_model and search_domain are present
        if vals.get('search_model') and vals.get('search_domain'):
            model_name = self.env['ir.model'].search([('model', '=', vals['search_model'])], limit=1).display_name
            domain_description = self._format_search_domain(vals['search_model'], vals['search_domain'])
            vals['question_title'] = f"{model_name} with the following criteria: {domain_description}"

        return super(DomainConfigurator, self).create(vals)
