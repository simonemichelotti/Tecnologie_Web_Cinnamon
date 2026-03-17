from django.urls import path
from . import views

urlpatterns = [
    path('', views.RecipeListView.as_view(), name='recipes-home'),
    path('recipe/<int:pk>/', views.RecipeDetailView.as_view(), name='recipes-detail'),
    path('recipe/<int:pk>/comment/', views.add_comment, name='add-comment'),
    path('recipe/create/', views.RecipeCreateView.as_view(), name='recipes-create'),
    path('recipe/<int:pk>/update/', views.RecipeUpdateView.as_view(), name='recipes-update'),
    path('recipe/<int:pk>/delete/', views.RecipeDeleteView.as_view(), name='recipes-delete'),
    path('recipe/<int:recipe_id>/like/', views.toggle_like, name='recipe-like'),
    
]