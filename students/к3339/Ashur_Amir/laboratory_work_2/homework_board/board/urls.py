from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeworkListView.as_view(), name='homework_list'),
    path('homework/new/', views.HomeworkCreateView.as_view(), name='homework_create'),
    path('homework/<int:pk>/', views.homework_detail, name='homework_detail'),
    path('homework/<int:pk>/edit/', views.HomeworkUpdateView.as_view(), name='homework_update'),
    path('homework/<int:pk>/delete/', views.HomeworkDeleteView.as_view(), name='homework_delete'),
    path('submissions/', views.my_submissions, name='my_submissions'),
    path('submissions/<int:pk>/delete/', views.submission_delete, name='submission_delete'),
    path('submissions/<int:pk>/grade/', views.grade_submission, name='grade_submission'),
    path('review/', views.review, name='review'),
    path('grades/', views.grades_table, name='grades_table'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
]
