from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .forms import CommentForm, PostForm
from .models import Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page_number': page_number, 'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    view_def = 'new_post'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(
            request,
            'new.html',
            {'form': form, 'view_def': view_def}
        )
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('index')


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    authors_posts = author.posts.all()
    post = get_object_or_404(authors_posts, id=post_id)
    posts_count = authors_posts.count()
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'author': author,
            'post': post,
            'posts_count': posts_count,
            'comments': comments,
            'form': form,
        }
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {
            'author': author,
            'page': page,
            'posts_count': posts_count,
        }
    )


def post_edit(request, username, post_id):
    if username != request.user.username:
        return redirect(
            reverse(
                'post',
                kwargs={'username': username, 'post_id': post_id}
            )
        )
    view_def = 'post_edit'
    old_post = Post.objects.get(id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=old_post
    )
    if not form.is_valid():
        return render(
            request,
            'new.html',
            {'form': form, 'old_post': old_post, 'view_def': view_def}
        )
    form.save()
    return redirect(
        reverse(
            'post',
            kwargs={'username': username, 'post_id': post_id}
        )
    )


@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    authors_posts = author.posts.all()
    post = get_object_or_404(authors_posts, id=post_id)
    posts_count = authors_posts.count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'post.html',
            {
                'author': author,
                'post': post,
                'posts_count': posts_count,
                'comments': comments,
                'form': form,
            }
        )
    new_comment = form.save(commit=False)
    new_comment.author = request.user
    new_comment.post = post
    new_comment.save()
    return redirect(
        reverse(
            'post',
            kwargs={'username': username, 'post_id': post_id}
        )
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
