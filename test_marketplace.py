from app import app, db, Users, Tasks
import unittest
import requests

# base test case to will set up the environment needed for all my tests
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # populate database with tasks and users
        db.create_all()
        db.session.add(Users("Favour", "GOAT"))
        db.session.add(Users("Philip", "sterne"))
        db.session.add(Tasks(1,"todo","cry"))
        db.session.add(Tasks(1, "doing", "sleep"))
        db.session.add(Tasks(2, "todo", "sing"))
        db.session.add(Tasks(2, "done", "run around"))
        db.session.commit()

    # remove database entries
    def tearDown(self):
        db.session.remove()
        db.drop_all()


class FlaskTestCase(BaseTestCase):

    # Ensure that Flask was set up correctly
    def test_login(self):
        tester = app.test_client(self)
        response = tester.get('/')
        self.assertIn(b"Username", response.data)
        self.assertIn(b"Enter Username", response.data)
        self.assertIn(b"Password", response.data)
        self.assertIn(b"Enter Password", response.data)

    # Ensure sign in required to view welcome
    def test_requires_authentication_welcome(self):
        tester = app.test_client(self)
        response = tester.get('/welcome', follow_redirects=True)
        self.assertIn(b"You need to log in!", response.data)

    # Ensure sign in required to view tasks
    def test_requires_authentication_tasks(self):
        tester = app.test_client(self)
        response = tester.get('/tasks', follow_redirects=True)
        self.assertIn(b"You need to log in!", response.data)

    # Ensure sign in required to view user info
    def test_requires_authentication_user_info(self):
        tester = app.test_client(self)
        response = tester.get('/user_info', follow_redirects=True)
        self.assertIn(b"You need to log in!", response.data)

    # test that we see the login page on sign up
    def test_login_to_welcome_old_user(self):
        tester = app.test_client(self)
        response = tester.post('/',
                               data=dict(user_name="Favour",password="GOAT"),
                               follow_redirects=True)
        self.assertIn(b"Welcome Favour", response.data)
        self.assertIn(b"Signed you in!", response.data)
        self.assertNotIn(b"Created profile for Favour", response.data)

    # test that we see the login page on sign up
    def test_login_to_welcome_new_user(self):
        tester = app.test_client(self)
        response = tester.post('/',
                               data=dict(user_name="Favour",password="GOATed"),
                               follow_redirects=True)
        self.assertIn(b"Welcome Favour", response.data)
        self.assertIn(b"Signed you in!", response.data)
        self.assertIn(b"Created profile for Favour", response.data)

    # don't allow a re-login if already logged in
    def test_no_login_after_initial_login(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour",password="GOAT"),
                    follow_redirects=True)
        response = tester.get("/", follow_redirects=True)
        self.assertIn(b"already logged in", response.data)
        self.assertIn(b"Enter Task", response.data)

    # show tasks page if logged in
    def test_render_tasks_if_logged_in(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour",password="GOAT"),
                    follow_redirects=True)
        response = tester.get("/tasks", follow_redirects=True)
        self.assertIn(b"Enter Task", response.data)

    # user's that are not Favour with password GOAT
    # can't view the database
    def test_no_access_to_database(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour",password="GO"),
                    follow_redirects=True)
        response = tester.get("/view", follow_redirects=True)
        self.assertIn(b"Only the GOAT can view this page", response.data)
        self.assertIn(b"Enter Task", response.data)

    # allow users to change their credentials
    def test_edit_credentials(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour",password="GOAT"),
                    follow_redirects=True)
        response = tester.post("/user_info",
                             data=dict(new_password="GOATed"),
                             follow_redirects=True)
        self.assertIn(b"Changed username from GOAT to GOATed", response.data)
        self.assertIn(b"Password:", response.data)
        self.assertIn(b"GOATed", response.data)

    # test that users are looged out correctly
    def test_logout_user(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour",password="GOAT"),
                    follow_redirects=True)
        response = tester.get("/logout",
                             follow_redirects=True)
        self.assertIn(b"Signed Favour out", response.data)

    # ensure tasks are correctly added to the database and page
    def test_add_tasks_to_todo(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour",password="GOAT"),
                    follow_redirects=True)
        response1 = tester.post("/tasks",
                                data=dict(add_todo="sign"),
                                follow_redirects=True)
        self.assertIn(b"Added task", response1.data)
        self.assertIn(b"sign", response1.data)
        response2 = tester.get("/tasks", follow_redirects=True)
        self.assertIn(b"sign", response2.data)

    # ensure tasks are correctly moved from todo to doing
    def test_move_tasks_to_doing(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour", password="GOAT"),
                    follow_redirects=True)
        response1 = tester.post("/tasks",
                                data=dict(add_doing="cry"),
                                follow_redirects=True)
        self.assertIn(b"as doing", response1.data)
        self.assertIn(b"cry", response1.data)
        response2 = tester.get("/tasks", follow_redirects=True)
        self.assertIn(b"cry", response2.data)

    # ensure tasks are correctly moved from todo to doing
    def test_task_not_found(self):
        tester = app.test_client(self)
        tester.post('/',
                    data=dict(user_name="Favour", password="GOAT"),
                    follow_redirects=True)
        response1 = tester.post("/tasks",
                                data=dict(add_doing="cryed"),
                                follow_redirects=True)
        self.assertIn(b"Task not found", response1.data)
        response2 = tester.get("/tasks", follow_redirects=True)
        self.assertNotIn(b"cryed", response2.data)


if __name__ == '__main__':
    unittest.main()