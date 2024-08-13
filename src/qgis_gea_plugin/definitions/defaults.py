# -*- coding: utf-8 -*-
"""
    Definitions for all defaults settings
"""

PLUGIN_ICON = ":/plugins/qgis_gea_plugin/icon.png"

ANIMATION_PLAY_ICON = ":/images/themes/default/mActionPlay.svg"
ANIMATION_PAUSE_ICON = ":/images/themes/default/temporal_navigation/pause.svg"

COUNTRY_NAMES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas",
    "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin",
    "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon",
    "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia",
    "Comoros", "Congo, Democratic Republic of the", "Congo, Republic of the",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark",
    "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
    "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji",
    "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
    "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti",
    "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq",
    "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan",
    "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kosovo", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia",
    "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
    "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands",
    "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway",
    "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
    "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal",
    "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
    "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka",
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan",
    "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
    "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

ADMIN_AREAS_GROUP_NAME = "Administrative Areas"
DISTRICTS_NAME_SEGMENT = "Districts"
EXCLUSION_MASK_GROUP_NAME = "Exclusion Masks"
GOOGLE_LAYER_NAME: str = "Google Satellite (latest)"
LANDSAT_IMAGERY_GROUP_NAME = "Historical Landsat Imagery"
LANDSAT_2013_LAYER_SEGMENT = "Landsat 2013"
MASK_NAME_SEGMENT = "Mask"
RECENT_IMAGERY_GROUP_NAME = "Recent Nicfi Imagery"
SITE_GROUP_NAME = "Proposed Site Boundaries"

SITE_REPORT_TEMPLATE_NAME = "reforestation_site.qpt"

OVERVIEW_ZOOM_OUT_FACTOR = 13
DETAILED_ZOOM_OUT_FACTOR = 3

# Style for the site boundary polygon in the report
REPORT_SITE_BOUNDARY_STYLE = {
    "style": "no",
    "outline_style": "solid",
    "outline_color": "0,0,0,255",
    "outline_width": "0.7",
    "outline_width_unit": "MM",
    "joinstyle": "round"
}

REPORT_LANDSCAPE_DESCRIPTION_SUFFIX = "with and without exclusion masks and proposed site:"
