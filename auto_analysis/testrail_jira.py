import base64
import json
import requests
import datetime
import logging
import os
import csv
import yaml
import sys
import argparse
import urllib3
import re
try:
    from jira.client import JIRA
    from jira.client import GreenHopper
except ImportError:
    print("Errorinfo:please install jira first")
    sys.exit(1)

# Testrail variables
PROJECT_FFV = 1
TEST_SUITE_ATOM = 13
TEST_SUITE_UEFI = 9
TEST_SUITE_BMC = 2
TEST_SUITE_DAE_ATOM = 1478
TEST_SUITE_DAE_BMC = 1477
CI_JIRA_URL = 'https://jira.cec.lab.emc.com:443'
testrail_url = r'https://psetrprd001.corp.emc.com/testrail'

"""
testrail_jira.log format
infrasim@infrasim:~$ cat .testrail_jira.conf
jira:
    url:   https://jira.cec.lab.emc.com:8443
    user_name:  111111
    user_key: xxxxxxxxx
"""
urllib3.disable_warnings()


def get_jira_config():
    """
    get jira config from config file, contain url , name, password
    """
    jira_config = {}
    conf_path = '{}/.testrail_jira.conf'.format(os.path.expanduser('~'))
    if os.path.isfile(conf_path):
        with open(conf_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        print("No Confluence config file.")
        sys.exit(1)

    jira_config['url'] = config['jira'].get('url')
    jira_config['user'] = config['jira'].get('user_name')
    jira_config['pwd'] = config['jira'].get('user_key')
    return jira_config


file_path = '{}/testrail_jira.log'.format(os.path.expanduser('~'))
logging.basicConfig(level=logging.DEBUG,
                    filename=file_path)

jira_config = get_jira_config()
jira_pwd = (base64.b64decode(jira_config['pwd'])).decode('utf-8')
myjira = JIRA(
    jira_config['url'],
    basic_auth=(jira_config['user'], (base64.b64decode(jira_config['pwd'])).decode('utf-8')),
    logging=True,
    validate=True,
    async_=True,
    async_workers=20,
    options={'verify': False},
)

greenhopper = GreenHopper(
    options={'server': CI_JIRA_URL, 'verify': False},
    basic_auth=(jira_config['user'], jira_pwd)
)


class Testclient(object):
    """
    testrail client, send request, and get info and data
    """
    def __init__(self, base_url):
        self.user = 'atom.dev@emc.com'
        self.password = '111111'
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'

    def send_get(self, uri, filepath=None):
        """Issue a GET request (read) against the API.

        Args:
            uri: The API method to call including parameters, e.g. get_case/1.
            filepath: The path and file name for attachment download; used only
                for 'get_attachment/:attachment_id'.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('GET', uri, filepath)

    def get_cases(self, project_id, case_filter=None):
        rest_uri = 'get_cases/{}{}'.format(project_id, case_filter)
        return self.send_get(rest_uri)

    def get_case(self, case_id):
        rest_uri = 'get_case/{}'.format(case_id)
        return self.send_get(rest_uri)

    def send_post(self, uri, data):
        """Issue a POST request (write) against the API.

        Args:
            uri: The API method to call, including parameters, e.g. add_case/1.
            data: The data to submit as part of the request as a dict; strings
                must be UTF-8 encoded. If adding an attachment, must be the
                path to the file.

        Returns:
            A dict containing the result of the request.
        """
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri
        logging.debug(url)
        if sys.version_info[0] < 3:
            auth = base64.b64encode('%s:%s' % (self.user, self.password))
            payload = bytes(json.dumps(data))
        else:
            auth = str(
                base64.b64encode(
                    bytes('%s:%s' % (self.user, self.password), 'utf-8')
                ),
                'ascii'
            ).strip()
            payload = bytes(json.dumps(data), 'utf-8')
        headers = {'Authorization': 'Basic ' + auth}

        if method == 'POST':
            if uri[:14] == 'add_attachment':    # add_attachment API method
                files = {'attachment': (open(data, 'rb'))}
                response = requests.post(url, headers=headers, files=files, verify=False)
                files['attachment'].close()
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, data=payload, verify=False)
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers, verify=False)

        if response.status_code > 201:
            try:
                error = response.json()
            except Exception:     # response.content not formatted as JSON
                error = str(response.content)
                raise Exception('TestRail API returned HTTP %s (%s)' % (response.status_code, error))
        else:
            if uri[:15] == 'get_attachment/':   # Expecting file, not JSON
                try:
                    open(data, 'wb').write(response.content)
                    return (data)
                except Exception:
                    return ("Error saving attachment.")
            else:
                return response.json()


def same_time_check(test_createtime, expect_date):
    """
    check if test_createtime is the same with expect date
    """
    timestamp = datetime.datetime.fromtimestamp(test_createtime)
    if timestamp.date() == expect_date:
        return True
    else:
        return False


def get_suite_mapping_issue_info(suite, tag=None):
    """
    bmc epic bmc :ATOM-3361
    uefi epic bios: ATOM-3360
    add dae_atom to epic ATOM-4496: Fornax Adaption
    add dae_bmc to epic ATOM-4581: DAE New Case
    DAE New Case - Redfish :ATOM-5157
    DAE New Case - SES: ATOM-5158
    tag: redfish:[6], Ses : [7]
    """
    issue_info = {}
    if suite == TEST_SUITE_DAE_ATOM:
        issue_info['epic'] = 'ATOM-4496'
        issue_info['components'] = 'DAE script'
    elif suite == TEST_SUITE_DAE_BMC:
        issue_info['components'] = 'DAE script'
        if tag == [6]:
            issue_info['epic'] = 'ATOM-5157'
        elif tag == [7]:
            issue_info['epic'] = 'ATOM-5158'
        else:
            issue_info['epic'] = 'ATOM-4581'
    elif suite == TEST_SUITE_UEFI:
        issue_info['components'] = 'BIOS Script'
        issue_info['epic'] = 'ATOM-3360'
    elif suite == TEST_SUITE_BMC:
        issue_info['epic'] = 'ATOM-3466'
        issue_info['components'] = 'BMC Script'
    else:
        raise Exception('now we do not support suite :{}'.format(suite))
    return issue_info


def get_case_id_from_issue(issue_info):
    """
    get case id from issue info
    """
    line = issue_info.fields.summary
    searchObj = re.search('\[C([0-9]{2,20})\]', line, re.M|re.I)
    if searchObj:
        return searchObj.group(1)
    else:
        return None


def check_case_create_issue(case, timestamp, dayissues):
    """
    1: filter cases and find if there is case's created time match
    2: check if case could automatable , automate value :
    unknown:1  No:2  Yes:3
    3: check duplicate
    """

    if not (same_time_check(case['created_on'], timestamp) or
            same_time_check(case['updated_on'], timestamp)):
        return False
    if not case['custom_ffv_automatable'] == 3:
        return False
    for issue in dayissues:
        if str(case['id']) == get_case_id_from_issue(issue):
            return False
    # csum = '[C{}]-{}'.format(case['id'], case['title'])
    dup_check = "project = atom  and summary ~ C{}".format(case['id'])
    sameissue = get_issues_by_jql(dup_check)
    # import pdb
    # pdb.set_trace()
    for issue in sameissue:
        if str(case['id']) == get_case_id_from_issue(issue):
            return False
    return True


def check_new_case_create_issue(cases, timestamp, suite, issuesdata):
    """
    filter cases and find if there is case's created time match
    add dae_atom to epic ATOM-4496: Fornax Adaption
    add dae_bmc  to epic ATOM-4581: DAE New Case
    check if case could automatable , automate value :
    unknown:1  No:2  Yes:3
    """
    for case in cases:
        case_tr_id = case['id']
        if check_case_create_issue(case, timestamp, issuesdata):
            try:
                summary = '[C{}]-{}'.format(case['id'], case['title'])
                logging.debug(summary)
                description = case.get('custom_preconds')
                if not description:
                    description = 'test case script'
                case_tag = case.get('custom_ffv_cpu_specific')
                issue_info = get_suite_mapping_issue_info(suite, case_tag)
                issue_dict_info = {
                    'project': {'key': 'ATOM'},
                    'summary': summary,
                    'description': description,
                    'issuetype': {'name': 'Feature'},
                    'customfield_10006': 2,
                    'components': [{'name': issue_info['components']}],
                    'labels': ['atom', 'autogenerate'],
                }
                new_issue = myjira.create_issue(fields=issue_dict_info)
                logging.debug('case {} : create jira story success {}'.format(case_tr_id, new_issue.key))
                write_isssue_info_to_csv(new_issue, timestamp.strftime("%Y-%m-%d"), case_tr_id)
                issue_list = []
                issue_list.append(new_issue.key)
                # ATOM-5159 EOL
                epic_link = issue_info['epic']
                greenhopper.add_issues_to_epic(epic_link, issue_list)
            except Exception as errorinfo:
                logging.error('case {} : create jira story fail on {}'.format(case_tr_id, timestamp))
                logging.error(errorinfo)


def filter_testrail_and_create_issue(day, issue_data):
    """
    filter all suites and check if there is cases created on the day
    TODO: add TEST_SUITE_ATOM
    """
    testrail_obj = Testclient(testrail_url)
    suites = [TEST_SUITE_BMC, TEST_SUITE_UEFI, TEST_SUITE_DAE_ATOM, TEST_SUITE_DAE_BMC]
    for suite in suites:
        case_filter = '&suite_id={}'.format(suite)
        cases = testrail_obj.get_cases(PROJECT_FFV, case_filter)
        check_new_case_create_issue(cases, day, suite, issue_data)


def write_isssue_info_to_csv(issuedata, dateday, case_id):
    """
    write issue info to csv file
    """
    filename = 'issue_create_by_tool.csv'
    logging.debug('add case {} to {}'.format(case_id, filename))
    if not os.path.isfile(filename):
        with open(filename, mode='w') as csv_file:
            field_names = ['case_id', 'issue_key', 'date', 'summary']
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()
            writer.writerow({'case_id': case_id,
                             'issue_key': issuedata.key,
                             'date': dateday,
                             'summary': issuedata.fields.summary})
    else:
        with open(filename, mode='a') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow([case_id, issuedata.key, dateday, issuedata.fields.summary])


def get_day_issue_info(date=None):
    """
    get all issues create on 'date'
    """
    if not date:
        timestamp = datetime.datetime.today()
        strdate_time = timestamp.strftime("%Y-%m-%d")
    JQL = "project = atom  and created >= {} and Status != completed".format(strdate_time)
    issuedata = myjira.search_issues(JQL)
    return issuedata


def get_cases_id_list(input, source='jira'):
    # source: jira or testrail
    # input: jira issues or testrail cases
    if source == 'jira':
        caseid_list = [int(get_case_id_from_issue(i)) for i in input if get_case_id_from_issue(i)]
    else:
        caseid_list = [i['id'] for i in input ]
    return caseid_list



def get_issues_by_jql(jql):
    if not jql:
        return None
    issuedata = myjira.search_issues(jql)
    return issuedata

class sync_cases_soluction(object):
    def get_jira_not_completed_cases_in_atomsuits(self):
        testrail_obj = Testclient(testrail_url)
        case_filter = '&suite_id={}'.format(TEST_SUITE_ATOM)
        automated_cases = testrail_obj.get_cases(PROJECT_FFV, case_filter)
        print (len(automated_cases))
        automated_cases_id_list = []
        for caseone in automated_cases:
            automated_cases_id_list.append(caseone['id'])
        #print(automated_cases_id_list)
        not_complete_case = {}
        for casetestrail in automated_cases_id_list:
            jql = 'project = ATOM and summary ~ C{} AND status != Completed AND "Epic Link" in (ATOM-4581,ATOM-4496,ATOM-5912)'.format(casetestrail)
            #print(jql)
            issues = get_issues_by_jql(jql)
            
            if len(issues) ==0:
                continue
            not_complete_case[str(issues[0].key)] = ['C{}'.format(casetestrail), str(issues[0].fields.status.name)]
            #issues[0].fields.status.name
            #print(issues)
        print (not_complete_case)
        print (len(not_complete_case))
        
    def get_need_auto_cases_not_created_in_jira(self):
        testrail_obj = Testclient(testrail_url)
        test_suites = [TEST_SUITE_BMC, TEST_SUITE_UEFI]
        automatable_cases = []
        automatable_cases_not_in_jira = []
        automatable_cases_in_jira_completed = {}
        for suite in test_suites:
            case_filter = '&suite_id={}'.format(suite)
            tr_cases = testrail_obj.get_cases(PROJECT_FFV, case_filter)
            print('all cases in suites {} total count is {}'.format(suite, len(tr_cases)))
            for tr_case in tr_cases:
                if tr_case['custom_ffv_need_physical_access'] == 2 and tr_case['custom_ffv_automatable'] == 3:
                    automatable_cases.append(tr_case['id'])
                    jql = 'project = ATOM and summary ~ C{} AND "Epic Link" in (ATOM-4581,ATOM-4496,ATOM-5912)'.format(tr_case['id'])
                    issues = get_issues_by_jql(jql)
                    if len(issues) == 0:
                        automatable_cases_not_in_jira.append(tr_case['id'])
                    else:
                        for issue in issues:
                            if str(issue.fields.status.name) == 'Completed':
                                automatable_cases_in_jira_completed[issue.key] = tr_case['id']
        print('automatable cases in BMC and UEFI suites total count is {}'.format(len(automatable_cases)))
        print('automatable cases is ---------------------------------')
        print(automatable_cases)
        print('automatable cases in BMC and UEFI suites but not in jira count is {}'.format(len(automatable_cases_not_in_jira)))
        print('automatable cases in BMC and UEFI suites but not in jira---------------------')
        print(automatable_cases_not_in_jira)
        print('automatable cases in BMC and UEFI suites and in jira completed total count is {}'.format(len(automatable_cases_in_jira_completed)))
        print(automatable_cases_in_jira_completed)

    def sync_cases(self, suite, jira_epic):
        jql = "project = atom and 'Epic Link' = {} and Status != 'completed'".format(jira_epic)
        issues = get_issues_by_jql(jql)
        testrail_obj = Testclient(testrail_url)
        case_filter = '&suite_id={}'.format(suite)
        cases = testrail_obj.get_cases(PROJECT_FFV, case_filter)

        jira_cases = get_cases_id_list(issues)
        valid_cases = []
        for single_case in cases:
            if single_case['custom_ffv_need_physical_access'] == 2 and single_case['custom_ffv_automatable'] == 3:
                # six platform we care
                if set(single_case['custom_ffvplatform']).intersection([12, 13, 15 ,17, 18, 19]):
                    valid_cases.append(single_case)
        testrail_cases = get_cases_id_list(valid_cases, 'testrail')
        diff_cases = (set(testrail_cases).difference(set(jira_cases)))
        same_cases = (set(testrail_cases).intersection(set(jira_cases)))
        print(diff_cases)
        print("diff case length is {}".format(len(diff_cases)))
        print("----------------------")
        print(same_cases)
        print("----------------------")
        print(jira_cases)
        print("----------------------")
        print(set(jira_cases).difference(set(same_cases)))
        print('33333333333333333333333333333333333')
        return [i for i in valid_cases if i['id'] in diff_cases]

    def create_cases_jira_issues(self, suite, cases):
        # cases list of case id
        for case in cases:
            case_tr_id = case['id']
            try:
                summary = '[C{}]-{}'.format(case['id'], case['title'])
                logging.debug(summary)
                description = case.get('custom_preconds')
                if not description:
                    description = 'test case script'
                case_tag = case.get('custom_ffv_cpu_specific')
                issue_info = get_suite_mapping_issue_info(suite, case_tag)
                issue_dict_info = {
                    'project': {'key': 'ATOM'},
                    'summary': summary,
                    'description': description,
                    'issuetype': {'name': 'Feature'},
                    'customfield_10006': 2,
                    'components': [{'name': issue_info['components']}],
                    'labels': ['atom', 'autogenerate'],
                }
                new_issue = myjira.create_issue(fields=issue_dict_info)
                logging.debug('case {} : create jira story success {}'.format(case_tr_id, new_issue.key))
                write_isssue_info_to_csv(new_issue, case['created_on'], case_tr_id)
                issue_list = []
                issue_list.append(new_issue.key)
                # ATOM-5159 EOL
                epic_link = issue_info['epic']
                greenhopper.add_issues_to_epic(epic_link, issue_list)
            except Exception as errorinfo:
                logging.error('case {} : create jira story fail on {}'.format(case_tr_id, timestamp))
                logging.error(errorinfo)



if __name__ == '__main__':
    #sync_cases_obj = sync_cases_soluction()
    #sync_cases_obj.get_jira_not_completed_cases_in_atomsuits()
    #sync_cases_obj.get_need_auto_cases_not_created_in_jira()
    
    parser = argparse.ArgumentParser(description='sync testrail cases to jira tool')

    parser.add_argument("-d", "--date", type=str,
                        help="date of testrail update time, example 2020-3-22")

    commandList = parser.parse_args()
    if not commandList.date:
        timestamp = datetime.datetime.today()
    else:
        timestamp = datetime.datetime.strptime(commandList.date, '%Y-%m-%d')
    timestamp = timestamp.date()
    logging.debug('update date: {}'.format(timestamp))
    issue_data = get_day_issue_info()
    filter_testrail_and_create_issue(timestamp, issue_data)

    # used for sync dpe cases with jira
    """
    test123 = sync_cases_soluction()
    bmc_diff_cases = test123.sync_cases(TEST_SUITE_BMC, 'ATOM-3466')
    uefi_diff_cases = test123.sync_cases(TEST_SUITE_UEFI, 'ATOM-3360')
    test123.create_cases_jira_issues(TEST_SUITE_UEFI, uefi_diff_cases)
    test123.create_cases_jira_issues(TEST_SUITE_BMC, bmc_diff_cases)
    """
