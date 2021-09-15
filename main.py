import configparser
import datetime
import json
import random
import re
import sys
import threading
import time
import urllib.request
from queue import Queue, PriorityQueue
from urllib.parse import urljoin
from threading import Lock

from lxml import etree
from selenium import webdriver


class CrawlThread(threading.Thread):
    def __init__(self, thread_id, queue, file, type_black_list, crawl_mode):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.file = file
        self.type_black_list = type_black_list
        self.crawl_mode = crawl_mode

    def run(self):
        self.crawl_spider()

    def crawl_spider(self):
        ag_list = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Mozilla/5.0 (Windows NT 6.1; rv2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
            "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"
        ]
        while True:
            if flag:
                while not self.queue.empty():
                    self.queue.get()
            if self.queue.empty():
                return
            else:
                if self.crawl_mode == '0':
                    page = self.queue.get()[0]
                    if page == 'h':
                        continue
                    distance = self.queue.get()[1]
                    print(self.thread_id, "is crawling", page, "distance: ", distance, "queue_size:",
                          self.queue.qsize())
                    try:
                        user_agent = random.choice(ag_list)
                        request = urllib.request.Request(page)
                        request.add_header('User-Agent', user_agent)
                        response = urllib.request.urlopen(request)
                        if response.getcode() != 200 or response.info().get_content_type() in self.type_black_list:
                            code = response.getcode()
                            if code != 200:
                                if code in error_info.keys():
                                    error_info[code] += 1
                                else:
                                    error_info[code] = 1
                            print(response.getcode(), response.info().get_content_type(), self.type_black_list)
                            continue
                        html = response.read()
                        crawl_info = {'url': page, 'page_size(byte)': sys.getsizeof(html),
                                      'download_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
                        self.file.write(json.dumps(crawl_info) + '\n')
                        data_queue.put({'html': html, 'distance': distance, 'url': page})
                        visited[page] = -1
                    except Exception as e:
                        print('crawl tread exception:', e)
                elif self.crawl_mode == '1':
                    if page == 'h':
                        continue
                    score = self.queue.get()[0]
                    page = self.queue.get()[1]
                    distance = self.queue.get()[2]
                    print(self.thread_id, ' is crawling', page)
                    try:
                        user_agent = random.choice(ag_list)
                        request = urllib.request.Request(page)
                        request.add_header('User-Agent', user_agent)
                        response = urllib.request.urlopen(request, timeout=3)
                        if response.getcode() != 200 or response.info().get_content_type() in self.type_black_list:
                            code = response.getcode()
                            if code != 200:
                                if code in error_info.keys():
                                    error_info[code] += 1
                                else:
                                    error_info[code] = 1
                            print(response.getcode(), response.info().get_content_type(), self.type_black_list)
                            continue
                        html = response.read()
                        crawl_info = {'url': page, 'score': score, 'page_size(byte)': sys.getsizeof(html),
                                      'download_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
                        self.file.write(json.dumps(crawl_info) + '\n')
                        data_queue.put({'score': score, 'html': html, 'distance': distance, 'url': page})
                        visited[page] = -1
                    except Exception as e:
                        error_info[e] += 1
                        print('crawl tread exception:', e)


class ParserThread(threading.Thread):
    def __init__(self, thread_id, queue, file, crawl_mode, crawl_limit):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.file = file
        self.crawl_mode = crawl_mode
        self.crawl_limit = crawl_limit

    def run(self):
        while not flag:
            try:
                item = self.queue.get(False)  # get参数为false时队列为空，会抛出异常

                if not item:
                    pass
                self.parse_data(item)
                self.queue.task_done()  # 每当发出一次get操作，就会提示是否堵塞
            except Exception as e:
                pass
        while not self.queue.empty():
            self.queue.get()

    def parse_data(self, item):
        mutex.acquire()
        global crawl_count
        if crawl_count >= self.crawl_limit:
            global flag
            flag = True
        if self.crawl_mode == '0':
            html = etree.HTML(item['html'])
            distance = item['distance']
            result = html.xpath("//div/a/@href")
            for i in range(0, len(result)):
                site = result[i]
                try:
                    if check_validation(site, visited):
                        # site = convert_sub_url(url, site)
                        url_info = {'url': site, 'distance': str(distance + 1)}
                        self.file.write(json.dumps(url_info) + '\n')
                        crawl_count += 1
                        if site not in visited.keys():
                            page_queue_bfs.put((site, distance + 1))
                            visited[site] = 1
                except Exception as e:
                    print('parse 2: ', e)
        elif self.crawl_mode == '1':
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
                            site = convert_sub_url(url, site)
                            cur_score = score + (i + 1) / sub_url_count  # novelty
                            url_info = {'url': site, "distance": distance + 1, 'score': cur_score}
                            self.file.write(json.dumps(url_info) + '\n')
                            self.count += 1
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
                    except Exception as e:
                        print('parse 2: ', e)

            except Exception as e:
                print('parse 1: ', e)
        mutex.release()


'''
convert url
example: dining.html -> https://housing.nyu.edu/summer/dining.html
'''


def convert_sub_url(url, sub_url):
    return urljoin(url, sub_url)


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
a url is invalid if it is in wrong format or the url is revisited and  has already been consumed by crawler
'''


def check_validation(url, visited):
    if (not re.match(r'^https?:/{2}\w.+$', url)) or (url in visited.keys() and visited[url] == -1 or url == 'h'):
        return False
    else:
        return True


def progress_bar(cur_process):
    print("\r", end="")
    print("Collecting from google: {}:".format(cur_process), "▋" * (cur_process // 2), end="")
    sys.stdout.flush()
    time.sleep(0.05)


page_queue = PriorityQueue()
page_queue_bfs = Queue()
data_queue = Queue()
visited = {}
min_distance = 0
flag = False
mode = ''
error_info = {}
crawl_count = 0
crawl_threads = []
parse_thread = []
mutex = Lock()


def main():
    seeds = []
    url = 'https://www.google.com'
    wd = input('input key word for searching:')
    wd = urllib.request.quote(wd)

    # output = open('./data_log/' + wd + '.log', 'a', encoding='utf-8')
    crawl_log_file = open('./crawl_log/' + 'crawl_' + wd + '.log', 'a', encoding='utf-8')
    full_url = url + '/search?q=' + wd

    config = configparser.ConfigParser()
    config.read("./config/config.ini")
    driver_url = config['chromedriver']['location']
    type_black_list = config['type_black_list']['list'].split(',')
    crawl_limit = int(config['crawl_limit']['number'])
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
    mode_choice = None
    while mode_choice != '0' and mode_choice != '1':
        mode_choice = input('please input 0 or 1:\n[0] BFS crawl\n[1]prioritized crawl\n')

    start_time = datetime.datetime.now()

    if mode_choice == '0':
        print('###################start with BFS mode#####################')
        output = open('./data_log/' + wd + '_bfs.log', 'a', encoding='utf-8')
        for i in range(0, len(seeds)):
            page_queue_bfs.put((seeds[i], 0))  # priority, url, distance, parent_url
            url_info = {'url': seeds[i], "distance": 0}
            output.write(json.dumps(url_info) + '\n')
            visited[seeds[i]] = 1
        # initialize the crawl threads
        # crawl_threads = []
        crawl_name_list = ['crawl_1', 'crawl_2', 'crawl_3', 'crawl_4', 'crawl_5', 'crawl_6']
        for thread_id in crawl_name_list:
            thread = CrawlThread(thread_id, page_queue_bfs, crawl_log_file, type_black_list,
                                 mode_choice)  # create crawl thread
            thread.start()  # start crawl thread
            crawl_threads.append(thread)
    elif mode_choice == '1':
        print('###################start with prioritized mode#############')
        output = open('./data_log/' + wd + '_prioritized.log', 'a', encoding='utf-8')
        for i in range(0, len(seeds)):
            page_queue.put((1, seeds[i], 0, ''))  # priority, url, distance, parent_url
            url_info = {'url': seeds[i], "distance": 0, 'score': 1}
            output.write(json.dumps(url_info) + '\n')
            visited[seeds[i]] = 1
        # initialize the crawl threads
        # crawl_threads = []
        crawl_name_list = ['crawl_1', 'crawl_2', 'crawl_3']
        for thread_id in crawl_name_list:
            thread = CrawlThread(thread_id, page_queue, crawl_log_file, type_black_list,
                                 mode_choice)  # create crawl thread
            thread.start()  # start crawl thread
            crawl_threads.append(thread)

    print('start crawling')

    # initialize parser thread
    # parse_thread = []
    parser_name_list = ['parse_1', 'parse_2', 'parse_3']
    for thread_id in parser_name_list:
        thread = ParserThread(thread_id, data_queue, output, mode_choice, crawl_limit)
        thread.start()
        parse_thread.append(thread)

    while not page_queue.empty():
        pass

    while not page_queue_bfs.empty():
        pass

    # for t in crawl_threads:
    #     print(t, "join")
    #     t.join()

    while not data_queue.empty():
        data_queue.get();

    while not data_queue.empty():
        pass

    global flag
    flag = True
    for t in parse_thread:
        t.join()

    print('quit main thread')
    output.close()

    end_time = datetime.datetime.now()

    print("total crawling time:", (end_time - start_time).seconds, "sec")
    print("total crawled pages:", crawl_count)

    print("error:", error_info)


if __name__ == '__main__':
    main()
