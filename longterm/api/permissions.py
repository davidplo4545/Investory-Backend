from rest_framework import permissions


class IsPortfolioOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ["list", "me"]:
            return True
        elif view.action in ["partial_update", "update", "destroy", "compare", "retrieve"]:
            # only portfolio user can edit/delete/compare the portfolio
            return obj.profile == request.user.profile
        return False


class IsPortfolioComparisonOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ["retrieve", "list"]:
            return True
        elif view.action in ["partial_update", "update", "destroy"]:
            # only portfolio user can edit/delete/compare the portfolio
            return obj.profile == request.user.profile
        return False
