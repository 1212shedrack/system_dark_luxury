# accounts/mixins.py

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class CashierOrAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and \
               self.request.user.role in ['admin', 'cashier']

    def handle_no_permission(self):
        return redirect('product_list')
