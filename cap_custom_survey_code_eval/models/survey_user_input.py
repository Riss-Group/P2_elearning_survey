import xmlrpc.client
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
from cryptography.fernet import Fernet
import base64
import os

_logger = logging.getLogger(__name__)

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    key = fields.Char(string='Encryption Key', readonly=True)  # Store the encryption key

    def _generate_key(self):
        """Generate a key for encryption."""
        key = Fernet.generate_key()
        return key

    def _encrypt_password(self, password):
        """Encrypt the password using Fernet symmetric encryption."""
        key = self._generate_key()  # Generate a new key
        f = Fernet(key)
        encrypted_password = f.encrypt(password.encode('utf-8'))

        # Store the key
        self.key = base64.urlsafe_b64encode(key).decode('utf-8')  # Store key as a string

        return encrypted_password.decode('utf-8')  # Return the encrypted password

    def _decrypt_password(self, encrypted_password):
        """Decrypt the password stored in value_char_box."""
        if isinstance(encrypted_password, list):
            encrypted_password = encrypted_password[0]  # Assuming you want the first item

        key = base64.urlsafe_b64decode(self.key.encode('utf-8'))  # Retrieve the key
        f = Fernet(key)
        decrypted_password = f.decrypt(encrypted_password.encode('utf-8'))
        return decrypted_password.decode('utf-8')

    def _connect_to_client_db(self, url, db, username, password):
        """ Connect to the client's database via XML-RPC """
        if not isinstance(url, str) or not url:
            raise UserError(_("The connection URL is invalid or not defined. Please provide a correct URL."))

        if not url.startswith("http://") and not url.startswith("https://"):
            raise UserError(
                _("The connection URL must start with 'http://' or 'https://'. The provided URL is: %s" % url))

        try:
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, username, password, {})
            if not uid:
                raise UserError(
                    _("Unable to authenticate to the client's database. Please check the login information."))

            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            return models, uid

        except OSError as e:
            _logger.error("Error connecting to the client's database: %s", e)
            raise UserError(_("Error connecting to the client's database: %s" % str(e)))

    def _get_answer_by_param_type(self, param_type):
        """ Retrieve the answer to a specific question by its param_type """
        answer_line = self.user_input_line_ids.filtered(lambda line: line.question_id.param_type == param_type)
        if answer_line:
            return answer_line[0].value_char_box or ''
        return ''

    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        # Search for old answers
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id)
        ])

        if question.param_type == 'password':
            # Encrypt the password before saving it
            encrypted_password = self._encrypt_password(answer)
            answer = encrypted_password  # Use the encrypted password for saving

        if question.question_type == 'code':
            # Retrieve connection details from the answers using param_type
            base_url = self._get_answer_by_param_type('base_url')
            db_name = self._get_answer_by_param_type('db_name')
            username = self._get_answer_by_param_type('user')
            encrypted_password = self._get_answer_by_param_type('password')

            if isinstance(encrypted_password, list):
                password = encrypted_password[0]
            else:
                password = encrypted_password

            # Decrypt the password before using it
            password = self._decrypt_password(password)

            _logger.info("Retrieved connection information: base_url=%s, db_name=%s, username=%s", base_url, db_name,
                         username)
            score = 0.0  # Default score

            try:
                # Try connecting to the client's database
                models, uid = self._connect_to_client_db(base_url, db_name, username, password)

                # If connection is successful, set score to 100
                value_boolean = False  # Default to False
                score = 100.0

                # Convert the search domain of the question
                try:
                    search_domain = eval(question.search_domain)
                    # Add user check to the domain
                    search_domain += [('create_uid', '=', self.env.user.id)]
                except Exception as e:
                    raise UserError(_("The search domain is invalid: %s" % str(e)))

                try:
                    # Perform the search on the specified model
                    records = models.execute_kw(db_name, uid, password, question.search_model, 'search',
                                                [search_domain])

                    # Determine the result based on the found records
                    if records:
                        value_boolean = True  # If records are found, the answer is True

                except Exception as e:
                    _logger.error("Error searching the client's database: %s", e)
                    raise UserError(_("Error searching the client's database: %s" % str(e)))

                old_answers.sudo().unlink()
                self.env['survey.user_input.line'].create({
                    'user_input_id': self.id,
                    'question_id': question.id,
                    'answer_type': 'numerical_box',
                    'value_numerical_box': 1 if value_boolean else 0,
                    'answer_score': score if value_boolean else 0.0,
                    'answer_is_correct': True if value_boolean else False,
                })
                return

            except UserError as e:
                _logger.error("Failed to connect to the client's database: %s", e)
                # Keep score at 0 if connection fails
                self._update_connection_scores(0.0)

                # Remove old answers and create a new answer line indicating failure
                old_answers.sudo().unlink()
                self.env['survey.user_input.line'].create({
                    'user_input_id': self.id,
                    'question_id': question.id,
                    'answer_type': 'text_box',
                    'value_text_box': 'False',
                    'answer_score': 0.0,
                })
                return

        # Store the encrypted password in value_char_box if the param_type is password
        if question.param_type == 'password':
            self.env['survey.user_input.line'].create({
                'user_input_id': self.id,
                'question_id': question.id,
                'answer_type': 'char_box',
                'value_char_box': encrypted_password,
                'answer_score': 0.0,  # You may adjust the score as needed
            })
            return

        # Call the parent method for other question types
        return super(SurveyUserInput, self)._save_lines(question, answer, comment, overwrite_existing)

    def _get_line_answer_values(self, question, answer, answer_type):
        # Call the parent method with super() to get the default values
        vals = super(SurveyUserInput, self)._get_line_answer_values(question, answer, answer_type)

        # Modify the values if the question type is 'code'
        if question.question_type == 'code':
            # Convert the answer to numerical value 1 or 0
            vals['value_numerical_box'] = 1 if answer else 0
            # Set the answer type as 'numerical_box'
            vals['answer_type'] = 'numerical_box'

        return vals

    def _update_connection_scores(self, score):
        """ Update the scores for the connection detail questions """
        connection_params = ['base_url', 'db_name', 'user', 'password']
        for param in connection_params:
            answer_line = self.user_input_line_ids.filtered(lambda line: line.question_id.param_type == param)
            if answer_line:
                answer_line.sudo().write({'answer_score': score})
