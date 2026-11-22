from django.urls import path
from .views import DisagreementsView

urlpatterns = [path("disagreements/", DisagreementsView.as_view())]