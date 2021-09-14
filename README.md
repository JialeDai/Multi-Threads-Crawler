# cs6913 - HW 1
## Jiale Dai (jd4678)
## How to run
The cralwer grab the seed url using chromedirver. If you are a mac user. Just run: \
'''

brew install chromedirver
'''

## Approach
- Queue: The web crawler involves two different queue which be processed by different type of thread.
  - page_queue:
    - The page_queue is a priority queue, 
  - data_queue