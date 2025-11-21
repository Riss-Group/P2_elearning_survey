# -*- coding: utf-8 -*-
{
    'name': 'CAP - Survey',
    'summary': 'manage survey changes',
    'description': ''' Features:
        - Override domain of field survey_id in slide.slide model''',
    'author': 'captivea-cga ',
    'website': 'https://captivea.com',
    'license': 'LGPL-3',
    'category': 'Captivea/',
    'version': '19.0.0.0',
    'depends': ['base','website_slides_survey'],
    'data': [
        "views/slide_slide_views_inherit.xml",
        ],
    'application': True,
    'installable': True,
    'auto_install': False,
}