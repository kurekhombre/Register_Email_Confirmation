from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect


from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage

from .forms import CustomUserCreationForm, LoginUser
from .tokens import acount_activation_token

# Create your views here.


def index(request):
    return render(request, 'app/index.html')


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and acount_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, 'Thank you for your email confirmation. Now you can login your account')
        # login(request, user)
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')

    return redirect('index')


def activate_email(request, user, to_email):
    mail_subject = "Activate your user account."
    message = render_to_string('app/template_activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': acount_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Dear <b>{user}</b>, please go to your email <b>{to_email}</b> inbox and click on ' \
                             f' received activation link to confirm and complete the registration. <b>Note:</b>' \
                             f'Check your spam folder.')
    else:
        messages.error(request, f'Problem sending to {to_email}, check if you typed it correctly.')


def register_user(request):
    form = CustomUserCreationForm

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # --- email confirmation
            user.is_active=False
            user.save()
            activate_email(request, user, form.cleaned_data.get('email'))
            # ---
            messages.success(request, "User account was created successfully")

            return redirect('index')
        else:
            messages.error(request, "Error!")

    return render(request, 'app/register.html', {'form': form})


def login_user(request):
    form = LoginUser

    if request.method == "POST":
        username = request.POST['username'].lower()
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You re logged in")
            return redirect('index')
        else:
            messages.error(request, "Username or password is incorrect")

    return render(request, 'app/login.html', {'form': form})


def logout_user(request):
    logout(request)
    messages.info(request, "User was logged out")
    return redirect('login')


@login_required(login_url='login')
def index(request):
    return render(request, 'app/index.html')


