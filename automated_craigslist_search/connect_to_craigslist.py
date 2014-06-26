#!/usr/bin/env python
# encoding: utf-8
"""
.. module:: connect_to_craigslist.py
    :synopsis: 
.. moduleauthor:: Robert D. West <robet.david.west@gmail.com>
"""

import urllib2
import bs4
import pandas
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pdb

def create_html_output(df_criteria, df_results, city) :    
    """ 'create_html_output' Takes in two pandas dataframes one containing the search criteria and one containing the results of the craigslist search. The function transforms this data into html, ready to be e-mailed. The function returns a string containing the html. 
     
    :param df_criteria: a pandas dataframe containing search criteria
    :type seach_key_words: pandas.DataFrame
    
    :param df_results: a pandas dataframe containing search results
    :type seach_key_words: pandas.DataFrame
    
    :param city: a string containing the city that the search was performed in
    :type seach_key_words: str or unicode
    
    :returns: a string containing html ready to be e-mailed
    :rtype: str
    """
    	
    # reconstruct hrefs for output e.g. (adding 'http://newyork.craigslist.org' if needed i.e. if search result is outside of new york
    start_string = ['<a href="http://' + city + '.craigslist.org/' if x[:4]!='http' else '<a href="' for x in df_results.urls]

    df_results.Results = start_string + df_results.urls + '">' + df_results.Results + '</a>' 
    df_results = df_results.drop('urls',1)
    # adjust the pandas max_colwidth so that the output is not truncated when it is converted to html table
    pandas.set_option('max_colwidth',200)

    # convert output dataframe into html table
    table = df_results.to_html(classes='df',index = False, justify='left',escape=False) # by setting escape=False we can keep the intended hrefs in the table

    # read in html template including css
    f = open('search_results_template.html', 'r')
    email_message = f.read()   
    f.close()

    # append the search results and criteria, then close the html body 
    email_message = email_message + '\n <p>Your automated craigslist query that had the following inputs: </p>'
    email_message = email_message + df_criteria.to_html()
    email_message = email_message + '\n <p> has the following matching search results live right now: </p>'
    email_message = email_message + table
    email_message = email_message + '\n </body>'
    email_message = email_message + '\n </html>'

    f.close()

    return email_message

def get_category(category):
    """ 'get_category' maps the craigslist category to the url search code

    :param category: a string specifying the craiglist category to search within
    :type seach_key_words: str or unicode

    :returns: the url search code
    :rtype: str

    """
    
    category_key = {'activity partners' : 'act', \
                    'man seeking women' : 'm4w', \
                    'all for sale / wanted' : 'sss', \
                    'antiques' : 'ata', \
                    'appliances' : 'ppa', \
                    'arts+crafts' : 'ara', \
                    'atvs/uts/snowmobiles' : 'sna', \
                    'auto parts' : 'pta', \
                    'baby+kids' : 'baa', \
                    'barter' : 'bar', \
                    'beauty+hlth' : 'haa', \
                    'bikes' : 'bia', \
                    'boats' : 'boo', \
                    'books' : 'bka', \
                    'business' : 'bfa', \
                    'cars+trucks' : 'cta', \
                    'cds/dvd/vhs' : 'ema', \
                    'cell phones' : 'moa', \
                    'clothes+acc' : 'cla', \
                    'collectibles' : 'cba', \
                    'computers' : 'sya', \
                    'electronics' : 'ela', \
                    'farm+garden' : 'gra', \
                    'free stuff' : 'zip', \
                    'furniture' : 'fua', \
                    'garage sales' : 'gms', \
                    'general' : 'foa', \
                    'heavy equipment' : 'hva', \
                    'household' : 'hsa', \
                    'jewelry' : 'jwa', \
                    'matierals' : 'maa', \
                    'motorcycle parts & acc' : 'mpa', \
                    'motorcycles' : 'mca', \
                    'music instr' : 'msa', \
                    'photo+video' : 'pha', \
                    'recreational vehicles' : 'rva', \
                    'sporting' : 'sga', \
                    'tickets' : 'tia', \
                    'tools' : 'tla', \
                    'toys+games' : 'taa', \
                    'video gaming' : 'vga', \
                    'wanted' : 'waa' }
    
    return category_key[category]

