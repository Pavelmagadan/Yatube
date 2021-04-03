from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page_number': page_number, 'page': page}
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
        {'group': group, 'page': page}
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
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    posts_count = author.posts.count()
    number_of_following = author.follower.count()
    number_of_follower = author.following.count()
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'author': author,
            'post': post,
            'posts_count': posts_count,
            'number_of_follower': number_of_follower,
            'number_of_following': number_of_following,
            'comments': comments,
            'form': form,
        }
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following_flag = None
    if request.user.is_authenticated and request.user != author:
        following_flag = author.following.filter(user=request.user).exists()
    post_list = author.posts.all()
    posts_count = author.posts.count()
    number_of_following = author.follower.count()
    number_of_follower = author.following.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {
            'author': author,
            'following_flag': following_flag,
            'number_of_follower': number_of_follower,
            'number_of_following': number_of_following,
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
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    posts_count = author.posts.count()
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


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page_number': page_number, 'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(
        User,
        # .objects.exclude(username=request.user.username),
        username=username
    )
    if author.following.filter(user=request.user).exists():
        return redirect(
            reverse(
                'profile',
                kwargs={'username': username}
            )
        )
    if author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect(
        reverse(
            'profile',
            kwargs={'username': username}
        )
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    delited_follow = get_object_or_404(
        Follow,
        user=request.user,
        author=author
    )
    delited_follow.delete()
    return redirect(
        reverse(
            'profile',
            kwargs={'username': username}
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
