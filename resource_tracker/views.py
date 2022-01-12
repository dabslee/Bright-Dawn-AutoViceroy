from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from .models import LedgerLog, Player, Character, Debt, Trade
from . import forms
from django.contrib.auth.models import User as AuthUser
from django.http import HttpResponse
from django.db.models import Q

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

def gold_by_tier(tier):
    if tier == 1:
        return 80
    elif tier == 2:
        return 250
    elif tier == 3:
        return 1000
    elif tier == 4:
        return 5000

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

def get_all_characters_from_username(request, username):
    result = ""
    for chr in Character.objects.filter(
            player__user__username=username
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
    if user_player.last_downtime_claim == None or user_player.last_downtime_claim < lastSundayMidnight():
        user_player.downtime += 10
        user_player.last_downtime_claim = datetime.now()
        user_player.save()

        most_recent = LedgerLog.objects.create(note="%s claimed 10 downtime days, going from %d days to %d days." % (
            user_player.user.username,
            user_player.downtime-10,
            user_player.downtime
        ))
        context["message"] = most_recent.note
        context["logs"] = LedgerLog.objects.all().order_by("-created")
        return render(request, "ledger.html", context)
    else:
        context["error"] = True
        context["message"] = "Unsuccessful! Downtime already claimed for this week!"
        context["logs"] = LedgerLog.objects.all().order_by("-created")
        return render(request, "ledger.html", context)

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
            note="%s spent %.3f gp (%.3f=>%.3f), %d downtime days (%d=>%d), and %.3f spellcasting hours (%.3f=>%.3f): \"%s\"" % (
                str(character),
                form.cleaned_data["spent_money"],
                character.money + form.cleaned_data["spent_money"],
                character.money,
                form.cleaned_data["spent_downtime"],
                user_player.downtime + form.cleaned_data["spent_downtime"],
                user_player.downtime,
                form.cleaned_data["spent_spellcaster_hours"],
                user_player.spellcaster_hours + form.cleaned_data["spent_spellcaster_hours"],
                user_player.spellcaster_hours,
                form.cleaned_data["reason_for_expenditure"],
            )
            LedgerLog.objects.create(note=note)
            context["message"] = note
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
        else:
            print(form.errors)
    else:
        context["form"] = forms.SpendResourcesForm(character_name_choices = list([
            (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
        ]))
        return render(request, "spend_resources.html", context)

@login_required
def character_approval(request):
    if not Player.objects.get(user=request.user).isViceroy:
        raise PermissionDenied()
    context = alwaysContext(request)
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
                LedgerLog.objects.create(note="%s received their first approval from viceroy %s." % (
                    str(character),
                    request.user.username)
                )
            else: # if second approval
                character.update(status="AC")
                character.update(approved=datetime.now())
                character.update(money=form.cleaned_data["character_starting_wealth"])
                character = character.first()
                LedgerLog.objects.create(note="%s received their second approval from viceroy %s." % (
                    str(character),
                    request.user.username)
                )
            tier = int(form.cleaned_data["character_tier"])
            viceroy = Player.objects.get(user=request.user)
            viceroy.viceroy_tokens += tier
            viceroy.save()
            note="%s received %d viceroy tokens for approving %s's tier %d character, %s." %(
                request.user.username,
                tier,
                player.user.username,
                tier,
                character.name
            )
            LedgerLog.objects.create(note=note)
            context["message"] = note
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
        else:
            print(form.errors)
    else:
        context["form"] = forms.CharacterApprovalForm()
        context["discords"] = [player.discord for player in Player.objects.all()]
        return render(request, "character_approval.html", context)

@login_required
def redeem_viceroy_rewards(request):
    if not Player.objects.get(user=request.user).isViceroy:
        raise PermissionDenied()
    context = alwaysContext(request)
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
            note="%s %s received %.3f gp (%.3f=>%.3f) by redeeming %d viceroy tokens." % (
                str(character),
                total_reward,
                character.money - total_reward,
                character.money,
                number_of_tokens
            )
            LedgerLog.objects.create(note=note)
            context["message"] = note
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
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
    context = alwaysContext(request)
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
            note="%s received %.3f gp (%.3f=>%.3f) and %.3f game's xp (%.3f=>%.3f) for completing game %s." % (
                str(character),
                form.cleaned_data["earned_gp"],
                character.money - form.cleaned_data["earned_gp"],
                character.money,
                form.cleaned_data["earned_xp"],
                character.xp - form.cleaned_data["earned_xp"],
                character.xp,
                form.cleaned_data["game_id"],
            )
            LedgerLog.objects.create(note=note)
            context["message"] = note
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
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
    context = alwaysContext(request)
    if request.method == 'POST':
        form = forms.ClaimGMRewardsForm(request.POST)

        if form.is_valid():
            player = Player.objects.get(user=request.user)
            player.gm_tokens += int(form.cleaned_data["gm_tokens"])
            player.save()
            note="%s received %d GM tokens for running game %s." % (
                request.user,
                int(form.cleaned_data["gm_tokens"]),
                form.cleaned_data["game_id"],
            )
            LedgerLog.objects.create(note=note)
            context["message"] = note
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.ClaimGMRewardsForm()
        return render(request, "claim_gm_rewards.html", context)

@login_required
def redeem_gm_rewards(request):
    if not Player.objects.get(user=request.user).isGM:
        raise PermissionDenied()
    context = alwaysContext(request)
    if request.method == 'POST':
        form = forms.RedeemGMRewardsForm(request.POST,
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ])
        )

        if form.is_valid():
            expenditure = form.cleaned_data["expenditure"]
            character = Character.objects.get(player__user=request.user, name=form.cleaned_data["character_name"])
            tier = get_tier(character)

            xp_reward = 0
            gp_reward = 0
            spent_tokens = 0
            if expenditure == "Full Game XP + Full Game GP":
                xp_reward = 1
                gp_reward = gold_by_tier(tier)
                spent_tokens = 8
            elif expenditure == "Half Game XP + Half Game GP":
                xp_reward = 0.5
                gp_reward = gold_by_tier(tier)/2
                spent_tokens = 4
            elif expenditure == "Full Game XP":
                xp_reward = 1
                spent_tokens = 6
            elif expenditure == "Half Game XP":
                xp_reward = 0.5
                spent_tokens = 3
            elif expenditure == "Full Game GP":
                gp_reward = gold_by_tier(tier)
                spent_tokens = 6
            elif expenditure == "Half Game GP":
                gp_reward = gold_by_tier(tier)/2
                spent_tokens = 3
            elif expenditure == "Other 6 token expenditure":
                spent_tokens = 6
            elif expenditure == "Other 3 token expenditure":
                spent_tokens = 3

            player = Player.objects.get(user=request.user)
            if player.gm_tokens < spent_tokens:
                context["message"] = "Insufficient GM tokens to do that! You tried to spend %d tokens but only have %d tokens." % (spent_tokens, player.gm_tokens)
                context["error"] = True
                context["logs"] = LedgerLog.objects.all().order_by("-created")
                return render(request, "ledger.html", context)
            player.gm_tokens -= spent_tokens
            player.save()

            character.xp += xp_reward
            character.money += gp_reward
            character.save()

            note="%s received %.3f gp (%.3f=>%.3f) and %.3f game XP (%.3f=>%.3f) by redeeming %d GM tokens: \"%s\"." % (
                str(character),
                gp_reward,
                character.money - gp_reward,
                character.money,
                xp_reward,
                character.xp - xp_reward,
                character.xp,
                spent_tokens,
                expenditure if "Other" not in expenditure else "%s [%s]" % (expenditure, form.cleaned_data["if_other_specify_here"])
            )
            LedgerLog.objects.create(note=note)
            context["message"] = note
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
            
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.RedeemGMRewardsForm(
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ]),
        )
        return render(request, "redeem_gm_rewards.html", context)

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

