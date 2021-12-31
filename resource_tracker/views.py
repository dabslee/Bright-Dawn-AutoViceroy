from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import LedgerLog, Player, Character, Debt
from . import forms
from django.contrib.auth.models import User as AuthUser
from django.http import HttpResponse

from datetime import datetime
from brightdawn.views import alwaysContext, lastSundayMidnight
from django.contrib.auth.decorators import login_required

# Utilities
def get_tier(character):
    games = character.xp
    if games < 9:
        return 1
    if games < 41:
        return 2
    if games < 73:
        return 3
    else:
        return 4

# AJAX views
def get_username_from_discord(request, discord):
    return HttpResponse(Player.objects.get(discord=discord).user.username)

def get_approval_characters_from_discord(request, discord):
    result = ""
    for chr in Character.objects.filter(
            status="PA",
            player__discord=discord
        ):
        result += str(chr.name) + "<br>"
    return HttpResponse(
        result
    )

def get_wealth_from_character(request, discord, character):
    return HttpResponse(Character.objects.get(
        player__discord=discord,
        name=character
    ).money)

# Standard views
@login_required
def ledger(request):
    context = alwaysContext(request)
    context["logs"] = LedgerLog.objects.all().order_by("-created")
    return render(request, "ledger.html", context)

@login_required
def claim_downtime(request):
    context = alwaysContext(request)
    user_player = context["user_player"]
    if user_player.last_downtime_claim < lastSundayMidnight():
        user_player.downtime += 10
        user_player.last_downtime_claim = datetime.now()
        user_player.save()
        LedgerLog.objects.create(note="%s claimed 10 downtime days." % user_player.user.username)
        return redirect("resource_tracker:ledger")
    else:
        context["message"] = "Unsuccessful! Downtime already claimed for this week!"
        return render(request, "success.html", context)

@login_required
def spend_resources(request):
    context = alwaysContext(request)
    if request.method == 'POST':
        form = forms.SpendResourcesForm(request.POST,
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ]))

        if form.is_valid():
            user_player = context["user_player"]
            character = Character.objects.get(player__user=request.user, name=form.cleaned_data["character_name"])
            character.money -= form.cleaned_data["spent_money"]
            user_player.downtime -= form.cleaned_data["spent_downtime"]
            user_player.spellcaster_hours -= form.cleaned_data["spent_spellcaster_hours"]
            character.save()
            user_player.save()
            LedgerLog.objects.create(note="%s's character %s spent %.3f gp, %d downtime days, and %.3f spellcasting hours: \"%s\"" % (
                request.user,
                character.name,
                form.cleaned_data["spent_money"],
                form.cleaned_data["spent_downtime"],
                form.cleaned_data["spent_spellcaster_hours"],
                form.cleaned_data["reason_for_expenditure"],
            ))
            return redirect("resource_tracker:ledger")
        else:
            print(form.errors)
    else:
        context["form"] = forms.SpendResourcesForm(character_name_choices = list([
            (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
        ]))
        return render(request, "spend_resources.html", context)

def character_approval(request):
    if not request.user.is_authenticated or not Player.objects.get(user=request.user).isViceroy:
        raise PermissionDenied()
    if request.method == 'POST':
        form = forms.CharacterApprovalForm(request.POST)

        if form.is_valid():
            # check if player exists
            if not Player.objects.filter(discord=form.cleaned_data['player_discord']).exists():
                user = AuthUser.objects.create_user(form.cleaned_data['player_username'], '', 'temp')
                player = Player.objects.create(
                    user = user,
                    discord = form.cleaned_data['player_discord'],
                )
                LedgerLog.objects.create(note="New player with discord %s and username %s joined." % (player.discord, user.username))
            player = Player.objects.get(discord=form.cleaned_data['player_discord'])

            character = Character.objects.filter(
                player = Player.objects.get(discord=form.cleaned_data['player_discord']),
                name = form.cleaned_data["character_name"]
            )
            if not character.exists(): # if first approval
                character = Character.objects.create(
                    player = player,
                    name = form.cleaned_data["character_name"],
                    money = form.cleaned_data["character_starting_wealth"]
                )
                LedgerLog.objects.create(note="%s's character %s received their first approval from viceroy %s." % (player.user.username, character.name, request.user.username))
            else: # if second approval
                character.update(status="AC")
                character.update(approved=datetime.now())
                character.update(money=form.cleaned_data["character_starting_wealth"])
                character = character.first()
                LedgerLog.objects.create(note="%s's character %s received their second approval from viceroy %s." % (player.user.username, character.name, request.user.username))
            tier = int(form.cleaned_data["character_tier"])
            viceroy = Player.objects.get(user=request.user)
            viceroy.viceroy_tokens += tier
            viceroy.save()
            LedgerLog.objects.create(note="%s received %d viceroy tokens for approving %s's tier %d character, %s." %(
                request.user.username,
                tier,
                player.user.username,
                tier,
                character.name
            ))
            return redirect("resource_tracker:ledger")
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.CharacterApprovalForm()
        context["discords"] = [player.discord for player in Player.objects.all()]
        return render(request, "character_approval.html", context)

@login_required
def redeem_viceroy_rewards(request):
    if not Player.objects.get(user=request.user).isViceroy:
        raise PermissionDenied()
    if request.method == 'POST':
        form = forms.RedeemViceroyRewardsForm(request.POST,
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ]),
            max_tokens = Player.objects.get(user=request.user).viceroy_tokens
        )

        if form.is_valid():
            character = Character.objects.get(player__user=request.user, name=form.cleaned_data["character_name"])
            reward_per_token = 0
            tier = get_tier(character)
            if tier == 1:
                reward_per_token = 5
            elif tier == 2:
                reward_per_token = 15
            elif tier == 3:
                reward_per_token = 60
            else:
                reward_per_token = 300
            number_of_tokens = int(form.cleaned_data["number_of_tokens"])
            total_reward = reward_per_token * number_of_tokens
            character.money += total_reward
            character.save()
            player = Player.objects.get(user=request.user)
            player.viceroy_tokens -= number_of_tokens
            player.save()
            LedgerLog.objects.create(note="%s's character %s received %.3f gp by redeeming %d viceroy tokens." % (
                request.user,
                character.name,
                total_reward,
                number_of_tokens
            ))
            return redirect("resource_tracker:ledger")
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.RedeemViceroyRewardsForm(
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ]),
            max_tokens = Player.objects.get(user=request.user).viceroy_tokens
        )
        return render(request, "redeem_viceroy_rewards.html", context)

