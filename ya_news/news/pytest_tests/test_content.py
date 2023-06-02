import pytest

from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_news_count(client, news_page_and_sorting_by_data):
    """Проверка количество постов на главное странице. """
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    news_count = len(object_list)
    assert news_count, settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, news_page_and_sorting_by_data):
    """
    Проверка сортировки от свежей к старой новости на главное странице.
    """
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    all_dates = [news.date for news in object_list]
    for i in range(len(all_dates) - 1):
        assert all_dates[i] >= all_dates[i + 1]


@pytest.mark.django_db
def test_comments_order(client, sorting_comments_by_data, news_id_for_args):
    """Проверка сортировки комментариев на странице новости."""
    url = reverse('news:detail', args=news_id_for_args)
    response = client.get(url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    for i in range(len(all_comments) - 1):
        assert all_comments[i].created <= all_comments[i + 1].created


def test_authorized_client_has_form(author_client, news):
    """Проверка наличии формы у авторизованного пользователя."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.get(url)
    assert 'form' in response.context


def test_anonymous_client_has_no_form(client, news):
    """Проверка отсутствии формы у анонимного пользователя."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context