@login_required
def declare_a_trade(request):
    context = alwaysContext(request)
    if request.method == 'POST':
        form = forms.TradeForm(request.POST,
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ])
        )

        if form.is_valid():
            if form.cleaned_data["selling_or_buying"] == "Selling":
                seller = Character.objects.get(player__user=request.user, name=form.cleaned_data["my_character_name"])
                buyer = Character.objects.get(player__user__username=form.cleaned_data["other_player_username"], name=form.cleaned_data["other_player_character_name"])
                seller_verified = True
                buyer_verified = False
            else:
                buyer = Character.objects.get(player__user=request.user, name=form.cleaned_data["my_character_name"])
                seller = Character.objects.get(player__user__username=form.cleaned_data["other_player_username"], name=form.cleaned_data["other_player_character_name"])
                buyer_verified = True
                seller_verified = False
            trade = Trade.objects.create(
                seller = seller,
                seller_verified = seller_verified,
                buyer = buyer,
                buyer_verified = buyer_verified,
                money_amount = form.cleaned_data["money_amount"],
                what_was_purchased = form.cleaned_data["what_is_being_purchased"],
                other_stipulations = form.cleaned_data["other_stipulations"],
            )
            context["message"] = "You have created the pending trade: \"%s\". Your resources will be updated and the trade will show up on the ledger once the other player has verified it." % str(trade)
            context["logs"] = LedgerLog.objects.all().order_by("-created")
            return render(request, "ledger.html", context)
        else:
            print(form.errors)
    else:
        context = alwaysContext(request)
        context["form"] = forms.TradeForm(
            character_name_choices = list([
                (character.name, character.name) for character in Character.objects.filter(player__user=request.user)
            ])
        )
        return render(request, "declare_a_trade.html", context)

