# Scrolling method: Scroll SCROLL_NUM times downwards with length DOWN_SCROLL_LENGTH, then scroll down LOAD_SCROLL_LENGTH (load new tweets) and scroll up LOAD_SCROLL_LENGTH

SCROLL_DELAY = 0.2  # Delay of scrolling operation
SCROLL_NUM = 10  # Time of scrolling down every iteration
DOWN_SCROLL_LENGTH = 25  # Length of scrolling down every iteration; 50 means 50% length of page
LOAD_SCROLL_LENGTH = SCROLL_NUM * DOWN_SCROLL_LENGTH  # Length of scrolling down & scrolling up after every SCROLL_NUM times of scrolling down
