from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('perusahaan/', views.company_list, name='company_list'),
    path('perusahaan/tambah/', views.company_create, name='company_create'),
    path('perusahaan/<int:pk>/edit/', views.company_update, name='company_update'),
    path('perusahaan/<int:pk>/hapus/', views.company_delete, name='company_delete'),

    path('pekerja/', views.worker_list, name='worker_list'),
    path('pekerja/tambah/', views.worker_create, name='worker_create'),
    path('pekerja/<int:pk>/', views.worker_detail, name='worker_detail'),
    path('pekerja/<int:pk>/edit/', views.worker_update, name='worker_update'),
    path('pekerja/<int:pk>/hapus/', views.worker_delete, name='worker_delete'),

    path('dokumen/', views.document_list, name='document_list'),
    path('dokumen/tambah/', views.document_create, name='document_create'),
    path('dokumen/<int:pk>/edit/', views.document_update, name='document_update'),
    path('dokumen/<int:pk>/hapus/', views.document_delete, name='document_delete'),
    path('dokumen/<int:pk>/perpanjang/', views.document_renew, name='document_renew'),

    path('export/workers.csv', views.export_workers_csv, name='export_workers_csv'),
    path('export/documents.csv', views.export_documents_csv, name='export_documents_csv'),
]

