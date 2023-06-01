from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestDetailNotes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='username')
        cls.another_user = User.objects.create(username='another user')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='текст.',
            author=cls.author,
        )
        cls.author_client = Client()
        cls.another_user_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user_client.force_login(cls.another_user)

    def test_authorized_client_has_form(self):
        """
        Проверка наличии формы страницы создания и
        редактирования заметки  авторизованного пользователя.
        """
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:add', None),
        )
        self.client.force_login(self.author)
        for name, args in (urls):
            with self.subTest(name=name):
                if args is not None:
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
            response = self.client.get(url)
            self.assertIn('form', response.context)

    def test_notes_list_for_different_users(self):
        """
        Проверка заметки, которая передаётся на страницу со списком заметок
         и чтобы заметки пользователя не попадали к другому пользователю.
        """
        url = reverse('notes:list')
        response = self.author_client.get(url)
        response_another_user = self.another_user_client.get(url)
        object_list = response.context['object_list']
        object_list_another_user = response_another_user.context['object_list']
        self.assertIn(self.note, object_list)
        self.assertNotIn(self.note, object_list_another_user)
