#!/usr/bin/env python3

# imports
import json
import urllib2
import argparse
import os


def get_head():
    Token = "3ccd1f8db230f0c59cb66988a73bcda3b662a32d"
    head = {'Authorization':'{token}'.format(token = Token)}
    return head

def send_get_request(url):
    head = get_head()
    req = urllib2.Request(url=url, headers=head)
    response = urllib2.urlopen(req)
    data = json.loads(response.read())
    return data

def list_commits_on_repo(commit_tag):
    commits_url = "https://api.github.com/repos/hanxiaohu1011/dragonfly/commits"
    data = send_get_request(commits_url)
    for commit in data:
        if commit['sha'].startswith(commit_tag):
            print commit['sha']
            return commit['sha']
    return None

def get_single_commit(commit_tag):
    sha = list_commits_on_repo(commit_tag)
    single_commit_url = "https://api.github.com/repos/hanxiaohu1011/dragonfly/commits/"+sha
    commit_data = send_get_request(single_commit_url)
    return commit_data

def get_contents(file_path, commit_tag):
    commit_data = get_single_commit(commit_tag)
    sha = commit_data['sha']
    contents_url = "https://api.github.com/repos/hanxiaohu1011/dragonfly/contents/"+file_path\
                    +'?ref='+sha
    contents_data = send_get_request(contents_url)
    return contents_data

def download_file(file_path, commit_tag):
    content = get_contents(file_path, commit_tag)
    print content['type'].strip()
    if content['type'].strip() == 'file':
        try:
            download_url = content['download_url']
            print download_url
            #download_path = os.getcwd()+'/'+content['name']
            download_path = os.path.join(os.getcwd(),content['name'])
            print download_path
            req = urllib2.Request(download_url)
            file_data = urllib2.urlopen(req).read()
            print file_data
            with open(download_path, 'wb') as f:
                f.write(file_data)
                print 'ok'
        except Exception as exc:
            pass

def main():
    parser = argparse.ArgumentParser(description='imput your args')
    parser.add_argument('--file_path', type = str, default = 'test', action = 'store')
    parser.add_argument('--commit_tag', type = str, default = '51d7f81', action = 'store')
    args = parser.parse_args()
    download_file(args.file_path, args.commit_tag)

if __name__ == '__main__':
    main()

