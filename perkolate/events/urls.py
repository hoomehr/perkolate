from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Event URLs
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/update/', views.event_update, name='event_update'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    
    # Target URLs
    path('targets/', views.target_list, name='target_list'),
    path('targets/create/', views.target_create, name='target_create'),
    path('targets/<int:pk>/', views.target_detail, name='target_detail'),
    path('targets/<int:pk>/update/', views.target_update, name='target_update'),
    path('targets/<int:pk>/delete/', views.target_delete, name='target_delete'),
    
    # Note URLs
    path('notes/', views.note_board, name='note_board'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/update/', views.note_update, name='note_update'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('notes/<int:pk>/vote/', views.note_vote, name='note_vote'),
] 