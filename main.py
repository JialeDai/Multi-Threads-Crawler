import configparser
import json
import random
import re
import sys
import threading
import time
import urllib.request
from queue import Queue, PriorityQueue

from lxml import etree
from selenium import webdriver


class CrawlThread(threading.Thread):
    def __init__(self, thread_id, queue, file):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.file = file

    def run(self):
        print('启动线程：', self.thread_id)
        self.crawl_spider()
        print('退出了该线程：', self.thread_id)

    def crawl_spider(self):
        while True:
            if self.queue.empty():
                continue
            else:
                score = self.queue.get()[0]
                page = self.queue.get()[1]
                distance = self.queue.get()[2]
                print('当前工作线程为：', self.thread_id, ' 正在采集：', page)
                ag_list = [
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv2.0.1) Gecko/20100101 Firefox/4.0.1",
                    "Mozilla/5.0 (Windows NT 6.1; rv2.0.1) Gecko/20100101 Firefox/4.0.1",
                    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
                    "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"
                ]

                try:
                    user_agent = random.choice(ag_list)
                    request = urllib.request.Request(page)
                    request.add_header('User-Agent', user_agent)
                    response = urllib.request.urlopen(request)
                    if response.getcode() != 200:
                        continue
                    html = response.read()
                    crawl_info = {'url': page, 'score': score}
                    self.file.write(json.dumps(crawl_info) + '\n')
                    data_queue.put({'score': score, 'html': html, 'distance': distance, 'url': page})
                    visited[page] = -1
                except Exception as e:
                    print('crawl tread exception:', e)


class ParserThread(threading.Thread):
    def __init__(self, thread_id, queue, file):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.file = file

    def run(self):
        # print('启动线程', self.thread_id)
        while not flag:
            try:
                item = self.queue.get(False)  # get参数为false时队列为空，会抛出异常

                if not item:
                    pass
                self.parse_data(item)
                self.queue.task_done()  # 每当发出一次get操作，就会提示是否堵塞
            except Exception as e:
                pass
            # print('退出了该线程：', self.thread_id)

    def parse_data(self, item):
        try:
            score = item['score']
            html = etree.HTML(item['html'])
            distance = item['distance']
            url = item['url']
            result = html.xpath("//div/a/@href")
            sub_url_count = len(result)
            for i in range(0, len(result)):
                site = result[i]
                try:
                    if check_validation(site, visited):
                        cur_score = score + (i + 1) / sub_url_count # novelty
                        url_info = {'url': site, "distance": distance + 1, 'score': cur_score}
                        self.file.write(json.dumps(url_info) + '\n')
                        if site not in visited.keys():
                            print(site)
                            page_queue.put((cur_score, site.encode('utf-8').decode(), distance + 1, url))
                            visited[site] = 1
                        else:
                            '''
                            importance: other already  crawled pages that have a hyperlink to this page.
                            increase the priority of site in priority queue
                            '''
                            increase_priority(page_queue, site.encode('utf-8').decode())
                            visited[site] = visited[site] + 1
                    # else:
                    #     cur_score = score + (i + 1) / sub_url_count
                    #     site = convert_sub_url(url, site)
                    #     url_info = {'url': site, "distance": distance + 1, 'score': cur_score}
                    #     self.file.write(json.dumps(url_info) + '\n')
                    #
                    #     if site not in visited.keys():
                    #         print(site)
                    #         page_queue.put((cur_score, site.encode('utf-8').decode(), distance + 1, url))
                    #         visited[site] = 1
                    #     else:
                    #         '''
                    #         importance: other already  crawled pages that have a hyperlink to this page.
                    #         increase the priority of site in priority queue
                    #         '''
                    #         increase_priority(page_queue, site.encode('utf-8').decode())
                    #         visited[site] = visited[site] + 1
                except Exception as e:
                    print('parse 2: ', e)

        except Exception as e:
            print('parse 1: ', e)


'''
convert url
example: dining.html -> https://housing.nyu.edu/summer/dining.html
'''


def convert_sub_url(url, sub_url):
    tmp = url.split('/')
    if sub_url == '/':
        url.replace(tmp[-1], '')
    elif re.match(r'\.html$', sub_url):
        url.replace(tmp[-1], sub_url)
    return url


'''
update the priority in page queue
'''


