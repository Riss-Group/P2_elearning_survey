{
    'name': 'Custom Survey Code Evaluation',
    'version': '1.1',
    'category': 'Survey',
    'summary': 'Enhance survey module with code evaluation questions for training modules',
    'description': """
        This module extends the Odoo survey capabilities to include code evaluation questions, 
        enabling automated assessment of coding exercises in training surveys.
    """,
    'author': 'Jordan Momper, Captivea',
    'website': 'https://www.captivea.com',
    'license': 'LGPL-3',
    'depends': ['base', 'survey'],
    'data': [
        'views/survey_question_views.xml',
        'views/survey_survey_views.xml',
    ],
    'installable': True,
    'application': True,
    'maintainer': 'Jordan Momper',
    'support': 'support@captivea.com',
}
