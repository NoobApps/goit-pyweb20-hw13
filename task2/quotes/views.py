from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Quote, Author
from .forms import RegisterForm, AuthorForm, QuoteForm

def home(request):
    quotes_list = Quote.objects.select_related('author').all().order_by('-created_at')

    author_id = request.GET.get('author')
    selected_author = None
    if author_id:
        selected_author = get_object_or_404(Author, pk=author_id)
        quotes_list = quotes_list.filter(author=selected_author)

    tag = request.GET.get('tag')
    if tag:
        quotes_list = quotes_list.filter(tags__icontains=tag)

    paginator = Paginator(quotes_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'quotes/home.html', {
        'page_obj': page_obj,
        'selected_author': selected_author,
        'selected_tag': tag,
    })

def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, 'quotes/author_detail.html', {'author': author})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'quotes/register.html', {'form': form})

@login_required
def add_author(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save(commit=False)
            author.created_by = request.user
            author.save()
            return redirect('home')
    else:
        form = AuthorForm()
    return render(request, 'quotes/add_author.html', {'form': form})

@login_required
def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by = request.user
            quote.save()
            return redirect('home')
    else:
        form = QuoteForm()
    return render(request, 'quotes/add_quote.html', {'form': form})
