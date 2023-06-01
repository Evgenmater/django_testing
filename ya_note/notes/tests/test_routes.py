from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

from http import HTTPStatus

User = get_user_model()


class TestRoutes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Ержан Макакович')
        cls.another_user = User.objects.create(username='Его тёща')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            author=cls.author,
        )

    def test_pages_availability_for_home_and_userslog(self):
        """
        Проверка доступность главной страницы, страницу логина, логаута
          и регистрации для анонимного пользователя.
        """
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes_detail_and_edit_and_delete(self):
        """
        Проверка доступности автора для редакции, удаления и страницы
        заметки и недоступность другого пользователя для чужих заметок.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.another_user, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:detail', 'notes:delete',):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_for_registered_users(self):
        """
        Проверка доступности страниц для создании, списка заметок
        и успешного выполнения операции для авторизированного пользователя.
        """
        users = self.author
        self.client.force_login(users)
        for name in ('notes:success', 'notes:list', 'notes:add'):
            with self.subTest(users=users, name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        Проверка редиректа для анонимного пользователя при посещении
        страниц: поиска заметок, успешного добавления записи, список
        заметок, отдельной заметки, редактирования или удаления заметки.
        """
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                if args is not None:
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
