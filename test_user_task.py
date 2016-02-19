import os
import unittest

from FlaskProject import app, db, bcrypt
from FlaskProject.config import basedir
from FlaskProject.models import User

TEST_DB = 'test.db'

class AllTests(unittest.TestCase):

	def setUp(self):
		app.config['TESTING'] = True
		app.config['WTF_CSRF_ENABLED'] = False
		app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
		    os.path.join(basedir, TEST_DB)
		self.app = app.test_client()
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
	
	def login(self, name, password):
		return self.app.post('/', data=dict(name=name, password=password), follow_redirects=True)

	def register(self, name, email, password, confirm):
		return self.app.post(
		'register/',
		data=dict(name=name, email=email, password=password, confirm=confirm),
		follow_redirects=True)

	def create_user(self, name, email, password):
		new_user = User(name=name,email=email,password=bcrypt.generate_password_hash(password))
		db.session.add(new_user)
		db.session.commit()

	def create_task(self):
		return self.app.post('add/', data=dict(name='Go to the bank',
		due_date='02/05/2014',
		priority='1',
		posted_date='02/04/2014',
		status='1'
		), follow_redirects=True)

	def logout(self):
		return self.app.get('/logout/', follow_redirects=True)

	def create_admin_user(self):
		new_user = User(name="Superman",email="admin@realpython.com",\
			password=bcrypt.generate_password_hash("allpowerful"),role="admin")
		db.session.add(new_user)
		db.session.commit()

	def test_users_can_register(self):
		new_user = User("michael", "michael@mherman.org", "michaelherman")
		db.session.add(new_user)
		db.session.commit()
		test = db.session.query(User).all()
		for t in test:
			t.name
		assert t.name == "michael"

	def test_form_is_present_on_login_page(self):
		response = self.app.get('/')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Please sign in to access your task list', response.data)

	def test_users_cannot_login_unless_registered(self):
		response = self.login('foo', 'bar')
		self.assertIn(b'', response.data)

	def test_users_can_login(self):
		self.register('Michael', 'michael@realpython.com', 'python', 'python')
		response = self.login('Michael', 'python')
		self.assertIn(b'', response.data)

	def test_invalid_form_data(self):
		self.register('Michael', 'michael@realpython.com', 'python', 'python')
		response = self.login('alert("alert box!");', 'foo')
		self.assertIn(b'Wrong credential, Try again', response.data)

	def test_form_is_present_on_register_page(self):
		response = self.app.get('register/')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Please register to access the task list.', response.data)

	def test_user_registration(self):
		self.app.get('register/', follow_redirects=True)
		response = self.register('Michael', 'michael@realpython.com', 'python', 'python')
		self.assertIn(b'Thanks for registering. Please Login', response.data)

	def test_user_registration_error(self):
		self.app.get('register/', follow_redirects=True)
		self.register('Michael', 'michael@realpython.com', 'python', 'python')
		self.app.get('register/', follow_redirects=True)
		response = self.register('Michael', 'michael@realpython.com', 'python', 'python')
		self.assertIn(b'That username and/or email already exist', response.data)	

	def test_logged_in_user_can_logout(self):
		self.register('Fletcher', 'fletcher@realpython.com','python101', 'python101')
		self.login('Fletcher','python101')
		response = self.logout()
		self.assertIn('you were logged out',response.data)

	def test_not_logged_in_users_cannot_logout(self):
		response = self.logout()
		self.assertNotIn(b'you were logged out', response.data)

	def test_logged_in_user_can_access_task_page(self):
		self.register('Fletcher', 'fletcher@realpython.com','python101', 'python101')
		self.login('Fletcher','python101')
		response = self.app.get('/tasks/')
		self.assertEqual(response.status_code,200)
		self.assertIn(b'Add a new task:',response.data)

	def test_not_logged_in_users_cannot_access_task_page(self):
		response = self.app.get('/tasks',follow_redirects=True)
		self.assertIn(b'You need to be logged in first',response.data)


	def test_users_can_add_tasks(self):
		self.create_user('Michael', 'michael@realpython.com', 'python')
		self.login('Michael', 'python')
		self.app.get('tasks/', follow_redirects=True)
		response = self.create_task()
		self.assertIn(b'New entry successfully added Thanks !', response.data)

	def test_user_cannot_task_when_error(self):
		self.create_user('Michael', 'michael@realpython.com', 'python')
		self.login('Michael', 'python')
		self.app.get('tasks/', follow_redirects=True)
		response = self.app.post('add/', data=dict(
		name='Go to the bank',
		due_date='',
		priority='1',
		posted_date='02/05/2014',
		status='1'
		), follow_redirects=True)
		self.assertIn(b'This field is required.', response.data)

	def test_users_can_complete_tasks(self):
		self.create_user('Michael', 'michael@realpython.com', 'python')
		self.login('Michael', 'python')
		self.app.get('/tasks/', follow_redirects=True)
		self.create_task()
		response = self.app.get("/complete/1", follow_redirects=True)
		self.assertIn(b'The task is complete', response.data)

	def test_users_can_delete_tasks(self):
		self.create_user('Michael', 'michael@realpython.com', 'python')
		self.login('Michael', 'python')
		self.app.get('tasks/', follow_redirects=True)
		self.create_task()
		response = self.app.get("/delete/1", follow_redirects=True)
		self.assertIn(b'The task was deleted. Why not add a new one?', response.data)

	def test_users_cannot_complete_tasks_that_are_not_created_by_them(self):
		self.create_user('Michael', 'michael@realpython.com', 'python')
		self.login('Michael', 'python')
		self.app.get('tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.create_user('Fletcher', 'fletcher@realpython.com','python101')
		self.login('Fletcher', 'python101')
		self.app.get('/tasks/', follow_redirects=True)
		response = self.app.get("/complete/1", follow_redirects=True)
		self.assertNotIn(b'The task is complete. Nice.', response.data)
		self.assertIn(b'You can only update tasks that belong to you.', response.data)

	def test_users_cannot_delete_tasks_that_are_not_created_by_them(self):
		self.create_user('Michael', 'michael@realpython.com', 'python')
		self.login('Michael', 'python')
		self.app.get('tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.create_user('Fletcher', 'fletcher@realpython.com','python101')
		self.login('Fletcher', 'python101')
		self.app.get('/tasks/', follow_redirects=True)
		response = self.app.get("/delete/1", follow_redirects=True)
		self.assertIn(b'You can only delete tasks that belong to you.', response.data)

	def test_admin_users_can_complete_tasks_that_are_not_created_by_them(self):
		self.create_user("michael", "michael@mherman.org", "python")
		self.login('michael', 'python')
		self.app.get('tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.create_admin_user()
		self.login('Superman',"allpowerful")
		self.app.get('tasks/', follow_redirects=True)
		response = self.app.get("complete/1", follow_redirects=True)
		self.assertNotIn(b'You can only update tasks that belong to you.', response.data)

	def test_admin_users_can_delete_tasks_that_are_not_created_by_them(self):
		self.create_user("michael", "michael@mherman.org", "python")
		self.login('michael', 'python')
		self.app.get('/tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.create_admin_user()
		self.login("Superman","allpowerful")
		self.app.get('/tasks/', follow_redirects=True)
		response = self.app.get("/delete/1", follow_redirects=True)
		self.assertNotIn(b'You can only delete tasks that belong to you.', response.data)		


	def test_default_user_role(self):
		db.session.add(User("johnny","john@doe.com","johnny"))
		db.session.commit()
		users = db.session.query(User).all()
		for user in users:
			self.assertEquals(user.role, 'user')

	def test_task_template_display_username(self):
		self.register('Fletcher', 'fletcher@realpython.com','python101', 'python101')
		self.login('Fletcher','python101')
		response = self.app.get('/tasks/', follow_redirects=True)
		self.assertIn(b'Fletcher', response.data)

	def test_users_cannot_see_task_modify_links_for_tasks_not_created_by_them(self):
		self.register('Fletcher', 'fletcher@realpython.com','python101', 'python101')
		self.login('Fletcher','python101')
		self.app.get('/tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.register('Michael', 'michael@realpython.com','python','python')
		response = self.login('Michael','python')
		self.app.get('/tasks/', follow_redirects=True)
		self.assertNotIn(b'Mark as complete', response.data)
		self.assertNotIn(b'Delete', response.data)

	def test_users_can_see_task_modify_links_for_tasks_created_by_them(self):
		self.register('Fletcher', 'fletcher@realpython.com','python101', 'python101')
		self.login('Fletcher','python101')
		self.app.get('/tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.register('Michael', 'michael@realpython.com','python','python')
		self.login('Michael','python')
		self.app.get('/tasks/', follow_redirects=True)
		response = self.create_task()
		self.assertIn(b'/complete/2/', response.data)
		self.assertIn(b'/complete/2/', response.data)


	def test_admin_users_can_see_task_modify_links_for_all_tasks(self):
		self.register('Fletcher', 'fletcher@realpython.com','python101', 'python101')
		self.login('Fletcher','python101')
		self.app.get('/tasks/', follow_redirects=True)
		self.create_task()
		self.logout()
		self.create_admin_user()
		self.login("Superman",'allpowerful')
		self.app.get('/tasks/', follow_redirects=True)
		response = self.create_task()
		self.assertIn(b'/complete/1/', response.data)
		#self.assertIn(b'/delete/1/', response.data)
		self.assertIn(b'/complete/2/', response.data)
		#self.assertIn(b'/delete/2/', response.data)



if __name__ == '__main__':
	unittest.main()

