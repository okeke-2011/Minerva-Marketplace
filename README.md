## What is Minerva MarketPlace?
A web app speciifcally for Minerva students that addresses the challenge of significant waste and expense generated by the limited baggage allowances for Minervans leaving and incoming students arriving at rotation cities. Minerva Marketplace connects incoming students needing items and outgoing students looking to get rid of items, reducing waste and saving money for Minervans.

It addresses the pain points of reach, categorization, and cross-city selling that were not adequately addressed by existing solutions, as determined by a gap analysis. Minerva Marketplace offers several features, such as intuitive item categorization, search/filtering, and a cross-city user base, to enhance users' buying and selling experience.

## Summary of Design
I took a simple approach to designing the web app as not to overcomplicate the initial design. The core idea of the web app is to bring buyers in contact with sellers. Most ecommerce websites do this by having an in-app chat system that users can communicate through. However, solid communication channels already exist between Minervans. I decided to make use of these to keep the design of my app simple. Users provide their contact info when signing up. When there is interest from both the buyer and seller’s side for the trade of an item, the full contact info of each party is disclosed to the other party. 

Each user has the ability to post items (with all the required info about the item). When an item is posted, it is displayed on the landing page. Other users can them view the item and request it (a requested item leaves the landing page i.e., only one requester per item). If you as a poster, see that one of your items has been requested, you can approve the request. Once a request is approved, both parties unlock each other’s contact info. At any stage of the process, either user can opt-out (either from the seller’s side by declining or from the buyer’s side by withdrawing a request). 

### Useful links
- Link to the hosted web app: https://minerva-marketplace.onrender.com/ 
- Link to Github repo: https://github.com/okeke-2011/Minerva-Marketplace 
- Detailed description of web pages, features, and DB schema: https://docs.google.com/document/d/1wgJIG_o-Hi17D6lLk2B0QHpsGPC3xUSeraNqoR_hkJY/edit# 
- For more information about the web app: https://docs.google.com/document/d/1eOLl162igY7Hygo8OFw3FKt3i0UUSMfkhT7Xip5RIDg/edit?usp=sharing

## Summary of tech stack
My knowledge regarding web application development is limited to the skills I developed taking Minerva University’s CS162 course - “Software Development: Building Powerful Applications.” Hence, most components of my web app follow the best practices and guidelines taught in that course.
- Frontend: Raw HTML with Jinja templates (to make the web app dynamic)
- Backend: Flask library in Python for the page login and routing between pages
- Database: PostgreSQL database. I specify the external database URI in the app so that the web app can connect to the database, but I use SQLAlchemy to manipulate the database (make queries, add new entries, etc) using Python, code.
- Image storage: I store the image metadata as text in my database, but I push the actual images that get uploaded to an AWS S3 bucket. 
- Hosting: Render. The Github repo with the web app code is linked to the hosted web app service on Render. Any changes to the repo trigger an automatic deployment of a new version of the web app.

## Installation for testing

Start virtual environment

    $ python3 -m venv venv
    $ source venv/bin/activate

Install necessary dependencies

    $ pip install -r requirements.txt

Start flask server (from the root directory)

    $ python3 app.py

The app should be up and running at http://127.0.0.1:5000/
