from django.shortcuts import render

# Create your views here.
# app/dealers/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Dealer, DealerRole
from .forms import JoinDealerForm, AddDealerUserForm
from .utils import is_dealer_admin

@login_required
def join_dealer(request):
    if request.method == "POST":
        form = JoinDealerForm(request.POST)
        if form.is_valid():
            secure_id = form.cleaned_data["secure_id"]
            dealer = get_object_or_404(Dealer, secure_id=secure_id)
            request.user.dealer = dealer
            request.user.save()
            DealerRole.objects.get_or_create(user=request.user, dealer=dealer, role="viewer")
            return redirect("dashboard")
    else:
        form = JoinDealerForm()
    return render(request, "dealers/join_dealer.html", {"form": form})

@login_required
def add_user_to_dealer(request, dealer_id):
    dealer = get_object_or_404(Dealer, id=dealer_id)
    if not is_dealer_admin(request.user, dealer):
        return HttpResponseForbidden("Yetkiniz yok.")

    if request.method == "POST":
        form = AddDealerUserForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            role = form.cleaned_data["role"]
            user.dealer = dealer
            user.save()
            DealerRole.objects.update_or_create(user=user, dealer=dealer, defaults={"role": role})
            return redirect("dealer_detail", dealer_id=dealer.id)
    else:
        form = AddDealerUserForm()

    return render(request, "dealers/add_user.html", {"form": form, "dealer": dealer})
