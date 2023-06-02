from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNotesCreation(TestCase):
    """Класс для проверки отправки заметки"""
    NOTES_TEXT = 'Текст заметки'
    NOTES_TITLE = 'Заголовок заметки'
    NOTES_SLUG = 'zagolovok-zametki'
    EMPTY_LIST_COUNT = 0

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
        )
        cls.url_add = reverse('notes:add')
        cls.url_list = reverse('notes:list')
        cls.url_done = reverse('notes:success')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {
            'title': cls.NOTES_TITLE,
            'text': cls.NOTES_TEXT,
        }

    def test_user_can_send_note(self):
        """Проверим, что залогиненный пользователь может создать заметку."""
        init_count = Note.objects.count()
        response = self.author_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        self.assertEqual(Note.objects.count(), init_count + 1)
        note = Note.objects.get(id=2)
        note_dict_objects = {
            note.text: self.NOTES_TEXT,
            note.title: self.NOTES_TITLE,
            note.slug: self.NOTES_SLUG,
            note.author: self.note.author,
        }
        for note_field, init_note_field in note_dict_objects.items():
            with self.subTest(
                note_field=note_field,
                init_note_field=init_note_field,
            ):
                self.assertEqual(note_field, init_note_field)

    def test_anonymous_user_can_create_note(self):
        """Проверим, что анонимный пользователь не может создать заметку."""
        init_count = Note.objects.count()
        response = self.client.post(self.url_add, data=self.form_data)
        login_url = reverse('users:login')
        redirect_url = f'{login_url}?next={self.url_add}'
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Note.objects.count(), init_count)
        self.assertEqual(
            Note.objects.filter(**self.form_data).count(),
            self.EMPTY_LIST_COUNT,
        )

    def test_not_unique_slug(self):
        """Проверка на невозможность создать две заметки с одинаковым slug."""
        init_count = Note.objects.count()
        new_data = {
            'text': self.NOTES_TEXT,
            'title': self.NOTES_TITLE,
            'slug': self.note.slug,
            'author': self.author,
        }
        response = self.author_client.post(self.url_add, data=new_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), init_count)
        note = Note.objects.get()
        note_dict_objects = {
            note.text: self.note.text,
            note.title: self.note.title,
            note.slug: self.note.slug,
            note.author: self.note.author,
        }
        for note_field, init_note_field in note_dict_objects.items():
            with self.subTest(
                note_field=note_field,
                init_note_field=init_note_field,
            ):
                self.assertEqual(note_field, init_note_field)


class TestNotesEditDelete(TestCase):
    """Класс для проверки отправки заметки."""
    NOTES_TEXT = 'Текст заметки'
    NOTES_TITLE = 'Заголовок заметки'
    NEW_NOTES_TEXT = 'Обновлённый текст заметки'
    NEW_NOTES_TITLE = 'Обновлённый заголовок заметки'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.another_user = User.objects.create(username='Пользователь')
        cls.note = Note.objects.create(
            title=cls.NOTES_TITLE,
            text=cls.NOTES_TEXT,
            author=cls.author
        )
        note_slug = cls.note.slug
        cls.url_detail = reverse('notes:detail', args=(note_slug,))
        cls.url_edit = reverse('notes:edit', args=(note_slug,))
        cls.url_delete = reverse('notes:delete', args=(note_slug,))
        cls.url_list = reverse('notes:list')
        cls.url_done = reverse('notes:success')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)
        cls.form_data = {
            'title': cls.NEW_NOTES_TITLE,
            'text': cls.NEW_NOTES_TEXT,
        }

    def test_author_can_edit_note(self):
        """Проверка доступа у автора на редактирования заметки."""
        response = self.author_client.post(self.url_edit, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        self.note.refresh_from_db()
        note_dict_object = {
            self.note.text: self.NEW_NOTES_TEXT,
            self.note.title: self.NEW_NOTES_TITLE,
        }
        for note_field, init_note_field in note_dict_object.items():
            with self.subTest(
                note_field=note_field,
                init_note_field=init_note_field,
            ):
                self.assertEqual(note_field, init_note_field)

    def test_user_cant_edit_note_of_another_user(self):
        """Проверка на редактирование чужой заметки."""
        response = self.another_user_client.post(
            self.url_edit,
            data=self.form_data,
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        note_dict_object = {
            self.note.text: self.NOTES_TEXT,
            self.note.title: self.NOTES_TITLE,
        }
        for note_field, init_note_field in note_dict_object.items():
            with self.subTest(
                note_field=note_field,
                init_note_field=init_note_field,
            ):
                self.assertEqual(note_field, init_note_field)

    def test_author_can_delete_note(self):
        """Проверка доступа у автора на удаление заметки."""
        init_count = Note.objects.count()
        response = self.author_client.delete(self.url_delete)
        self.assertRedirects(response, self.url_done)
        self.assertEqual(Note.objects.count(), init_count - 1)

    def test_user_cant_delete_note_of_another_user(self):
        """Проверка на удаление чужой заметки."""
        init_count = Note.objects.count()
        response = self.another_user_client.delete(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), init_count)


class TestModelSlug(TestCase):
    """
    Класс для проверки ограничений символов и на автоматическое
    формирование slug из содержимого поля title.
    """
    TITLE_COUNT = 100

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.note = Note.objects.create(
            title='Ж' * cls.TITLE_COUNT,
            text='Тестовый текст',
            author=cls.author,
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

    def test_text_convert_to_slug(self):
        """
        Проверка slug на ограничение символов и на автоматическое
        формирование slug из содержимого поля title.
        """
        data = {
            'title': 'душнила',
            'text': self.note.text,
            'author': self.note.author,
        }
        self.author_client.post(reverse('notes:add'), data=data)
        note = Note.objects.get(title='душнила')
        self.assertEqual(
            note.slug,
            slugify(note.title)[:self.TITLE_COUNT],
        )

    def test_text_slug_max_length_not_exceed(self):
        """Проверка длинны slug(не более 100 символов)."""
        max_length_slug = self.note._meta.get_field('slug').max_length
        length_slug = len(self.note.slug)
        self.assertEqual(max_length_slug, length_slug)
