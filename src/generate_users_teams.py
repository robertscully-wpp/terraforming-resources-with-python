from email import header
import logging
from xml import dom
import requests
import argparse
import csv

parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter, description='Export TfE/TfC resources in a form to be managed by tfe provider.')
parser.add_argument('--bearer_token', type=str, help='Bearer token for TfE/TfC')
parser.add_argument('--hostname', type=str, help='URL for target terraform')
parser.add_argument('--org', type=str, help='Organization to interact with', nargs='*', default=[], required=False)
parser.add_argument('command', help='workspaces, teams or users', nargs='?', choices=('workspaces', 'teams', 'users'))
users_dict={}
WORKSPACE_HEREDOC="""resource "tfe_workspace" "{workspace_name}" {{
  name         = "{workspace_name}"
  organization = "wpp-wppit-dev"
  execution_mode = "{execution_mode}"
  terraform_version = "{terraform_version}"
  tag_names    = [{tags}]
}}
"""

REPORT_HEREDOC="""#########################
  Total: {count} {resource}
##############################
"""

def export_users_csv(filename,data):
    # open file in write mode
    with open(filename, 'w') as fp:
        for item in data:
            # write each item on a new line
            fp.write("%s\n" % item)

def generate_headers(bearer_token):
    headers={'Authorization': 'BEARER ' + bearer_token}
    return headers

def generate_api_url(hostname, api_version='v2'):
    url =f'https://{hostname}/api/{api_version}'
    return url

def get_organization_ids(hostname, headers):
    orgs=requests.get(url=f'{hostname}/organizations?page%5Bsize%5D=100', headers=headers).json().get('data')
    return [org.get('id') for org in orgs]

def verified_email_domain(email):
    # Verifies if email account is an OpCo
    domain=email.split("@")[-1]
    if domain in ['groupm.com','groupm.tech','mediacom.com','wpp.com','hashicorp.com']:
        return True
        
def get_users(hostname, headers):
    users=requests.get(url=f'{hostname}/admin/users?filter[suspended]=false', headers=headers).json().get('data')
    verified_users=[]
    for user in users:
        if verified_email_domain (user['attributes']['email']) :
            verified_users.append(user['id']+","+user['attributes']['email'])
    return verified_users

def get_user(hostname, headers,user_id):
    user=requests.get(url=f'{hostname}/users/{user_id}', headers=headers).json().get('data')
    return user

    
def get_teams(hostname, headers):
    teams=requests.get(url=f'{hostname}/organizations/WPP-Open-Central/teams', headers=headers).json().get('data')
    verified_teams=[]
    for team in teams:
        verified_teams.append(team['id']+","+team['attributes']['name']+","+str(team['attributes']['users-count'])+","+str(len(team['relationships']['users']['data'])))
        if len(team['relationships']['users']['data']) > 0:
             for user in team['relationships']['users']['data']:
                user_details=get_user(hostname,headers,user['id'])
                verified_teams.append(user['id']+","+user['type']+","+user_details['attributes']['username'])
    return verified_teams

def get_all_users_no_filter(hostname, headers):
    users=requests.get(url=f'{hostname}/admin/users', headers=headers).json().get('data')
    verified_users=[]
    for user in users:
        verified_users.append(user['id']+","+user['attributes']['email'])
    return verified_users

def get_all_users_dict(hostname, headers):
    users=requests.get(url=f'{hostname}/admin/users', headers=headers).json().get('data')
    for user in users:
        users_dict[user['id']]=user['attributes']['email']
    return users_dict

def get_workspaces_for_org(hostname, headers, organization):
    workspaces=[]
    orgs=requests.get(url=f'{hostname}/organizations/{organization}/workspaces?page%5Bsize%5D=20', headers=headers).json()
    workspaces.extend(orgs.get('data'))
    while(orgs.get('meta').get('pagination').get('next-page') is not None):
        orgs=requests.get(url=orgs.get('links').get('next'), headers=headers).json()
        workspaces.extend(orgs.get('data'))
    return workspaces

def generateTerraformWorkspacesFile(workspaces):
    for workspace in workspaces:
        print(WORKSPACE_HEREDOC.format(
            workspace_name=workspace['attributes']['name'],
            execution_mode=workspace['attributes']['execution-mode'],
            terraform_version=workspace['attributes']['terraform-version'],
            tags=', '.join(['"'+tag+'"' for tag in workspace['attributes']['tag-names']])))

def main():
    args=parser.parse_args()
    headers=generate_headers(args.bearer_token)
    url=generate_api_url(args.hostname)
    organization_ids=args.org if len(args.org) >0 else get_organization_ids(url, headers)

    if args.command=='workspaces':
        workspaces=[]
        for org_id in organization_ids:
            workspaces.extend(get_workspaces_for_org(url, headers, org_id))
        generateTerraformWorkspacesFile(workspaces)
        print(REPORT_HEREDOC.format(count=len(workspaces), resource='workspaces'))
    elif args.command=='users':
        users=[]
        users=get_users(url, headers)
        export_users_csv ('all_active_users.csv',users)
        print(REPORT_HEREDOC.format(count=len(users), resource='users'))
        
        users=[]
        users=get_all_users_no_filter(url, headers)
        export_users_csv ('all_users_no_filter.csv',users)
        print(REPORT_HEREDOC.format(count=len(users), resource='users'))
    elif args.command=='teams':
        teams=[]
        teams=get_teams(url, headers)
        export_users_csv ('teams-by-users.csv',teams)
        print(REPORT_HEREDOC.format(count=len(teams), resource='teams'))
    else:
        print ("no command applied")
        exit(1)

if __name__ == "__main__":
    main()