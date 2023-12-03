import praw
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

MY_CLIENT_ID = os.getenv("MY_CLIENT_ID")
MY_CLIENT_SECRET = os.getenv("MY_CLIENT_SECRET")
MY_USER_AGENT= os.getenv("MY_USER_AGENT")
MY_REDDIT_USERNAME = os.getenv("MY_REDDIT_USERNAME")
MY_REDDIT_PASSWORD = os.getenv("MY_REDDIT_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

SUBREDDIT_TO_EXPLORE = 'askphysics'
NUM_POSTS_TO_EXPLORE = 10
SCORE_WEIGHT = 3
COMMENT_WEIGHT = 1
# The following is the minimum relevant weighted score to be a match, 
# where weighted score = SCORE_WEIGHT * score + COMMENT_WEIGHT * num comments
MIN_RELEVANT_WEIGHTED_SCORE = 0
# The following tuple contains 1. list of required terms/stems, 2. list of secondary terms, 
# 3. min number of secondary terms needed to be a match
KEYWORDS_GROUP = ['metaphysics', "falsificationism", "falsified", "falsifiability"]

# Returns a count of secondary terms if is relevant, -1 otherwise
def get_keyword_count(_str):
    keyword_count = 0
    for keyword in KEYWORDS_GROUP:
        if keyword in _str:
            keyword_count += 1

    return keyword_count

# Returns tuples containing keyword count, weighted score, post info dict of matching posts
def get_reddit_posts():
    # Authenticate
    reddit = praw.Reddit(client_id=MY_CLIENT_ID,
                         client_secret=MY_CLIENT_SECRET,
                         user_agent=MY_USER_AGENT,
                         username=MY_REDDIT_USERNAME,
                         password=MY_REDDIT_PASSWORD)
    # Designate subreddit to explore
    subreddit = reddit.subreddit(SUBREDDIT_TO_EXPLORE)
    matching_posts_info = []
    # Explore rising posts in subreddit and store info if is relevant and popular enough
    # Tip: You could also explore top posts, new posts, etc.
    # See https://praw.readthedocs.io/en/latest/getting_started/quick_start.html#obtain-submission-instances-from-a-subreddit
    for submission in subreddit.new(limit=NUM_POSTS_TO_EXPLORE):
        keyword_count = get_keyword_count(submission.title.lower())

        if keyword_count > 0:
            post_dict = {'title': submission.title, \
            'score': submission.score, \
            'url': submission.url, \
            'comment_count': len(list(submission.comments))}
            matching_posts_info.append((keyword_count, 0, post_dict))
    # Sort asc by the keyword count, then desc by weighted score (can't sort by post_dict)
    matching_posts_info.sort(key=lambda x: (x[0], -1 * x[1]))
    return matching_posts_info

# Send email of matching posts
def send_email():
    matching_posts_info = get_reddit_posts()
    reddit_email_content = ''
    for keyword_count, weighted_score, post in matching_posts_info:
        # Append info for this relevant post to the email content
        reddit_email_content += post['title'] + '<br>' + 'Score: ' + str(post['score']) + \
        '<br>' + 'Comments: ' + str(post['comment_count']) + '<br>' + post['url'] + '<br><br>'
    if len(matching_posts_info) > 0:
        email_list = [
            RECEIVER_EMAIL
            # Add any other email addresses to send to
        ]
        subject = 'Hey you! I have something SPECIAL for you to check out...'
        # Port 587 is used when sending emails from an app with TLS required
        # See https://support.google.com/a/answer/176600?hl=en
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for email_address in email_list:
            # Send emails in multiple part messages
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SENDER_EMAIL
            msg['To'] = email_address
            # HTML of email content
            html = '''\
            <html>
              <head></head>
              <body>
                <p>
                    <b style='font-size:20px'>Hello to my favorite person!</b><br><br>
                    I am ecstatic to report that the following posts may be of interest to you:<br>
                </p>
                %s
                <p>
                    <b style='font-size:20px'>With love from your reddit notification script <span style='color:#e06d81'>♥</span></b>
                </p>
              </body>
            </html>
            ''' % reddit_email_content
            msg.attach(MIMEText(html, 'html'))
            server.sendmail(SENDER_EMAIL, email_address, msg.as_string())
        server.quit()

if __name__ == "__main__":
    send_email()
