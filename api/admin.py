from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Profile, Asset, IsraelPaper, USPaper, Crypto, AssetRecord,\
    Portfolio, PortfolioRecord, PortfolioAction

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Asset)
admin.site.register(IsraelPaper)
admin.site.register(USPaper)
admin.site.register(Crypto)
admin.site.register(AssetRecord)
admin.site.register(Portfolio)
admin.site.register(PortfolioRecord)
admin.site.register(PortfolioAction)
