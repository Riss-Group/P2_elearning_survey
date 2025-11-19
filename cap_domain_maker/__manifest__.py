# -*- coding: utf-8 -*-
{
    'name': 'CAP - Domain Maker ',
    'summary': 'Transform logical rule in a python domain. Just have to copy/paste to include in your python file',
    'description': ' awesome modul ',
    'author': 'captivea-cga ',
    'website': 'https://captivea.com',
    'license': 'LGPL-3',
    'category': 'Captivea/',
    'version': '17.0.0.2',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/domain_menus.xml',
        'views/domain_views.xml',
        ],
    'application': True,
    'installable': True,
    'auto_install': False,

}
