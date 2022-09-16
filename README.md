# terraforming-resources-with-python
Python application for reading from a Terraform Enterprise or Terraform Cloud API, and produce terraform resources for the tfe provider.

# Get all the teams and their users
python3 generate_users_teams.py --bearer_token=$TF_TOKEN --hostname=iacdev.wpp.cloud --org=WPP-Open-Central teams

# Get all the users
python3 generate_users_teams.py --bearer_token=$TF_TOKEN --hostname=iacdev.wpp.cloud --org=WPP-Open-Central users
