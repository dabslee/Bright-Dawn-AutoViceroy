import datetime
import pytz
from django.shortcuts import render
from resource_tracker.models import Player

def lastSundayMidnight():
    today = datetime.date.today()
    idx = (today.weekday() + 1) % 7
    last_sunday = today - datetime.timedelta(idx)
    last_sunday = datetime.datetime.combine(last_sunday, datetime.datetime.min.time())
    last_sunday = pytz.timezone("US/Eastern").localize(last_sunday)
    return last_sunday

def alwaysContext(request):
    if request.user.is_authenticated:
        user_player = Player.objects.get(user=request.user)
        if user_player.last_spellcaster_claim < lastSundayMidnight():
            user_player.spellcaster_hours = 24
            user_player.last_spellcaster_claim = datetime.datetime.now()
            user_player.save()
        return {
            "user_player" : user_player
        }

def home(request):
    return render(request, "home.html", alwaysContext(request))

def success(request):
    return render(request, "success.html", alwaysContext(request))