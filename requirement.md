
Please follow the following guidelines on how to 
submit your homework #1 and what you should submit. 
First, some general rules for all homeworks:

 - please submit electronically on NYU BrightspaceClasses.

 - please submit everything in a gzipped tar file or 
   a zip file with a directory CONTAINING your files. 
   The directory should have the name "smith1" and 
   the tar file should have the name "smith1.tar" 
   if your last name is smith and you are submitting
   your first homework. DO NOT SUBMIT rar files or
   other compressed archive formats. Only zip or tar. 

 - if your code has bugs or any features that are 
   missing, you should always DECLARE these as 
   described below. Bugs and problems that are 
   declared are graded much more leniently than
   bugs that I find myself. Also, disclose any
   libraries or other resources that you are using.

 - always provide the readme files described below.

 - DO NOT submit the content of all the files 
   that your crawler crawled.

Now the details on what to submit for the first 
homework. Note that in addition, there will also be
a demo - you should submit your material before the
demo, or at the latest by the evening of the demo day. 
In particular, submit:
 
 - your well-commented Python program source
 
 - 4 output logs, each listing all pages crawled by
   your crawler for one run. Try to crawl at least 10000
   pages for each, more if you can and less if you cannot.
   You will be given 2 queries, and for each query you
   should do two runs, one for your prioritized crawl, and
   one using a simple BFS strategy.

   There should be one line for each crawled URL, containing
   the URL of the crawled page, the time when it was crawled,
   its size, the return code (e.g., 200, 404), and the priority
   score it had at the time it was crawled. You should also output 
   some basic statistics at the end of the crawl, like number of 
   files, total size, total time, number of 404 errors, etc. 

   Output only lines for pages that are actually crawled, please,
   not one line for each hyperlink parsed out of a page. (You may
   want to output such additional information during debugging, but
   not in the final submission.)

 - the two queries are "brooklyn union" and "paris texas"

 - a readme.txt file in ascii format with a list of
   the files in your submission and what they do, 
   and with a short description on how to compile 
   and run your program (meaning of input parameters, 
   any configuration files etc). Also, point out any 
   limitations on parameters (e.g., "query must have
   at most 3 words" if that is the case) when running
   your code.

 - an explain.txt file containing a precise and 
   succinct description of how the program works and 
   what the major functions are. Also, provide a list 
   of any bugs or non-working features in your program, 
   and disclose any additional resources that you used. 
   Finally, a list of any special features beyond the 
   basic requirements, if there are any.

A demo schedule will be announced later, where you will be 
able to choose a demo slot from a set of available slots.