@login_required
def claim_game_rewards(request):
    if request.method == 'POST':
        form = forms.ClaimGameRewardsForm(request.POST,
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ]))

        if form.is_valid():
            character = Character.objects.get(player__user=request.user, name=form.cleaned_data["character_name"])
            character.xp += form.cleaned_data["earned_xp"]
            character.money += form.cleaned_data["earned_gp"]
            character.save()
            LedgerLog.objects.create(note="%s's character %s received %.3f gp and %.3f game's xp for completing game %s." % (
                request.user,
                character.name,
                form.cleaned_data["earned_gp"],
                form.cleaned_data["earned_xp"],
                form.cleaned_data["game_id"],
            ))
            return redirect("resource_tracker:ledger")
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.ClaimGameRewardsForm(character_name_choices = list([
            (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
        ]))
        return render(request, "claim_game_rewards.html", context)

@login_required
def claim_gm_rewards(request):
    if not Player.objects.get(user=request.user).isGM:
        raise PermissionDenied()
    if request.method == 'POST':
        form = forms.ClaimGMRewardsForm(request.POST)

        if form.is_valid():
            player = Player.objects.get(user=request.user)
            player.gm_tokens += form.cleaned_data["gm_tokens"]
            player.save()
            LedgerLog.objects.create(note="%s received %d GM tokens for running game %s." % (
                request.user,
                form.cleaned_data["gm_tokens"],
                form.cleaned_data["game_id"],
            ))
            return redirect("resource_tracker:ledger")
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.ClaimGMRewardsForm()
        return render(request, "claim_gm_rewards.html", context)

@login_required
def character_list(request):
    if not (Player.objects.get(user=request.user).isViceroy or Player.objects.get(user=request.user).isGM):
        raise PermissionDenied()
    context = alwaysContext(request)
    context["characters"] = Character.objects.all()
    return render(request, "character_list.html", context)

@login_required
def player_list(request):
    if not (Player.objects.get(user=request.user).isViceroy or Player.objects.get(user=request.user).isGM):
        raise PermissionDenied()
    context = alwaysContext(request)
    context["players"] = Player.objects.all()
    return render(request, "player_list.html", context)

@login_required
def my_account(request):
    context = alwaysContext(request)
    context["player"] = Player.objects.get(user=request.user)
    context["characters"] = Character.objects.filter(player__user=request.user)
    return render(request, "my_account.html", context)
