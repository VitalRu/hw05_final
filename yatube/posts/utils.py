import django
from django.core.paginator import Paginator


def get_page(
        queryset: django.db.models.query.QuerySet,
        obj_per_page: int,
        request: django.http.HttpRequest,
) -> django.core.paginator.Paginator:
    paginator = Paginator(queryset, obj_per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