def update_priority(queue, url, priority):
    tmp = []
    while not queue.empty():
        cur = queue.get()
        if cur[1] == url:
            cur[0] = priority
            queue.put(cur)
            break
        tmp.append(cur)
    for each in tmp:
        queue.put(each)


'''
increase the priority of certain url
'''


def increase_priority(queue, url):
    tmp = []
    while not queue.empty():
        cur = queue.get()
        if cur[1] == url:
            cur_score = cur[0]
            site = cur[1]
            distance = cur[2]
            url = cur[3]
            new_item = (cur_score - 1, site, distance, url)
            tmp.append(new_item)
            break
        tmp.append(cur)
    for each in tmp:
        queue.put(each)


'''
decrease the priority of certain url
'''


def decrease_priority(queue, url):
    tmp = []
    while not queue.empty():
        cur = queue.get()
        if cur[1] == url:
            cur[0] += 1
            break
        tmp.append(cur)
    for each in tmp:
        queue.put(each)


'''
a url is invalid if it is in wrong format or the url is revisited and  has already been consumed by crawler
'''


def check_validation(url, visited):
    if (not re.match(r'^https?:/{2}\w.+$', url)) or (url in visited.keys() and visited[url] == -1):
        return False
    else:
        return True


def progress_bar(cur_process):
    print("\r", end="")
    print("Collecting from google: {}:".format(cur_process), "▋" * (cur_process // 2), end="")
    sys.stdout.flush()
    time.sleep(0.05)


page_queue = PriorityQueue()
data_queue = Queue()

'''
visited is a dict record the status of the url
value has two condition: 
    0-> haven't been consume by page queue
    1-> already be consumed by page queue
'''
visited = {}
min_distance = 0
flag = False


def main():
    seeds = []
    url = 'https://www.google.com'
    wd = input('input key word for searching:')
    wd = urllib.request.quote(wd)

    output = open(wd + '.log', 'a', encoding='utf-8')
    crawl_log_file = open('crawl_' + wd + '.log', 'a', encoding='utf-8')
    full_url = url + '/search?q=' + wd

    config = configparser.ConfigParser()
    config.read("./config/config.ini")
    driver_url = config['chromedriver']['macbook']
    driver = webdriver.Chrome(driver_url)
    driver.get(full_url)

    count = 0
    while True:
        page_content = driver.page_source
        html = etree.HTML(page_content)
        res = html.xpath("//div[@class='yuRUbf']/a/@href")
        for each in res:
            seeds.append(each)
            count += 1
            progress_bar(count)
        try:
            driver.find_element_by_xpath('//*[@id="pnnext"]').click()
        except:
            driver.close()
            break
    seeds = set(seeds)
    seeds = list(seeds)
    print('\ncollected seeds url:\n', seeds)
    if len(seeds) == 0:
        print("no seed url available")
        return
    num_seeds = input("input the number of seeds you want to start with:")
    num_seeds = int(num_seeds)
    if num_seeds > len(seeds):
        num_seeds = len(seeds)
    print('start crawling')
    print('seeds:\n', seeds)
    print('Initialize seed queue......')
    for i in range(0, num_seeds):
        page_queue.put((1, seeds[i], 0, ''))  # priority, url, distance, parent_url
        url_info = {'url': seeds[i], "distance": 0, 'score': 1}
        output.write(json.dumps(url_info) + '\n')
        visited[seeds[i]] = 1
    # initialize the crawl threads
    crawl_threads = []
    crawl_name_list = ['crawl_1', 'crawl_2', 'crawl_3']
    for thread_id in crawl_name_list:
        thread = CrawlThread(thread_id, page_queue, crawl_log_file)  # create crawl thread
        thread.start()  # start crawl thread
        crawl_threads.append(thread)

    # initialize parser thread
    parse_thread = []
    parser_name_list = ['parse_1', 'parse_2', 'parse_3']
    for thread_id in parser_name_list:
        thread = ParserThread(thread_id, data_queue, output)
        thread.start()
        parse_thread.append(thread)

    while not page_queue.empty():
        pass

    for t in crawl_threads:
        t.join()

    while not data_queue.empty():
        pass

    global flag
    flag = True
    for t in parse_thread:
        t.join()

    print('quit main thread')
    output.close()


if __name__ == '__main__':
    main()
