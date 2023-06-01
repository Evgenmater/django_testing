import pytest

from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING

from news.models import Comment

from http import HTTPStatus


COMMENT_DELET = 0
COMMENT_NOT_DELET = 1


def test_user_can_create_comment(author_client, author, form_data, news):
    """Проверим, что залогиненный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    assert Comment.objects.count() == COMMENT_NOT_DELET
    new_note = Comment.objects.get()
    assert new_note.text == form_data['text']
    assert new_note.news == news
    assert new_note.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, form_data, news):
    """Проверка, что анонимный пользователь не может добавить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == COMMENT_DELET


def test_author_can_edit_comment(author_client, form_data, comment):
    """Проверка доступа у автора на редактирование комментария."""
    url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(url, form_data)
    url_comment = reverse('news:detail', args=(comment.id,))
    assertRedirects(response, f'{url_comment}#comments')
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_author_can_delete_comment(author_client, comment):
    """Проверка доступа у автора на удаление комментария."""
    url = reverse('news:delete', args=(comment.id,))
    response = author_client.post(url)
    url_comment = reverse('news:detail', args=(comment.id,))
    assertRedirects(response, f'{url_comment}#comments')
    assert Comment.objects.count() == COMMENT_DELET


def test_other_user_cant_edit_note(admin_client, form_data, comment):
    """
    Проверка доступа у авторизованного пользователя на
    редактирование чужого комментария.
    """
    url = reverse('news:edit', args=(comment.id,))
    response = admin_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text


def test_other_user_cant_delete_note(admin_client, form_data, comment):
    """
    Проверка доступа у авторизованного пользователя на
    удаление чужого комментария.
    """
    url = reverse('news:delete', args=(comment.id,))
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == COMMENT_NOT_DELET


def test_user_cant_use_bad_words(author_client, comment, form_data):
    """Проверка на зпрещённые слова при комментировании."""
    url = reverse('news:detail', args=(comment.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, bad_words_data)
    assertFormError(response, 'form', 'text', errors=WARNING)
    assert Comment.objects.count() == COMMENT_NOT_DELET