def search_craigslist(seach_key_words, min_value=None, max_value=None, category='all for sale / wanted', words_not_included='', city='newyork'):
    """ 'search_craigslist' for specific keys words and over a specified price 
    range. The function will return a Pandas Dataframe containing the 'price',
    'title' and 'url' for every search result

    :param seach_key_words: a string of search key words separated by spaces
    :type seach_key_words: str or unicode

    :param min_value: minimum dollar value for search. Default value is nan, no lower bound on search.
    :type min_value: integer or float

    :param max_value: maximum dollar value for search. Default value is nan, no upper bound on search.
    :type max_value: integer or float

    :param category: craigslist search category. Default value is 'all for sale / wanted'
    :type category: str or unicode

    :param words_not_included: a string of words to be excluded from search results separated by spaces. Default value is empty string/
    :type priority: str or unicode

    :param city: a string specifing the city to search in. Default value is 'newyork'
    :type priority: str or unicode
        
    :returns: a pandas dataframe containing search results
    :rtype: Pandas.DataFrame
    """  
    
    # construct search url from specified criteria    
    seach_key_words = seach_key_words.replace(' ','+')
    url = 'http://' + city + '.craigslist.org/search/' + get_category(category) + '?query=' + seach_key_words 
    if pandas.isnull(min_value) is not None:
        url = url + '&minAsk=' + str(min_value)
    
    if pandas.isnull(max_value) is not None:
        url = url + '&maxAsk=' + str(max_value)
        
    url = url + '&sort=rel'
    
    # Open url and use beautiful soup to find search results    
    response = urllib2.urlopen(url)
    soup = bs4.BeautifulSoup(response)
       
    # initialise lists that will hold results of the search
    results = []
    urls = []
    price = []
    dates = []
    location = []
   
    # Check to see if multiple pages have been returned from the search
    # if so, loop through each page and append the results
    multi_page_info = soup.find('span', {'class':'paginator buttongroup'})
    multi_page_info = multi_page_info.find('span', {'class':'button pagenum'})

    idx1 = multi_page_info.text.find("of")
    if multi_page_info.text == "no results":
        num_loops = 0
    elif idx1 == -1 :
        num_loops = 1
    else : 
        num_results = float(multi_page_info.text[idx1+3:])
        num_loops = int(num_results/100) + 1
    
    # craigslist results are broken into blocks of 100, loop through each set of 100 and append the results
    for i in range(num_loops):        
        
        if idx1 == -1:
            current_url = url
        else :
            idx2 = url.find("?")
            current_url = url[:idx2+1] + "s=" + str(i*100) +  url[:idx2+1]

        # Open url and use beautiful soup to find search results    
        response = urllib2.urlopen(current_url)
        soup = bs4.BeautifulSoup(response)

        # All data returned from the query is stored in <div class="content">
        search_content = soup.find_all('div', {'class':'content'})
        assert(len(search_content)==1) # There should only be one div class="content", if more than one returned, stop program
        search_content = search_content.pop()
          
        for row in search_content.find_all('p',{'class':'row'}):    
            # text and url data
            class_pl_info = row.find('span',{'class':'pl'}) 
            # there is an href stored in 'class_pl_info' with a single 'a' tag
            #    - the method 'getText' will return unicode containing the search entry title
            #    - the method 'attrs' will return a dict, and the key 'href' will then return the respective url
            results.append(class_pl_info.find('a').getText())
            urls.append(class_pl_info.find('a').attrs['href'])
            
            # price data
            class_price_info = row.find('span',{'class':'price'}) 
            # class_price_info contains the respective price if one is specified
            if class_price_info == None:
                price.append(None)   
            else :
                price.append(class_price_info.getText())        
            
            # date of craigslist post
            date_info = row.find('span',{'class','date'})
            dates.append(date_info.getText())
        
            # Location
            location_info = row.find('span',{'class':'pnr'})
            location_info = location_info.find('small')
            # class_price_info contains the respective price if one is specified
           
            if location_info == None:
                location.append(None)   
            else :
                location.append(location_info.getText()) 
           
    # store results in pandas dataframe
    d = {'Results' : results, 'urls' : urls, 'Price' : price, 'Date' : dates, 'Location' : location }
    df = pandas.DataFrame(d)
        
    # Remove rows that contain words from the string 'words_not_included'
    words = words_not_included.split()
    for word in words:
        idx = [x.find(word) ==-1 for x in df.Results] # idx shows which rows do not contain excluded words
        df = df[idx] # only keep rows that do not contain excluded words
    
    return df

def send_email(me, you, password, html):
    """ 'send_email' will send an email from the e-mail address 'me', to 'you'. The email message sent is stored in 'html'. The function has no return output 
     
    :param me: a string containing the gmail address that mail will be sent from
    :type seach_key_words: str or unicode

    :param you: a string containing the recipients email address
    :type seach_key_words: str or unicode

    :param password: a string containing the gmail user's password
    :type seach_key_words: str or unicode

    :param html: a string containing the html e-mail message to be sent
    :type seach_key_words: str or unicode

    """
    # me == my email address
    # you == recipient's email address
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "A match was found for your crasiglist search: "
    msg['From'] = me
    msg['To'] = you
    
    # Create the body of the message (a plain-text and an HTML version).
    # No text version available, just send a msg explaining the html is requied to read email
    text = 'html is required to read this e-mail'
    
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    
    # Send the message via local SMTP server.
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(me, password)
    
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    server.sendmail(me, you, msg.as_string())
    server.quit()
    
                                      
if __name__ == "__main__":    
    
    #############################################
    # Search criteria
    #############################################
    
    search_key_words = 'burning man tickets'
    words_not_included = ''#'wanted Wanted WANTED'
    min_value = 1
    max_value = 1500
    category = 'all for sale / wanted'
    city = 'newyork'
    
    #############################################
    # E-mail information
    #############################################
     
    # the gmail address that alerts will come from: this will require the users password
    send_alerts_from = "ticket.alerts.from.robert@gmail.com"
     
    # the mailing list. A Python List of strings, each containing e-mail addresses:
    mailing_list = ["robert.david.west@gmail.com", "robertdavidwest@gmail.com"]
     
    ############################################# 
    # Dataframe containing all search criteria
    index = ['search key words', 'Words excluded','Category', 'Minimum Price', 'Maximum Price', 'City']
    d = {'Search Criteria' : [search_key_words, words_not_included, 'all for sale / wanted', min_value, max_value, city]}
    criteria_df = pandas.DataFrame(d,index=index)
     
    # Dataframe containing results
    df = search_craigslist(search_key_words, min_value,max_value, category, words_not_included, city)
    
    # If Dataframe is not empty then e-mail results
    if len(df != 0):
        email_message = create_html_output(criteria_df,df, city)
 
        password = raw_input("Please enter your gmail password: ")
        for x in mailing_list:
            send_email(send_alerts_from, x, password,email_message)
    
    
    
    