@login_required
def verify_a_trade(request):
    context = alwaysContext(request)
    context["trades_verify"] = Trade.objects.filter(
        ((Q(seller__player__user=request.user)
        & Q(seller_verified=False))
        | (Q(buyer__player__user=request.user)
        & Q(buyer_verified=False)))
        
        & (Q(rejected=False))
    ).order_by("-created")
    context["trades_pending"] = Trade.objects.filter(
        ((Q(seller__player__user=request.user)
        & Q(buyer_verified=False))
        | (Q(buyer__player__user=request.user)
        & Q(seller_verified=False)))

        & (Q(rejected=False))
    ).order_by("-created")
    return render(request, "verify_a_trade.html", context)

@login_required
def past_trades(request):
    context = alwaysContext(request)
    context["trades_past"] = Trade.objects.filter(
        (Q(seller__player__user=request.user)
        | Q(buyer__player__user=request.user))

        & ((Q(seller_verified=True) & Q(buyer_verified=True))
        | (Q(rejected=True)))
    ).order_by("-created")
    return render(request, "past_trades.html", context)

@login_required
def verify_trade_id(request, trade_id):
    context = alwaysContext(request)
    trade = Trade.objects.get(id=trade_id)

    # verify resources
    if trade.buyer.money < trade.money_amount:
        context["message"] = "The buyer does not have enough money for this trade to go through!"
        context["error"] = True
        context["logs"] = LedgerLog.objects.all().order_by("-created")
        return render(request, "ledger.html", context)

    # verify authorization
    if not trade.seller_verified and request.user == trade.seller.player.user:
        trade.seller_verified = True
    elif not trade.buyer_verified and request.user == trade.buyer.player.user:
        trade.buyer_verified = True
    else:
        raise PermissionDenied()
    trade.save()
    
    # update resources
    trade.buyer.money -= trade.money_amount
    trade.seller.money += trade.money_amount

    # log trade
    before_and_after = "%s has gone from %.3f gp to %.3f, and %s has gone from %.3f to %.3f." % (
        str(trade.buyer),
        trade.buyer.money + trade.money_amount,
        trade.buyer.money,
        str(trade.seller),
        trade.seller.money - trade.money_amount,
        trade.seller.money,
    )
    LedgerLog.objects.create(note="%s %s" % (str(trade), before_and_after))
    context["message"] = "The trade \"%s\" has been completed. %s" % (str(trade), before_and_after)
    context["logs"] = LedgerLog.objects.all().order_by("-created")
    return render(request, "ledger.html", context)

@login_required
def reject_trade_id(request, trade_id):
    context = alwaysContext(request)
    trade = Trade.objects.get(id=trade_id)

    # verify authorization
    if not trade.seller_verified and request.user == trade.seller.player.user:
        trade.rejected = True
    elif not trade.buyer_verified and request.user == trade.buyer.player.user:
        trade.rejected = True
    else:
        raise PermissionDenied()
    trade.save()
    
    # log trade
    context["message"] = "You have successfully rejected trade \"" + str(trade) + "\"."
    context["logs"] = LedgerLog.objects.all().order_by("-created")
    return render(request, "ledger.html", context)