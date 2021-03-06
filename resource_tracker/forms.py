from django import forms
from .models import Player

class CharacterApprovalForm(forms.Form):
    player_discord = forms.CharField(max_length=50)
    player_username = forms.CharField(max_length=50, required=False)
    character_name = forms.CharField(max_length=100)
    character_starting_wealth = forms.FloatField(initial=0)
    character_tier = forms.ChoiceField(choices=(
        (1, "Tier 1"),
        (2, "Tier 2"),
        (3, "Tier 3"),
        (4, "Tier 4")
    ))

class ClaimGameRewardsForm(forms.Form):
    character_name = forms.ChoiceField(choices=())
    earned_gp = forms.FloatField()
    earned_xp = forms.FloatField()
    game_id = forms.CharField(max_length=50)

    def __init__(self, *args, **kwargs):
        character_name_choices = kwargs.pop('character_name_choices')
        super().__init__(*args, **kwargs)
        self.fields["character_name"].choices = character_name_choices

class ClaimGMRewardsForm(forms.Form):
    gm_tokens = forms.ChoiceField(choices=(
        (3, "Half game (1.5-3 hours): 3 token reward"),
        (6, "Full game (3-5.5 hours): 6 token reward"),
        (9, "1.5 game (5.5-7 hours): 9 token reward"),
        (12, "Double game (7-9.5 hours): 12 token reward"),
    ))
    game_id = forms.CharField(max_length=50)

class RedeemViceroyRewardsForm(forms.Form):
    character_name = forms.ChoiceField(choices=())
    number_of_tokens = forms.ChoiceField(choices=())

    def __init__(self, *args, **kwargs):
        character_name_choices = kwargs.pop('character_name_choices')
        max_tokens = kwargs.pop('max_tokens')
        super().__init__(*args, **kwargs)
        self.fields["character_name"].choices = character_name_choices
        self.fields["number_of_tokens"].choices = list([(i, i) for i in range(1, max_tokens+1)])

class RedeemGMRewardsForm(forms.Form):
    character_name = forms.ChoiceField(choices=())
    expenditure = forms.ChoiceField(choices=(
        ("Full Game XP + Full Game GP", "Full Game XP + Full Game GP (8 tokens)"),
        ("Half Game XP + Half Game GP", "Half Game XP + Half Game GP (4 tokens)"),
        ("Full Game XP", "Full Game XP (6 tokens)"),
        ("Half Game XP", "Half Game XP (3 tokens)"),
        ("Full Game GP", "Full Game GP (6 tokens)"),
        ("Half Game GP", "Half Game GP (3 tokens)"),
        ("Other 6 token expenditure", "Other 6 token expenditure (6 tokens)"),
        ("Other 3 token expenditure", "Other 3 token expenditure (3 tokens)"),
    ))
    if_other_specify_here = forms.CharField(max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        character_name_choices = kwargs.pop('character_name_choices')
        super().__init__(*args, **kwargs)
        self.fields["character_name"].choices = character_name_choices

class SpendResourcesForm(forms.Form):
    character_name = forms.ChoiceField(choices=())
    spent_money = forms.FloatField(min_value=0, initial=0)
    spent_downtime = forms.IntegerField(min_value=0, initial=0)
    spent_spellcaster_hours = forms.FloatField(min_value=0, initial=0)
    reason_for_expenditure = forms.CharField(max_length=1000)

    def __init__(self, *args, **kwargs):
        character_name_choices = kwargs.pop('character_name_choices')
        super().__init__(*args, **kwargs)
        self.fields["character_name"].choices = character_name_choices

class TradeForm(forms.Form):
    my_character_name = forms.ChoiceField(choices=())
    other_player_username = forms.ChoiceField(choices=list([(player.user.username, player.user.username) for player in Player.objects.all()]))
    other_player_character_name = forms.CharField()
    selling_or_buying = forms.ChoiceField(choices=(
        ("Selling", "Selling"),
        ("Buying", "Buying")
    ))
    money_amount = forms.FloatField(min_value=0)
    what_is_being_purchased = forms.CharField(max_length=1000)
    other_stipulations = forms.CharField(max_length=1000)

    def __init__(self, *args, **kwargs):
        character_name_choices = kwargs.pop('character_name_choices')
        super().__init__(*args, **kwargs)
        self.fields["my_character_name"].choices = character_name_choices