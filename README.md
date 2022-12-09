### General Project Description
I built a web app in Flask that allows users to add 
tasks to a to do list, move them to doing or done and 
delete tasks as well. 

### Project Specifics
The web app has a Tasks page where you can add, move and
delete the tasks. I implement the web app to facilitate 
user authentication. 

The user's input their username and
password in the login page, and it takes them to the
welcome page. Once logged in a user can edit their tasks.
Without logging in, you can not view any pages on the 
website. 

To ensure that each user has access to their own Kanban 
board, I created a database to store login credentials
and all tasks. To render a user's Task's page, 
I query the database for all tasks with the user's id
and render the on the page based on the task category.  

