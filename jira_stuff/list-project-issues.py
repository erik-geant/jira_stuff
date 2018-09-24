import json

from jira import JIRA
from jsonschema import validate


CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "type": "object",
    "properties": {
        "jira": {"type": "string"},
        "project": {"type": "string"},
        "oauth": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string"},
                "access_token_secret": {"type": "string"},
                "consumer_key": {"type": "string"},
                "private_key_filename": {"type": "string"}
            },
            "required": [
                "access_token",
                "access_token_secret",
                "consumer_key",
                "private_key_filename"
            ],
            "additionalProperties": False
        }
    },
    "required": ["jira", "project", "oauth"],
    "additionalProperties": False
}

with open('config.json') as f:
    config = json.loads(f.read())
    validate(config, CONFIG_SCHEMA)

    oauth_dict = {
        'access_token': config['oauth']['access_token'],
        'access_token_secret': config['oauth']['access_token_secret'],
        'consumer_key': config['oauth']['consumer_key']

    }
    with open(config['oauth']["private_key_filename"]) as k:
        oauth_dict['key_cert'] = k.read()

jira = JIRA(config['jira'], oauth=oauth_dict)

# # Get all projects viewable by the current user
# projects = jira.projects()

issues = {}
for issue in jira.search_issues(
                'project=%s and resolution=NULL' % config["project"]):
    issues[issue.key] = {
        # "issue": issue,
        "depends on": [],
        "is needed by": []
    }
    for link in issue.fields.issuelinks:
        if hasattr(link, "outwardIssue"):
            dep = getattr(link, "outwardIssue")
            issues[issue.key]["depends on"].append(dep.key)
        if hasattr(link, "inwardIssue"):
            dep = getattr(link, "inwardIssue")
            issues[issue.key]["is needed by"].append(dep.key)


def _print_issue_and_dependencies(issue_key, indent=0):
    if issues[issue_key]["is needed by"]:
        is_needed_by = ", is needed by:"
    else:
        is_needed_by = ""
    print("%s%s%s" % (indent*'\t', issue_key, is_needed_by))
    for dep_key in issues[issue_key]["is needed by"]:
        _print_issue_and_dependencies(dep_key, indent+1)


for issue, links in issues.items():
    if len(links["depends on"]):
        continue
    _print_issue_and_dependencies(issue)
