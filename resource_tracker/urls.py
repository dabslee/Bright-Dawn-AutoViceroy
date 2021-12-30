from django.urls import path

from . import views

app_name = 'resource_tracker'
urlpatterns = [
    path('ledger/', views.ledger, name='ledger'),
    path('claim_downtime/', views.claim_downtime, name='claim_downtime'),
    path('spend_resources', views.spend_resources, name='spend_resources'),
    path('character_approval/', views.character_approval, name='character_approval'),
    path('redeem_viceroy_rewards/', views.redeem_viceroy_rewards, name='redeem_viceroy_rewards'),
    path('claim_game_rewards/', views.claim_game_rewards, name='claim_game_rewards'),
    path('claim_gm_rewards/', views.claim_gm_rewards, name='claim_gm_rewards'),
    path('character_list/', views.character_list, name='character_list'),
    path('player_list/', views.player_list, name='player_list'),
    path('my_account/', views.my_account, name='my_account'),

    # AJAX views
    path('get_approval_characters_from_discord/<discord>/', views.get_approval_characters_from_discord, name='get_approval_characters_from_discord'),
    path('get_username_from_discord/<discord>/', views.get_username_from_discord, name='get_username_from_discord'),
    path('get_wealth_from_character/<discord>/<character>/', views.get_wealth_from_character, name='get_wealth_from_character'),
]
