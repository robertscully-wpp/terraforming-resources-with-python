import logging
import requests
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter, description='Process some integers.')
parser.add_argument('--bearer_token', type=str, help='Bearer token for TfE/TfC')
parser.add_argument('--hostname', type=str, help='URL for target terraform')
parser.add_argument('--org', type=str, help='Organization to interact with', nargs='*', default=[], required=False)
parser.add_argument('command', help='workspaces or teams', nargs='?', choices=('workspaces', 'teams'))

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

def generate_headers(bearer_token):
    headers={'Authorization': 'BEARER ' + bearer_token}
    return headers

def generate_api_url(hostname, api_version='v2'):
    url =f'https://{hostname}/api/{api_version}'
    return url

def get_organization_ids(hostname, headers):
    orgs=requests.get(url=f'{hostname}/organizations?page%5Bsize%5D=100', headers=headers).json().get('data')
    return [org.get('id') for org in orgs]


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
    elif args.command=='teams':
        print ("teams is not implemented.")
    else:
        print ("no command applied")
        exit(1)

if __name__ == "__main__":
    main()
