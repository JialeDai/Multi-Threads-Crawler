# CS_GY_6913 (Web search engine HW1)
Build a multi-threaded web crawler that downloads pages with priorities based on some combination of novelty and importance
## file structure:
### fold:
- config: contains the crawler configuration
- crawl_log: contains the urls which have been visited
- data_log: contains the urls crawled
### files
- crawl_log/*_bfs.log: log file of crawled urls for bfs crawler
- crawl_log/*_prioritized.log: log file of crawled urls for prioritized crawler
- data_log/*_bfs.log: log file of all visited urls for bfs crawler
- data_log/*_prioritized.log: log file of all visited urls for prioritized crawler
- config/config.ini: crawler configuration file
- main.py: the entrance of the crawler
##$ configuration
- [chromedriver][location]: install location of chromedriver
- [type_black_list][list]: types of file ignored by crawler
- [crawl_limit][total_number]: number of url which regulate when the crawler should stop
- [crawl_limit][number_per_url]: the max number for url grabbed from one page
- [seeds][number]: the number of seed urls initialized before crawling

## missing feature: robot.txt, updating heap in linear time
## please do not set the number of parser thread more then the number of crawl thread
