"""Account-management views (profile + admin user list)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import UserCreateForm
from .models import Role, User
from .permissions import role_required


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"user_obj": request.user})


@role_required(Role.ADMIN)
def user_list(request):
    users = User.objects.order_by("username")
    return render(request, "accounts/user_list.html", {"users": users, "Role": Role})


@role_required(Role.ADMIN)
def user_create(request):
    """Admin-only form to invite/create a teammate."""
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"User '{user.username}' created with role '{user.get_role_display()}'.",
            )
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {"form": form})


@role_required(Role.ADMIN)
@require_http_methods(["POST"])
def change_role(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    new_role = request.POST.get("role")
    if new_role not in dict(Role.choices):
        messages.error(request, "Invalid role.")
        return redirect("accounts:user_list")
    # An admin cannot lower their own privileges. Prevents both
    # accidental self-demotion AND a takeover scenario where a compromised
    # admin session is used to leave only the attacker with admin rights.
    if request.user.pk == target.pk and new_role != Role.ADMIN:
        messages.error(request, "You can't change your own role. Ask another admin to do it.")
        return redirect("accounts:user_list")
    target.role = new_role
    target.save(update_fields=["role"])
    messages.success(request, f"Updated {target.username} to {new_role}.")
    return redirect("accounts:user_list")
