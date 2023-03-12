from django.core.paginator import Paginator


def paginator_posts(request, posts, post_per_page=10):
    paginator = Paginator(posts, post_per_page)
    num_page = request.GET.get('page')
    return paginator.get_page(num_page)
