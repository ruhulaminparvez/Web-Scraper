from bs4 import BeautifulSoup
import requests
import requests.exceptions
import urllib.parse
from collections import deque
import re
import csv
import validators
from googlesearch import search
import pandas as pd

dict = {}

mainlinks = set()
brokenlinks = set()

def main():
    query = input("Search for: ")
    numberofresults = input("Number of results you want: ")
    dict = take_input_and_put_in_dict(query, int(numberofresults))
    put_links_into_csv(dict)
    links = read_csv()
    with open('results.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Title', 'Emails'])
    counter = 0
    while counter < len(mainlinks):
        emails = email_finder(list(links)[counter])
        titles = title_finder(list(links)[counter])
        write_emails_on_csv(list(links)[counter], titles, emails)
        cleaner("<title>", "")
        cleaner("</title>", "")
        counter += 1

def take_input_and_put_in_dict(query, numberofresults):
    link = search(query, num_results=numberofresults, lang="en")
    i = 0
    while i < numberofresults:
        dict[link[i]] = link[i]
        i += 1
    return dict


def put_links_into_csv(dict):
    with open('results.csv', 'w', newline='') as file:
        fieldname = ["URL", "Title", "Emails"]
        dictwriter = csv.DictWriter(file, fieldnames=fieldname)
        dictwriter.writeheader()
        for links in dict:
            dictwriter.writerow({'URL': dict[links]})


def read_csv():
    with open('results.csv', 'r', newline='') as file:
        dictreader = csv.DictReader(file)
        for row in dictreader:
            valid = validators.url(row['URL'])
            if valid == True:
                mainlinks.add(row['URL'])
            else:
                brokenlinks.add(row['URL'])
    return mainlinks


def write_emails_on_csv(url, titles, email_list):
    with open('results.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([url, titles , email_list])
    excel_file_path = 'results.csv'
    df = pd.read_csv(excel_file_path)
    for column in df.columns:
        df[column] = df[column].str.replace(r"[^\w@.:/|, ]", "", regex=True)
    df.to_csv("results_final.csv")


def title_finder(url):
    linkgetter = requests.get(url)
    soup = BeautifulSoup(linkgetter.text, 'html.parser')
    title = soup.findAll('title')
    return title

def email_finder(urllist):
    user_url = urllist

    urls = deque([user_url])
    scraped_url = set()
    emails = set()

    count = 0

    try:
        while (len(urls) and not "#" in urls):
            count += 1
            if (count == 2):
                break
            url = urls.popleft()
            scraped_url.add(url)
            parts = urllib.parse.urlsplit(url)
            base_url = '{0.scheme}://{0.netloc}'.format(parts)
            path = url[:url.rfind('/') + 1] if '/' in parts.path else url
            print("[%d] Processing %s" % (count, url))
            try:
                if requests.get(url).status_code == 200:
                    response = requests.get(url)
                else:
                    continue
            except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL,
                requests.exceptions.InvalidSchema, requests.exceptions.SSLError):
                continue
            new_emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,3}", response.text, re.I))
            emails.update(new_emails)
            soup = BeautifulSoup(response.text, features="lxml")
            for anchor in soup.find_all("a"):
                link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
                if link.startswith('/'):
                    link = base_url + link
                elif not link.startswith('http'):
                    link = path + link
                if not link in urls and not link in scraped_url:
                    urls.append(link)
    except KeyboardInterrupt:
        print("[-] Closing")
    return emails

def cleaner(find, replace):
    # open your csv and read as a text string
    with open("results.csv", 'r') as f:
        my_csv_text = f.read()

    find_str = find
    replace_str = replace

    # substitute
    new_csv_str = re.sub(find_str, replace_str, my_csv_text)

    # open new file and save
    new_csv_path = './results.csv'  # or whatever path and name you want
    with open(new_csv_path, 'w') as f:
        f.write(new_csv_str)

if __name__ == '__main__':
    main()
