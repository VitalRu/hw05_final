from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_page

AMOUNT_POSTS = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = get_page(posts, AMOUNT_POSTS, request)
    return render(
        request,
        'posts/index.html',
        {
            'page_obj': page_obj,
        }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_page(group.posts.all(), AMOUNT_POSTS, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj = get_page(author.posts.all(), AMOUNT_POSTS, request)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': author,
        'user': request.user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(
        request.POST,
        instance=post
    )
    context = {
        'post': post,
        'form': form,
        'comments': post.comments.all()
    }
    return render(
        request,
        'posts/post_detail.html',
        context
    )


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {
                'form': form,
            }
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(
        'posts:profile',
        post.author.username
    )


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(
        request,
        'posts/create_post.html',
        context
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(
        'posts:post_detail',
        post_id=post_id
    )


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page(posts, AMOUNT_POSTS, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not Follow.objects.filter(
        user=request.user,
        author=author
    ):
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect(
        'posts:profile',
        author.username
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.filter(
            user=request.user,
            author=author,
        ).delete()
    return redirect(
        'posts:profile',
        author.username
    )
