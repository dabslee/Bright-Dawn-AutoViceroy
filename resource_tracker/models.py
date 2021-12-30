# Create your models here.
from django.conf import settings
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields import related

# Create your models here.
class Player(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    discord = models.CharField(max_length=50)
    downtime = models.PositiveIntegerField(default=0)
    last_downtime_claim = models.DateTimeField()
    spellcaster_hours = models.FloatField(default=0)
    last_spellcaster_claim = models.DateTimeField()

    isViceroy = models.BooleanField(default=False)
    viceroy_tokens = models.PositiveIntegerField(default=0)
    isGM = models.BooleanField(default=False)
    gm_tokens = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username

class Character(models.Model):
    created = models.DateTimeField(null=True, auto_now_add=True)
    approved = models.DateTimeField(null=True)
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    money = models.FloatField(default=0)
    xp = models.FloatField(default=0)
    status = models.CharField(
        max_length=2,
        choices=[
            ("PA", "Pre-Approval"),
            ("AC", "Active"),
            ("RD", "Retired or Dead"),
        ],
        default="PA"
    )

    def __str__(self):
        return "%s (%s)" % (self.name, self.player.user.username)

class Debt(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    debtor = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="debt_of_debtor"
    )
    creditor = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="debt_of_creditor"
    )
    amount = models.FloatField()

    def __str__(self):
        return "%s owes %s %.3fgp" % (self.debtor, self.creditor, self.amount)

class Trade(models.Model):
    seller = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="trade_of_seller")
    seller_verified = models.BooleanField()
    buyer = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="trade_of_buyer")
    buyer_verified = models.BooleanField()
    money_amount = models.FloatField()
    what_was_purchased = models.TextField(max_length=1000)
    other_stipulations = models.TextField(max_length=1000)

class LedgerLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=500)
    tag = models.CharField(max_length=50)

    def __str__(self):
        return "[" + str(self.created) + "]\t" + self.note