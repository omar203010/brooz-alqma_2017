from django.urls import path
from . import views

app_name = 'units'

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('policy/', views.policy, name='policy'),
    path('units/', views.units, name='units'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/unit/<int:unit_id>/bookings/', views.unit_bookings, name='unit_bookings'),
    path('api/unit/<int:unit_id>/bookings/create/', views.create_booking, name='create_booking'),
    path('api/unit/<int:unit_id>/bookings/cancel/', views.cancel_booking, name='cancel_booking'),
    # admin reports
    path('reports/payment-reports/', views.payment_reports, name='payment_reports'),
    path('reports/payment-reports/pdf/', views.payment_reports_pdf, name='payment_reports_pdf'),
    path('reports/payment-reports/excel/', views.payment_reports_excel, name='payment_reports_excel'),
    # auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # expenses
    path('unit/<int:unit_id>/expenses/', views.unit_expenses, name='unit_expenses'),
    path('expense/<int:expense_id>/', views.expense_detail, name='expense_detail'),
    # pricing
    path('unit/<int:unit_id>/pricing/', views.unit_pricing, name='unit_pricing'),
    # gallery
    path('unit/<int:unit_id>/gallery/', views.unit_gallery, name='unit_gallery'),
]

