# SiteReview

The python class which helps to take the category of website
It will be useful when there are hundered of site to find category
You can store the site which want to find category in CSV and run python script like in example.py.Then get the required keys from response , and save it in another output file
The output of the response are given in sitereview_response.json.

Feature
  - The site category is cached In-memory  as dict, so it will be faster , if the same site requested for again review 
  - The site categoryt cache  is store as pickle , and resued by the class automatically .

 
