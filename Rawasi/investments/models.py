from django.db import models
from accounts.models import CustomUser, Investor
from investment_fund.models import InvestmentFund
from datetime import datetime

# Create your models here.

class InvestorFund(models.Model):
    fund = models.ForeignKey(InvestmentFund, on_delete=models.CASCADE, related_name='fund_investments') 
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='investments')  
    amount_invested = models.DecimalField(max_digits=12, decimal_places=2)
    invested_at = models.DateTimeField(auto_now_add=True)  
    status = models.CharField(max_length=100, choices=[('Completed', 'Completed'), ('Pending', 'Pending')], default='Pending') 

    def __str__(self):
        return f'{self.investor.user.username} in {self.fund.name}'


class InvestmentOpportunity(models.Model):
    INVESTMENT_TYPE_CHOICES = [
        ('Stocks', 'Stocks'),
        ('Real Estate', 'Real Estate')
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    company_name = models.CharField(max_length=255)
    fund = models.ForeignKey(InvestmentFund, on_delete=models.CASCADE, related_name='investment_opportunities') 
    investment_type = models.CharField(max_length=100, choices=INVESTMENT_TYPE_CHOICES, blank=False, null=False)
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    expected_return = models.FloatField()
    status = models.CharField(max_length=100, choices=[('Open', 'Open'), ('Closed', 'Closed'), ('Completed', 'Completed')], default='Open')
    pdf_file = models.FileField(upload_to='investment_opportunities/pdf/', blank=True, null=True)
    image = models.ImageField(upload_to='investment_opportunities/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.title


class Voting(models.Model):
    APPROVAL_CHOICES = [
        ('Accepted', 'Accepted'), 
        ('Rejected', 'Rejected'),  
    ]

    opportunity = models.ForeignKey('InvestmentOpportunity', on_delete=models.CASCADE, related_name='votes')  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) 
    vote = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='Rejected') 
    required_approval_percentage = models.FloatField(default=70.0)  
    voting_start_time = models.DateTimeField(default=datetime.now)
    voting_end_time = models.DateTimeField(default=datetime.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'opportunity')  

    def __str__(self):
        return f"{self.user.username} voted {self.vote} on {self.opportunity.title}"

class BuySellTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('Buy', 'Buy'), 
        ('Sell', 'Sell'), 
    ]
    opportunity = models.ForeignKey(InvestmentOpportunity, on_delete=models.CASCADE, related_name='buy_sell_transactions') 
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE_CHOICES) 
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True) 
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],default='Pending') 
    required_approval_percentage = models.FloatField(default=70.0)

    def __str__(self):
        return f"{self.get_transaction_type_display()} Transaction for {self.opportunity.title}"

